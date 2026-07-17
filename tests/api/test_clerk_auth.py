from enum import Enum
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from starlette.requests import Request

from apps.api.ringiq_api.auth import clerk as clerk_module
from apps.api.ringiq_api.auth.clerk import (
    ActiveOrganizationRequired,
    ClerkAuthenticationRejected,
    ClerkAuthenticator,
    ClerkPrincipal,
    require_clerk_principal,
)
from tests.api.helpers import make_settings


class RejectionReason(Enum):
    TOKEN_INVALID = "TOKEN_INVALID"


def make_request() -> Request:
    return Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/v1/me",
            "headers": [],
            "query_string": b"",
            "server": ("testserver", 80),
            "scheme": "http",
        }
    )


def test_authenticator_returns_principal_and_restricts_token_type(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured_options = None

    def fake_authenticate_request(request: Request, options: object) -> object:
        nonlocal captured_options
        captured_options = options
        return SimpleNamespace(
            is_signed_in=True,
            payload={
                "sub": "user_1",
                "org_id": "org_1",
                "org_role": "member",
                "sid": "sess_1",
            },
            reason=None,
        )

    monkeypatch.setattr(clerk_module, "authenticate_request", fake_authenticate_request)

    principal = ClerkAuthenticator(make_settings()).authenticate(make_request())

    assert principal == ClerkPrincipal(
        user_id="user_1",
        organization_id="org_1",
        session_id="sess_1",
        organization_role="member",
    )
    assert captured_options.accepts_token == ["session_token"]
    assert captured_options.authorized_parties == ["http://localhost:3000"]


def test_authenticator_supports_v2_nested_organization_claim(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        clerk_module,
        "authenticate_request",
        lambda *_: SimpleNamespace(
            is_signed_in=True,
            payload={"sub": "user_1", "o": {"id": "org_1", "rol": "admin"}},
            reason=None,
        ),
    )

    principal = ClerkAuthenticator(make_settings()).authenticate(make_request())

    assert principal.organization_id == "org_1"
    assert principal.organization_role == "admin"


def test_authenticator_rejects_invalid_session(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        clerk_module,
        "authenticate_request",
        lambda *_: SimpleNamespace(
            is_signed_in=False,
            payload=None,
            reason=RejectionReason.TOKEN_INVALID,
        ),
    )

    with pytest.raises(ClerkAuthenticationRejected) as exc_info:
        ClerkAuthenticator(make_settings()).authenticate(make_request())

    assert exc_info.value.reason == "TOKEN_INVALID"


def test_authenticator_requires_active_organization(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        clerk_module,
        "authenticate_request",
        lambda *_: SimpleNamespace(
            is_signed_in=True,
            payload={"sub": "user_1"},
            reason=None,
        ),
    )

    with pytest.raises(ActiveOrganizationRequired):
        ClerkAuthenticator(make_settings()).authenticate(make_request())


@pytest.mark.parametrize("payload", [None, [], "not-a-payload"])
def test_authenticator_rejects_malformed_payload(
    monkeypatch: pytest.MonkeyPatch,
    payload: object,
) -> None:
    monkeypatch.setattr(
        clerk_module,
        "authenticate_request",
        lambda *_: SimpleNamespace(is_signed_in=True, payload=payload, reason=None),
    )

    with pytest.raises(ClerkAuthenticationRejected) as exc_info:
        ClerkAuthenticator(make_settings()).authenticate(make_request())

    assert exc_info.value.reason == "TOKEN_INVALID_PAYLOAD"


@pytest.mark.asyncio
async def test_auth_dependency_maps_rejection_to_401() -> None:
    class RejectingAuthenticator:
        def authenticate(self, request: Request) -> ClerkPrincipal:
            raise ClerkAuthenticationRejected("TOKEN_INVALID")

    with pytest.raises(HTTPException) as exc_info:
        await require_clerk_principal(make_request(), RejectingAuthenticator())

    assert exc_info.value.status_code == 401
    assert exc_info.value.headers == {"WWW-Authenticate": "Bearer"}


@pytest.mark.asyncio
async def test_auth_dependency_maps_missing_org_to_403() -> None:
    class OrganizationlessAuthenticator:
        def authenticate(self, request: Request) -> ClerkPrincipal:
            raise ActiveOrganizationRequired

    with pytest.raises(HTTPException) as exc_info:
        await require_clerk_principal(make_request(), OrganizationlessAuthenticator())

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "active_organization_required"
