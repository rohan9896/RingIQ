import secrets
import uuid

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from apps.api.ringiq_api.auth.context import TenantContext, get_current_tenant_context
from apps.api.ringiq_api.config import AppSettings, get_app_settings
from apps.api.ringiq_api.db.session import get_db_session
from apps.api.ringiq_api.models.campaigns import (
    CallAttempt,
    CallAttemptStatus,
    Campaign,
    CampaignEnrollment,
    CampaignStatus,
    EnrollmentStatus,
    Job,
    JobStatus,
)
from apps.api.ringiq_api.models.identity import Tenant
from apps.api.ringiq_api.models.leads import Lead, LeadImport, LeadStatus
from apps.api.ringiq_api.schemas.campaigns import (
    CallAttemptResponse,
    CallAttemptResultRequest,
    CampaignCreateRequest,
    CampaignDetailResponse,
    CampaignEnrollmentResponse,
    CampaignLeadHistoryResponse,
    CampaignProgressResponse,
    CampaignReadinessResponse,
    CampaignResponse,
)
from apps.api.ringiq_api.services.campaign_operations import (
    add_outbox_event,
    apply_attempt_result,
    campaign_counts,
    campaign_readiness,
    cancel_pending_jobs,
    load_campaign,
    queue_campaign,
    utcnow,
)

router = APIRouter(prefix="/v1", tags=["campaigns"])


async def _commit(session: AsyncSession, detail: str) -> None:
    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(status_code=409, detail=detail) from exc
    except SQLAlchemyError as exc:
        await session.rollback()
        raise HTTPException(status_code=503, detail="campaign_store_unavailable") from exc


async def _require_campaign(
    session: AsyncSession,
    tenant_id: uuid.UUID,
    campaign_id: uuid.UUID,
) -> Campaign:
    campaign = await load_campaign(session, tenant_id, campaign_id)
    if campaign is None:
        raise HTTPException(status_code=404, detail="campaign_not_found")
    return campaign


async def _campaign_response(
    session: AsyncSession,
    campaign: Campaign,
) -> CampaignResponse:
    blockers, _ = await campaign_readiness(session, campaign)
    counts = await campaign_counts(session, campaign.id)
    progress = CampaignProgressResponse(
        total=sum(counts.values()),
        **{key: value for key, value in counts.items() if key in CampaignProgressResponse.model_fields},
    )
    return CampaignResponse(
        id=campaign.id,
        name=campaign.name,
        status=campaign.status,
        source_import_id=campaign.source_import_id,
        knowledge_base_version_id=campaign.knowledge_base_version_id,
        retry_limit=campaign.retry_limit,
        retry_policy_json=campaign.retry_policy_json,
        started_at=campaign.started_at,
        completed_at=campaign.completed_at,
        created_at=campaign.created_at,
        updated_at=campaign.updated_at,
        readiness=CampaignReadinessResponse(is_ready=not blockers, blockers=blockers),
        progress=progress,
    )


async def _campaign_detail_response(
    session: AsyncSession,
    campaign: Campaign,
) -> CampaignDetailResponse:
    base = await _campaign_response(session, campaign)
    lead_ids = [enrollment.lead_id for enrollment in campaign.enrollments]
    leads = {
        lead.id: lead
        for lead in (
            await session.execute(
                select(Lead).where(
                    Lead.tenant_id == campaign.tenant_id,
                    Lead.id.in_(lead_ids),
                )
            )
        ).scalars()
    }
    enrollments = []
    for enrollment in campaign.enrollments:
        lead = leads[enrollment.lead_id]
        enrollments.append(
            CampaignEnrollmentResponse(
                id=enrollment.id,
                lead_id=lead.id,
                lead_name=lead.name,
                lead_email=lead.email,
                lead_phone_number=lead.normalized_phone_number,
                status=enrollment.status,
                attempt_count=enrollment.attempt_count,
                next_attempt_at=enrollment.next_attempt_at,
                last_error_code=enrollment.last_error_code,
                attempts=[CallAttemptResponse.model_validate(item) for item in enrollment.attempts],
            )
        )
    return CampaignDetailResponse(**base.model_dump(), enrollments=enrollments)


@router.get("/campaigns", response_model=list[CampaignResponse])
async def list_campaigns(
    context: TenantContext = Depends(get_current_tenant_context),
    session: AsyncSession = Depends(get_db_session),
) -> list[CampaignResponse]:
    campaigns = list(
        (
            await session.execute(
                select(Campaign)
                .options(selectinload(Campaign.enrollments))
                .where(Campaign.tenant_id == context.tenant_id)
                .order_by(Campaign.created_at.desc())
            )
        ).scalars()
    )
    return [await _campaign_response(session, campaign) for campaign in campaigns]


@router.post("/campaigns", response_model=CampaignDetailResponse, status_code=201)
async def create_campaign(
    payload: CampaignCreateRequest,
    context: TenantContext = Depends(get_current_tenant_context),
    session: AsyncSession = Depends(get_db_session),
) -> CampaignDetailResponse:
    lead_ids = list(dict.fromkeys(payload.lead_ids))
    leads = list(
        (
            await session.execute(
                select(Lead).where(
                    Lead.tenant_id == context.tenant_id,
                    Lead.id.in_(lead_ids),
                    Lead.status == LeadStatus.ACTIVE.value,
                )
            )
        ).scalars()
    )
    if len(leads) != len(lead_ids):
        raise HTTPException(status_code=422, detail="campaign_leads_invalid_or_archived")
    if payload.source_import_id is not None:
        source_import = (
            await session.execute(
                select(LeadImport).where(
                    LeadImport.id == payload.source_import_id,
                    LeadImport.tenant_id == context.tenant_id,
                )
            )
        ).scalar_one_or_none()
        if source_import is None:
            raise HTTPException(status_code=404, detail="lead_import_not_found")

    campaign = Campaign(
        tenant_id=context.tenant_id,
        name=payload.name.strip(),
        source_import_id=payload.source_import_id,
        retry_limit=payload.retry_limit,
        retry_policy_json={"delay_minutes": 15},
        created_by_user_id=context.user_id,
        updated_by_user_id=context.user_id,
    )
    session.add(campaign)
    await session.flush()
    session.add_all(
        CampaignEnrollment(
            tenant_id=context.tenant_id,
            campaign_id=campaign.id,
            lead_id=lead.id,
        )
        for lead in leads
    )
    add_outbox_event(session, campaign, "campaign.created", {"lead_count": len(leads)})
    await _commit(session, "campaign_create_conflict")
    campaign = await _require_campaign(session, context.tenant_id, campaign.id)
    blockers, _ = await campaign_readiness(session, campaign)
    if not blockers:
        campaign.status = CampaignStatus.READY.value
        await _commit(session, "campaign_readiness_conflict")
        campaign = await _require_campaign(session, context.tenant_id, campaign.id)
    return await _campaign_detail_response(session, campaign)


@router.get("/campaigns/{campaign_id}", response_model=CampaignDetailResponse)
async def get_campaign(
    campaign_id: uuid.UUID,
    context: TenantContext = Depends(get_current_tenant_context),
    session: AsyncSession = Depends(get_db_session),
) -> CampaignDetailResponse:
    campaign = await _require_campaign(session, context.tenant_id, campaign_id)
    return await _campaign_detail_response(session, campaign)


@router.post("/leads/{lead_id}/call-now", response_model=CampaignDetailResponse, status_code=201)
async def call_lead_now(
    lead_id: uuid.UUID,
    context: TenantContext = Depends(get_current_tenant_context),
    session: AsyncSession = Depends(get_db_session),
) -> CampaignDetailResponse:
    lead = (
        await session.execute(
            select(Lead).where(
                Lead.id == lead_id,
                Lead.tenant_id == context.tenant_id,
                Lead.status == LeadStatus.ACTIVE.value,
            )
        )
    ).scalar_one_or_none()
    if lead is None:
        raise HTTPException(status_code=404, detail="lead_not_found")
    tenant = await session.get(Tenant, context.tenant_id)
    if tenant is None or tenant.primary_category_id is None:
        raise HTTPException(status_code=422, detail={"code": "call_not_ready", "blockers": ["organization_category_required"]})

    campaign = Campaign(
        tenant_id=context.tenant_id,
        name=f"Call now: {lead.name}",
        retry_limit=0,
        retry_policy_json={"mode": "manual"},
        created_by_user_id=context.user_id,
        updated_by_user_id=context.user_id,
    )
    session.add(campaign)
    await session.flush()
    session.add(CampaignEnrollment(tenant_id=context.tenant_id, campaign_id=campaign.id, lead_id=lead.id))
    await session.flush()
    campaign = await _require_campaign(session, context.tenant_id, campaign.id)
    blockers, active_version = await campaign_readiness(session, campaign)
    if active_version is not None and active_version.category_id != tenant.primary_category_id:
        blockers.append("knowledge_base_category_mismatch")
    if blockers or active_version is None:
        await session.rollback()
        raise HTTPException(status_code=422, detail={"code": "call_not_ready", "blockers": blockers})
    campaign.status = CampaignStatus.RUNNING.value
    campaign.knowledge_base_version_id = active_version.id
    campaign.started_at = utcnow()
    await queue_campaign(session, campaign)
    add_outbox_event(session, campaign, "manual_call.started", {"lead_id": str(lead.id)})
    await _commit(session, "manual_call_create_conflict")
    return await _campaign_detail_response(
        session, await _require_campaign(session, context.tenant_id, campaign.id)
    )


@router.post("/campaigns/{campaign_id}/start", response_model=CampaignDetailResponse)
async def start_campaign(
    campaign_id: uuid.UUID,
    context: TenantContext = Depends(get_current_tenant_context),
    session: AsyncSession = Depends(get_db_session),
) -> CampaignDetailResponse:
    campaign = await _require_campaign(session, context.tenant_id, campaign_id)
    if campaign.status not in {CampaignStatus.DRAFT.value, CampaignStatus.READY.value}:
        raise HTTPException(status_code=409, detail="campaign_not_startable")
    blockers, active_version = await campaign_readiness(session, campaign)
    if blockers or active_version is None:
        raise HTTPException(status_code=422, detail={"code": "campaign_not_ready", "blockers": blockers})
    campaign.status = CampaignStatus.RUNNING.value
    campaign.knowledge_base_version_id = active_version.id
    campaign.started_at = utcnow()
    campaign.updated_by_user_id = context.user_id
    await queue_campaign(session, campaign)
    add_outbox_event(session, campaign, "campaign.started")
    await _commit(session, "campaign_start_conflict")
    return await _campaign_detail_response(
        session, await _require_campaign(session, context.tenant_id, campaign.id)
    )


@router.post("/campaigns/{campaign_id}/pause", response_model=CampaignDetailResponse)
async def pause_campaign(
    campaign_id: uuid.UUID,
    context: TenantContext = Depends(get_current_tenant_context),
    session: AsyncSession = Depends(get_db_session),
) -> CampaignDetailResponse:
    campaign = await _require_campaign(session, context.tenant_id, campaign_id)
    if campaign.status != CampaignStatus.RUNNING.value:
        raise HTTPException(status_code=409, detail="campaign_not_running")
    campaign.status = CampaignStatus.PAUSED.value
    campaign.updated_by_user_id = context.user_id
    add_outbox_event(session, campaign, "campaign.paused")
    await _commit(session, "campaign_pause_conflict")
    return await _campaign_detail_response(
        session, await _require_campaign(session, context.tenant_id, campaign.id)
    )


@router.post("/campaigns/{campaign_id}/resume", response_model=CampaignDetailResponse)
async def resume_campaign(
    campaign_id: uuid.UUID,
    context: TenantContext = Depends(get_current_tenant_context),
    session: AsyncSession = Depends(get_db_session),
) -> CampaignDetailResponse:
    campaign = await _require_campaign(session, context.tenant_id, campaign_id)
    if campaign.status != CampaignStatus.PAUSED.value:
        raise HTTPException(status_code=409, detail="campaign_not_paused")
    campaign.status = CampaignStatus.RUNNING.value
    campaign.updated_by_user_id = context.user_id
    add_outbox_event(session, campaign, "campaign.resumed")
    await _commit(session, "campaign_resume_conflict")
    return await _campaign_detail_response(
        session, await _require_campaign(session, context.tenant_id, campaign.id)
    )


@router.post("/campaigns/{campaign_id}/cancel", response_model=CampaignDetailResponse)
async def cancel_campaign(
    campaign_id: uuid.UUID,
    context: TenantContext = Depends(get_current_tenant_context),
    session: AsyncSession = Depends(get_db_session),
) -> CampaignDetailResponse:
    campaign = await _require_campaign(session, context.tenant_id, campaign_id)
    if campaign.status not in {
        CampaignStatus.DRAFT.value,
        CampaignStatus.READY.value,
        CampaignStatus.RUNNING.value,
        CampaignStatus.PAUSED.value,
    }:
        raise HTTPException(status_code=409, detail="campaign_not_cancellable")
    campaign.status = CampaignStatus.CANCELLED.value
    campaign.completed_at = utcnow()
    campaign.updated_by_user_id = context.user_id
    for enrollment in campaign.enrollments:
        if enrollment.status not in {
            EnrollmentStatus.CALLING.value,
            EnrollmentStatus.CONNECTED.value,
            EnrollmentStatus.COMPLETED.value,
        }:
            enrollment.status = EnrollmentStatus.CANCELLED.value
            enrollment.next_attempt_at = None
    await cancel_pending_jobs(session, campaign.id)
    add_outbox_event(session, campaign, "campaign.cancelled")
    await _commit(session, "campaign_cancel_conflict")
    return await _campaign_detail_response(
        session, await _require_campaign(session, context.tenant_id, campaign.id)
    )


@router.post("/call-attempts/{attempt_id}/result", response_model=CampaignDetailResponse)
async def record_call_attempt_result(
    attempt_id: uuid.UUID,
    payload: CallAttemptResultRequest,
    context: TenantContext = Depends(get_current_tenant_context),
    session: AsyncSession = Depends(get_db_session),
) -> CampaignDetailResponse:
    attempt = (
        await session.execute(
            select(CallAttempt).where(
                CallAttempt.id == attempt_id,
                CallAttempt.tenant_id == context.tenant_id,
            )
        )
    ).scalar_one_or_none()
    if attempt is None:
        raise HTTPException(status_code=404, detail="call_attempt_not_found")
    terminal_statuses = {
        CallAttemptStatus.COMPLETED.value,
        CallAttemptStatus.UNANSWERED.value,
        CallAttemptStatus.BUSY.value,
        CallAttemptStatus.INVALID_NUMBER.value,
        CallAttemptStatus.FAILED.value,
        CallAttemptStatus.CANCELLED.value,
    }
    if attempt.status in terminal_statuses:
        if attempt.status == payload.status:
            enrollment = (
                await session.execute(
                    select(CampaignEnrollment).where(
                        CampaignEnrollment.id == attempt.campaign_enrollment_id,
                        CampaignEnrollment.tenant_id == context.tenant_id,
                    )
                )
            ).scalar_one()
            campaign = await _require_campaign(
                session, context.tenant_id, enrollment.campaign_id
            )
            return await _campaign_detail_response(session, campaign)
        raise HTTPException(status_code=409, detail="call_attempt_already_terminal")
    if attempt.status == CallAttemptStatus.CONNECTED.value and payload.status != "completed":
        raise HTTPException(status_code=409, detail="connected_call_cannot_regress")
    enrollment = (
        await session.execute(
            select(CampaignEnrollment).where(
                CampaignEnrollment.id == attempt.campaign_enrollment_id,
                CampaignEnrollment.tenant_id == context.tenant_id,
            )
        )
    ).scalar_one()
    campaign = await _require_campaign(session, context.tenant_id, enrollment.campaign_id)
    await apply_attempt_result(
        session,
        campaign,
        enrollment,
        attempt,
        result_status=payload.status,
        provider_call_id=payload.provider_call_id,
        duration_seconds=payload.duration_seconds,
        failure_code=payload.failure_code,
        failure_detail=payload.failure_detail,
    )
    await _commit(session, "call_attempt_result_conflict")
    return await _campaign_detail_response(
        session, await _require_campaign(session, context.tenant_id, campaign.id)
    )


@router.get(
    "/leads/{lead_id}/campaign-history",
    response_model=list[CampaignLeadHistoryResponse],
)
async def get_lead_campaign_history(
    lead_id: uuid.UUID,
    context: TenantContext = Depends(get_current_tenant_context),
    session: AsyncSession = Depends(get_db_session),
) -> list[CampaignLeadHistoryResponse]:
    lead = (
        await session.execute(
            select(Lead).where(Lead.id == lead_id, Lead.tenant_id == context.tenant_id)
        )
    ).scalar_one_or_none()
    if lead is None:
        raise HTTPException(status_code=404, detail="lead_not_found")
    enrollments = list(
        (
            await session.execute(
                select(CampaignEnrollment)
                .options(
                    selectinload(CampaignEnrollment.campaign),
                    selectinload(CampaignEnrollment.attempts),
                )
                .where(
                    CampaignEnrollment.lead_id == lead_id,
                    CampaignEnrollment.tenant_id == context.tenant_id,
                )
                .order_by(CampaignEnrollment.created_at.desc())
            )
        ).scalars()
    )
    return [
        CampaignLeadHistoryResponse(
            campaign_id=item.campaign.id,
            campaign_name=item.campaign.name,
            campaign_status=item.campaign.status,
            enrollment_id=item.id,
            enrollment_status=item.status,
            attempt_count=item.attempt_count,
            attempts=[CallAttemptResponse.model_validate(attempt) for attempt in item.attempts],
        )
        for item in enrollments
    ]


@router.post("/internal/call-attempts/{attempt_id}/result")
async def record_internal_call_attempt_result(
    attempt_id: uuid.UUID,
    payload: CallAttemptResultRequest,
    internal_key: str | None = Header(default=None, alias="X-RingIQ-Internal-Key"),
    settings: AppSettings = Depends(get_app_settings),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, str]:
    if (
        not settings.internal_api_key
        or not internal_key
        or not secrets.compare_digest(internal_key, settings.internal_api_key)
    ):
        raise HTTPException(status_code=401, detail="invalid_internal_api_key")
    attempt = await session.get(CallAttempt, attempt_id)
    if attempt is None:
        raise HTTPException(status_code=404, detail="call_attempt_not_found")
    enrollment = await session.get(CampaignEnrollment, attempt.campaign_enrollment_id)
    if enrollment is None:
        raise HTTPException(status_code=404, detail="campaign_enrollment_not_found")
    campaign = await _require_campaign(session, attempt.tenant_id, enrollment.campaign_id)
    terminal_statuses = {
        CallAttemptStatus.COMPLETED.value,
        CallAttemptStatus.UNANSWERED.value,
        CallAttemptStatus.BUSY.value,
        CallAttemptStatus.INVALID_NUMBER.value,
        CallAttemptStatus.FAILED.value,
        CallAttemptStatus.CANCELLED.value,
    }
    if attempt.status in terminal_statuses:
        if attempt.status == payload.status:
            return {"status": "already_applied"}
        raise HTTPException(status_code=409, detail="call_attempt_already_terminal")
    if attempt.status == CallAttemptStatus.CONNECTED.value and payload.status != "completed":
        raise HTTPException(status_code=409, detail="connected_call_cannot_regress")
    await apply_attempt_result(
        session,
        campaign,
        enrollment,
        attempt,
        result_status=payload.status,
        provider_call_id=payload.provider_call_id,
        duration_seconds=payload.duration_seconds,
        failure_code=payload.failure_code,
        failure_detail=payload.failure_detail,
    )
    await _commit(session, "call_attempt_result_conflict")
    return {"status": "applied"}
