import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from apps.api.ringiq_api.config import VoiceSettings
from apps.api.ringiq_api.schemas.demo_calls import DemoCallRequest
from apps.api.ringiq_api.services.livekit_calls import (
    AGENT_READY_ATTRIBUTE,
    LiveKitCallService,
    LiveKitCallServiceError,
)


def _settings(**overrides: object) -> VoiceSettings:
    values: dict[str, object] = {
        "_env_file": None,
        "livekit_url": "wss://example.livekit.cloud",
        "livekit_api_key": "api-key",
        "livekit_api_secret": "api-secret",
        "livekit_sip_outbound_trunk_id": "ST_example",
    }
    values.update(overrides)
    return VoiceSettings(**values)


@pytest.mark.asyncio
async def test_call_waits_for_agent_readiness_before_dialing(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []
    observed_call_ids: list[str] = []
    fake_api = SimpleNamespace(aclose=AsyncMock())
    monkeypatch.setattr(
        "apps.api.ringiq_api.services.livekit_calls.api.LiveKitAPI",
        lambda **_: fake_api,
    )
    service = LiveKitCallService(_settings())

    async def dispatch(
        _: object,
        __: str,
        metadata: dict[str, str],
    ) -> None:
        calls.append("dispatch")
        observed_call_ids.append(metadata["call_id"])

    async def wait_until_ready(
        _: object,
        *,
        room_name: str,
        call_id: str,
    ) -> None:
        calls.append("ready")
        assert room_name == "ringiq-call-attempt-1"
        observed_call_ids.append(call_id)

    async def dial(*_: object, **__: object) -> object:
        calls.append("dial")
        return SimpleNamespace(attributes={"sip.callID": "sip-call-1"})

    monkeypatch.setattr(service, "_dispatch_agent", dispatch)
    monkeypatch.setattr(service, "_wait_for_agent_ready", wait_until_ready)
    monkeypatch.setattr(service, "_create_sip_participant", dial)

    response = await service.create_demo_call(
        DemoCallRequest(
            phone_number="+919876543210",
            room_name="ringiq-call-attempt-1",
            metadata={"call_id": "attempt-1", "demo": "false"},
        )
    )

    assert calls == ["dispatch", "ready", "dial"]
    assert observed_call_ids == ["attempt-1", "attempt-1"]
    assert response.call_id == "attempt-1"
    assert response.livekit_sip_call_id == "sip-call-1"
    fake_api.aclose.assert_awaited_once()


@pytest.mark.asyncio
async def test_readiness_failure_does_not_dial_lead(monkeypatch: pytest.MonkeyPatch) -> None:
    delete_room = AsyncMock()
    fake_api = SimpleNamespace(
        aclose=AsyncMock(),
        room=SimpleNamespace(delete_room=delete_room),
    )
    monkeypatch.setattr(
        "apps.api.ringiq_api.services.livekit_calls.api.LiveKitAPI",
        lambda **_: fake_api,
    )
    service = LiveKitCallService(_settings())
    monkeypatch.setattr(service, "_dispatch_agent", AsyncMock())
    monkeypatch.setattr(
        service,
        "_wait_for_agent_ready",
        AsyncMock(side_effect=LiveKitCallServiceError("agent startup failed")),
    )
    dial = AsyncMock()
    monkeypatch.setattr(service, "_create_sip_participant", dial)

    with pytest.raises(LiveKitCallServiceError, match="agent startup failed"):
        await service.create_demo_call(DemoCallRequest(phone_number="+919876543210"))

    dial.assert_not_awaited()
    delete_room.assert_awaited_once()
    assert delete_room.await_args.args[0].room.startswith("ringiq-demo-")
    fake_api.aclose.assert_awaited_once()


@pytest.mark.asyncio
async def test_readiness_poll_recovers_after_a_stalled_livekit_request(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = 0

    async def list_participants(_: object) -> object:
        nonlocal calls
        calls += 1
        if calls == 1:
            await asyncio.sleep(0.02)
        return SimpleNamespace(
            participants=[
                SimpleNamespace(
                    identity="agent-worker",
                    attributes={AGENT_READY_ATTRIBUTE: "attempt-1"},
                )
            ]
        )

    fake_api = SimpleNamespace(
        room=SimpleNamespace(list_participants=list_participants),
    )
    service = LiveKitCallService(
        _settings(livekit_agent_ready_timeout_seconds=0.2)
    )
    monkeypatch.setattr(
        "apps.api.ringiq_api.services.livekit_calls.READINESS_PROBE_TIMEOUT_SECONDS",
        0.005,
    )

    await service._wait_for_agent_ready(
        fake_api,
        room_name="ringiq-call-attempt-1",
        call_id="attempt-1",
    )

    assert calls == 2
