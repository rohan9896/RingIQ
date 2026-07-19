import asyncio
import uuid
from collections.abc import AsyncIterator, Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from apps.api.ringiq_api.auth.context import TenantContext, get_current_tenant_context
from apps.api.ringiq_api.db.session import get_db_session
from apps.api.ringiq_api.main import create_app
from apps.api.ringiq_api.models.campaigns import Job, JobStatus
from apps.api.ringiq_api.models.catalog import Category
from apps.api.ringiq_api.models.identity import Tenant, User
from apps.api.ringiq_api.models.knowledge import TenantKnowledgeBase, TenantKnowledgeBaseVersion
from tests.api.postgres import create_test_engine, reset_database


def make_context() -> TenantContext:
    return TenantContext(
        tenant_id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        membership_id=uuid.uuid4(),
        clerk_organization_id="org_activation",
        clerk_user_id="user_activation",
        clerk_membership_id="orgmem_activation",
        tenant_name="Activation Realty",
        tenant_slug="activation-realty",
        timezone="Asia/Kolkata",
    )


@pytest.fixture
def activation_client() -> Iterator[tuple[TestClient, async_sessionmaker[AsyncSession], TenantContext, uuid.UUID]]:
    engine = create_test_engine()
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    context = make_context()
    category_id = uuid.uuid4()

    async def setup() -> None:
        await reset_database(engine)
        async with session_factory() as session:
            session.add_all([
                Category(id=category_id, key="real-estate", name="Real Estate"),
                Tenant(
                    id=context.tenant_id,
                    clerk_organization_id=context.clerk_organization_id,
                    name=context.tenant_name,
                    slug=context.tenant_slug,
                ),
                User(id=context.user_id, clerk_user_id=context.clerk_user_id),
            ])
            await session.commit()

    async def override_session() -> AsyncIterator[AsyncSession]:
        async with session_factory() as session:
            yield session

    asyncio.run(setup())
    app = create_app()
    app.dependency_overrides[get_current_tenant_context] = lambda: context
    app.dependency_overrides[get_db_session] = override_session
    with TestClient(app) as client:
        yield client, session_factory, context, category_id
    asyncio.run(engine.dispose())


async def publish_kb(
    session_factory: async_sessionmaker[AsyncSession],
    context: TenantContext,
    category_id: uuid.UUID,
) -> None:
    async with session_factory() as session:
        workspace = TenantKnowledgeBase(tenant_id=context.tenant_id)
        session.add(workspace)
        await session.flush()
        version = TenantKnowledgeBaseVersion(
            knowledge_base_id=workspace.id,
            tenant_id=context.tenant_id,
            category_id=category_id,
            version=1,
            title="Activation knowledge",
            business_profile_json={"business_name": "Activation Realty"},
            status="published",
            created_by_user_id=context.user_id,
        )
        session.add(version)
        await session.flush()
        workspace.active_version_id = version.id
        await session.commit()


def test_activation_readiness_manual_lead_click_to_call_and_dashboard(
    activation_client: tuple[TestClient, async_sessionmaker[AsyncSession], TenantContext, uuid.UUID],
) -> None:
    client, session_factory, context, category_id = activation_client
    initial = client.get("/v1/workspace")
    assert initial.status_code == 200
    assert initial.json()["readiness_blockers"] == [
        "organization_category_required",
        "active_knowledge_base_required",
    ]

    categories = client.get("/v1/workspace/categories")
    assert categories.status_code == 200
    assert categories.json()[0]["id"] == str(category_id)
    selected = client.patch("/v1/workspace", json={"primary_category_id": str(category_id)})
    assert selected.status_code == 200
    assert selected.json()["category"]["key"] == "real-estate"

    lead = client.post("/v1/leads", json={
        "name": "Rohan Lead",
        "email": "lead@example.com",
        "phone_number": "9896634576",
        "attributes_json": {"area": "Gurugram"},
    })
    assert lead.status_code == 201
    lead_id = lead.json()["id"]
    blocked = client.post(f"/v1/leads/{lead_id}/call-now")
    assert blocked.status_code == 422
    assert blocked.json()["detail"]["blockers"] == ["active_knowledge_base_required"]

    asyncio.run(publish_kb(session_factory, context, category_id))
    ready = client.get("/v1/workspace")
    assert ready.json()["is_call_ready"] is True
    called = client.post(f"/v1/leads/{lead_id}/call-now")
    assert called.status_code == 201
    assert called.json()["status"] == "running"
    assert called.json()["retry_limit"] == 0
    assert called.json()["progress"]["queued"] == 1

    async def pending_jobs() -> list[Job]:
        async with session_factory() as session:
            return list((await session.execute(select(Job).where(Job.status == JobStatus.PENDING.value))).scalars())

    assert len(asyncio.run(pending_jobs())) == 1
    dashboard = client.get("/v1/dashboard")
    assert dashboard.status_code == 200
    assert dashboard.json()["workspace"]["is_call_ready"] is True
    assert dashboard.json()["totals"]["leads"] == 1
    assert dashboard.json()["totals"]["campaigns"] == 1
