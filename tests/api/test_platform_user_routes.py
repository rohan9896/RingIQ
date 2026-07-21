import asyncio
import hashlib
import uuid
from collections.abc import AsyncIterator, Iterator, Mapping
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from apps.api.ringiq_api.auth.clerk import ClerkPrincipal, require_clerk_principal
from apps.api.ringiq_api.auth.context import PlatformContext, get_current_platform_context
from apps.api.ringiq_api.config import get_identity_settings
from apps.api.ringiq_api.db.session import get_db_session
from apps.api.ringiq_api.main import create_app
from apps.api.ringiq_api.models.identity import (
    PlatformRole,
    PlatformUserInvitation,
    RecordStatus,
    User,
    UserRealm,
    WebhookReceipt,
)
from apps.api.ringiq_api.routes import webhooks
from apps.api.ringiq_api.services.clerk_directory import (
    ClerkDirectoryUnavailable,
    ClerkPlatformUser,
    get_clerk_directory,
)
from apps.api.ringiq_api.services.platform_identity import (
    INVITATION_METADATA_KEY,
    platform_user_from_webhook,
)
from tests.api.helpers import make_settings
from tests.api.postgres import create_test_engine, reset_database


class FakePlatformDirectory:
    def __init__(self) -> None:
        self.created: list[dict[str, str]] = []
        self.revoked: list[str] = []
        self.mirrored: list[tuple[str, Mapping[str, Any]]] = []
        self.platform_user: ClerkPlatformUser | None = None
        self.create_error = False
        self.mirror_error = False

    async def create_platform_invitation(
        self, *, email: str, invitation_id: str, redirect_url: str
    ) -> str:
        if self.create_error:
            raise ClerkDirectoryUnavailable
        self.created.append(
            {"email": email, "invitation_id": invitation_id, "redirect_url": redirect_url}
        )
        return f"inv_{len(self.created)}"

    async def revoke_platform_invitation(self, *, invitation_id: str) -> None:
        self.revoked.append(invitation_id)

    async def get_platform_user(self, *, user_id: str) -> ClerkPlatformUser:
        assert self.platform_user is not None
        assert self.platform_user.user_id == user_id
        return self.platform_user

    async def mirror_platform_metadata(
        self, *, user_id: str, metadata: Mapping[str, Any]
    ) -> None:
        if self.mirror_error:
            raise ClerkDirectoryUnavailable
        self.mirrored.append((user_id, metadata))


@pytest.fixture
def platform_identity_client() -> Iterator[
    tuple[
        TestClient,
        async_sessionmaker[AsyncSession],
        FakePlatformDirectory,
        PlatformContext,
        ClerkPrincipal,
    ]
]:
    engine = create_test_engine()
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    context = PlatformContext(
        user_id=uuid.uuid4(),
        clerk_user_id="user_admin",
        primary_email="admin@ringiq.in",
        display_name="Admin",
        role=PlatformRole.SUPER_ADMIN,
    )
    principal = ClerkPrincipal(user_id="user_invited", organization_id=None)
    directory = FakePlatformDirectory()

    async def setup() -> None:
        await reset_database(engine)
        async with session_factory() as session:
            session.add(
                User(
                    id=context.user_id,
                    clerk_user_id=context.clerk_user_id,
                    primary_email=context.primary_email,
                    display_name=context.display_name,
                    realm=UserRealm.PLATFORM.value,
                    platform_role=context.role.value,
                )
            )
            await session.commit()

    async def override_session() -> AsyncIterator[AsyncSession]:
        async with session_factory() as session:
            yield session

    asyncio.run(setup())
    app = create_app()
    app.dependency_overrides[get_db_session] = override_session
    app.dependency_overrides[get_current_platform_context] = lambda: context
    app.dependency_overrides[require_clerk_principal] = lambda: principal
    app.dependency_overrides[get_clerk_directory] = lambda: directory
    app.dependency_overrides[get_identity_settings] = lambda: make_settings(
        clerk_webhook_signing_secret="whsec_test"
    )
    with TestClient(app) as client:
        yield client, session_factory, directory, context, principal
    asyncio.run(engine.dispose())


def test_super_admin_can_invite_list_and_revoke_platform_user(
    platform_identity_client,
) -> None:
    client, _, directory, _, _ = platform_identity_client
    created = client.post(
        "/v1/platform/user-invitations",
        json={
            "email": " Ops@Example.com ",
            "display_name": "Ops User",
            "role": "platform_operations",
        },
    )
    assert created.status_code == 201
    body = created.json()
    assert body["email"] == "ops@example.com"
    assert body["platform_role"] == "platform_operations"
    assert body["status"] == "pending"
    assert directory.created[0]["redirect_url"].endswith(
        "/platform/accept-invitation"
    )

    listed = client.get("/v1/platform/user-invitations")
    assert listed.status_code == 200
    assert listed.json()[0]["id"] == body["id"]

    revoked = client.post(
        f"/v1/platform/user-invitations/{body['id']}/revoke"
    )
    assert revoked.status_code == 200
    assert revoked.json()["status"] == "revoked"
    assert directory.revoked == ["inv_1"]


def test_duplicate_open_invitation_returns_conflict(platform_identity_client) -> None:
    client, _, _, _, _ = platform_identity_client
    payload = {"email": "ops@example.com", "role": "platform_operations"}
    assert client.post("/v1/platform/user-invitations", json=payload).status_code == 201
    response = client.post("/v1/platform/user-invitations", json=payload)
    assert response.status_code == 409
    assert response.json()["detail"] == "platform_identity_conflict"


def test_non_super_admin_cannot_manage_platform_users(
    platform_identity_client,
) -> None:
    client, _, _, context, _ = platform_identity_client
    operations = PlatformContext(
        user_id=context.user_id,
        clerk_user_id=context.clerk_user_id,
        primary_email=context.primary_email,
        display_name=context.display_name,
        role=PlatformRole.OPERATIONS,
    )
    client.app.dependency_overrides[get_current_platform_context] = lambda: operations

    assert client.get("/v1/platform/users").status_code == 403
    assert client.get("/v1/platform/user-invitations").status_code == 403
    assert (
        client.post(
            "/v1/platform/user-invitations",
            json={"email": "blocked@example.com", "role": "platform_operations"},
        ).status_code
        == 403
    )


def test_existing_tenant_email_conflicts_with_platform_invitation(
    platform_identity_client,
) -> None:
    client, session_factory, _, _, _ = platform_identity_client

    async def seed_tenant_user() -> None:
        async with session_factory() as session:
            session.add(
                User(
                    clerk_user_id="user_tenant",
                    primary_email="tenant@example.com",
                    realm=UserRealm.TENANT.value,
                    platform_role=None,
                )
            )
            await session.commit()

    asyncio.run(seed_tenant_user())
    response = client.post(
        "/v1/platform/user-invitations",
        json={"email": "TENANT@example.com", "role": "platform_operations"},
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "platform_identity_conflict"


def test_clerk_invitation_failure_marks_local_record_failed(
    platform_identity_client,
) -> None:
    client, session_factory, directory, _, _ = platform_identity_client
    directory.create_error = True

    response = client.post(
        "/v1/platform/user-invitations",
        json={"email": "failure@example.com", "role": "platform_operations"},
    )
    assert response.status_code == 502

    async def invitation_status() -> tuple[str, str | None]:
        async with session_factory() as session:
            invitation = await session.scalar(
                select(PlatformUserInvitation).where(
                    PlatformUserInvitation.email == "failure@example.com"
                )
            )
            assert invitation is not None
            return invitation.status, invitation.failure_reason

    assert asyncio.run(invitation_status()) == (
        "failed",
        "clerk_directory_unavailable",
    )


def test_synchronous_completion_provisions_from_database_invitation(
    platform_identity_client,
) -> None:
    client, _, directory, _, principal = platform_identity_client
    invitation = client.post(
        "/v1/platform/user-invitations",
        json={"email": "invited@example.com", "role": "template_manager"},
    ).json()
    directory.platform_user = ClerkPlatformUser(
        user_id=principal.user_id,
        primary_email="invited@example.com",
        primary_email_verified=True,
        display_name="Invited User",
        public_metadata={INVITATION_METADATA_KEY: invitation["id"]},
    )

    first = client.post("/v1/platform/onboarding/complete")
    second = client.post("/v1/platform/onboarding/complete")

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["platform_role"] == "template_manager"
    assert first.json()["status"] == "active"
    assert second.json()["id"] == first.json()["id"]
    assert directory.mirrored[-1][1]["platform_role"] == "template_manager"


def test_completion_rejects_active_organization(platform_identity_client) -> None:
    client, _, _, _, principal = platform_identity_client
    principal_with_org = ClerkPrincipal(
        user_id=principal.user_id, organization_id="org_tenant"
    )
    client.app.dependency_overrides[require_clerk_principal] = lambda: principal_with_org

    response = client.post("/v1/platform/onboarding/complete")

    assert response.status_code == 403
    assert response.json()["detail"] == "platform_identity_has_active_organization"


def test_completion_rejects_mismatched_verified_email(
    platform_identity_client,
) -> None:
    client, _, directory, _, principal = platform_identity_client
    invitation = client.post(
        "/v1/platform/user-invitations",
        json={"email": "expected@example.com", "role": "template_manager"},
    ).json()
    directory.platform_user = ClerkPlatformUser(
        user_id=principal.user_id,
        primary_email="different@example.com",
        primary_email_verified=True,
        display_name="Wrong Account",
        public_metadata={INVITATION_METADATA_KEY: invitation["id"]},
    )

    response = client.post("/v1/platform/onboarding/complete")

    assert response.status_code == 403
    assert response.json()["detail"] == "platform_invitation_invalid"


def test_webhook_provisions_once_and_deduplicates_delivery(
    platform_identity_client, monkeypatch
) -> None:
    client, session_factory, directory, _, _ = platform_identity_client
    invitation = client.post(
        "/v1/platform/user-invitations",
        json={"email": "hook@example.com", "role": "platform_operations"},
    ).json()
    event = {
        "type": "user.created",
        "data": {
            "id": "user_hook",
            "primary_email_address_id": "idn_primary",
            "email_addresses": [
                {
                    "id": "idn_primary",
                    "email_address": "hook@example.com",
                    "verification": {"status": "verified"},
                }
            ],
            "first_name": "Hook",
            "last_name": "User",
            "public_metadata": {INVITATION_METADATA_KEY: invitation["id"]},
        },
    }
    directory.platform_user = platform_user_from_webhook(event["data"])
    monkeypatch.setattr(webhooks, "verify_clerk_webhook", lambda *_: event)
    headers = {"webhook-id": "evt_1", "webhook-signature": "test"}

    assert client.post("/webhooks/clerk", content=b"event", headers=headers).status_code == 200
    assert client.post("/webhooks/clerk", content=b"event", headers=headers).status_code == 200

    async def counts() -> tuple[int, int, str]:
        async with session_factory() as session:
            users = await session.scalar(select(func.count()).select_from(User))
            receipts = await session.scalar(
                select(func.count()).select_from(WebhookReceipt)
            )
            invite = await session.get(PlatformUserInvitation, uuid.UUID(invitation["id"]))
            return users or 0, receipts or 0, invite.status

    assert asyncio.run(counts()) == (2, 1, "accepted")
    assert len(directory.mirrored) == 1


def test_deleted_user_webhook_marks_local_user_inactive(
    platform_identity_client, monkeypatch
) -> None:
    client, session_factory, _, context, _ = platform_identity_client
    event = {"type": "user.deleted", "data": {"id": context.clerk_user_id}}
    monkeypatch.setattr(webhooks, "verify_clerk_webhook", lambda *_: event)

    response = client.post(
        "/webhooks/clerk",
        content=b"deleted",
        headers={"webhook-id": "evt_deleted"},
    )
    assert response.status_code == 200

    async def status() -> str:
        async with session_factory() as session:
            user = await session.get(User, context.user_id)
            return user.status

    assert asyncio.run(status()) == RecordStatus.INACTIVE.value


def test_webhook_private_metadata_cannot_change_database_authority(
    platform_identity_client, monkeypatch
) -> None:
    client, session_factory, directory, context, _ = platform_identity_client
    event = {
        "type": "user.updated",
        "data": {
            "id": context.clerk_user_id,
            "primary_email_address_id": "idn_primary",
            "email_addresses": [
                {
                    "id": "idn_primary",
                    "email_address": "renamed@ringiq.in",
                    "verification": {"status": "verified"},
                }
            ],
            "first_name": "Renamed",
            "private_metadata": {
                "ringiq": {
                    "realm": "tenant",
                    "platform_role": "template_manager",
                    "status": "suspended",
                }
            },
        },
    }
    directory.platform_user = platform_user_from_webhook(event["data"])
    monkeypatch.setattr(webhooks, "verify_clerk_webhook", lambda *_: event)

    response = client.post(
        "/webhooks/clerk",
        content=b"updated",
        headers={"webhook-id": "evt_tampered_metadata"},
    )
    assert response.status_code == 200

    async def authority() -> tuple[str, str | None, str, str | None]:
        async with session_factory() as session:
            user = await session.get(User, context.user_id)
            assert user is not None
            return user.realm, user.platform_role, user.status, user.primary_email

    assert asyncio.run(authority()) == (
        UserRealm.PLATFORM.value,
        PlatformRole.SUPER_ADMIN.value,
        RecordStatus.ACTIVE.value,
        "renamed@ringiq.in",
    )


def test_webhook_fetches_current_clerk_profile_and_does_not_remirror_equal_metadata(
    platform_identity_client, monkeypatch
) -> None:
    client, session_factory, directory, context, _ = platform_identity_client
    event = {
        "type": "user.updated",
        "data": {
            "id": context.clerk_user_id,
            "primary_email_address_id": "idn_primary",
            "email_addresses": [
                {
                    "id": "idn_primary",
                    "email_address": "old@ringiq.in",
                    "verification": {"status": "verified"},
                }
            ],
            "first_name": "Old",
        },
    }
    directory.platform_user = ClerkPlatformUser(
        user_id=context.clerk_user_id,
        primary_email="current@ringiq.in",
        primary_email_verified=True,
        display_name="Current Profile",
        public_metadata={},
        private_metadata={
            "ringiq": {
                "internal_user_id": str(context.user_id),
                "realm": "platform",
                "platform_role": "platform_super_admin",
                "status": "active",
            }
        },
    )
    monkeypatch.setattr(webhooks, "verify_clerk_webhook", lambda *_: event)

    response = client.post(
        "/webhooks/clerk",
        content=b"stale-update",
        headers={"webhook-id": "evt_stale_update"},
    )
    assert response.status_code == 200

    async def profile() -> tuple[str | None, str | None]:
        async with session_factory() as session:
            user = await session.get(User, context.user_id)
            assert user is not None
            return user.primary_email, user.display_name

    assert asyncio.run(profile()) == ("current@ringiq.in", "Current Profile")
    assert directory.mirrored == []


def test_failed_webhook_retry_converges_without_duplicate_user(
    platform_identity_client, monkeypatch
) -> None:
    client, session_factory, directory, _, _ = platform_identity_client
    invitation = client.post(
        "/v1/platform/user-invitations",
        json={"email": "retry@example.com", "role": "platform_operations"},
    ).json()
    event = {
        "type": "user.created",
        "data": {
            "id": "user_retry",
            "primary_email_address_id": "idn_primary",
            "email_addresses": [
                {
                    "id": "idn_primary",
                    "email_address": "retry@example.com",
                    "verification": {"status": "verified"},
                }
            ],
            "public_metadata": {INVITATION_METADATA_KEY: invitation["id"]},
        },
    }
    directory.platform_user = platform_user_from_webhook(event["data"])
    monkeypatch.setattr(webhooks, "verify_clerk_webhook", lambda *_: event)
    directory.mirror_error = True
    headers = {"webhook-id": "evt_retry"}

    assert client.post("/webhooks/clerk", content=b"retry", headers=headers).status_code == 500
    directory.mirror_error = False
    assert client.post("/webhooks/clerk", content=b"retry", headers=headers).status_code == 200

    async def state() -> tuple[int, str]:
        async with session_factory() as session:
            user_count = await session.scalar(
                select(func.count())
                .select_from(User)
                .where(User.clerk_user_id == "user_retry")
            )
            receipt = await session.scalar(
                select(WebhookReceipt).where(WebhookReceipt.delivery_id == "evt_retry")
            )
            assert receipt is not None
            return user_count or 0, receipt.status

    assert asyncio.run(state()) == (1, "processed")


def test_invalid_webhook_signature_is_rejected(platform_identity_client, monkeypatch) -> None:
    client, _, _, _, _ = platform_identity_client

    def reject(*_):
        raise ValueError("bad signature")

    monkeypatch.setattr(webhooks, "verify_clerk_webhook", reject)
    response = client.post(
        "/webhooks/clerk", content=b"event", headers={"webhook-id": "evt_bad"}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "invalid_webhook_signature"


def test_processing_webhook_receipt_retries_after_lease_expires(
    platform_identity_client, monkeypatch
) -> None:
    client, session_factory, _, _, _ = platform_identity_client
    body = b"lease"
    event = {"type": "session.created", "data": {"id": "session_1"}}
    monkeypatch.setattr(webhooks, "verify_clerk_webhook", lambda *_: event)

    async def seed_receipt() -> None:
        async with session_factory() as session:
            session.add(
                WebhookReceipt(
                    provider="clerk",
                    delivery_id="evt_processing",
                    event_type="session.created",
                    payload_hash=hashlib.sha256(body).hexdigest(),
                    status="processing",
                    updated_at=datetime.now(UTC),
                )
            )
            await session.commit()

    asyncio.run(seed_receipt())
    headers = {"webhook-id": "evt_processing"}
    assert client.post("/webhooks/clerk", content=body, headers=headers).status_code == 503

    async def expire_lease() -> None:
        async with session_factory() as session:
            receipt = await session.scalar(
                select(WebhookReceipt).where(
                    WebhookReceipt.delivery_id == "evt_processing"
                )
            )
            assert receipt is not None
            receipt.updated_at = datetime.now(UTC) - timedelta(minutes=2)
            await session.commit()

    asyncio.run(expire_lease())
    assert client.post("/webhooks/clerk", content=body, headers=headers).status_code == 200
