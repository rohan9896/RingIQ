import uuid
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError

from apps.api.ringiq_api.auth.clerk import ClerkPrincipal
from apps.api.ringiq_api.auth.context import get_current_tenant_context
from apps.api.ringiq_api.models.identity import Tenant, TenantMembership, User


class FakeResult:
    def __init__(self, row: object) -> None:
        self._row = row

    def one_or_none(self) -> object:
        return self._row


def make_principal() -> ClerkPrincipal:
    return ClerkPrincipal(user_id="user_1", organization_id="org_1")


@pytest.mark.asyncio
async def test_active_membership_resolves_tenant_context() -> None:
    tenant = Tenant(
        id=uuid.uuid4(),
        clerk_organization_id="org_1",
        name="Acme Realty",
        slug="acme-realty",
    )
    user = User(id=uuid.uuid4(), clerk_user_id="user_1")
    membership = TenantMembership(
        id=uuid.uuid4(),
        tenant_id=tenant.id,
        user_id=user.id,
        clerk_membership_id="orgmem_1",
    )
    session = AsyncMock()
    session.execute.return_value = FakeResult((membership, tenant, user))

    context = await get_current_tenant_context(make_principal(), session)

    assert context.tenant_id == tenant.id
    assert context.user_id == user.id
    assert context.clerk_organization_id == "org_1"


@pytest.mark.asyncio
async def test_missing_membership_is_forbidden() -> None:
    session = AsyncMock()
    session.execute.return_value = FakeResult(None)

    with pytest.raises(HTTPException) as exc_info:
        await get_current_tenant_context(make_principal(), session)

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "tenant_membership_not_provisioned"


@pytest.mark.asyncio
async def test_database_failure_is_service_unavailable() -> None:
    session = AsyncMock()
    session.execute.side_effect = SQLAlchemyError("database unavailable")

    with pytest.raises(HTTPException) as exc_info:
        await get_current_tenant_context(make_principal(), session)

    assert exc_info.value.status_code == 503
    assert exc_info.value.detail == "identity_store_unavailable"
