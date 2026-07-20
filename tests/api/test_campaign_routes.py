import asyncio
import uuid
from collections.abc import AsyncIterator, Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from types import SimpleNamespace

from apps.api.ringiq_api.auth.context import TenantContext, get_current_tenant_context
from apps.api.ringiq_api.config import AppSettings, get_app_settings
from apps.api.ringiq_api.db.session import get_db_session
from apps.api.ringiq_api.main import create_app
from apps.api.ringiq_api.models.campaigns import Job, JobStatus
from apps.api.ringiq_api.models.identity import Tenant, User
from apps.api.ringiq_api.models.knowledge import (
    TenantKnowledgeBase,
    TenantKnowledgeBaseVersion,
)
from apps.api.ringiq_api.services.campaign_operations import CALL_JOB_TYPE
from tests.api.postgres import create_test_engine, reset_database


def make_context() -> TenantContext:
    return TenantContext(
        tenant_id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        membership_id=uuid.uuid4(),
        clerk_organization_id="org_campaign",
        clerk_user_id="user_campaign",
        clerk_membership_id="orgmem_campaign",
        tenant_name="Campaign Realty",
        tenant_slug="campaign-realty",
        timezone="Asia/Kolkata",
    )


@pytest.fixture
def campaign_client() -> Iterator[tuple[TestClient, async_sessionmaker[AsyncSession], TenantContext]]:
    engine = create_test_engine()
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    context = make_context()

    async def setup() -> None:
        await reset_database(engine)
        async with session_factory() as session:
            session.add_all(
                [
                    Tenant(
                        id=context.tenant_id,
                        clerk_organization_id=context.clerk_organization_id,
                        name=context.tenant_name,
                        slug=context.tenant_slug,
                    ),
                    User(id=context.user_id, clerk_user_id=context.clerk_user_id),
                ]
            )
            await session.commit()

    async def override_session() -> AsyncIterator[AsyncSession]:
        async with session_factory() as session:
            yield session

    asyncio.run(setup())
    app = create_app()
    app.dependency_overrides[get_current_tenant_context] = lambda: context
    app.dependency_overrides[get_db_session] = override_session
    with TestClient(app) as client:
        yield client, session_factory, context
    asyncio.run(engine.dispose())


def import_leads(client: TestClient, count: int = 2) -> list[str]:
    rows = [
        f"Lead {index},lead{index}@example.com,98986345{index:02d}"
        for index in range(count)
    ]
    response = client.post(
        "/v1/lead-imports",
        json={
            "filename": "campaign.csv",
            "csv_content": "Name,Email,Phone\n" + "\n".join(rows) + "\n",
        },
    )
    assert response.status_code == 201
    return [row["lead_id"] for row in response.json()["rows"]]


async def seed_active_knowledge_base(
    session_factory: async_sessionmaker[AsyncSession],
    context: TenantContext,
    *,
    title: str = "Campaign knowledge",
    business_name: str = "Campaign Realty",
) -> uuid.UUID:
    async with session_factory() as session:
        workspace = TenantKnowledgeBase(tenant_id=context.tenant_id)
        session.add(workspace)
        await session.flush()
        version = TenantKnowledgeBaseVersion(
            knowledge_base_id=workspace.id,
            tenant_id=context.tenant_id,
            version=1,
            title=title,
            business_profile_json={"business_name": business_name},
            status="published",
            created_by_user_id=context.user_id,
        )
        session.add(version)
        await session.flush()
        workspace.active_version_id = version.id
        await session.commit()
        return version.id


async def publish_next_active_knowledge_base(
    session_factory: async_sessionmaker[AsyncSession],
    context: TenantContext,
    *,
    title: str,
) -> uuid.UUID:
    async with session_factory() as session:
        workspace = (
            await session.execute(
                select(TenantKnowledgeBase).where(
                    TenantKnowledgeBase.tenant_id == context.tenant_id
                )
            )
        ).scalar_one()
        version = TenantKnowledgeBaseVersion(
            knowledge_base_id=workspace.id,
            tenant_id=context.tenant_id,
            version=2,
            title=title,
            business_profile_json={"business_name": "Campaign Realty"},
            status="published",
            created_by_user_id=context.user_id,
        )
        session.add(version)
        await session.flush()
        workspace.active_version_id = version.id
        await session.commit()
        return version.id


def test_campaign_draft_reports_readiness_blockers(
    campaign_client: tuple[TestClient, async_sessionmaker[AsyncSession], TenantContext],
) -> None:
    client, _, _ = campaign_client
    lead_ids = import_leads(client, 1)

    created = client.post(
        "/v1/campaigns",
        json={"name": "July prospects", "lead_ids": lead_ids},
    )

    assert created.status_code == 201
    assert created.json()["status"] == "draft"
    assert created.json()["readiness"] == {
        "is_ready": False,
        "blockers": ["active_knowledge_base_required"],
    }
    start = client.post(f"/v1/campaigns/{created.json()['id']}/start")
    assert start.status_code == 422
    assert start.json()["detail"]["code"] == "campaign_not_ready"


def test_campaign_lifecycle_creates_durable_call_jobs(
    campaign_client: tuple[TestClient, async_sessionmaker[AsyncSession], TenantContext],
) -> None:
    client, session_factory, context = campaign_client
    kb_id = asyncio.run(seed_active_knowledge_base(session_factory, context))
    lead_ids = import_leads(client, 2)
    created = client.post(
        "/v1/campaigns",
        json={"name": "Ready campaign", "lead_ids": lead_ids, "retry_limit": 3},
    )
    assert created.status_code == 201
    assert created.json()["status"] == "ready"
    assert created.json()["knowledge_base_version_id"] == str(kb_id)
    assert created.json()["knowledge_base"] == {
        "id": str(kb_id),
        "title": "Campaign knowledge",
        "version": 1,
        "status": "published",
        "category_id": None,
        "is_pinned": True,
    }
    assert created.json()["progress"]["total"] == 2

    started = client.post(f"/v1/campaigns/{created.json()['id']}/start")
    assert started.status_code == 200
    assert started.json()["status"] == "running"
    assert started.json()["retry_limit"] == 3
    assert started.json()["progress"]["queued"] == 2
    assert started.json()["knowledge_base_version_id"] == str(kb_id)
    assert started.json()["knowledge_base"]["is_pinned"] is True

    async def job_count() -> int:
        async with session_factory() as session:
            return len(
                list(
                    (
                        await session.execute(
                            select(Job).where(
                                Job.job_type == CALL_JOB_TYPE,
                                Job.status == JobStatus.PENDING.value,
                            )
                        )
                    ).scalars()
                )
            )

    assert asyncio.run(job_count()) == 2
    assert client.post(f"/v1/campaigns/{created.json()['id']}/pause").json()["status"] == "paused"
    assert client.post(f"/v1/campaigns/{created.json()['id']}/resume").json()["status"] == "running"
    cancelled = client.post(f"/v1/campaigns/{created.json()['id']}/cancel")
    assert cancelled.status_code == 200
    assert cancelled.json()["status"] == "cancelled"
    assert cancelled.json()["progress"]["cancelled"] == 2


def test_campaign_start_keeps_creation_time_knowledge_base_pin(
    campaign_client: tuple[TestClient, async_sessionmaker[AsyncSession], TenantContext],
) -> None:
    client, session_factory, context = campaign_client
    first_kb_id = asyncio.run(
        seed_active_knowledge_base(session_factory, context, title="Launch KB v1")
    )
    lead_id = import_leads(client, 1)[0]
    campaign = client.post(
        "/v1/campaigns", json={"name": "Stable KB campaign", "lead_ids": [lead_id]}
    ).json()
    assert campaign["knowledge_base_version_id"] == str(first_kb_id)

    second_kb_id = asyncio.run(
        publish_next_active_knowledge_base(session_factory, context, title="Launch KB v2")
    )
    assert second_kb_id != first_kb_id

    fetched = client.get(f"/v1/campaigns/{campaign['id']}").json()
    assert fetched["knowledge_base"] == {
        "id": str(first_kb_id),
        "title": "Launch KB v1",
        "version": 1,
        "status": "published",
        "category_id": None,
        "is_pinned": True,
    }

    started = client.post(f"/v1/campaigns/{campaign['id']}/start")
    assert started.status_code == 200
    assert started.json()["knowledge_base_version_id"] == str(first_kb_id)
    assert started.json()["knowledge_base"]["title"] == "Launch KB v1"


def test_campaigns_and_lead_history_are_tenant_scoped(
    campaign_client: tuple[TestClient, async_sessionmaker[AsyncSession], TenantContext],
) -> None:
    client, session_factory, context = campaign_client
    asyncio.run(seed_active_knowledge_base(session_factory, context))
    lead_id = import_leads(client, 1)[0]
    campaign = client.post(
        "/v1/campaigns", json={"name": "Private", "lead_ids": [lead_id]}
    ).json()
    history = client.get(f"/v1/leads/{lead_id}/campaign-history")
    assert history.status_code == 200
    assert history.json()[0]["campaign_id"] == campaign["id"]

    client.app.dependency_overrides[get_current_tenant_context] = lambda: TenantContext(
        tenant_id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        membership_id=uuid.uuid4(),
        clerk_organization_id="org_other",
        clerk_user_id="user_other",
        clerk_membership_id="orgmem_other",
        tenant_name="Other",
        tenant_slug="other",
        timezone="Asia/Kolkata",
    )
    assert client.get(f"/v1/campaigns/{campaign['id']}").status_code == 404
    assert client.get(f"/v1/leads/{lead_id}/campaign-history").status_code == 404


def test_call_artifacts_are_stored_and_tenant_scoped(
    campaign_client: tuple[TestClient, async_sessionmaker[AsyncSession], TenantContext],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client, session_factory, context = campaign_client
    asyncio.run(seed_active_knowledge_base(session_factory, context))
    lead_id = import_leads(client, 1)[0]
    campaign = client.post(
        "/v1/campaigns", json={"name": "Recorded calls", "lead_ids": [lead_id]}
    ).json()
    client.post(f"/v1/campaigns/{campaign['id']}/start")

    from apps.worker import main as worker_module

    async def fake_create_campaign_call(*args, **kwargs):
        return SimpleNamespace(
            livekit_sip_call_id="sip_artifact",
            room_name=kwargs["room_name"],
        )

    monkeypatch.setattr(worker_module, "get_session_factory", lambda: session_factory)
    monkeypatch.setattr(worker_module, "get_voice_settings", lambda: object())
    monkeypatch.setattr(
        worker_module.LiveKitCallService,
        "create_campaign_call",
        fake_create_campaign_call,
    )
    asyncio.run(worker_module.process_next_call_job("artifact-worker"))
    detail = client.get(f"/v1/campaigns/{campaign['id']}").json()
    attempt_id = detail["enrollments"][0]["attempts"][0]["id"]
    client.app.dependency_overrides[get_app_settings] = lambda: AppSettings(
        internal_api_key="artifact-secret"
    )

    unauthorized = client.post(
        f"/v1/internal/call-attempts/{attempt_id}/artifacts",
        json={"transcript": []},
    )
    assert unauthorized.status_code == 401

    stored = client.post(
        f"/v1/internal/call-attempts/{attempt_id}/artifacts",
        headers={"X-RingIQ-Internal-Key": "artifact-secret"},
        json={
            "transcript": [
                {"role": "assistant", "text": "Aapka budget kya hai?"},
                {"role": "user", "text": "Do crore."},
            ],
            "recording_egress_id": "EG_test",
            "recording_status": "available",
            "recording_storage_uri": "s3://recordings/call.mp3",
            "recording_url": "https://media.example.com/call.mp3",
        },
    )
    assert stored.status_code == 200
    assert stored.json() == {"status": "stored"}

    completed = client.post(
        f"/v1/internal/call-attempts/{attempt_id}/result",
        headers={"X-RingIQ-Internal-Key": "artifact-secret"},
        json={
            "status": "completed",
            "terminal_reason": "participant_disconnected",
        },
    )
    assert completed.status_code == 200
    repeated = client.post(
        f"/v1/internal/call-attempts/{attempt_id}/artifacts",
        headers={"X-RingIQ-Internal-Key": "artifact-secret"},
        json={
            "transcript": [
                {"role": "assistant", "text": "Aapka budget kya hai?"},
                {"role": "user", "text": "Do crore."},
            ]
        },
    )
    assert repeated.status_code == 200
    changed_transcript = client.post(
        f"/v1/internal/call-attempts/{attempt_id}/artifacts",
        headers={"X-RingIQ-Internal-Key": "artifact-secret"},
        json={"transcript": [{"role": "user", "text": "Different."}]},
    )
    assert changed_transcript.status_code == 409
    null_transcript = client.post(
        f"/v1/internal/call-attempts/{attempt_id}/artifacts",
        headers={"X-RingIQ-Internal-Key": "artifact-secret"},
        json={"transcript": None},
    )
    assert null_transcript.status_code == 422

    from apps.api.ringiq_api.services.post_call_outcomes import (
        ExtractedOutcome,
        OutcomeEvidence,
        QualificationFacts,
    )

    class FakeExtractor:
        provider = "test"
        model = "test-model"

        async def extract(self, **_: object) -> ExtractedOutcome:
            return ExtractedOutcome(
                label="warm",
                confidence=0.9,
                rationale="The customer shared a budget.",
                summary="The customer has a two crore budget.",
                qualification_facts=QualificationFacts(budget="Do crore"),
                evidence=[OutcomeEvidence(turn_index=1, speaker="user", quote="Do crore.")],
            )

    monkeypatch.setattr(worker_module, "extractor_from_settings", lambda _: FakeExtractor())
    monkeypatch.setattr(
        worker_module,
        "get_app_settings",
        lambda: AppSettings(post_call_outcome_api_key="test-key"),
    )
    assert asyncio.run(worker_module.process_next_call_job("outcome-worker")) is True

    calls = client.get("/v1/calls")
    assert calls.status_code == 200
    call = calls.json()[0]
    assert call["id"] == attempt_id
    assert call["lead_id"] == lead_id
    assert call["transcript"][1]["text"] == "Do crore."
    assert call["recording_url"] == "https://media.example.com/call.mp3"
    assert call["terminal_reason"] == "participant_disconnected"
    assert call["outcome"]["label"] == "warm"
    assert call["outcome"]["evidence"][0]["quote"] == "Do crore."
    history = client.get(f"/v1/leads/{lead_id}/campaign-history").json()
    assert history[0]["attempts"][0]["outcome"] == call["outcome"]

    async def post_call_job_count() -> int:
        async with session_factory() as session:
            return len(
                list(
                    (
                        await session.execute(
                            select(Job).where(Job.job_type == "call.post_call_outcome")
                        )
                    ).scalars()
                )
            )

    assert asyncio.run(post_call_job_count()) == 1

    client.app.dependency_overrides[get_current_tenant_context] = lambda: TenantContext(
        tenant_id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        membership_id=uuid.uuid4(),
        clerk_organization_id="org_artifact_other",
        clerk_user_id="user_artifact_other",
        clerk_membership_id="orgmem_artifact_other",
        tenant_name="Other tenant",
        tenant_slug="other-tenant",
        timezone="Asia/Kolkata",
    )
    assert client.get("/v1/calls").json() == []


def test_worker_creates_attempt_and_connected_call_completes_campaign(
    campaign_client: tuple[TestClient, async_sessionmaker[AsyncSession], TenantContext],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client, session_factory, context = campaign_client
    asyncio.run(seed_active_knowledge_base(session_factory, context))
    lead_id = import_leads(client, 1)[0]
    campaign = client.post(
        "/v1/campaigns", json={"name": "Worker campaign", "lead_ids": [lead_id]}
    ).json()
    client.post(f"/v1/campaigns/{campaign['id']}/start")

    from apps.worker import main as worker_module

    dispatched: dict = {}

    async def fake_create_campaign_call(*args, **kwargs):
        dispatched.update(kwargs)
        return SimpleNamespace(
            livekit_sip_call_id="sip_call_1",
            room_name=kwargs["room_name"],
        )

    monkeypatch.setattr(worker_module, "get_session_factory", lambda: session_factory)
    monkeypatch.setattr(worker_module, "get_voice_settings", lambda: object())
    monkeypatch.setattr(
        worker_module.LiveKitCallService,
        "create_campaign_call",
        fake_create_campaign_call,
    )

    assert asyncio.run(worker_module.process_next_call_job("test-worker")) is True
    detail = client.get(f"/v1/campaigns/{campaign['id']}").json()
    assert detail["progress"]["calling"] == 1
    attempt = detail["enrollments"][0]["attempts"][0]
    assert attempt["attempt_number"] == 1
    assert attempt["status"] == "dialing"
    assert attempt["provider_call_id"] == "sip_call_1"
    assert dispatched["metadata"]["lead_name"] == "Lead 0"
    assert '"organization_name": "Campaign Realty"' in dispatched["metadata"]["agent_context_json"]

    connected = client.post(
        f"/v1/call-attempts/{attempt['id']}/result",
        json={"status": "connected", "provider_call_id": "sip_call_1"},
    )
    assert connected.status_code == 200
    assert connected.json()["progress"]["connected"] == 1

    completed = client.post(
        f"/v1/call-attempts/{attempt['id']}/result",
        json={"status": "completed", "duration_seconds": 42},
    )
    assert completed.status_code == 200
    assert completed.json()["status"] == "completed"
    assert completed.json()["progress"]["completed"] == 1

    regression = client.post(
        f"/v1/call-attempts/{attempt['id']}/result",
        json={"status": "unanswered"},
    )
    assert regression.status_code == 409


def test_unanswered_call_schedules_one_retry_idempotently(
    campaign_client: tuple[TestClient, async_sessionmaker[AsyncSession], TenantContext],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client, session_factory, context = campaign_client
    asyncio.run(seed_active_knowledge_base(session_factory, context))
    lead_id = import_leads(client, 1)[0]
    campaign = client.post(
        "/v1/campaigns", json={"name": "Retry campaign", "lead_ids": [lead_id]}
    ).json()
    client.post(f"/v1/campaigns/{campaign['id']}/start")

    from apps.worker import main as worker_module

    async def fake_create_campaign_call(*args, **kwargs):
        return SimpleNamespace(livekit_sip_call_id="sip_retry", room_name=kwargs["room_name"])

    monkeypatch.setattr(worker_module, "get_session_factory", lambda: session_factory)
    monkeypatch.setattr(worker_module, "get_voice_settings", lambda: object())
    monkeypatch.setattr(worker_module.LiveKitCallService, "create_campaign_call", fake_create_campaign_call)
    asyncio.run(worker_module.process_next_call_job("retry-worker"))
    attempt = client.get(f"/v1/campaigns/{campaign['id']}").json()["enrollments"][0]["attempts"][0]

    first = client.post(
        f"/v1/call-attempts/{attempt['id']}/result",
        json={"status": "unanswered"},
    )
    assert first.status_code == 200
    assert first.json()["progress"]["retry_scheduled"] == 1
    assert first.json()["enrollments"][0]["next_attempt_at"] is not None

    repeated = client.post(
        f"/v1/call-attempts/{attempt['id']}/result",
        json={"status": "unanswered"},
    )
    assert repeated.status_code == 200

    async def pending_jobs() -> int:
        async with session_factory() as session:
            return len(
                list(
                    (
                        await session.execute(
                            select(Job).where(
                                Job.job_type == CALL_JOB_TYPE,
                                Job.status == JobStatus.PENDING.value,
                            )
                        )
                    ).scalars()
                )
            )

    assert asyncio.run(pending_jobs()) == 1
    assert client.post(
        f"/v1/call-attempts/{attempt['id']}/result",
        json={"status": "connected"},
    ).status_code == 409
