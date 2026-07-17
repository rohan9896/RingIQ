import asyncio
import uuid
from collections.abc import AsyncIterator, Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from apps.api.ringiq_api.auth.context import TenantContext, get_current_tenant_context
from apps.api.ringiq_api.db.session import get_db_session
from apps.api.ringiq_api.main import create_app
from apps.api.ringiq_api.models.identity import Tenant, User
from tests.api.postgres import create_test_engine, reset_database


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


@pytest.fixture
def lead_client() -> Iterator[TestClient]:
    engine = create_test_engine()
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    context = make_context()

    async def setup() -> None:
        await reset_database(engine)
        async with session_factory() as session:
            session.add_all([
                Tenant(id=context.tenant_id, clerk_organization_id=context.clerk_organization_id, name=context.tenant_name, slug=context.tenant_slug),
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
        yield client
    asyncio.run(engine.dispose())


def test_csv_import_records_valid_invalid_and_duplicate_rows(lead_client: TestClient) -> None:
    response = lead_client.post("/v1/lead-imports", json={
        "filename": "prospects.csv",
        "csv_content": "Full Name,Email Address,Mobile,Area of Interest\nAsha Sharma,asha@example.com,9898634576,Gurugram\nBad Email,not-an-email,9988665544,Noida\nDuplicate Phone,duplicate@example.com,+919898634576,Delhi\n",
        "column_mapping": {"name": "Full Name", "email": "Email Address", "phone_number": "Mobile"},
    })

    assert response.status_code == 201
    payload = response.json()
    assert payload["total_rows"] == 3
    assert payload["imported_rows"] == 1
    assert payload["invalid_rows"] == 1
    assert payload["duplicate_rows"] == 1
    assert [row["status"] for row in payload["rows"]] == ["imported", "invalid", "duplicate"]

    leads = lead_client.get("/v1/leads")
    assert leads.status_code == 200
    assert len(leads.json()) == 1
    assert leads.json()[0]["normalized_phone_number"] == "+919898634576"
    assert leads.json()[0]["attributes_json"]["area_of_interest"] == "Gurugram"

    imports = lead_client.get("/v1/lead-imports")
    assert imports.status_code == 200
    assert imports.json()[0]["id"] == payload["id"]


def test_import_requires_mapped_mandatory_columns(lead_client: TestClient) -> None:
    response = lead_client.post("/v1/lead-imports", json={
        "filename": "incomplete.csv",
        "csv_content": "Name,Phone\nAsha,9898634576\n",
    })

    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "required_columns_missing"
    assert response.json()["detail"]["columns"] == ["email"]


def test_leads_are_scoped_to_the_active_tenant(lead_client: TestClient) -> None:
    lead_client.post("/v1/lead-imports", json={
        "filename": "one.csv",
        "csv_content": "Name,Email,Phone\nAsha,asha@example.com,9898634576\n",
    })
    app = lead_client.app
    app.dependency_overrides[get_current_tenant_context] = lambda: TenantContext(
        tenant_id=uuid.uuid4(), user_id=uuid.uuid4(), membership_id=uuid.uuid4(),
        clerk_organization_id="org_other", clerk_user_id="user_other", clerk_membership_id="orgmem_other",
        tenant_name="Other Realty", tenant_slug="other-realty", timezone="Asia/Kolkata",
    )

    response = lead_client.get("/v1/leads")

    assert response.status_code == 200
    assert response.json() == []
