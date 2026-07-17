import asyncio
import json
import logging
import os
from typing import Any

import aiohttp
from dotenv import load_dotenv
from livekit import agents
from livekit.agents import Agent, AgentSession, JobContext, TurnHandlingOptions
from livekit.plugins import deepgram, groq, sarvam, silero

load_dotenv()

logger = logging.getLogger("ringiq.voice_worker")
DEFAULT_API_BASE_URL = "http://127.0.0.1:8000"


def _csv_env(name: str, default: str) -> list[str]:
    value = os.getenv(name, default)
    return [item.strip() for item in value.split(",") if item.strip()]


def _bool_env(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


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
    phone_number = metadata.get("phone_number", "the lead")
    return f"""
You are RingIQ's demo real-estate lead qualification voice agent.

You are calling {phone_number} for a short demo conversation.

Conversation rules:
- Introduce yourself as an AI assistant calling on behalf of a real estate business.
- Keep responses short and natural for a phone call.
- Speak in simple English, Hindi, or mixed Hindi-English depending on the user's language.
- Ask whether the person is interested in discussing property options.
- If they are interested, ask for preferred area, budget, property type, and callback preference.
- If they are not interested, politely end the call.
- Do not claim real project availability, pricing, discounts, legal approvals, or possession dates.
- If asked for details you do not know, say a sales representative can confirm that.
""".strip()


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


async def entrypoint(ctx: JobContext) -> None:
    metadata = _metadata(ctx)
    metadata.setdefault("room_name", ctx.room.name)
    logger.info("Starting RingIQ demo voice worker for metadata=%s", metadata)
    sip_participant_identity = metadata.get("sip_participant_identity")
    await _emit_pipeline_event(
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
    deepgram_eot_timeout_ms = int(os.getenv("DEEPGRAM_EOT_TIMEOUT_MS", "2000"))
    groq_model = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")
    sarvam_model = os.getenv("SARVAM_TTS_MODEL", "bulbul:v3")
    sarvam_speaker = os.getenv("SARVAM_TTS_SPEAKER", "shubh").strip().lower()
    sarvam_language = os.getenv("SARVAM_TARGET_LANGUAGE_CODE", "hi-IN")
    sarvam_sample_rate = int(os.getenv("SARVAM_TTS_SAMPLE_RATE", "16000"))
    sarvam_min_buffer_size = int(os.getenv("SARVAM_TTS_MIN_BUFFER_SIZE", "30"))
    sarvam_max_chunk_length = int(os.getenv("SARVAM_TTS_MAX_CHUNK_LENGTH", "100"))
    sarvam_output_audio_codec = os.getenv("SARVAM_TTS_OUTPUT_AUDIO_CODEC", "linear16")
    preemptive_tts = _bool_env("LIVEKIT_PREEMPTIVE_TTS", True)

    await _emit_pipeline_event(
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
    await _emit_pipeline_event(
        metadata,
        stage="llm_configured",
        provider="Groq",
        message="LLM configured",
        extra_metadata={"model": groq_model},
    )
    await _emit_pipeline_event(
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

    session = AgentSession(
        vad=silero.VAD.load(),
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
        llm=groq.LLM(
            model=groq_model,
            temperature=float(os.getenv("GROQ_TEMPERATURE", "0.4")),
        ),
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

    @session.on("conversation_item_added")
    def _log_turn_latency(event: Any) -> None:
        item = getattr(event, "item", None)
        role = getattr(item, "role", None)
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

    await session.start(
        room=ctx.room,
        agent=Agent(instructions=_agent_instructions(metadata)),
    )
    await _emit_pipeline_event(
        metadata,
        stage="session_started",
        provider="LiveKit",
        message="Agent session started",
    )
    if sip_participant_identity:
        logger.info("Waiting for SIP participant %s before greeting", sip_participant_identity)
        await _emit_pipeline_event(
            metadata,
            stage="participant_waiting",
            provider="LiveKit SIP",
            message="Waiting for SIP participant before greeting",
            extra_metadata={"sip_participant_identity": str(sip_participant_identity)},
        )
        participant = await ctx.wait_for_participant(identity=sip_participant_identity)
    else:
        logger.info("No SIP participant identity in metadata; waiting for the first participant")
        participant = await ctx.wait_for_participant()

    logger.info("SIP participant connected: identity=%s", participant.identity)
    await _emit_pipeline_event(
        metadata,
        stage="participant_connected",
        provider="LiveKit SIP",
        message="SIP participant connected",
        extra_metadata={"participant_identity": participant.identity},
    )
    session.say(
        "Namaste, main RingIQ ka AI assistant bol raha hoon. Kya aap property options ke baare mein baat karna chahenge?",
        allow_interruptions=True,
    )
    await _emit_pipeline_event(
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
            agent_name=os.getenv("LIVEKIT_AGENT_NAME", "ringiq-demo-agent"),
        )
    )
