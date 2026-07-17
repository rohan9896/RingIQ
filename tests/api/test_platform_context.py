import uuid
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError

from apps.api.ringiq_api.auth.clerk import ClerkPrincipal
from apps.api.ringiq_api.auth.context import get_current_platform_context
from apps.api.ringiq_api.models.identity import PlatformRole, User, UserRealm


class FakeScalarResult:
    def __init__(self, value: object) -> None:
        self._value = value

    def scalar_one_or_none(self) -> object:
        return self._value


def make_principal(organization_id: str | None = None) -> ClerkPrincipal:
    return ClerkPrincipal(user_id="user_platform", organization_id=organization_id)


@pytest.mark.asyncio
async def test_active_platform_user_resolves_context() -> None:
    user = User(
        id=uuid.uuid4(),
        clerk_user_id="user_platform",
        primary_email="ops@ringiq.in",
        realm=UserRealm.PLATFORM.value,
        platform_role=PlatformRole.OPERATIONS.value,
    )
    session = AsyncMock()
    session.execute.return_value = FakeScalarResult(user)

    context = await get_current_platform_context(make_principal(), session)

    assert context.user_id == user.id
    assert context.role == PlatformRole.OPERATIONS


@pytest.mark.asyncio
async def test_platform_context_rejects_active_tenant_organization() -> None:
    session = AsyncMock()

    with pytest.raises(HTTPException) as exc_info:
        await get_current_platform_context(make_principal("org_1"), session)

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "platform_identity_has_active_organization"
    session.execute.assert_not_awaited()


@pytest.mark.asyncio
async def test_unprovisioned_platform_user_is_forbidden() -> None:
    session = AsyncMock()
    session.execute.return_value = FakeScalarResult(None)

    with pytest.raises(HTTPException) as exc_info:
        await get_current_platform_context(make_principal(), session)

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "platform_access_not_provisioned"


@pytest.mark.asyncio
async def test_platform_database_failure_is_service_unavailable() -> None:
    session = AsyncMock()
    session.execute.side_effect = SQLAlchemyError("database unavailable")

    with pytest.raises(HTTPException) as exc_info:
        await get_current_platform_context(make_principal(), session)

    assert exc_info.value.status_code == 503
    assert exc_info.value.detail == "identity_store_unavailable"
