import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import delete, func, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from apps.api.ringiq_api.auth.context import TenantContext, get_current_tenant_context
from apps.api.ringiq_api.db.session import get_db_session
from apps.api.ringiq_api.models.catalog import (
    Category,
    CategoryStatus,
    CategoryTemplateVersion,
    QnaQuestion,
    TemplateStatus,
)
from apps.api.ringiq_api.models.identity import Tenant
from apps.api.ringiq_api.models.knowledge import (
    TenantKnowledgeBase,
    TenantKnowledgeBaseVersion,
    TenantKnowledgeQuestion,
)
from apps.api.ringiq_api.schemas.knowledge import (
    CreateKnowledgeBaseDraftRequest,
    ReplaceTenantKnowledgeQuestionsRequest,
    StarterTemplateResponse,
    TenantKnowledgeBaseResponse,
    TenantKnowledgeQuestionWrite,
    TenantKnowledgeVersionResponse,
    UpdateKnowledgeBaseDraftRequest,
)

router = APIRouter(prefix="/v1/knowledge-base", tags=["knowledge-base"])


async def _commit(session: AsyncSession, detail: str) -> None:
    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=detail) from exc
    except SQLAlchemyError as exc:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="knowledge_store_unavailable",
        ) from exc


def _questions_response(version: TenantKnowledgeBaseVersion) -> TenantKnowledgeVersionResponse:
    return TenantKnowledgeVersionResponse.model_validate(version)


async def _get_version(
    session: AsyncSession,
    tenant_id: uuid.UUID,
    version_id: uuid.UUID,
) -> TenantKnowledgeBaseVersion:
    statement = (
        select(TenantKnowledgeBaseVersion)
        .options(selectinload(TenantKnowledgeBaseVersion.questions))
        .where(
            TenantKnowledgeBaseVersion.id == version_id,
            TenantKnowledgeBaseVersion.tenant_id == tenant_id,
        )
    )
    version = (await session.execute(statement)).scalar_one_or_none()
    if version is None:
        raise HTTPException(status_code=404, detail="knowledge_base_version_not_found")
    return version


async def _get_workspace(
    session: AsyncSession,
    tenant_id: uuid.UUID,
) -> TenantKnowledgeBase | None:
    statement = (
        select(TenantKnowledgeBase)
        .options(
            selectinload(TenantKnowledgeBase.versions).selectinload(
                TenantKnowledgeBaseVersion.questions
            ),
            selectinload(TenantKnowledgeBase.active_version).selectinload(
                TenantKnowledgeBaseVersion.questions
            ),
        )
        .where(TenantKnowledgeBase.tenant_id == tenant_id)
    )
    return (await session.execute(statement)).scalar_one_or_none()


def _workspace_response(workspace: TenantKnowledgeBase) -> TenantKnowledgeBaseResponse:
    draft = next(
        (version for version in workspace.versions if version.status == TemplateStatus.DRAFT.value),
        None,
    )
    return TenantKnowledgeBaseResponse(
        id=workspace.id,
        tenant_id=workspace.tenant_id,
        active_version=_questions_response(workspace.active_version)
        if workspace.active_version is not None
        else None,
        draft_version=_questions_response(draft) if draft is not None else None,
    )


def _validate_question_uniqueness(questions: list[TenantKnowledgeQuestionWrite]) -> None:
    keys = [question.key for question in questions]
    orders = [question.display_order for question in questions]
    if len(keys) != len(set(keys)):
        raise HTTPException(status_code=422, detail="duplicate_question_key")
    if len(orders) != len(set(orders)):
        raise HTTPException(status_code=422, detail="duplicate_question_display_order")


def _build_questions(
    version_id: uuid.UUID,
    questions: list[TenantKnowledgeQuestionWrite],
) -> list[TenantKnowledgeQuestion]:
    _validate_question_uniqueness(questions)
    return [
        TenantKnowledgeQuestion(
            tenant_knowledge_base_version_id=version_id,
            key=question.key,
            label=question.label,
            help_text=question.help_text,
            answer_type=question.answer_type.value,
            required=question.required,
            display_order=question.display_order,
            validation_json=question.validation_json,
            options_json=question.options_json,
            answer_value_json=question.answer_value_json,
        )
        for question in questions
    ]


def _has_answer(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, dict)):
        return bool(value)
    return True


@router.get("/starter-templates", response_model=list[StarterTemplateResponse])
async def list_starter_templates(
    context: TenantContext = Depends(get_current_tenant_context),
    session: AsyncSession = Depends(get_db_session),
) -> list[StarterTemplateResponse]:
    statement = (
        select(CategoryTemplateVersion, Category)
        .join(Category, Category.id == CategoryTemplateVersion.category_id)
        .options(selectinload(CategoryTemplateVersion.qna_questions))
        .where(
            Category.status == CategoryStatus.ACTIVE.value,
            CategoryTemplateVersion.status == TemplateStatus.PUBLISHED.value,
        )
        .order_by(Category.name, CategoryTemplateVersion.version.desc())
    )
    tenant = await session.get(Tenant, context.tenant_id)
    if tenant is not None and tenant.primary_category_id is not None:
        statement = statement.where(Category.id == tenant.primary_category_id)
    rows = (await session.execute(statement)).all()
    return [
        StarterTemplateResponse(
            id=template.id,
            category_id=category.id,
            category_key=category.key,
            category_name=category.name,
            title=template.title,
            description=template.description,
            lead_schema_json=template.lead_schema_json,
            qna_questions=template.qna_questions,
        )
        for template, category in rows
    ]


@router.get("", response_model=TenantKnowledgeBaseResponse | None)
async def get_knowledge_base(
    context: TenantContext = Depends(get_current_tenant_context),
    session: AsyncSession = Depends(get_db_session),
) -> TenantKnowledgeBaseResponse | None:
    workspace = await _get_workspace(session, context.tenant_id)
    return _workspace_response(workspace) if workspace is not None else None


@router.post("/drafts", response_model=TenantKnowledgeVersionResponse, status_code=201)
async def create_knowledge_base_draft(
    payload: CreateKnowledgeBaseDraftRequest,
    context: TenantContext = Depends(get_current_tenant_context),
    session: AsyncSession = Depends(get_db_session),
) -> TenantKnowledgeVersionResponse:
    workspace = await _get_workspace(session, context.tenant_id)
    if workspace is not None and any(
        version.status == TemplateStatus.DRAFT.value for version in workspace.versions
    ):
        raise HTTPException(status_code=409, detail="knowledge_base_draft_already_exists")

    source_template: CategoryTemplateVersion | None = None
    source_version: TenantKnowledgeBaseVersion | None = None
    if payload.starter_template_version_id is not None:
        source_statement = (
            select(CategoryTemplateVersion)
            .options(selectinload(CategoryTemplateVersion.qna_questions))
            .where(
                CategoryTemplateVersion.id == payload.starter_template_version_id,
                CategoryTemplateVersion.status == TemplateStatus.PUBLISHED.value,
            )
        )
        source_template = (await session.execute(source_statement)).scalar_one_or_none()
        if source_template is None:
            raise HTTPException(status_code=404, detail="starter_template_not_found")
        tenant = await session.get(Tenant, context.tenant_id)
        if tenant is not None and tenant.primary_category_id is not None and tenant.primary_category_id != source_template.category_id:
            raise HTTPException(status_code=422, detail="starter_template_category_mismatch")
        if tenant is not None and tenant.primary_category_id is None:
            tenant.primary_category_id = source_template.category_id
    elif workspace is not None and workspace.active_version is not None:
        source_version = workspace.active_version
    else:
        raise HTTPException(status_code=422, detail="starter_template_required")

    if workspace is None:
        workspace = TenantKnowledgeBase(tenant_id=context.tenant_id)
        session.add(workspace)
        await session.flush()

    next_version = (
        (await session.execute(
            select(func.max(TenantKnowledgeBaseVersion.version)).where(
                TenantKnowledgeBaseVersion.knowledge_base_id == workspace.id
            )
        )).scalar_one()
        or 0
    ) + 1
    draft = TenantKnowledgeBaseVersion(
        knowledge_base_id=workspace.id,
        tenant_id=context.tenant_id,
        category_id=source_template.category_id if source_template else source_version.category_id,
        source_template_version_id=source_template.id if source_template else source_version.source_template_version_id,
        version=next_version,
        title=source_template.title if source_template else source_version.title,
        business_profile_json=source_version.business_profile_json.copy() if source_version else {},
        additional_notes=source_version.additional_notes if source_version else None,
        created_by_user_id=context.user_id,
        updated_by_user_id=context.user_id,
    )
    session.add(draft)
    await session.flush()
    if source_template is not None:
        cloned = [
            TenantKnowledgeQuestionWrite(
                key=question.key,
                label=question.label,
                help_text=question.help_text,
                answer_type=question.answer_type,
                required=question.required,
                display_order=question.display_order,
                validation_json=question.validation_json,
                options_json=question.options_json,
            )
            for question in source_template.qna_questions
        ]
    else:
        cloned = [
            TenantKnowledgeQuestionWrite(
                key=question.key,
                label=question.label,
                help_text=question.help_text,
                answer_type=question.answer_type,
                required=question.required,
                display_order=question.display_order,
                validation_json=question.validation_json,
                options_json=question.options_json,
                answer_value_json=question.answer_value_json,
            )
            for question in source_version.questions
        ]
    session.add_all(_build_questions(draft.id, cloned))
    await _commit(session, "knowledge_base_draft_conflict")
    return _questions_response(await _get_version(session, context.tenant_id, draft.id))


@router.patch("/drafts/{version_id}", response_model=TenantKnowledgeVersionResponse)
async def update_knowledge_base_draft(
    version_id: uuid.UUID,
    payload: UpdateKnowledgeBaseDraftRequest,
    context: TenantContext = Depends(get_current_tenant_context),
    session: AsyncSession = Depends(get_db_session),
) -> TenantKnowledgeVersionResponse:
    draft = await _get_version(session, context.tenant_id, version_id)
    if draft.status != TemplateStatus.DRAFT.value:
        raise HTTPException(status_code=409, detail="knowledge_base_version_not_editable")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(draft, field, value)
    draft.updated_by_user_id = context.user_id
    await _commit(session, "knowledge_base_draft_conflict")
    return _questions_response(await _get_version(session, context.tenant_id, version_id))


@router.put("/drafts/{version_id}/questions", response_model=TenantKnowledgeVersionResponse)
async def replace_knowledge_base_questions(
    version_id: uuid.UUID,
    payload: ReplaceTenantKnowledgeQuestionsRequest,
    context: TenantContext = Depends(get_current_tenant_context),
    session: AsyncSession = Depends(get_db_session),
) -> TenantKnowledgeVersionResponse:
    draft = await _get_version(session, context.tenant_id, version_id)
    if draft.status != TemplateStatus.DRAFT.value:
        raise HTTPException(status_code=409, detail="knowledge_base_version_not_editable")
    await session.execute(
        delete(TenantKnowledgeQuestion).where(
            TenantKnowledgeQuestion.tenant_knowledge_base_version_id == draft.id
        )
    )
    session.add_all(_build_questions(draft.id, payload.questions))
    draft.updated_by_user_id = context.user_id
    await _commit(session, "knowledge_base_questions_conflict")
    return _questions_response(await _get_version(session, context.tenant_id, version_id))


@router.post("/drafts/{version_id}/publish", response_model=TenantKnowledgeVersionResponse)
async def publish_knowledge_base_draft(
    version_id: uuid.UUID,
    context: TenantContext = Depends(get_current_tenant_context),
    session: AsyncSession = Depends(get_db_session),
) -> TenantKnowledgeVersionResponse:
    draft = await _get_version(session, context.tenant_id, version_id)
    if draft.status != TemplateStatus.DRAFT.value:
        raise HTTPException(status_code=409, detail="knowledge_base_version_not_editable")
    missing_keys = [
        question.key
        for question in draft.questions
        if question.required and not _has_answer(question.answer_value_json)
    ]
    if missing_keys:
        raise HTTPException(status_code=422, detail={"code": "required_answers_missing", "keys": missing_keys})
    workspace = await _get_workspace(session, context.tenant_id)
    if workspace is None:
        raise HTTPException(status_code=404, detail="knowledge_base_not_found")
    if workspace.active_version is not None:
        workspace.active_version.status = TemplateStatus.ARCHIVED.value
    draft.status = TemplateStatus.PUBLISHED.value
    draft.published_at = datetime.now(timezone.utc)
    draft.published_by_user_id = context.user_id
    draft.updated_by_user_id = context.user_id
    workspace.active_version_id = draft.id
    await _commit(session, "knowledge_base_publish_conflict")
    return _questions_response(await _get_version(session, context.tenant_id, version_id))


@router.get("/active", response_model=TenantKnowledgeVersionResponse)
async def get_active_knowledge_base_version(
    context: TenantContext = Depends(get_current_tenant_context),
    session: AsyncSession = Depends(get_db_session),
) -> TenantKnowledgeVersionResponse:
    workspace = await _get_workspace(session, context.tenant_id)
    if workspace is None or workspace.active_version is None:
        raise HTTPException(status_code=404, detail="active_knowledge_base_not_found")
    return _questions_response(workspace.active_version)
