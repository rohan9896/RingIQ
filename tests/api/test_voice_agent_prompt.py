import asyncio
import json
from types import SimpleNamespace

import pytest
from livekit.agents import StopResponse, llm

from apps.voice_worker.agent import (
    _CallOpeningHarness,
    _OpeningStage,
    _QualificationTurnHarness,
    _RecordingHandle,
    _RingIQVoiceAgent,
    _agent_instructions,
    _bounded_int_env,
    _callback_confirmation,
    _conversation_transcript,
    _duration_limit_closing_message,
    _identity_confirmation,
    _initial_greeting,
    _report_call_result,
    _start_call_recording,
    _stop_call_recording,
)


def production_metadata() -> dict[str, str]:
    return {
        "agent_context_json": json.dumps(
            {
                "organization_name": "Acme Realty",
                "lead": {"name": "Rohan"},
                "knowledge_base": {"business_profile": {"city": "Gurugram"}},
            }
        )
    }


def test_initial_greeting_only_opens_the_line() -> None:
    greeting = _initial_greeting(production_metadata())

    assert greeting == "Hello?"
    assert "AI" not in greeting
    assert "RingIQ" not in greeting


def test_opening_harness_waits_for_reply_then_confirms_identity() -> None:
    harness = _CallOpeningHarness(production_metadata())

    assert harness.respond("...") is None
    response = harness.respond("Hello")

    assert response is not None
    assert response.text == "Namaste, kya meri baat Rohan ji se ho rahi hai?"
    assert harness.stage is _OpeningStage.AWAITING_IDENTITY_CONFIRMATION


def test_opening_harness_introduces_tenant_only_after_confirmation() -> None:
    harness = _CallOpeningHarness(production_metadata())
    harness.respond("Hello")

    response = harness.respond("Haan ji, main Rohan bol raha hoon")

    assert response is not None
    assert response.completes_opening is True
    assert response.text.startswith("Main Acme Realty ka assistant bol raha hoon")
    assert "enquiry ke silsile" in response.text
    assert "AI" not in response.text
    assert "RingIQ" not in response.text
    assert harness.stage is _OpeningStage.COMPLETE
    assert harness.respond("Haan, boliye") is None


def test_opening_harness_does_not_introduce_tenant_without_confirmation() -> None:
    harness = _CallOpeningHarness(production_metadata())
    harness.respond("Hello")

    ambiguous = harness.respond("Kaun?")
    negative = harness.respond("Nahi, wrong number")

    assert ambiguous is not None
    assert ambiguous.text == "Maaf kijiye, kya aap Rohan ji bol rahe hain?"
    assert negative is not None
    assert negative.text == "Theek hai. Kya Rohan ji se baat ho sakti hai?"
    assert "Acme Realty" not in ambiguous.text + negative.text
    assert harness.stage is _OpeningStage.AWAITING_IDENTITY_CONFIRMATION


def test_identity_confirmation_understands_hindi_and_english() -> None:
    assert _identity_confirmation("जी हां") is True
    assert _identity_confirmation("मैं ही रोहन बोल रहा हूँ") is True
    assert _identity_confirmation("Yes, speaking") is True
    assert _identity_confirmation("Nahi, galat number") is False
    assert _identity_confirmation("Kaun?") is None


def test_voice_agent_suppresses_llm_and_remembers_staged_opening_turn(monkeypatch) -> None:
    spoken: list[str] = []

    class FakeSession:
        def say(self, text: str, **_: object) -> None:
            spoken.append(text)

    monkeypatch.setattr(
        _RingIQVoiceAgent,
        "session",
        property(lambda _: FakeSession()),
    )
    agent = _RingIQVoiceAgent(production_metadata())
    message = llm.ChatMessage(role="user", content=["Hello"])

    with pytest.raises(StopResponse):
        asyncio.run(agent.on_user_turn_completed(agent.chat_ctx.copy(), message))

    assert agent.chat_ctx.messages() == [message]
    assert spoken == ["Namaste, kya meri baat Rohan ji se ho rahi hai?"]


def test_qualification_harness_requires_specific_acknowledgment_before_next_question() -> None:
    harness = _QualificationTurnHarness()
    turn_ctx = llm.ChatContext.empty()

    prepared = harness.prepare_response(turn_ctx, "Haan, mera budget 2 crore ka hai")

    assert prepared is True
    instruction = turn_ctx.messages()[-1].text_content
    assert "First briefly acknowledge" in instruction
    assert "2 crore budget has been noted" in instruction
    assert "exactly one useful next question" in instruction
    assert "Never ask again" in instruction


def test_qualification_harness_ignores_empty_transcript() -> None:
    harness = _QualificationTurnHarness()
    turn_ctx = llm.ChatContext.empty()

    assert harness.prepare_response(turn_ctx, "...") is False
    assert turn_ctx.messages() == []


def callback_turn_context() -> llm.ChatContext:
    turn_ctx = llm.ChatContext.empty()
    turn_ctx.add_message(
        role="assistant",
        content="Kya aap chahenge ki hamari sales team aapko callback kare?",
    )
    return turn_ctx


def test_qualification_harness_closes_after_callback_confirmation() -> None:
    harness = _QualificationTurnHarness()

    response = harness.callback_closing_response(
        callback_turn_context(),
        "Haan ji, callback kar dijiye",
    )

    assert response == (
        "Bilkul, hamari sales team aapko callback karegi. "
        "Aapke samay aur jaankari ke liye dhanyavaad."
    )
    assert "?" not in response


def test_qualification_harness_closes_when_callback_is_declined() -> None:
    harness = _QualificationTurnHarness()

    response = harness.callback_closing_response(
        callback_turn_context(),
        "Nahi, callback ki zarurat nahi hai",
    )

    assert response == (
        "Theek hai, callback ki zarurat nahi hai. "
        "Aapke samay aur jaankari ke liye dhanyavaad."
    )
    assert "?" not in response


def test_qualification_harness_only_clarifies_ambiguous_callback_answer() -> None:
    harness = _QualificationTurnHarness()
    turn_ctx = callback_turn_context()

    assert harness.callback_closing_response(turn_ctx, "Dekhte hain") is None
    assert harness.prepare_response(turn_ctx, "Dekhte hain") is True
    instruction = turn_ctx.messages()[-1].text_content
    assert "ask only whether they want a callback" in instruction
    assert "Do not return to any earlier qualification question" in instruction


def test_qualification_harness_does_not_close_after_non_question_sales_team_mention() -> None:
    harness = _QualificationTurnHarness()
    turn_ctx = llm.ChatContext.empty()
    turn_ctx.add_message(
        role="assistant",
        content="Ye detail hamari sales team confirm karegi.",
    )

    assert harness.callback_closing_response(turn_ctx, "Haan ji") is None
    assert harness.is_answering_callback_question(turn_ctx) is False


def test_callback_confirmation_understands_hindi_and_english() -> None:
    assert _callback_confirmation("Haan ji, kar dijiye") is True
    assert _callback_confirmation("Yes, please call me") is True
    assert _callback_confirmation("Nahi, zarurat nahi hai") is False
    assert _callback_confirmation("Not required") is False
    assert _callback_confirmation("Dekhte hain") is None


def test_voice_agent_applies_qualification_contract_after_opening() -> None:
    agent = _RingIQVoiceAgent(production_metadata())
    agent.opening.stage = _OpeningStage.COMPLETE
    turn_ctx = agent.chat_ctx.copy()
    message = llm.ChatMessage(
        role="user",
        content=["Haan, mera budget 2 crore ka hai"],
    )

    asyncio.run(agent.on_user_turn_completed(turn_ctx, message))

    assert "2 crore budget has been noted" in turn_ctx.messages()[-1].text_content


def test_voice_agent_plays_callback_closing_before_ending_call(monkeypatch) -> None:
    events: list[str] = []

    class FakeSpeechHandle:
        async def wait_for_playout(self) -> None:
            events.append("closing_played")

    class FakeSession:
        def say(self, text: str, **_: object) -> FakeSpeechHandle:
            events.append(text)
            return FakeSpeechHandle()

    async def end_call() -> None:
        events.append("call_ended")

    monkeypatch.setattr(
        _RingIQVoiceAgent,
        "session",
        property(lambda _: FakeSession()),
    )
    agent = _RingIQVoiceAgent(production_metadata(), end_call_fnc=end_call)
    agent.opening.stage = _OpeningStage.COMPLETE
    message = llm.ChatMessage(role="user", content=["Haan ji"])

    async def run_turn() -> None:
        chat_ctx = agent.chat_ctx.copy()
        chat_ctx.add_message(
            role="assistant",
            content="Kya hamari sales team aapko callback kare?",
        )
        await agent.update_chat_ctx(chat_ctx)
        with pytest.raises(StopResponse):
            await agent.on_user_turn_completed(agent.chat_ctx.copy(), message)
        assert agent._end_call_task is not None
        await agent._end_call_task

    asyncio.run(run_turn())

    assert events == [
        "Bilkul, hamari sales team aapko callback karegi. Aapke samay aur jaankari ke liye dhanyavaad.",
        "closing_played",
        "call_ended",
    ]
    assert agent.chat_ctx.messages()[-1] == message


def test_production_instructions_forbid_ai_and_ringiq_introduction() -> None:
    instructions = _agent_instructions(production_metadata())

    assert "Never describe yourself as an AI assistant" in instructions
    assert "never mention RingIQ" in instructions
    assert "calling on behalf of Acme Realty" in instructions
    assert '"bol raha hoon", never "bol rahi hoon"' in instructions
    assert "Never restart the greeting" in instructions


def test_production_instructions_track_qualification_facts_without_repeating() -> None:
    instructions = _agent_instructions(production_metadata())

    assert "silent ledger" in instructions
    assert "Never ask for a fact that is already in the ledger" in instructions
    assert "area and budget" in instructions
    assert "Ask at most one useful question per turn" in instructions


def test_bounded_integer_environment_prevents_invalid_provider_config(monkeypatch) -> None:
    monkeypatch.setenv("TEST_BUFFER_SIZE", "20")

    assert _bounded_int_env("TEST_BUFFER_SIZE", 30, minimum=30, maximum=200) == 30


def test_conversation_transcript_keeps_only_spoken_roles() -> None:
    session = SimpleNamespace(
        history=SimpleNamespace(
            items=[
                SimpleNamespace(role="system", text_content="Internal prompt"),
                SimpleNamespace(role="assistant", text_content="Budget kya hai?", interrupted=False),
                SimpleNamespace(role="user", text_content="Do crore.", interrupted=False),
                SimpleNamespace(role="assistant", text_content="  ", interrupted=False),
            ]
        )
    )

    assert _conversation_transcript(session) == [
        {"role": "assistant", "text": "Budget kya hai?", "interrupted": False},
        {"role": "user", "text": "Do crore.", "interrupted": False},
    ]


def test_recording_is_additive_and_disabled_by_default(monkeypatch) -> None:
    monkeypatch.delenv("LIVEKIT_RECORDING_ENABLED", raising=False)
    ctx = SimpleNamespace(room=SimpleNamespace(name="test-room"))

    assert asyncio.run(_start_call_recording(ctx, {})) is None


def test_recording_uses_dual_channel_egress_after_it_is_enabled(monkeypatch) -> None:
    from apps.voice_worker import agent as agent_module

    requests: list[object] = []

    class FakeEgress:
        async def start_room_composite_egress(self, request):
            requests.append(request)
            return SimpleNamespace(egress_id="EG_recording")

    class FakeLiveKitAPI:
        def __init__(self, **_: object) -> None:
            self.egress = FakeEgress()

        async def aclose(self) -> None:
            return None

    monkeypatch.setattr(agent_module.api, "LiveKitAPI", FakeLiveKitAPI)
    monkeypatch.setenv("LIVEKIT_RECORDING_ENABLED", "true")
    monkeypatch.setenv("LIVEKIT_RECORDING_S3_BUCKET", "ringiq-recordings")
    monkeypatch.setenv("LIVEKIT_RECORDING_S3_REGION", "ap-south-1")
    monkeypatch.setenv("LIVEKIT_RECORDING_S3_ACCESS_KEY", "access")
    monkeypatch.setenv("LIVEKIT_RECORDING_S3_SECRET", "secret")
    monkeypatch.setenv("LIVEKIT_RECORDING_PUBLIC_BASE_URL", "https://media.example.com")
    monkeypatch.delenv("RINGIQ_INTERNAL_API_KEY", raising=False)
    ctx = SimpleNamespace(
        room=SimpleNamespace(name="ringiq-call-test"),
        job=SimpleNamespace(id="job-test"),
    )

    handle = asyncio.run(
        _start_call_recording(
            ctx,
            {"tenant_id": "tenant-test", "call_attempt_id": "attempt-test"},
        )
    )

    assert handle is not None
    assert handle.egress_id == "EG_recording"
    assert handle.playback_url == (
        "https://media.example.com/ringiq/recordings/tenant-test/attempt-test.mp3"
    )
    request = requests[0]
    assert request.audio_only is True
    assert request.audio_mixing == agent_module.api.AudioMixing.DUAL_CHANNEL_AGENT
    assert request.file_outputs[0].filepath.endswith("/attempt-test.mp3")


def test_recording_waits_for_terminal_upload_failure(monkeypatch) -> None:
    from apps.voice_worker import agent as agent_module

    class FakeEgress:
        async def stop_egress(self, _request):
            return SimpleNamespace(
                status=agent_module.api.EgressStatus.EGRESS_ENDING,
                error="",
            )

        async def list_egress(self, _request):
            return SimpleNamespace(
                items=[
                    SimpleNamespace(
                        status=agent_module.api.EgressStatus.EGRESS_FAILED,
                        error="S3 AccessDenied",
                    )
                ]
            )

    class FakeLiveKitAPI:
        def __init__(self, **_: object) -> None:
            self.egress = FakeEgress()

        async def aclose(self) -> None:
            return None

    async def no_wait(_: float) -> None:
        return None

    monkeypatch.setattr(agent_module.api, "LiveKitAPI", FakeLiveKitAPI)
    monkeypatch.setattr(agent_module.asyncio, "sleep", no_wait)

    status = asyncio.run(
        _stop_call_recording(
            _RecordingHandle(
                egress_id="EG_failed",
                storage_uri="s3://bucket/call.mp3",
                playback_url=None,
            )
        )
    )

    assert status == "failed"


def test_duration_limit_closing_matches_customer_language() -> None:
    assert _duration_limit_closing_message("hi", "मुझे प्रॉपर्टी चाहिए") == (
        "Aapki interest ke liye dhanyavaad. "
        "Hamari sales team aapko jaldi callback karegi."
    )
    assert _duration_limit_closing_message("en", "I am interested") == (
        "Thank you for your interest. "
        "Our sales team will call you back shortly."
    )
    assert "sales team" in _duration_limit_closing_message(None, "हाँ, ठीक है")


def test_call_result_reports_bounded_terminal_reason(monkeypatch) -> None:
    from apps.voice_worker import agent as agent_module

    requests: list[dict] = []

    class FakeResponse:
        status = 200

        async def __aenter__(self):
            return self

        async def __aexit__(self, *_: object) -> None:
            return None

    class FakeSession:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *_: object) -> None:
            return None

        def post(self, url: str, **kwargs: object) -> FakeResponse:
            requests.append({"url": url, **kwargs})
            return FakeResponse()

    monkeypatch.setenv("RINGIQ_INTERNAL_API_KEY", "internal-secret")
    monkeypatch.setattr(agent_module.aiohttp, "ClientSession", FakeSession)

    asyncio.run(
        _report_call_result(
            {"call_attempt_id": "attempt-1"},
            "completed",
            terminal_reason="participant_disconnected",
        )
    )

    assert requests[0]["json"] == {
        "status": "completed",
        "terminal_reason": "participant_disconnected",
    }
