import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.ringiq_api.auth.context import TenantContext, get_current_tenant_context
from apps.api.ringiq_api.db.session import get_db_session
from apps.api.ringiq_api.models.campaigns import CallAttempt, Campaign, CampaignEnrollment
from apps.api.ringiq_api.models.catalog import Category, CategoryStatus
from apps.api.ringiq_api.models.identity import Tenant
from apps.api.ringiq_api.models.knowledge import TenantKnowledgeBase, TenantKnowledgeBaseVersion
from apps.api.ringiq_api.models.leads import Lead, LeadStatus
from apps.api.ringiq_api.schemas.workspace import (
    DashboardRecentCallResponse,
    DashboardResponse,
    DashboardTotalsResponse,
    WorkspaceCategoryResponse,
    WorkspaceResponse,
    WorkspaceUpdateRequest,
)

router = APIRouter(prefix="/v1", tags=["workspace"])


async def _workspace_response(session: AsyncSession, tenant: Tenant) -> WorkspaceResponse:
    category = await session.get(Category, tenant.primary_category_id) if tenant.primary_category_id else None
    active_version = (
        await session.execute(
            select(TenantKnowledgeBaseVersion)
            .join(TenantKnowledgeBase, TenantKnowledgeBase.active_version_id == TenantKnowledgeBaseVersion.id)
            .where(TenantKnowledgeBase.tenant_id == tenant.id)
        )
    ).scalar_one_or_none()
    blockers: list[str] = []
    if category is None:
        blockers.append("organization_category_required")
    if active_version is None:
        blockers.append("active_knowledge_base_required")
    elif not active_version.business_profile_json:
        blockers.append("business_profile_required")
    elif category is not None and active_version.category_id != category.id:
        blockers.append("knowledge_base_category_mismatch")
    return WorkspaceResponse(
        tenant_id=tenant.id,
        name=tenant.name,
        timezone=tenant.timezone,
        category=WorkspaceCategoryResponse(id=category.id, key=category.key, name=category.name) if category else None,
        has_active_knowledge_base=active_version is not None,
        is_call_ready=not blockers,
        readiness_blockers=blockers,
    )


async def _tenant(session: AsyncSession, tenant_id: uuid.UUID) -> Tenant:
    tenant = await session.get(Tenant, tenant_id)
    if tenant is None:
        raise HTTPException(status_code=404, detail="tenant_not_found")
    return tenant


@router.get("/workspace", response_model=WorkspaceResponse)
async def get_workspace(
    context: TenantContext = Depends(get_current_tenant_context),
    session: AsyncSession = Depends(get_db_session),
) -> WorkspaceResponse:
    return await _workspace_response(session, await _tenant(session, context.tenant_id))


@router.get("/workspace/categories", response_model=list[WorkspaceCategoryResponse])
async def list_workspace_categories(
    _: TenantContext = Depends(get_current_tenant_context),
    session: AsyncSession = Depends(get_db_session),
) -> list[WorkspaceCategoryResponse]:
    categories = (
        await session.execute(
            select(Category)
            .where(Category.status == CategoryStatus.ACTIVE.value)
            .order_by(Category.name)
        )
    ).scalars().all()
    return [WorkspaceCategoryResponse(id=item.id, key=item.key, name=item.name) for item in categories]


@router.patch("/workspace", response_model=WorkspaceResponse)
async def update_workspace(
    payload: WorkspaceUpdateRequest,
    context: TenantContext = Depends(get_current_tenant_context),
    session: AsyncSession = Depends(get_db_session),
) -> WorkspaceResponse:
    category = await session.get(Category, payload.primary_category_id)
    if category is None or category.status != CategoryStatus.ACTIVE.value:
        raise HTTPException(status_code=422, detail="active_category_required")
    tenant = await _tenant(session, context.tenant_id)
    tenant.primary_category_id = category.id
    await session.commit()
    return await _workspace_response(session, tenant)


@router.get("/dashboard", response_model=DashboardResponse)
async def get_dashboard(
    context: TenantContext = Depends(get_current_tenant_context),
    session: AsyncSession = Depends(get_db_session),
) -> DashboardResponse:
    tenant = await _tenant(session, context.tenant_id)
    scalar = lambda statement: session.scalar(statement)  # noqa: E731
    leads = await scalar(select(func.count(Lead.id)).where(Lead.tenant_id == tenant.id, Lead.status == LeadStatus.ACTIVE.value))
    campaigns = await scalar(select(func.count(Campaign.id)).where(Campaign.tenant_id == tenant.id))
    attempts = await scalar(select(func.count(CallAttempt.id)).where(CallAttempt.tenant_id == tenant.id))
    connected = await scalar(select(func.count(CallAttempt.id)).where(CallAttempt.tenant_id == tenant.id, CallAttempt.answered_at.is_not(None)))
    completed = await scalar(select(func.count(CallAttempt.id)).where(CallAttempt.tenant_id == tenant.id, CallAttempt.status == "completed"))
    failed = await scalar(select(func.count(CallAttempt.id)).where(CallAttempt.tenant_id == tenant.id, CallAttempt.status.in_(["failed", "invalid_number"])))
    rows = (
        await session.execute(
            select(CallAttempt, CampaignEnrollment, Campaign, Lead)
            .join(CampaignEnrollment, CampaignEnrollment.id == CallAttempt.campaign_enrollment_id)
            .join(Campaign, Campaign.id == CampaignEnrollment.campaign_id)
            .join(Lead, Lead.id == CampaignEnrollment.lead_id)
            .where(CallAttempt.tenant_id == tenant.id)
            .order_by(CallAttempt.created_at.desc())
            .limit(8)
        )
    ).all()
    return DashboardResponse(
        workspace=await _workspace_response(session, tenant),
        totals=DashboardTotalsResponse(
            leads=leads or 0,
            campaigns=campaigns or 0,
            call_attempts=attempts or 0,
            connected=connected or 0,
            completed=completed or 0,
            failed=failed or 0,
        ),
        recent_calls=[
            DashboardRecentCallResponse(
                attempt_id=attempt.id,
                lead_id=lead.id,
                lead_name=lead.name,
                campaign_id=campaign.id,
                campaign_name=campaign.name,
                status=attempt.status,
                started_at=attempt.started_at,
                ended_at=attempt.ended_at,
                duration_seconds=attempt.duration_seconds,
                failure_code=attempt.failure_code,
                failure_detail=attempt.failure_detail,
            )
            for attempt, _, campaign, lead in rows
        ],
    )
