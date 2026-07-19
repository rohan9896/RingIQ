from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.ringiq_api.auth.context import (
    PlatformContext,
    get_current_platform_context,
)
from apps.api.ringiq_api.db.session import get_db_session
from apps.api.ringiq_api.models.catalog import (
    Category,
    CategoryStatus,
    CategoryTemplateVersion,
    QnaQuestion,
    QuestionAnswerType,
    TemplateStatus,
)
from apps.api.ringiq_api.models.identity import (
    PlatformRole,
    RecordStatus,
    Tenant,
    User,
    UserRealm,
)
from apps.api.ringiq_api.schemas.platform import (
    PlatformMeResponse,
    PlatformOverviewCounts,
    PlatformOverviewResponse,
    PlatformStarterSeedResponse,
)

router = APIRouter(prefix="/v1/platform", tags=["platform"])

REAL_ESTATE_CATEGORY_KEY = "real_estate"
REAL_ESTATE_TEMPLATE_TITLE = "Real estate lead qualification starter"


def require_platform_roles(*allowed_roles: PlatformRole):
    async def dependency(
        context: PlatformContext = Depends(get_current_platform_context),
    ) -> PlatformContext:
        if context.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="platform_role_not_allowed",
            )
        return context

    return dependency


async def _count(session: AsyncSession, statement) -> int:
    return int((await session.execute(statement)).scalar_one() or 0)


async def _get_or_create_real_estate_category(
    session: AsyncSession,
    context: PlatformContext,
) -> tuple[Category, bool]:
    category = (
        await session.execute(
            select(Category).where(Category.key == REAL_ESTATE_CATEGORY_KEY)
        )
    ).scalar_one_or_none()
    if category is not None:
        return category, False

    category = Category(
        key=REAL_ESTATE_CATEGORY_KEY,
        name="Real Estate",
        description=(
            "Residential developers, brokers, and channel partners qualifying "
            "property buyer leads."
        ),
        status=CategoryStatus.ACTIVE.value,
        created_by_user_id=context.user_id,
        updated_by_user_id=context.user_id,
    )
    session.add(category)
    await session.flush()
    return category, True


def _initial_real_estate_questions(template_version_id) -> list[QnaQuestion]:
    question_specs = [
        {
            "key": "business_overview",
            "label": "What should the assistant know about your real-estate business?",
            "help_text": "Include developer or brokerage name, city, target customer, and what makes the offering credible.",
            "answer_type": QuestionAnswerType.LONG_TEXT.value,
            "required": True,
        },
        {
            "key": "active_projects",
            "label": "Which projects or localities should the assistant discuss?",
            "help_text": "List project names, neighborhoods, property types, possession stage, and availability.",
            "answer_type": QuestionAnswerType.LONG_TEXT.value,
            "required": True,
        },
        {
            "key": "budget_ranges",
            "label": "What budget ranges and pricing guidance can be shared?",
            "help_text": "Mention safe public ranges only. Avoid private discounts unless callers may hear them.",
            "answer_type": QuestionAnswerType.LONG_TEXT.value,
            "required": True,
        },
        {
            "key": "qualification_rules",
            "label": "How should RingIQ identify a qualified lead?",
            "help_text": "For example: target location, budget fit, buying timeline, property type, and site-visit interest.",
            "answer_type": QuestionAnswerType.LONG_TEXT.value,
            "required": True,
        },
        {
            "key": "callback_policy",
            "label": "When should the assistant promise a sales callback?",
            "help_text": "Describe business hours, callback windows, and who follows up.",
            "answer_type": QuestionAnswerType.LONG_TEXT.value,
            "required": False,
        },
        {
            "key": "restricted_claims",
            "label": "What should the assistant avoid saying?",
            "help_text": "Add legal, pricing, possession, availability, or financing claims that require human confirmation.",
            "answer_type": QuestionAnswerType.LONG_TEXT.value,
            "required": True,
        },
    ]
    return [
        QnaQuestion(
            category_template_version_id=template_version_id,
            key=spec["key"],
            label=spec["label"],
            help_text=spec["help_text"],
            answer_type=spec["answer_type"],
            required=spec["required"],
            display_order=index,
            validation_json={},
            options_json=None,
        )
        for index, spec in enumerate(question_specs)
    ]


async def _get_or_create_real_estate_template(
    session: AsyncSession,
    category: Category,
    context: PlatformContext,
) -> tuple[CategoryTemplateVersion, bool]:
    template = (
        await session.execute(
            select(CategoryTemplateVersion).where(
                CategoryTemplateVersion.category_id == category.id,
                CategoryTemplateVersion.title == REAL_ESTATE_TEMPLATE_TITLE,
            )
        )
    ).scalar_one_or_none()
    if template is not None:
        return template, False

    next_version = (
        (
            await session.execute(
                select(func.max(CategoryTemplateVersion.version)).where(
                    CategoryTemplateVersion.category_id == category.id
                )
            )
        ).scalar_one()
        or 0
    ) + 1
    template = CategoryTemplateVersion(
        category_id=category.id,
        version=next_version,
        title=REAL_ESTATE_TEMPLATE_TITLE,
        description=(
            "Initial real-estate onboarding questionnaire for buyer lead "
            "qualification calls."
        ),
        status=TemplateStatus.DRAFT.value,
        lead_schema_json={
            "fields": [
                "name",
                "email",
                "phone_number",
                "preferred_location",
                "budget",
                "property_type",
                "buying_timeline",
                "lead_source",
            ]
        },
        created_by_user_id=context.user_id,
        updated_by_user_id=context.user_id,
    )
    session.add(template)
    await session.flush()
    session.add_all(_initial_real_estate_questions(template.id))
    await session.flush()
    await session.refresh(template, attribute_names=["qna_questions"])
    return template, True


@router.get("/me", response_model=PlatformMeResponse)
async def get_platform_me(
    context: PlatformContext = Depends(get_current_platform_context),
) -> PlatformMeResponse:
    return PlatformMeResponse(**context.__dict__)


@router.get("/overview", response_model=PlatformOverviewResponse)
async def get_platform_overview(
    _: PlatformContext = Depends(get_current_platform_context),
    session: AsyncSession = Depends(get_db_session),
) -> PlatformOverviewResponse:
    organizations = await _count(session, select(func.count()).select_from(Tenant))
    active_organizations = await _count(
        session,
        select(func.count())
        .select_from(Tenant)
        .where(Tenant.status == RecordStatus.ACTIVE.value),
    )
    suspended_organizations = await _count(
        session,
        select(func.count())
        .select_from(Tenant)
        .where(Tenant.status == RecordStatus.SUSPENDED.value),
    )
    tenant_users = await _count(
        session,
        select(func.count())
        .select_from(User)
        .where(User.realm == UserRealm.TENANT.value),
    )
    platform_users = await _count(
        session,
        select(func.count())
        .select_from(User)
        .where(User.realm == UserRealm.PLATFORM.value),
    )
    categories = await _count(session, select(func.count()).select_from(Category))
    active_categories = await _count(
        session,
        select(func.count())
        .select_from(Category)
        .where(Category.status == CategoryStatus.ACTIVE.value),
    )
    draft_templates = await _count(
        session,
        select(func.count()).select_from(CategoryTemplateVersion).where(
            CategoryTemplateVersion.status == TemplateStatus.DRAFT.value
        ),
    )
    published_templates = await _count(
        session,
        select(func.count()).select_from(CategoryTemplateVersion).where(
            CategoryTemplateVersion.status == TemplateStatus.PUBLISHED.value
        ),
    )
    first_template_seeded = await _count(
        session,
        select(func.count()).select_from(CategoryTemplateVersion).join(Category).where(
            Category.key == REAL_ESTATE_CATEGORY_KEY,
            CategoryTemplateVersion.title == REAL_ESTATE_TEMPLATE_TITLE,
        ),
    ) > 0
    return PlatformOverviewResponse(
        counts=PlatformOverviewCounts(
            organizations=organizations,
            active_organizations=active_organizations,
            suspended_organizations=suspended_organizations,
            tenant_users=tenant_users,
            platform_users=platform_users,
            categories=categories,
            active_categories=active_categories,
            draft_templates=draft_templates,
            published_templates=published_templates,
        ),
        first_template_seeded=first_template_seeded,
    )


@router.post(
    "/starter-template-seeds/real-estate",
    response_model=PlatformStarterSeedResponse,
)
async def seed_real_estate_starter_template(
    context: PlatformContext = Depends(
        require_platform_roles(PlatformRole.SUPER_ADMIN, PlatformRole.TEMPLATE_MANAGER)
    ),
    session: AsyncSession = Depends(get_db_session),
) -> PlatformStarterSeedResponse:
    category, created_category = await _get_or_create_real_estate_category(session, context)
    template, created_template = await _get_or_create_real_estate_template(
        session,
        category,
        context,
    )
    await session.commit()
    await session.refresh(category)
    await session.refresh(template, attribute_names=["qna_questions"])
    return PlatformStarterSeedResponse(
        category=category,
        template_version=template,
        created_category=created_category,
        created_template=created_template,
    )
