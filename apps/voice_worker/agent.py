import asyncio
import json
import logging
import os
import re
from dataclasses import dataclass
from enum import Enum
from typing import Any, Awaitable, Callable

import aiohttp
from dotenv import load_dotenv
from livekit import api
from livekit import agents
from livekit.agents import Agent, AgentSession, JobContext, StopResponse, TurnHandlingOptions
from livekit.plugins import deepgram, groq, sarvam, silero

load_dotenv()

logger = logging.getLogger("ringiq.voice_worker")
DEFAULT_API_BASE_URL = "http://127.0.0.1:8000"
AGENT_READY_ATTRIBUTE = "ringiq.agent_ready"
PREWARMED_VAD_KEY = "ringiq.silero_vad"


class _OpeningStage(str, Enum):
    AWAITING_REPLY = "awaiting_reply"
    AWAITING_IDENTITY_CONFIRMATION = "awaiting_identity_confirmation"
    COMPLETE = "complete"


@dataclass(frozen=True)
class _OpeningResponse:
    text: str
    completes_opening: bool = False


@dataclass(frozen=True)
class _RecordingHandle:
    egress_id: str
    storage_uri: str
    playback_url: str | None


def _call_context(metadata: dict[str, Any]) -> dict[str, Any]:
    raw_context = metadata.get("agent_context_json")
    try:
        context = json.loads(raw_context) if isinstance(raw_context, str) else {}
    except json.JSONDecodeError:
        context = {}
    return context if isinstance(context, dict) else {}


def _normalized_transcript(transcript: str) -> str:
    return re.sub(r"[^\w\u0900-\u097f]+", " ", transcript.casefold()).strip()


def _identity_confirmation(transcript: str) -> bool | None:
    normalized = _normalized_transcript(transcript)
    negative_phrases = (
        "गलत नंबर",
        "नहीं",
        "नही",
        "galat number",
        "nahin",
        "nahi",
        "not here",
        "not speaking",
        "wrong number",
    )
    if normalized == "no" or any(phrase in normalized for phrase in negative_phrases):
        return False

    positive_phrases = (
        "हाँ",
        "हां",
        "जी हाँ",
        "जी हां",
        "बोल रहा",
        "बोल रही",
        "मैं ही",
        "bol raha hoon",
        "bol rahi hoon",
        "main hi hoon",
        "speaking",
        "this is",
    )
    positive_words = {"haan", "han", "ha", "yes", "yeah", "yep", "ji"}
    words = set(normalized.split())
    if words.intersection(positive_words) or any(
        phrase in normalized for phrase in positive_phrases
    ):
        return True
    return None


class _CallOpeningHarness:
    def __init__(self, metadata: dict[str, Any]) -> None:
        context = _call_context(metadata)
        lead = context.get("lead") if isinstance(context.get("lead"), dict) else {}
        self.organization_name = str(context.get("organization_name") or "the business")
        self.lead_name = str(lead.get("name") or "").strip()
        self.stage = _OpeningStage.AWAITING_REPLY

    def respond(self, transcript: str) -> _OpeningResponse | None:
        if not any(character.isalnum() for character in transcript):
            return None
        if self.stage is _OpeningStage.COMPLETE:
            return None

        if self.stage is _OpeningStage.AWAITING_REPLY:
            self.stage = _OpeningStage.AWAITING_IDENTITY_CONFIRMATION
            if self.lead_name:
                return _OpeningResponse(
                    f"Namaste, kya meri baat {self.lead_name} ji se ho rahi hai?"
                )
            return _OpeningResponse("Namaste, kya main sahi vyakti se baat kar raha hoon?")

        confirmation = _identity_confirmation(transcript)
        if confirmation is True:
            self.stage = _OpeningStage.COMPLETE
            return _OpeningResponse(
                f"Main {self.organization_name} ka assistant bol raha hoon; "
                "aapki enquiry ke silsile mein call kiya hai. "
                "Kya abhi ek minute baat kar sakte hain?",
                completes_opening=True,
            )
        if confirmation is False:
            if self.lead_name:
                return _OpeningResponse(
                    f"Theek hai. Kya {self.lead_name} ji se baat ho sakti hai?"
                )
            return _OpeningResponse("Theek hai. Kya main sahi vyakti se baat kar sakta hoon?")
        if self.lead_name:
            return _OpeningResponse(
                f"Maaf kijiye, kya aap {self.lead_name} ji bol rahe hain?"
            )
        return _OpeningResponse("Maaf kijiye, kya main sahi vyakti se baat kar raha hoon?")


class _QualificationTurnHarness:
    _RESPONSE_CONTRACT = """
Response contract for this turn:
- First briefly acknowledge the customer's concrete answer or newly provided facts in the same language or Hindi-English mix they used.
- Make the acknowledgment specific. For example, for "mera budget 2 crore ka hai", say that the 2 crore budget has been noted; do not use only a generic "okay".
- After acknowledging, continue naturally by asking exactly one useful next question about a genuinely missing qualification detail.
- Never ask again for a detail the customer just supplied or that already exists in the conversation.
- If the customer primarily asked a question, answer it before advancing. If they declined or want to end the call, acknowledge that and close politely instead of asking another qualification question.
- Keep the complete spoken response to one or two short sentences.
""".strip()
    _CALLBACK_CLARIFICATION_CONTRACT = """
The customer is answering the callback question, but their preference is unclear. Briefly acknowledge what they said and ask only whether they want a callback from the sales team. Do not return to any earlier qualification question.
""".strip()
    _CALLBACK_MARKERS = (
        "callback",
        "call back",
        "sales team",
        "sales representative",
        "वापस कॉल",
        "कॉल बैक",
        "सेल्स टीम",
    )
    _QUESTION_CUES = (
        "?",
        "kya ",
        "chahenge",
        "chaahenge",
        "would you",
        "do you",
        "should we",
        "क्या ",
        "चाहेंगे",
    )

    @staticmethod
    def _last_assistant_text(turn_ctx: Any) -> str:
        return next(
            (
                message.text_content or ""
                for message in reversed(turn_ctx.messages())
                if message.role == "assistant"
            ),
            "",
        )

    def is_answering_callback_question(self, turn_ctx: Any) -> bool:
        previous_response = self._last_assistant_text(turn_ctx).casefold()
        has_callback_marker = any(
            marker in previous_response for marker in self._CALLBACK_MARKERS
        )
        has_question_cue = any(cue in previous_response for cue in self._QUESTION_CUES)
        return has_callback_marker and has_question_cue

    def callback_closing_response(self, turn_ctx: Any, transcript: str) -> str | None:
        if not self.is_answering_callback_question(turn_ctx):
            return None
        confirmation = _callback_confirmation(transcript)
        if confirmation is True:
            return (
                "Bilkul, hamari sales team aapko callback karegi. "
                "Aapke samay aur jaankari ke liye dhanyavaad."
            )
        if confirmation is False:
            return (
                "Theek hai, callback ki zarurat nahi hai. "
                "Aapke samay aur jaankari ke liye dhanyavaad."
            )
        return None

    def prepare_response(self, turn_ctx: Any, transcript: str) -> bool:
        if not any(character.isalnum() for character in transcript):
            return False
        contract = (
            self._CALLBACK_CLARIFICATION_CONTRACT
            if self.is_answering_callback_question(turn_ctx)
            else self._RESPONSE_CONTRACT
        )
        turn_ctx.add_message(role="system", content=contract)
        return True


def _callback_confirmation(transcript: str) -> bool | None:
    normalized = _normalized_transcript(transcript)
    negative_phrases = (
        "नहीं",
        "नही",
        "जरूरत नहीं",
        "ज़रूरत नहीं",
        "मत करिए",
        "mat kariye",
        "zarurat nahi",
        "no callback",
        "do not call",
        "dont call",
        "not required",
    )
    if normalized == "no" or any(phrase in normalized for phrase in negative_phrases):
        return False

    positive_phrases = (
        "हाँ",
        "हां",
        "कर दीजिए",
        "कर दीजिये",
        "zaroor",
        "kar dijiye",
        "please call",
        "call me",
    )
    positive_words = {"haan", "han", "ha", "yes", "yeah", "yep", "sure", "ji"}
    words = set(normalized.split())
    if words.intersection(positive_words) or any(
        phrase in normalized for phrase in positive_phrases
    ):
        return True
    return None


def _duration_limit_closing_message(
    language: str | None,
    transcript: str,
) -> str:
    language_code = (language or "").casefold()
    is_hindi = language_code.startswith("hi") or bool(
        re.search(r"[\u0900-\u097f]", transcript)
    )
    if is_hindi:
        return (
            "Aapki interest ke liye dhanyavaad. "
            "Hamari sales team aapko jaldi callback karegi."
        )
    return (
        "Thank you for your interest. "
        "Our sales team will call you back shortly."
    )


class _RingIQVoiceAgent(Agent):
    def __init__(
        self,
        metadata: dict[str, Any],
        *,
        end_call_fnc: Callable[[], Awaitable[None]] | None = None,
    ) -> None:
        super().__init__(instructions=_agent_instructions(metadata))
        self.opening = _CallOpeningHarness(metadata)
        self.qualification = _QualificationTurnHarness()
        self._end_call_fnc = end_call_fnc
        self._end_call_task: asyncio.Task[None] | None = None

    async def _remember_user_turn(self, new_message: Any) -> None:
        persistent_context = self.chat_ctx.copy()
        persistent_context.items.append(new_message)
        await self.update_chat_ctx(persistent_context)

    async def _finish_call_after_playout(self, speech_handle: Any) -> None:
        await speech_handle.wait_for_playout()
        if self._end_call_fnc is not None:
            await self._end_call_fnc()
        else:
            self.session.shutdown(drain=False)

    async def on_user_turn_completed(self, turn_ctx: Any, new_message: Any) -> None:
        if self.opening.stage is _OpeningStage.COMPLETE:
            transcript = new_message.text_content or ""
            closing_response = self.qualification.callback_closing_response(
                turn_ctx,
                transcript,
            )
            if closing_response is not None:
                await self._remember_user_turn(new_message)
                speech_handle = self.session.say(
                    closing_response,
                    allow_interruptions=False,
                )
                self._end_call_task = asyncio.create_task(
                    self._finish_call_after_playout(speech_handle)
                )
                raise StopResponse()
            self.qualification.prepare_response(turn_ctx, transcript)
            return

        response = self.opening.respond(new_message.text_content or "")
        if response is None:
            raise StopResponse()

        # StopResponse prevents LiveKit's generic LLM reply, so retain this user turn explicitly.
        await self._remember_user_turn(new_message)
        self.session.say(response.text, allow_interruptions=True)
        raise StopResponse()


def _csv_env(name: str, default: str) -> list[str]:
    value = os.getenv(name, default)
    return [item.strip() for item in value.split(",") if item.strip()]


def _bool_env(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _bounded_int_env(name: str, default: int, *, minimum: int, maximum: int) -> int:
    raw_value = os.getenv(name)
    value = int(raw_value) if raw_value is not None else default
    bounded_value = min(max(value, minimum), maximum)
    if bounded_value != value:
        logger.warning(
            "%s=%s is outside the supported range %s-%s; using %s",
            name,
            value,
            minimum,
            maximum,
            bounded_value,
        )
    return bounded_value


def _metrics_metadata(metrics: dict[str, Any]) -> dict[str, str]:
    return {key: str(value) for key, value in metrics.items() if value is not None}


def _metadata(ctx: JobContext) -> dict[str, Any]:
    raw_metadata = getattr(ctx.job, "metadata", "") or "{}"
    try:
        parsed = json.loads(raw_metadata)
    except json.JSONDecodeError:
        logger.warning("Received non-JSON job metadata: %s", raw_metadata)
        return {}
    if isinstance(parsed, dict):
        return parsed
    return {}


def _agent_instructions(metadata: dict[str, Any]) -> str:
    context = _call_context(metadata)
    if isinstance(context, dict) and context:
        organization_name = context.get("organization_name", "the business")
        lead = context.get("lead") if isinstance(context.get("lead"), dict) else {}
        knowledge = context.get("knowledge_base") if isinstance(context.get("knowledge_base"), dict) else {}
        return f"""
You are a voice representative calling on behalf of {organization_name}.

Lead context:
{json.dumps(lead, ensure_ascii=False, default=str)}

Approved private business knowledge:
{json.dumps(knowledge, ensure_ascii=False, default=str)}

Conversation rules:
- You represent {organization_name} throughout the conversation.
- Never describe yourself as an AI assistant and never mention RingIQ to the lead.
- The opening greeting, identity confirmation, and introduction have already been handled before you respond.
- Never restart the greeting, reconfirm the lead's identity, or reintroduce yourself unless the lead explicitly asks.
- Always use masculine Hindi self-reference, such as "bol raha hoon", never "bol rahi hoon".
- Keep every response to one or two short sentences suitable for a phone call.
- Speak in simple English, Hindi, or mixed Hindi-English based on the lead's language.
- Use only the approved private business knowledge above for factual claims.
- Do not run a fixed questionnaire. Ask at most one useful question per turn.
- Maintain a silent ledger of facts already provided in the lead context or conversation.
- For real estate, the ledger includes area or locality, budget or price range, property type, purchase timeline, and callback preference.
- Extract every fact from the lead's full utterance, even when they provide several answers together or answer a different question.
- Never ask for a fact that is already in the ledger. A synonym counts: location, locality, sector, and area are the same fact.
- When the lead provides multiple facts such as area and budget, briefly acknowledge them and move to one genuinely missing detail.
- Only clarify a captured fact when it is contradictory or too ambiguous to use. If corrected, replace the old value.
- Do not invent availability, pricing, discounts, approvals, dates, or policies.
- If the approved knowledge does not answer a question, say the sales team will confirm it.
- If the lead is not interested, politely end the conversation.
""".strip()
    phone_number = metadata.get("phone_number", "the lead")
    return f"""
You are a real-estate lead qualification voice representative.

You are calling {phone_number} for a short demo conversation.

Conversation rules:
- The opening greeting, identity confirmation, and introduction have already been handled.
- Never restart the greeting, reconfirm identity, or reintroduce yourself unless asked.
- Never describe yourself as an AI assistant.
- Always use masculine Hindi self-reference, such as "bol raha hoon", never "bol rahi hoon".
- Keep responses short and natural for a phone call.
- Speak in simple English, Hindi, or mixed Hindi-English depending on the user's language.
- Ask whether the person is interested in discussing property options.
- If they are interested, silently track preferred area, budget, property type, and callback preference.
- Extract all details supplied in an utterance and never ask for an already captured detail.
- Ask at most one missing detail per turn instead of running a fixed questionnaire.
- If they are not interested, politely end the call.
- Do not claim real project availability, pricing, discounts, legal approvals, or possession dates.
- If asked for details you do not know, say a sales representative can confirm that.
    """.strip()


def _initial_greeting(metadata: dict[str, Any]) -> str:
    return "Hello?"


async def _emit_pipeline_event(
    metadata: dict[str, Any],
    *,
    stage: str,
    message: str,
    provider: str | None = None,
    status: str = "info",
    extra_metadata: dict[str, str] | None = None,
) -> None:
    api_base_url = os.getenv("RINGIQ_API_BASE_URL", DEFAULT_API_BASE_URL).rstrip("/")
    payload = {
        "call_id": str(metadata.get("call_id", "unknown")),
        "room_name": str(metadata.get("room_name", "unknown")),
        "stage": stage,
        "provider": provider,
        "status": status,
        "message": message,
        "metadata": extra_metadata or {},
    }

    try:
        async with aiohttp.ClientSession() as http:
            async with http.post(f"{api_base_url}/demo/pipeline-events", json=payload, timeout=3) as response:
                if response.status >= 300:
                    logger.warning("Pipeline event logging failed with status=%s payload=%s", response.status, payload)
    except Exception as exc:
        logger.warning("Pipeline event logging failed: %s", exc)


def _schedule_pipeline_event(
    metadata: dict[str, Any],
    *,
    stage: str,
    message: str,
    provider: str | None = None,
    status: str = "info",
    extra_metadata: dict[str, str] | None = None,
) -> None:
    asyncio.create_task(
        _emit_pipeline_event(
            metadata,
            stage=stage,
            message=message,
            provider=provider,
            status=status,
            extra_metadata=extra_metadata,
        )
    )


def _conversation_transcript(session: AgentSession) -> list[dict[str, Any]]:
    history = getattr(session, "history", None)
    turns: list[dict[str, Any]] = []
    for item in getattr(history, "items", []):
        role = getattr(item, "role", "")
        role = getattr(role, "value", role)
        text = (getattr(item, "text_content", None) or "").strip()
        if role not in {"user", "assistant"} or not text:
            continue
        turns.append(
            {
                "role": role,
                "text": text,
                "interrupted": bool(getattr(item, "interrupted", False)),
            }
        )
    return turns[-500:]


async def _store_call_artifacts(
    metadata: dict[str, Any],
    payload: dict[str, Any],
) -> bool:
    call_attempt_id = metadata.get("call_attempt_id")
    internal_api_key = os.getenv("RINGIQ_INTERNAL_API_KEY")
    if not call_attempt_id or not internal_api_key:
        return False
    api_base_url = os.getenv("RINGIQ_API_BASE_URL", DEFAULT_API_BASE_URL).rstrip("/")
    try:
        async with aiohttp.ClientSession() as http:
            async with http.post(
                f"{api_base_url}/v1/internal/call-attempts/{call_attempt_id}/artifacts",
                json=payload,
                headers={"X-RingIQ-Internal-Key": internal_api_key},
                timeout=5,
            ) as response:
                if response.status >= 300:
                    logger.warning(
                        "Call artifact update failed status=%s attempt_id=%s",
                        response.status,
                        call_attempt_id,
                    )
                    return False
    except Exception as exc:
        logger.warning(
            "Call artifact update failed attempt_id=%s error=%s",
            call_attempt_id,
            exc,
        )
        return False
    return True


async def _start_call_recording(
    ctx: JobContext,
    metadata: dict[str, Any],
) -> _RecordingHandle | None:
    if not _bool_env("LIVEKIT_RECORDING_ENABLED", False):
        return None

    required_names = (
        "LIVEKIT_RECORDING_S3_BUCKET",
        "LIVEKIT_RECORDING_S3_REGION",
        "LIVEKIT_RECORDING_S3_ACCESS_KEY",
        "LIVEKIT_RECORDING_S3_SECRET",
    )
    config = {name: os.getenv(name, "").strip() for name in required_names}
    missing = [name for name, value in config.items() if not value]
    if missing:
        logger.error("Recording disabled for this call; missing settings=%s", missing)
        return None

    tenant_id = re.sub(r"[^A-Za-z0-9_-]", "", str(metadata.get("tenant_id", "unknown")))
    call_id = re.sub(
        r"[^A-Za-z0-9_-]",
        "",
        str(metadata.get("call_attempt_id") or metadata.get("call_id") or ctx.job.id),
    )
    prefix = os.getenv("LIVEKIT_RECORDING_PATH_PREFIX", "ringiq/recordings").strip("/")
    filepath = f"{prefix}/{tenant_id}/{call_id}.mp3"
    public_base_url = os.getenv("LIVEKIT_RECORDING_PUBLIC_BASE_URL", "").rstrip("/")
    playback_url = f"{public_base_url}/{filepath}" if public_base_url else None
    storage_uri = f"s3://{config['LIVEKIT_RECORDING_S3_BUCKET']}/{filepath}"

    lkapi = api.LiveKitAPI(
        url=os.getenv("LIVEKIT_URL"),
        api_key=os.getenv("LIVEKIT_API_KEY"),
        api_secret=os.getenv("LIVEKIT_API_SECRET"),
    )
    try:
        response = await lkapi.egress.start_room_composite_egress(
            api.RoomCompositeEgressRequest(
                room_name=ctx.room.name,
                audio_only=True,
                audio_mixing=api.AudioMixing.DUAL_CHANNEL_AGENT,
                file_outputs=[
                    api.EncodedFileOutput(
                        file_type=api.EncodedFileType.MP3,
                        filepath=filepath,
                        s3=api.S3Upload(
                            access_key=config["LIVEKIT_RECORDING_S3_ACCESS_KEY"],
                            secret=config["LIVEKIT_RECORDING_S3_SECRET"],
                            region=config["LIVEKIT_RECORDING_S3_REGION"],
                            endpoint=os.getenv("LIVEKIT_RECORDING_S3_ENDPOINT", ""),
                            bucket=config["LIVEKIT_RECORDING_S3_BUCKET"],
                            force_path_style=_bool_env(
                                "LIVEKIT_RECORDING_S3_FORCE_PATH_STYLE", False
                            ),
                        ),
                    )
                ],
            )
        )
    except Exception as exc:
        logger.warning("LiveKit recording could not start room=%s error=%s", ctx.room.name, exc)
        await _store_call_artifacts(metadata, {"recording_status": "failed"})
        return None
    finally:
        await lkapi.aclose()

    handle = _RecordingHandle(
        egress_id=response.egress_id,
        storage_uri=storage_uri,
        playback_url=playback_url,
    )
    await _store_call_artifacts(
        metadata,
        {
            "recording_egress_id": handle.egress_id,
            "recording_status": "recording",
            "recording_storage_uri": handle.storage_uri,
            "recording_url": handle.playback_url,
        },
    )
    logger.info("LiveKit recording started room=%s egress_id=%s", ctx.room.name, handle.egress_id)
    return handle


async def _stop_call_recording(handle: _RecordingHandle) -> str:
    lkapi = api.LiveKitAPI(
        url=os.getenv("LIVEKIT_URL"),
        api_key=os.getenv("LIVEKIT_API_KEY"),
        api_secret=os.getenv("LIVEKIT_API_SECRET"),
    )
    try:
        response = await lkapi.egress.stop_egress(
            api.StopEgressRequest(egress_id=handle.egress_id)
        )
        timeout_seconds = float(
            os.getenv("LIVEKIT_RECORDING_FINALIZE_TIMEOUT_SECONDS", "30")
        )
        deadline = asyncio.get_running_loop().time() + timeout_seconds
        while True:
            status_name = api.EgressStatus.Name(response.status)
            if status_name == "EGRESS_COMPLETE":
                logger.info("LiveKit recording finalized egress_id=%s", handle.egress_id)
                return "available"
            if status_name in {"EGRESS_FAILED", "EGRESS_ABORTED", "EGRESS_LIMIT_REACHED"}:
                logger.warning(
                    "LiveKit recording failed egress_id=%s status=%s error=%s",
                    handle.egress_id,
                    status_name,
                    response.error,
                )
                return "failed"
            if asyncio.get_running_loop().time() >= deadline:
                logger.warning(
                    "LiveKit recording finalization timed out egress_id=%s status=%s",
                    handle.egress_id,
                    status_name,
                )
                return "failed"
            await asyncio.sleep(1)
            result = await lkapi.egress.list_egress(
                api.ListEgressRequest(egress_id=handle.egress_id)
            )
            if not result.items:
                logger.warning(
                    "LiveKit recording disappeared during finalization egress_id=%s",
                    handle.egress_id,
                )
                return "failed"
            response = result.items[0]
    except Exception as exc:
        logger.warning(
            "LiveKit recording could not be finalized egress_id=%s error=%s",
            handle.egress_id,
            exc,
        )
        return "failed"
    finally:
        await lkapi.aclose()


def prewarm(proc: agents.JobProcess) -> None:
    logger.info("Prewarming Silero VAD for the next voice job")
    proc.userdata[PREWARMED_VAD_KEY] = silero.VAD.load()


async def _report_call_result(
    metadata: dict[str, Any],
    result_status: str,
    *,
    terminal_reason: str | None = None,
) -> None:
    call_attempt_id = metadata.get("call_attempt_id")
    internal_api_key = os.getenv("RINGIQ_INTERNAL_API_KEY")
    if not call_attempt_id or not internal_api_key:
        return
    api_base_url = os.getenv("RINGIQ_API_BASE_URL", DEFAULT_API_BASE_URL).rstrip("/")
    try:
        async with aiohttp.ClientSession() as http:
            async with http.post(
                f"{api_base_url}/v1/internal/call-attempts/{call_attempt_id}/result",
                json={
                    "status": result_status,
                    **(
                        {"terminal_reason": terminal_reason}
                        if terminal_reason is not None
                        else {}
                    ),
                },
                headers={"X-RingIQ-Internal-Key": internal_api_key},
                timeout=3,
            ) as response:
                if response.status >= 300 and response.status != 409:
                    logger.warning(
                        "Call result update failed status=%s attempt_id=%s",
                        response.status,
                        call_attempt_id,
                    )
    except Exception as exc:
        logger.warning("Call result update failed attempt_id=%s error=%s", call_attempt_id, exc)


async def entrypoint(ctx: JobContext) -> None:
    metadata = _metadata(ctx)
    metadata.setdefault("room_name", ctx.room.name)
    logger.info("Starting RingIQ voice worker for call_id=%s room=%s", metadata.get("call_id"), ctx.room.name)
    sip_participant_identity = metadata.get("sip_participant_identity")
    _schedule_pipeline_event(
        metadata,
        stage="worker_started",
        provider="LiveKit Agents",
        message="Voice worker job started",
        extra_metadata={"agent_name": os.getenv("LIVEKIT_AGENT_NAME", "ringiq-demo-agent")},
    )

    deepgram_model = os.getenv("DEEPGRAM_MODEL", "flux-general-multi")
    deepgram_language_hints = _csv_env("DEEPGRAM_LANGUAGE_HINTS", "en,hi")
    deepgram_eager_eot_threshold = float(os.getenv("DEEPGRAM_EAGER_EOT_THRESHOLD", "0.4"))
    deepgram_eot_threshold = float(os.getenv("DEEPGRAM_EOT_THRESHOLD", "0.65"))
    deepgram_eot_timeout_ms = int(os.getenv("DEEPGRAM_EOT_TIMEOUT_MS", "1200"))
    groq_model = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")
    groq_reasoning_effort = os.getenv("GROQ_REASONING_EFFORT", "low").strip().lower()
    groq_max_completion_tokens = int(os.getenv("GROQ_MAX_COMPLETION_TOKENS", "256"))
    sarvam_model = os.getenv("SARVAM_TTS_MODEL", "bulbul:v3")
    sarvam_speaker = os.getenv("SARVAM_TTS_SPEAKER", "shubh").strip().lower()
    sarvam_language = os.getenv("SARVAM_TARGET_LANGUAGE_CODE", "hi-IN")
    sarvam_sample_rate = int(os.getenv("SARVAM_TTS_SAMPLE_RATE", "16000"))
    sarvam_min_buffer_size = _bounded_int_env(
        "SARVAM_TTS_MIN_BUFFER_SIZE", 30, minimum=30, maximum=200
    )
    sarvam_max_chunk_length = _bounded_int_env(
        "SARVAM_TTS_MAX_CHUNK_LENGTH", 100, minimum=50, maximum=500
    )
    sarvam_output_audio_codec = os.getenv("SARVAM_TTS_OUTPUT_AUDIO_CODEC", "linear16")
    preemptive_tts = _bool_env("LIVEKIT_PREEMPTIVE_TTS", True)
    sip_participant_wait_timeout = float(
        os.getenv("LIVEKIT_SIP_PARTICIPANT_WAIT_TIMEOUT_SECONDS", "60")
    )
    call_idle_timeout = max(
        1.0, float(os.getenv("LIVEKIT_CALL_IDLE_TIMEOUT_SECONDS", "15"))
    )
    call_max_duration = max(
        call_idle_timeout,
        float(os.getenv("LIVEKIT_CALL_MAX_DURATION_SECONDS", "180")),
    )

    _schedule_pipeline_event(
        metadata,
        stage="stt_configured",
        provider="Deepgram",
        message="STT configured",
        extra_metadata={
            "model": deepgram_model,
            "language_hints": ",".join(deepgram_language_hints),
            "eager_eot_threshold": str(deepgram_eager_eot_threshold),
            "eot_threshold": str(deepgram_eot_threshold),
            "eot_timeout_ms": str(deepgram_eot_timeout_ms),
        },
    )
    _schedule_pipeline_event(
        metadata,
        stage="llm_configured",
        provider="Groq",
        message="LLM configured",
        extra_metadata={
            "model": groq_model,
            "reasoning_effort": groq_reasoning_effort,
            "max_completion_tokens": str(groq_max_completion_tokens),
        },
    )
    _schedule_pipeline_event(
        metadata,
        stage="tts_configured",
        provider="Sarvam",
        message="TTS configured",
        extra_metadata={
            "model": sarvam_model,
            "speaker": sarvam_speaker,
            "language": sarvam_language,
            "sample_rate": str(sarvam_sample_rate),
            "min_buffer_size": str(sarvam_min_buffer_size),
            "max_chunk_length": str(sarvam_max_chunk_length),
            "output_audio_codec": sarvam_output_audio_codec,
        },
    )

    llm_options: dict[str, Any] = {
        "model": groq_model,
        "temperature": float(os.getenv("GROQ_TEMPERATURE", "0.4")),
        "max_completion_tokens": groq_max_completion_tokens,
    }
    if groq_model.startswith("openai/gpt-oss"):
        llm_options["reasoning_effort"] = groq_reasoning_effort

    session = AgentSession(
        vad=ctx.proc.userdata.get(PREWARMED_VAD_KEY) or silero.VAD.load(),
        turn_handling=TurnHandlingOptions(
            turn_detection="stt",
            preemptive_generation={
                "enabled": True,
                "preemptive_tts": preemptive_tts,
                "max_retries": 2,
            },
        ),
        stt=deepgram.STTv2(
            model=deepgram_model,
            eager_eot_threshold=deepgram_eager_eot_threshold,
            language_hint=deepgram_language_hints,
            eot_threshold=deepgram_eot_threshold,
            eot_timeout_ms=deepgram_eot_timeout_ms,
        ),
        llm=groq.LLM(**llm_options),
        tts=sarvam.TTS(
            target_language_code=sarvam_language,
            model=sarvam_model,
            speaker=sarvam_speaker,
            speech_sample_rate=sarvam_sample_rate,
            pace=float(os.getenv("SARVAM_TTS_PACE", "1.0")),
            min_buffer_size=sarvam_min_buffer_size,
            max_chunk_length=sarvam_max_chunk_length,
            output_audio_codec=sarvam_output_audio_codec,
        ),
    )
    recording_task: asyncio.Task[_RecordingHandle | None] | None = None
    artifacts_persisted = False
    artifacts_lock = asyncio.Lock()
    call_ending = asyncio.Event()
    activity_event = asyncio.Event()
    last_activity_at = asyncio.get_running_loop().time()
    speaking = {"user": False, "agent": False}
    customer_language: str | None = None
    customer_transcript = ""
    lifecycle_tasks: list[asyncio.Task[None]] = []

    def _mark_activity() -> None:
        nonlocal last_activity_at
        last_activity_at = asyncio.get_running_loop().time()
        activity_event.set()

    async def _cancel_lifecycle_tasks() -> None:
        current_task = asyncio.current_task()
        pending = [task for task in lifecycle_tasks if task is not current_task]
        for task in pending:
            task.cancel()
        if pending:
            await asyncio.gather(*pending, return_exceptions=True)

    async def _persist_call_artifacts() -> None:
        nonlocal artifacts_persisted
        async with artifacts_lock:
            if artifacts_persisted:
                return
            artifacts_persisted = True
            try:
                recording = await recording_task if recording_task is not None else None
            except asyncio.CancelledError:
                recording = None
            except Exception as exc:
                logger.warning("Recording task failed during shutdown: %s", exc)
                recording = None
            payload: dict[str, Any] = {"transcript": _conversation_transcript(session)}
            if recording is not None:
                payload.update(
                    {
                        "recording_egress_id": recording.egress_id,
                        "recording_status": await _stop_call_recording(recording),
                        "recording_storage_uri": recording.storage_uri,
                        "recording_url": recording.playback_url,
                    }
                )
            await _store_call_artifacts(metadata, payload)

    ctx.add_shutdown_callback(_cancel_lifecycle_tasks)
    ctx.add_shutdown_callback(_persist_call_artifacts)

    @session.on("conversation_item_added")
    def _log_turn_latency(event: Any) -> None:
        item = getattr(event, "item", None)
        role = getattr(item, "role", None)
        if role in {"user", "assistant"}:
            _mark_activity()
        metrics = getattr(item, "metrics", None) or {}
        if role not in {"user", "assistant"} or not metrics:
            return

        if role == "user":
            latency_metrics = {
                "transcription_delay": metrics.get("transcription_delay"),
                "end_of_turn_delay": metrics.get("end_of_turn_delay"),
                "on_user_turn_completed_delay": metrics.get("on_user_turn_completed_delay"),
            }
            provider = "Deepgram"
        else:
            latency_metrics = {
                "llm_node_ttft": metrics.get("llm_node_ttft"),
                "tts_node_ttfb": metrics.get("tts_node_ttfb"),
                "playback_latency": metrics.get("playback_latency"),
                "e2e_latency": metrics.get("e2e_latency"),
            }
            provider = "LiveKit Agents"

        latency_metrics = {key: value for key, value in latency_metrics.items() if value is not None}
        if not latency_metrics:
            return

        logger.info("voice_turn_latency role=%s metrics=%s", role, latency_metrics)
        asyncio.create_task(
            _emit_pipeline_event(
                metadata,
                stage=f"{role}_turn_latency",
                provider=provider,
                message=f"{role.title()} turn latency metrics collected",
                extra_metadata=_metrics_metadata(latency_metrics),
            )
        )

    @session.on("user_state_changed")
    def _track_user_state(event: Any) -> None:
        new_state = getattr(event, "new_state", "")
        speaking["user"] = str(getattr(new_state, "value", new_state)) == "speaking"
        _mark_activity()

    @session.on("agent_state_changed")
    def _track_agent_state(event: Any) -> None:
        new_state = getattr(event, "new_state", "")
        speaking["agent"] = str(getattr(new_state, "value", new_state)) == "speaking"
        _mark_activity()

    @session.on("user_input_transcribed")
    def _track_customer_language(event: Any) -> None:
        nonlocal customer_language, customer_transcript
        if not getattr(event, "is_final", False):
            return
        customer_transcript = str(getattr(event, "transcript", "") or "")
        detected_language = getattr(event, "language", None)
        if detected_language:
            customer_language = str(detected_language)
        _mark_activity()

    @session.on("error")
    def _track_pipeline_error(event: Any) -> None:
        logger.warning(
            "Voice pipeline error; starting recovery timeout source=%s error=%s",
            getattr(event, "source", "unknown"),
            getattr(event, "error", "unknown"),
        )
        speaking["user"] = False
        speaking["agent"] = False
        _mark_activity()

    async def _finalize_call(reason: str, terminal_reason: str) -> None:
        lkapi = api.LiveKitAPI(
            url=os.getenv("LIVEKIT_URL"),
            api_key=os.getenv("LIVEKIT_API_KEY"),
            api_secret=os.getenv("LIVEKIT_API_SECRET"),
        )
        try:
            await lkapi.room.delete_room(api.DeleteRoomRequest(room=ctx.room.name))
            logger.info("Ended LiveKit room=%s reason=%s", ctx.room.name, reason)
        except Exception as exc:
            logger.warning("Failed to end call room=%s error=%s", ctx.room.name, exc)
        finally:
            await lkapi.aclose()
            await _persist_call_artifacts()
            await _report_call_result(
                metadata,
                "completed",
                terminal_reason=terminal_reason,
            )
            ctx.shutdown(reason=reason)

    async def _end_completed_call() -> None:
        if call_ending.is_set():
            return
        call_ending.set()
        await _finalize_call(
            "qualification and callback preference complete",
            "qualification_complete",
        )

    async def _end_inactive_call() -> None:
        if call_ending.is_set():
            return
        call_ending.set()
        _schedule_pipeline_event(
            metadata,
            stage="call_inactivity_timeout",
            provider="LiveKit Agents",
            status="warning",
            message="Call ended after sustained inactivity or unrecovered pipeline error",
            extra_metadata={"timeout_seconds": str(call_idle_timeout)},
        )
        await _finalize_call(
            f"call inactive for {call_idle_timeout:g} seconds",
            "inactivity_timeout",
        )

    async def _end_duration_limited_call() -> None:
        if call_ending.is_set():
            return
        call_ending.set()
        _schedule_pipeline_event(
            metadata,
            stage="call_duration_limit",
            provider="LiveKit Agents",
            status="warning",
            message="Call reached the qualification duration limit",
            extra_metadata={"duration_seconds": str(call_max_duration)},
        )
        closing_message = _duration_limit_closing_message(
            customer_language,
            customer_transcript,
        )
        try:
            session.interrupt()
        except Exception:
            pass
        try:
            speech_handle = session.say(closing_message, allow_interruptions=False)
            await speech_handle.wait_for_playout()
        except Exception as exc:
            logger.warning("Duration-limit closing message failed: %s", exc)
        await _finalize_call(
            "call reached maximum qualification duration",
            "duration_limit",
        )

    async def _watch_for_inactivity() -> None:
        while not call_ending.is_set():
            if speaking["user"] or speaking["agent"]:
                activity_event.clear()
                await activity_event.wait()
                continue
            remaining = call_idle_timeout - (
                asyncio.get_running_loop().time() - last_activity_at
            )
            if remaining <= 0:
                await _end_inactive_call()
                return
            activity_event.clear()
            try:
                await asyncio.wait_for(activity_event.wait(), timeout=remaining)
            except asyncio.TimeoutError:
                await _end_inactive_call()
                return

    async def _watch_call_duration() -> None:
        await asyncio.sleep(call_max_duration)
        await _end_duration_limited_call()

    await session.start(
        room=ctx.room,
        agent=_RingIQVoiceAgent(metadata, end_call_fnc=_end_completed_call),
    )
    await ctx.room.local_participant.set_attributes(
        {AGENT_READY_ATTRIBUTE: str(metadata.get("call_id", ctx.job.id))}
    )
    logger.info("Voice agent ready for SIP participant: room=%s", ctx.room.name)
    _schedule_pipeline_event(
        metadata,
        stage="session_started",
        provider="LiveKit",
        message="Agent session started and is ready for the SIP participant",
    )
    try:
        if sip_participant_identity:
            logger.info("Waiting for SIP participant %s before greeting", sip_participant_identity)
            _schedule_pipeline_event(
                metadata,
                stage="participant_waiting",
                provider="LiveKit SIP",
                message="Waiting for SIP participant before greeting",
                extra_metadata={"sip_participant_identity": str(sip_participant_identity)},
            )
            participant_wait = ctx.wait_for_participant(identity=sip_participant_identity)
        else:
            logger.info("No SIP participant identity in metadata; waiting for the first participant")
            participant_wait = ctx.wait_for_participant()
        participant = await asyncio.wait_for(
            participant_wait,
            timeout=sip_participant_wait_timeout,
        )
    except asyncio.TimeoutError:
        logger.warning(
            "SIP participant did not join within %s seconds; shutting down room=%s",
            sip_participant_wait_timeout,
            ctx.room.name,
        )
        _schedule_pipeline_event(
            metadata,
            stage="participant_wait_timeout",
            provider="LiveKit SIP",
            status="error",
            message="SIP participant did not join before the voice job timeout",
            extra_metadata={"timeout_seconds": str(sip_participant_wait_timeout)},
        )
        await _report_call_result(
            metadata,
            "unanswered",
            terminal_reason="participant_wait_timeout",
        )
        ctx.shutdown(reason="SIP participant wait timed out")
        return
    except RuntimeError as exc:
        if "room disconnected while waiting for participant" not in str(exc):
            raise
        logger.info(
            "Room disconnected before the SIP participant joined: room=%s",
            ctx.room.name,
        )
        await _report_call_result(
            metadata,
            "unanswered",
            terminal_reason="room_disconnected_before_answer",
        )
        return

    logger.info("SIP participant connected: identity=%s", participant.identity)
    _mark_activity()
    lifecycle_tasks.extend(
        [
            asyncio.create_task(_watch_for_inactivity()),
            asyncio.create_task(_watch_call_duration()),
        ]
    )
    recording_task = asyncio.create_task(_start_call_recording(ctx, metadata))
    asyncio.create_task(_report_call_result(metadata, "connected"))

    @ctx.room.on("participant_disconnected")
    def _on_participant_disconnected(disconnected_participant: Any) -> None:
        if disconnected_participant.identity != participant.identity:
            return
        if call_ending.is_set():
            return
        call_ending.set()

        async def _store_and_report_disconnect() -> None:
            await _persist_call_artifacts()
            await _report_call_result(
                metadata,
                "completed",
                terminal_reason="participant_disconnected",
            )

        asyncio.create_task(_store_and_report_disconnect())

    _schedule_pipeline_event(
        metadata,
        stage="participant_connected",
        provider="LiveKit SIP",
        message="SIP participant connected",
        extra_metadata={"participant_identity": participant.identity},
    )
    session.say(_initial_greeting(metadata), allow_interruptions=True)
    _schedule_pipeline_event(
        metadata,
        stage="greeting_queued",
        provider="Sarvam",
        message="Initial greeting queued for TTS playback",
        extra_metadata={"speaker": sarvam_speaker, "language": sarvam_language},
    )


if __name__ == "__main__":
    agents.cli.run_app(
        agents.WorkerOptions(
            entrypoint_fnc=entrypoint,
            prewarm_fnc=prewarm,
            num_idle_processes=1,
            agent_name=os.getenv("LIVEKIT_AGENT_NAME", "ringiq-demo-agent"),
        )
    )
