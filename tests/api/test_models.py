import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import async_sessionmaker

from apps.api.ringiq_api.models.catalog import (
    Category,
    CategoryTemplateVersion,
    QnaQuestion,
    QuestionAnswerType,
    TemplateStatus,
)
from apps.api.ringiq_api.models.identity import (
    PlatformRole,
    Tenant,
    TenantMembership,
    User,
    UserRealm,
)
from tests.api.postgres import create_test_engine, reset_database


def test_identity_models_use_uuid_primary_keys_and_expected_defaults() -> None:
    assert Tenant.__table__.c.timezone.default.arg == "Asia/Kolkata"
    assert Tenant.__table__.c.status.default.arg == "active"
    assert User.__table__.c.status.default.arg == "active"
    assert User.__table__.c.realm.default.arg == "tenant"
    assert TenantMembership.__table__.c.status.default.arg == "active"
    assert TenantMembership.__table__.c.role_key.default.arg == "member"
    assert Category.__table__.c.status.default.arg == "active"
    assert CategoryTemplateVersion.__table__.c.status.default.arg == "draft"


def test_membership_table_has_tenant_user_uniqueness() -> None:
    unique_column_sets = {
        tuple(column.name for column in constraint.columns)
        for constraint in TenantMembership.__table__.constraints
        if constraint.__class__.__name__ == "UniqueConstraint"
    }

    assert ("tenant_id", "user_id") in unique_column_sets


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("records"),
    [
        (
            Tenant(clerk_organization_id="org_1", name="One", slug="one"),
            Tenant(clerk_organization_id="org_1", name="Two", slug="two"),
        ),
        (
            User(clerk_user_id="user_1"),
            User(clerk_user_id="user_1"),
        ),
    ],
)
async def test_external_identity_ids_are_database_unique(records: tuple[object, object]) -> None:
    engine = create_test_engine()
    try:
        await reset_database(engine)
        session_factory = async_sessionmaker(engine, expire_on_commit=False)
        async with session_factory() as session:
            session.add_all(records)
            with pytest.raises(IntegrityError):
                await session.commit()
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_category_template_question_invariants_are_enforced() -> None:
    engine = create_test_engine()
    try:
        await reset_database(engine)
        session_factory = async_sessionmaker(engine, expire_on_commit=False)
        async with session_factory() as session:
            category = Category(key="real_estate", name="Real Estate")
            session.add(category)
            await session.flush()
            template = CategoryTemplateVersion(
                category_id=category.id,
                version=1,
                title="Initial real estate template",
                status=TemplateStatus.DRAFT.value,
            )
            session.add(template)
            await session.flush()
            session.add_all(
                [
                    QnaQuestion(
                        category_template_version_id=template.id,
                        key="project_name",
                        label="Project name",
                        answer_type=QuestionAnswerType.SHORT_TEXT.value,
                        display_order=0,
                    ),
                    QnaQuestion(
                        category_template_version_id=template.id,
                        key="project_name",
                        label="Duplicate project name",
                        answer_type=QuestionAnswerType.SHORT_TEXT.value,
                        display_order=1,
                    ),
                ]
            )

            with pytest.raises(IntegrityError):
                await session.commit()
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_invalid_record_status_is_rejected_by_database() -> None:
    engine = create_test_engine()
    try:
        await reset_database(engine)
        session_factory = async_sessionmaker(engine, expire_on_commit=False)
        async with session_factory() as session:
            session.add(
                Tenant(
                    clerk_organization_id="org_1",
                    name="One",
                    slug="one",
                    status="unknown",
                )
            )
            with pytest.raises(IntegrityError):
                await session.commit()
    finally:
        await engine.dispose()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "user",
    [
        User(
            clerk_user_id="tenant_with_platform_role",
            realm=UserRealm.TENANT.value,
            platform_role=PlatformRole.SUPER_ADMIN.value,
        ),
        User(clerk_user_id="platform_without_role", realm=UserRealm.PLATFORM.value),
        User(
            clerk_user_id="platform_with_unknown_role",
            realm=UserRealm.PLATFORM.value,
            platform_role="unknown",
        ),
    ],
)
async def test_user_realm_and_platform_role_invariant_is_enforced(user: User) -> None:
    engine = create_test_engine()
    try:
        await reset_database(engine)
        session_factory = async_sessionmaker(engine, expire_on_commit=False)
        async with session_factory() as session:
            session.add(user)
            with pytest.raises(IntegrityError):
                await session.commit()
    finally:
        await engine.dispose()
