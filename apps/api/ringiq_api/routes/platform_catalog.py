import uuid
from collections.abc import Sequence
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import delete, func, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from apps.api.ringiq_api.auth.context import (
    PlatformContext,
    get_current_platform_context,
)
from apps.api.ringiq_api.db.session import get_db_session
from apps.api.ringiq_api.models.catalog import (
    Category,
    CategoryTemplateVersion,
    QnaQuestion,
    TemplateStatus,
)
from apps.api.ringiq_api.models.identity import PlatformRole
from apps.api.ringiq_api.schemas.catalog import (
    CategoryCreateRequest,
    CategoryResponse,
    CategoryTemplateVersionResponse,
    CategoryUpdateRequest,
    QnaQuestionWrite,
    TemplateQuestionsReplaceRequest,
    TemplateVersionCreateRequest,
    TemplateVersionUpdateRequest,
)

router = APIRouter(prefix="/v1/platform", tags=["platform-catalog"])

TEMPLATE_WRITE_ROLES = {
    PlatformRole.SUPER_ADMIN,
    PlatformRole.TEMPLATE_MANAGER,
}


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


async def _commit_or_conflict(session: AsyncSession, detail: str) -> None:
    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=detail) from exc
    except SQLAlchemyError as exc:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="catalog_store_unavailable",
        ) from exc


async def _get_category(session: AsyncSession, category_id: uuid.UUID) -> Category:
    category = await session.get(Category, category_id)
    if category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="category_not_found",
        )
    return category


async def _get_template_version(
    session: AsyncSession,
    template_version_id: uuid.UUID,
) -> CategoryTemplateVersion:
    statement = (
        select(CategoryTemplateVersion)
        .options(selectinload(CategoryTemplateVersion.qna_questions))
        .where(CategoryTemplateVersion.id == template_version_id)
    )
    template_version = (await session.execute(statement)).scalar_one_or_none()
    if template_version is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="template_version_not_found",
        )
    return template_version


def _ensure_draft(template_version: CategoryTemplateVersion) -> None:
    if template_version.status != TemplateStatus.DRAFT.value:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="template_version_not_editable",
        )


def _validate_question_uniqueness(questions: Sequence[QnaQuestionWrite]) -> None:
    keys = [question.key for question in questions]
    display_orders = [question.display_order for question in questions]
    if len(keys) != len(set(keys)):
        raise HTTPException(
            status_code=422,
            detail="duplicate_question_key",
        )
    if len(display_orders) != len(set(display_orders)):
        raise HTTPException(
            status_code=422,
            detail="duplicate_question_display_order",
        )


def _build_questions(
    template_version_id: uuid.UUID,
    questions: Sequence[QnaQuestionWrite],
) -> list[QnaQuestion]:
    _validate_question_uniqueness(questions)
    return [
        QnaQuestion(
            category_template_version_id=template_version_id,
            key=question.key,
            label=question.label,
            help_text=question.help_text,
            answer_type=question.answer_type.value,
            required=question.required,
            display_order=question.display_order,
            validation_json=question.validation_json,
            options_json=question.options_json,
        )
        for question in questions
    ]


@router.get("/categories", response_model=list[CategoryResponse])
async def list_categories(
    _: PlatformContext = Depends(get_current_platform_context),
    session: AsyncSession = Depends(get_db_session),
) -> list[Category]:
    statement = select(Category).order_by(Category.name.asc())
    return list((await session.execute(statement)).scalars().all())


@router.post(
    "/categories",
    response_model=CategoryResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_category(
    payload: CategoryCreateRequest,
    context: PlatformContext = Depends(require_platform_roles(*TEMPLATE_WRITE_ROLES)),
    session: AsyncSession = Depends(get_db_session),
) -> Category:
    category = Category(
        key=payload.key,
        name=payload.name,
        description=payload.description,
        status=payload.status.value,
        created_by_user_id=context.user_id,
        updated_by_user_id=context.user_id,
    )
    session.add(category)
    await _commit_or_conflict(session, "category_key_already_exists")
    await session.refresh(category)
    return category


@router.get("/categories/{category_id}", response_model=CategoryResponse)
async def get_category(
    category_id: uuid.UUID,
    _: PlatformContext = Depends(get_current_platform_context),
    session: AsyncSession = Depends(get_db_session),
) -> Category:
    return await _get_category(session, category_id)


@router.patch("/categories/{category_id}", response_model=CategoryResponse)
async def update_category(
    category_id: uuid.UUID,
    payload: CategoryUpdateRequest,
    context: PlatformContext = Depends(require_platform_roles(*TEMPLATE_WRITE_ROLES)),
    session: AsyncSession = Depends(get_db_session),
) -> Category:
    category = await _get_category(session, category_id)
    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(category, field, value.value if hasattr(value, "value") else value)
    category.updated_by_user_id = context.user_id
    await _commit_or_conflict(session, "category_update_conflict")
    await session.refresh(category)
    return category


@router.get(
    "/categories/{category_id}/template-versions",
    response_model=list[CategoryTemplateVersionResponse],
)
async def list_category_template_versions(
    category_id: uuid.UUID,
    _: PlatformContext = Depends(get_current_platform_context),
    session: AsyncSession = Depends(get_db_session),
) -> list[CategoryTemplateVersion]:
    await _get_category(session, category_id)
    statement = (
        select(CategoryTemplateVersion)
        .options(selectinload(CategoryTemplateVersion.qna_questions))
        .where(CategoryTemplateVersion.category_id == category_id)
        .order_by(CategoryTemplateVersion.version.desc())
    )
    return list((await session.execute(statement)).scalars().all())


@router.post(
    "/categories/{category_id}/template-versions",
    response_model=CategoryTemplateVersionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_category_template_version(
    category_id: uuid.UUID,
    payload: TemplateVersionCreateRequest,
    context: PlatformContext = Depends(require_platform_roles(*TEMPLATE_WRITE_ROLES)),
    session: AsyncSession = Depends(get_db_session),
) -> CategoryTemplateVersion:
    await _get_category(session, category_id)
    version_statement = select(func.max(CategoryTemplateVersion.version)).where(
        CategoryTemplateVersion.category_id == category_id
    )
    next_version = ((await session.execute(version_statement)).scalar_one() or 0) + 1
    template_version = CategoryTemplateVersion(
        category_id=category_id,
        version=next_version,
        title=payload.title,
        description=payload.description,
        lead_schema_json=payload.lead_schema_json,
        created_by_user_id=context.user_id,
        updated_by_user_id=context.user_id,
    )
    session.add(template_version)
    await session.flush()
    session.add_all(_build_questions(template_version.id, payload.qna_questions))
    await _commit_or_conflict(session, "template_version_conflict")
    return await _get_template_version(session, template_version.id)


@router.get(
    "/template-versions/{template_version_id}",
    response_model=CategoryTemplateVersionResponse,
)
async def get_category_template_version(
    template_version_id: uuid.UUID,
    _: PlatformContext = Depends(get_current_platform_context),
    session: AsyncSession = Depends(get_db_session),
) -> CategoryTemplateVersion:
    return await _get_template_version(session, template_version_id)


@router.patch(
    "/template-versions/{template_version_id}",
    response_model=CategoryTemplateVersionResponse,
)
async def update_category_template_version(
    template_version_id: uuid.UUID,
    payload: TemplateVersionUpdateRequest,
    context: PlatformContext = Depends(require_platform_roles(*TEMPLATE_WRITE_ROLES)),
    session: AsyncSession = Depends(get_db_session),
) -> CategoryTemplateVersion:
    template_version = await _get_template_version(session, template_version_id)
    _ensure_draft(template_version)
    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(template_version, field, value)
    template_version.updated_by_user_id = context.user_id
    await _commit_or_conflict(session, "template_version_update_conflict")
    return await _get_template_version(session, template_version_id)


@router.put(
    "/template-versions/{template_version_id}/questions",
    response_model=CategoryTemplateVersionResponse,
)
async def replace_category_template_questions(
    template_version_id: uuid.UUID,
    payload: TemplateQuestionsReplaceRequest,
    context: PlatformContext = Depends(require_platform_roles(*TEMPLATE_WRITE_ROLES)),
    session: AsyncSession = Depends(get_db_session),
) -> CategoryTemplateVersion:
    template_version = await _get_template_version(session, template_version_id)
    _ensure_draft(template_version)
    await session.execute(
        delete(QnaQuestion).where(
            QnaQuestion.category_template_version_id == template_version.id
        )
    )
    session.add_all(_build_questions(template_version.id, payload.qna_questions))
    template_version.updated_by_user_id = context.user_id
    await _commit_or_conflict(session, "template_questions_conflict")
    return await _get_template_version(session, template_version_id)


@router.post(
    "/template-versions/{template_version_id}/publish",
    response_model=CategoryTemplateVersionResponse,
)
async def publish_category_template_version(
    template_version_id: uuid.UUID,
    context: PlatformContext = Depends(require_platform_roles(*TEMPLATE_WRITE_ROLES)),
    session: AsyncSession = Depends(get_db_session),
) -> CategoryTemplateVersion:
    template_version = await _get_template_version(session, template_version_id)
    _ensure_draft(template_version)
    template_version.status = TemplateStatus.PUBLISHED.value
    template_version.published_at = datetime.now(timezone.utc)
    template_version.published_by_user_id = context.user_id
    template_version.updated_by_user_id = context.user_id
    await _commit_or_conflict(session, "template_version_publish_conflict")
    return await _get_template_version(session, template_version_id)
