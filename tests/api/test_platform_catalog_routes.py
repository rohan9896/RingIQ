import asyncio
import uuid
from collections.abc import AsyncIterator, Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from apps.api.ringiq_api.auth.context import (
    PlatformContext,
    get_current_platform_context,
)
from apps.api.ringiq_api.db.session import get_db_session
from apps.api.ringiq_api.main import create_app
from apps.api.ringiq_api.models.identity import PlatformRole, User, UserRealm
from tests.api.postgres import create_test_engine, reset_database


def make_platform_context(
    role: PlatformRole = PlatformRole.SUPER_ADMIN,
) -> PlatformContext:
    return PlatformContext(
        user_id=uuid.uuid4(),
        clerk_user_id="user_platform",
        primary_email="admin@ringiq.in",
        display_name="RingIQ Admin",
        role=role,
    )


def make_template_payload() -> dict:
    return {
        "title": "Real estate starter template",
        "description": "Starter questions for first-touch qualification.",
        "lead_schema_json": {
            "fields": [
                {"key": "area_of_interest", "label": "Area of interest"},
            ]
        },
        "qna_questions": [
            {
                "key": "project_name",
                "label": "Which project should the assistant introduce?",
                "help_text": "Use the public project name.",
                "answer_type": "short_text",
                "required": True,
                "display_order": 0,
            },
            {
                "key": "pricing",
                "label": "What pricing details can the assistant mention?",
                "answer_type": "long_text",
                "required": False,
                "display_order": 1,
            },
        ],
    }


async def create_platform_user(
    session_factory: async_sessionmaker[AsyncSession],
    context: PlatformContext,
) -> None:
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


@pytest.fixture
def platform_client() -> Iterator[tuple[TestClient, PlatformContext]]:
    engine = create_test_engine()
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    context = make_platform_context()

    async def setup() -> None:
        await reset_database(engine)
        await create_platform_user(session_factory, context)

    async def override_session() -> AsyncIterator[AsyncSession]:
        async with session_factory() as session:
            yield session

    asyncio.run(setup())
    app = create_app()
    app.dependency_overrides[get_current_platform_context] = lambda: context
    app.dependency_overrides[get_db_session] = override_session

    with TestClient(app) as client:
        yield client, context

    asyncio.run(engine.dispose())


def test_platform_can_create_category_and_starter_template(
    platform_client: tuple[TestClient, PlatformContext],
) -> None:
    client, _ = platform_client

    category_response = client.post(
        "/v1/platform/categories",
        json={
            "key": "real_estate",
            "name": "Real Estate",
            "description": "Property developers and brokers.",
        },
    )
    assert category_response.status_code == 201
    category = category_response.json()
    assert category["key"] == "real_estate"

    template_response = client.post(
        f"/v1/platform/categories/{category['id']}/template-versions",
        json=make_template_payload(),
    )
    assert template_response.status_code == 201
    template = template_response.json()
    assert template["version"] == 1
    assert template["status"] == "draft"
    assert [question["key"] for question in template["qna_questions"]] == [
        "project_name",
        "pricing",
    ]

    list_response = client.get(
        f"/v1/platform/categories/{category['id']}/template-versions"
    )
    assert list_response.status_code == 200
    assert list_response.json()[0]["id"] == template["id"]


def test_duplicate_category_key_returns_conflict(
    platform_client: tuple[TestClient, PlatformContext],
) -> None:
    client, _ = platform_client
    payload = {"key": "real_estate", "name": "Real Estate"}

    assert client.post("/v1/platform/categories", json=payload).status_code == 201
    response = client.post("/v1/platform/categories", json=payload)

    assert response.status_code == 409
    assert response.json()["detail"] == "category_key_already_exists"


def test_operations_role_cannot_write_catalog() -> None:
    engine = create_test_engine()
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    context = make_platform_context(PlatformRole.OPERATIONS)

    async def setup() -> None:
        await reset_database(engine)
        await create_platform_user(session_factory, context)

    async def override_session() -> AsyncIterator[AsyncSession]:
        async with session_factory() as session:
            yield session

    asyncio.run(setup())
    app = create_app()
    app.dependency_overrides[get_current_platform_context] = lambda: context
    app.dependency_overrides[get_db_session] = override_session

    with TestClient(app) as client:
        response = client.post(
            "/v1/platform/categories",
            json={"key": "real_estate", "name": "Real Estate"},
        )

    asyncio.run(engine.dispose())
    assert response.status_code == 403
    assert response.json()["detail"] == "platform_role_not_allowed"


def test_published_template_cannot_be_edited(
    platform_client: tuple[TestClient, PlatformContext],
) -> None:
    client, _ = platform_client
    category = client.post(
        "/v1/platform/categories",
        json={"key": "real_estate", "name": "Real Estate"},
    ).json()
    template = client.post(
        f"/v1/platform/categories/{category['id']}/template-versions",
        json=make_template_payload(),
    ).json()

    publish_response = client.post(
        f"/v1/platform/template-versions/{template['id']}/publish"
    )
    assert publish_response.status_code == 200
    assert publish_response.json()["status"] == "published"

    edit_response = client.patch(
        f"/v1/platform/template-versions/{template['id']}",
        json={"title": "New title"},
    )
    assert edit_response.status_code == 409
    assert edit_response.json()["detail"] == "template_version_not_editable"


def test_duplicate_question_order_is_rejected(
    platform_client: tuple[TestClient, PlatformContext],
) -> None:
    client, _ = platform_client
    category = client.post(
        "/v1/platform/categories",
        json={"key": "real_estate", "name": "Real Estate"},
    ).json()
    payload = make_template_payload()
    payload["qna_questions"][1]["display_order"] = 0

    response = client.post(
        f"/v1/platform/categories/{category['id']}/template-versions",
        json=payload,
    )

    assert response.status_code == 422
    assert response.json()["detail"] == "duplicate_question_display_order"


def test_platform_overview_returns_live_counts(
    platform_client: tuple[TestClient, PlatformContext],
) -> None:
    client, _ = platform_client

    category = client.post(
        "/v1/platform/categories",
        json={"key": "real_estate", "name": "Real Estate"},
    ).json()
    client.post(
        f"/v1/platform/categories/{category['id']}/template-versions",
        json=make_template_payload(),
    )

    response = client.get("/v1/platform/overview")

    assert response.status_code == 200
    body = response.json()
    assert body["counts"]["platform_users"] == 1
    assert body["counts"]["categories"] == 1
    assert body["counts"]["active_categories"] == 1
    assert body["counts"]["draft_templates"] == 1
    assert body["first_template_seeded"] is False


def test_real_estate_starter_template_seed_is_idempotent(
    platform_client: tuple[TestClient, PlatformContext],
) -> None:
    client, _ = platform_client

    first_response = client.post("/v1/platform/starter-template-seeds/real-estate")
    second_response = client.post("/v1/platform/starter-template-seeds/real-estate")

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    first = first_response.json()
    second = second_response.json()
    assert first["created_category"] is True
    assert first["created_template"] is True
    assert second["created_category"] is False
    assert second["created_template"] is False
    assert first["category"]["key"] == "real_estate"
    assert first["template_version"]["title"] == "Real estate lead qualification starter"
    assert len(first["template_version"]["qna_questions"]) == 6
    assert second["template_version"]["id"] == first["template_version"]["id"]

    overview = client.get("/v1/platform/overview").json()
    assert overview["counts"]["categories"] == 1
    assert overview["counts"]["draft_templates"] == 1
    assert overview["first_template_seeded"] is True


def test_operations_role_cannot_seed_real_estate_template() -> None:
    engine = create_test_engine()
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    context = make_platform_context(PlatformRole.OPERATIONS)

    async def setup() -> None:
        await reset_database(engine)
        await create_platform_user(session_factory, context)

    async def override_session() -> AsyncIterator[AsyncSession]:
        async with session_factory() as session:
            yield session

    asyncio.run(setup())
    app = create_app()
    app.dependency_overrides[get_current_platform_context] = lambda: context
    app.dependency_overrides[get_db_session] = override_session

    with TestClient(app) as client:
        response = client.post("/v1/platform/starter-template-seeds/real-estate")

    asyncio.run(engine.dispose())
    assert response.status_code == 403
    assert response.json()["detail"] == "platform_role_not_allowed"
