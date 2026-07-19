import asyncio
from collections.abc import AsyncIterator, Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from apps.api.ringiq_api.auth.clerk import ClerkPrincipal, require_tenant_principal
from apps.api.ringiq_api.db.session import get_db_session
from apps.api.ringiq_api.main import create_app
from apps.api.ringiq_api.models.identity import (
    PlatformRole,
    Tenant,
    TenantMembership,
    User,
    UserRealm,
)
from apps.api.ringiq_api.services.clerk_directory import (
    ClerkMembershipNotFound,
    ClerkTenantMembership,
    get_clerk_directory,
)
from tests.api.postgres import create_test_engine, reset_database


class FakeClerkDirectory:
    def __init__(self, membership: ClerkTenantMembership | None) -> None:
        self.membership = membership
        self.calls = 0

    async def get_tenant_membership(
        self,
        *,
        user_id: str,
        organization_id: str,
    ) -> ClerkTenantMembership:
        self.calls += 1
        if self.membership is None:
            raise ClerkMembershipNotFound
        assert user_id == self.membership.user_id
        assert organization_id == self.membership.organization_id
        return self.membership


@pytest.fixture
def onboarding_client() -> Iterator[
    tuple[
        TestClient,
        async_sessionmaker[AsyncSession],
        FakeClerkDirectory,
        ClerkPrincipal,
    ]
]:
    engine = create_test_engine()
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    membership = ClerkTenantMembership(
        organization_id="org_onboarding",
        organization_name="Onboarding Realty",
        organization_slug="onboarding-realty",
        user_id="user_onboarding",
        membership_id="orgmem_onboarding",
        role="org:admin",
        primary_email="owner@example.com",
        display_name="Owner User",
    )
    principal = ClerkPrincipal(
        user_id=membership.user_id,
        organization_id=membership.organization_id,
        organization_role=membership.role,
    )
    directory = FakeClerkDirectory(membership)

    async def setup() -> None:
        await reset_database(engine)

    async def override_session() -> AsyncIterator[AsyncSession]:
        async with session_factory() as session:
            yield session

    asyncio.run(setup())
    app = create_app()
    app.dependency_overrides[get_db_session] = override_session
    app.dependency_overrides[require_tenant_principal] = lambda: principal
    app.dependency_overrides[get_clerk_directory] = lambda: directory
    with TestClient(app) as client:
        yield client, session_factory, directory, principal
    asyncio.run(engine.dispose())


def test_bootstrap_creates_exactly_one_local_tenant_membership(
    onboarding_client: tuple[
        TestClient,
        async_sessionmaker[AsyncSession],
        FakeClerkDirectory,
        ClerkPrincipal,
    ],
) -> None:
    client, session_factory, directory, principal = onboarding_client

    first = client.post("/v1/onboarding/bootstrap")
    second = client.post("/v1/onboarding/bootstrap")

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["clerk_membership_id"] == "orgmem_onboarding"
    assert first.json()["clerk_organization_id"] == principal.organization_id
    assert directory.calls == 2

    async def identity_counts() -> tuple[int, int, int, TenantMembership]:
        async with session_factory() as session:
            users = await session.scalar(select(func.count()).select_from(User))
            tenants = await session.scalar(select(func.count()).select_from(Tenant))
            memberships = await session.scalar(
                select(func.count()).select_from(TenantMembership)
            )
            membership = (
                await session.execute(select(TenantMembership))
            ).scalar_one()
            return users or 0, tenants or 0, memberships or 0, membership

    users, tenants, memberships, local_membership = asyncio.run(identity_counts())
    assert (users, tenants, memberships) == (1, 1, 1)
    assert local_membership.clerk_membership_id == "orgmem_onboarding"
    assert local_membership.role_key == "org:admin"


def test_bootstrap_rejects_user_without_clerk_membership(
    onboarding_client: tuple[
        TestClient,
        async_sessionmaker[AsyncSession],
        FakeClerkDirectory,
        ClerkPrincipal,
    ],
) -> None:
    client, _, directory, _ = onboarding_client
    directory.membership = None

    response = client.post("/v1/onboarding/bootstrap")

    assert response.status_code == 403
    assert response.json()["detail"] == "clerk_organization_membership_required"


def test_bootstrap_does_not_convert_platform_user_into_tenant_user(
    onboarding_client: tuple[
        TestClient,
        async_sessionmaker[AsyncSession],
        FakeClerkDirectory,
        ClerkPrincipal,
    ],
) -> None:
    client, session_factory, _, principal = onboarding_client

    async def seed_platform_user() -> None:
        async with session_factory() as session:
            session.add(
                User(
                    clerk_user_id=principal.user_id,
                    primary_email="platform@ringiq.in",
                    realm=UserRealm.PLATFORM.value,
                    platform_role=PlatformRole.OPERATIONS.value,
                )
            )
            await session.commit()

    asyncio.run(seed_platform_user())
    response = client.post("/v1/onboarding/bootstrap")

    assert response.status_code == 409
    assert response.json()["detail"] == "tenant_identity_conflict"
