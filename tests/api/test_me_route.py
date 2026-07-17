import uuid
from unittest.mock import AsyncMock

from fastapi.testclient import TestClient

from apps.api.ringiq_api.auth.context import TenantContext, get_current_tenant_context
from apps.api.ringiq_api.config import VoiceSettings, get_voice_settings
from apps.api.ringiq_api.main import create_app
from apps.api.ringiq_api.schemas.demo_calls import DemoCallResponse
from apps.api.ringiq_api.services.livekit_calls import LiveKitCallService


def make_context() -> TenantContext:
    return TenantContext(
        tenant_id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        membership_id=uuid.uuid4(),
        clerk_organization_id="org_1",
        clerk_user_id="user_1",
        clerk_membership_id="orgmem_1",
        tenant_name="Acme Realty",
        tenant_slug="acme-realty",
        timezone="Asia/Kolkata",
    )


def test_me_route_returns_resolved_context() -> None:
    app = create_app()
    context = make_context()
    app.dependency_overrides[get_current_tenant_context] = lambda: context

    with TestClient(app) as client:
        response = client.get("/v1/me")

    assert response.status_code == 200
    assert response.json()["tenant_id"] == str(context.tenant_id)
    assert response.json()["clerk_organization_id"] == "org_1"


def test_health_route_remains_public() -> None:
    with TestClient(create_app()) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_demo_call_route_does_not_require_identity_configuration(
    monkeypatch,
) -> None:
    settings = VoiceSettings(
        _env_file=None,
        livekit_url="wss://example.livekit.cloud",
        livekit_api_key="api-key",
        livekit_api_secret="api-secret",
        livekit_sip_outbound_trunk_id="ST_example",
    )
    response_payload = DemoCallResponse(
        call_id="call_1",
        room_name="room_1",
        phone_number="+919876543210",
        agent_name="ringiq-demo-agent",
        sip_participant_identity="phone_user-1",
        status="call_started",
        message="started",
    )
    create_call = AsyncMock(return_value=response_payload)
    monkeypatch.setattr(LiveKitCallService, "create_demo_call", create_call)
    app = create_app()
    app.dependency_overrides[get_voice_settings] = lambda: settings

    with TestClient(app) as client:
        response = client.post(
            "/demo/calls",
            json={"phone_number": "+919876543210"},
        )

    assert response.status_code == 202
    assert response.json()["call_id"] == "call_1"
    create_call.assert_awaited_once()
