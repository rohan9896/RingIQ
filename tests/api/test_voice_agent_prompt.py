import asyncio
import json

import pytest
from livekit.agents import StopResponse, llm

from apps.voice_worker.agent import (
    _CallOpeningHarness,
    _OpeningStage,
    _QualificationTurnHarness,
    _RingIQVoiceAgent,
    _agent_instructions,
    _bounded_int_env,
    _callback_confirmation,
    _identity_confirmation,
    _initial_greeting,
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
