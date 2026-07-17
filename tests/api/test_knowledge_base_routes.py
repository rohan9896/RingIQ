import asyncio
import uuid
from collections.abc import AsyncIterator, Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from apps.api.ringiq_api.auth.context import TenantContext, get_current_tenant_context
from apps.api.ringiq_api.db.base import Base
from apps.api.ringiq_api.db.session import get_db_session
from apps.api.ringiq_api.main import create_app
from apps.api.ringiq_api.models.catalog import (
    Category,
    CategoryTemplateVersion,
    QnaQuestion,
    TemplateStatus,
)
from apps.api.ringiq_api.models.identity import Tenant, User


def make_context() -> TenantContext:
    return TenantContext(
        tenant_id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        membership_id=uuid.uuid4(),
        clerk_organization_id="org_acme",
        clerk_user_id="user_acme",
        clerk_membership_id="orgmem_acme",
        tenant_name="Acme Realty",
        tenant_slug="acme-realty",
        timezone="Asia/Kolkata",
    )


async def seed_tenant_and_template(
    session_factory: async_sessionmaker[AsyncSession],
    context: TenantContext,
) -> uuid.UUID:
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
        category = Category(key="real_estate", name="Real Estate")
        session.add(category)
        await session.flush()
        template = CategoryTemplateVersion(
            category_id=category.id,
            version=1,
            title="Real estate discovery",
            status=TemplateStatus.PUBLISHED.value,
            lead_schema_json={"fields": ["name", "email", "phone_number"]},
        )
        session.add(template)
        await session.flush()
        session.add_all(
            [
                QnaQuestion(
                    category_template_version_id=template.id,
                    key="project_name",
                    label="What project should we introduce?",
                    answer_type="short_text",
                    required=True,
                    display_order=0,
                ),
                QnaQuestion(
                    category_template_version_id=template.id,
                    key="project_notes",
                    label="What else should the assistant know?",
                    answer_type="long_text",
                    required=False,
                    display_order=1,
                ),
            ]
        )
        await session.commit()
        return template.id


@pytest.fixture
def tenant_knowledge_client(tmp_path) -> Iterator[tuple[TestClient, uuid.UUID]]:
    database_path = tmp_path / "knowledge.sqlite3"
    engine = create_async_engine(f"sqlite+aiosqlite:///{database_path}")
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    context = make_context()

    async def setup() -> uuid.UUID:
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        return await seed_tenant_and_template(session_factory, context)

    async def override_session() -> AsyncIterator[AsyncSession]:
        async with session_factory() as session:
            yield session

    template_id = asyncio.run(setup())
    app = create_app()
    app.dependency_overrides[get_current_tenant_context] = lambda: context
    app.dependency_overrides[get_db_session] = override_session

    with TestClient(app) as client:
        yield client, template_id

    asyncio.run(engine.dispose())


def test_tenant_can_create_edit_and_publish_knowledge_base(
    tenant_knowledge_client: tuple[TestClient, uuid.UUID],
) -> None:
    client, template_id = tenant_knowledge_client

    templates = client.get("/v1/knowledge-base/starter-templates")
    assert templates.status_code == 200
    assert templates.json()[0]["id"] == str(template_id)

    created = client.post(
        "/v1/knowledge-base/drafts",
        json={"starter_template_version_id": str(template_id)},
    )
    assert created.status_code == 201
    draft = created.json()
    assert draft["status"] == "draft"
    assert [question["key"] for question in draft["questions"]] == [
        "project_name",
        "project_notes",
    ]

    updated = client.patch(
        f"/v1/knowledge-base/drafts/{draft['id']}",
        json={
            "title": "Acme project facts",
            "business_profile_json": {"business_name": "Acme Realty"},
            "additional_notes": "Use a concise, professional introduction.",
        },
    )
    assert updated.status_code == 200
    assert updated.json()["business_profile_json"]["business_name"] == "Acme Realty"

    questions = draft["questions"]
    questions[0]["answer_value_json"] = "Acme Heights"
    replaced = client.put(
        f"/v1/knowledge-base/drafts/{draft['id']}/questions",
        json={"questions": [{key: value for key, value in question.items() if key not in {"id", "created_at", "updated_at"}} for question in questions]},
    )
    assert replaced.status_code == 200

    published = client.post(f"/v1/knowledge-base/drafts/{draft['id']}/publish")
    assert published.status_code == 200
    assert published.json()["status"] == "published"

    workspace = client.get("/v1/knowledge-base")
    assert workspace.status_code == 200
    assert workspace.json()["draft_version"] is None
    assert workspace.json()["active_version"]["id"] == draft["id"]

    active = client.get("/v1/knowledge-base/active")
    assert active.status_code == 200
    assert active.json()["title"] == "Acme project facts"


def test_publish_requires_answers_to_required_questions(
    tenant_knowledge_client: tuple[TestClient, uuid.UUID],
) -> None:
    client, template_id = tenant_knowledge_client
    draft = client.post(
        "/v1/knowledge-base/drafts",
        json={"starter_template_version_id": str(template_id)},
    ).json()

    response = client.post(f"/v1/knowledge-base/drafts/{draft['id']}/publish")

    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "required_answers_missing"
    assert response.json()["detail"]["keys"] == ["project_name"]


def test_tenant_cannot_read_another_tenants_knowledge_base(
    tenant_knowledge_client: tuple[TestClient, uuid.UUID],
) -> None:
    client, template_id = tenant_knowledge_client
    draft = client.post(
        "/v1/knowledge-base/drafts",
        json={"starter_template_version_id": str(template_id)},
    ).json()

    app = client.app
    app.dependency_overrides[get_current_tenant_context] = lambda: TenantContext(
        tenant_id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        membership_id=uuid.uuid4(),
        clerk_organization_id="org_other",
        clerk_user_id="user_other",
        clerk_membership_id="orgmem_other",
        tenant_name="Other Realty",
        tenant_slug="other-realty",
        timezone="Asia/Kolkata",
    )
    response = client.patch(
        f"/v1/knowledge-base/drafts/{draft['id']}",
        json={"title": "Attempted cross-tenant update"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "knowledge_base_version_not_found"
