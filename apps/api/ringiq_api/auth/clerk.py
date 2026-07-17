import logging
from dataclasses import dataclass
from collections.abc import Mapping
from typing import Any

from clerk_backend_api import AuthenticateRequestOptions, authenticate_request
from fastapi import Depends, HTTPException, Request, status

from apps.api.ringiq_api.config import IdentitySettings, get_identity_settings

logger = logging.getLogger("ringiq.api.auth")


@dataclass(frozen=True)
class ClerkPrincipal:
    user_id: str
    organization_id: str
    session_id: str | None = None
    organization_role: str | None = None


class ClerkAuthenticationRejected(Exception):
    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


class ActiveOrganizationRequired(Exception):
    pass


class ClerkAuthenticator:
    def __init__(self, settings: IdentitySettings) -> None:
        self._settings = settings

    def authenticate(self, request: Request) -> ClerkPrincipal:
        state = authenticate_request(
            request,
            AuthenticateRequestOptions(
                secret_key=self._settings.clerk_secret_key,
                jwt_key=self._settings.clerk_jwt_public_key,
                authorized_parties=self._settings.clerk_authorized_parties,
                accepts_token=["session_token"],
            ),
        )
        if not state.is_signed_in:
            reason = state.reason.name if state.reason else "UNAUTHORIZED"
            raise ClerkAuthenticationRejected(reason)

        if not isinstance(state.payload, Mapping):
            raise ClerkAuthenticationRejected("TOKEN_INVALID_PAYLOAD")
        payload: Mapping[str, Any] = state.payload
        user_id = payload.get("sub")
        if not isinstance(user_id, str) or not user_id:
            raise ClerkAuthenticationRejected("TOKEN_MISSING_SUBJECT")

        organization_id = payload.get("org_id")
        organization_claim = payload.get("o")
        if not organization_id and isinstance(organization_claim, Mapping):
            organization_id = organization_claim.get("id")
        if not isinstance(organization_id, str) or not organization_id:
            raise ActiveOrganizationRequired

        organization_role = payload.get("org_role")
        if not organization_role and isinstance(organization_claim, Mapping):
            organization_role = organization_claim.get("rol")

        session_id = payload.get("sid")
        return ClerkPrincipal(
            user_id=user_id,
            organization_id=organization_id,
            session_id=session_id if isinstance(session_id, str) else None,
            organization_role=(
                organization_role if isinstance(organization_role, str) else None
            ),
        )


def get_clerk_authenticator(
    settings: IdentitySettings = Depends(get_identity_settings),
) -> ClerkAuthenticator:
    return ClerkAuthenticator(settings)


async def require_clerk_principal(
    request: Request,
    authenticator: ClerkAuthenticator = Depends(get_clerk_authenticator),
) -> ClerkPrincipal:
    try:
        return authenticator.authenticate(request)
    except ClerkAuthenticationRejected as exc:
        logger.info("clerk_auth.rejected path=%s reason=%s", request.url.path, exc.reason)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="unauthorized",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
    except ActiveOrganizationRequired as exc:
        logger.info("clerk_auth.active_organization_required path=%s", request.url.path)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="active_organization_required",
        ) from exc
