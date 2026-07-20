import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from apps.api.ringiq_api.models.campaigns import (
    CallAttempt,
    CallAttemptStatus,
    Campaign,
    CampaignEnrollment,
    CampaignStatus,
    EnrollmentStatus,
    Job,
    JobStatus,
    OutboxEvent,
)
from apps.api.ringiq_api.models.knowledge import (
    TenantKnowledgeBase,
    TenantKnowledgeBaseVersion,
)
from apps.api.ringiq_api.services.post_call_outcomes import (
    get_or_create_outcome,
    mark_outcome_failed,
)

CALL_JOB_TYPE = "campaign.outbound_call"
POST_CALL_JOB_TYPE = "call.post_call_outcome"
TERMINAL_ENROLLMENT_STATUSES = {
    EnrollmentStatus.COMPLETED.value,
    EnrollmentStatus.INVALID_NUMBER.value,
    EnrollmentStatus.EXHAUSTED.value,
    EnrollmentStatus.CANCELLED.value,
}
RETRYABLE_ATTEMPT_STATUSES = {
    CallAttemptStatus.UNANSWERED.value,
    CallAttemptStatus.BUSY.value,
}


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


async def load_campaign(
    session: AsyncSession,
    tenant_id: uuid.UUID,
    campaign_id: uuid.UUID,
) -> Campaign | None:
    statement = (
        select(Campaign)
        .options(
            selectinload(Campaign.enrollments).selectinload(
                CampaignEnrollment.attempts
            ).selectinload(CallAttempt.outcome)
        )
        .where(Campaign.id == campaign_id, Campaign.tenant_id == tenant_id)
    )
    return (await session.execute(statement)).scalar_one_or_none()


async def campaign_readiness(
    session: AsyncSession,
    campaign: Campaign,
) -> tuple[list[str], TenantKnowledgeBaseVersion | None]:
    blockers: list[str] = []
    if not campaign.enrollments:
        blockers.append("campaign_leads_required")

    if campaign.knowledge_base_version_id is not None:
        pinned_version = await session.get(
            TenantKnowledgeBaseVersion,
            campaign.knowledge_base_version_id,
        )
        if pinned_version is None or pinned_version.tenant_id != campaign.tenant_id:
            blockers.append("campaign_knowledge_base_unavailable")
            return blockers, None
        if pinned_version.status != "published":
            blockers.append("campaign_knowledge_base_unpublished")
        if not pinned_version.business_profile_json:
            blockers.append("business_profile_required")
        return blockers, pinned_version

    workspace = (
        await session.execute(
            select(TenantKnowledgeBase)
            .options(selectinload(TenantKnowledgeBase.active_version))
            .where(TenantKnowledgeBase.tenant_id == campaign.tenant_id)
        )
    ).scalar_one_or_none()
    active_version = workspace.active_version if workspace is not None else None
    if active_version is None or active_version.status != "published":
        blockers.append("active_knowledge_base_required")
        return blockers, None
    if not active_version.business_profile_json:
        blockers.append("business_profile_required")
    return blockers, active_version


def enqueue_call_job(
    session: AsyncSession,
    enrollment: CampaignEnrollment,
    *,
    attempt_number: int,
    available_at: datetime,
) -> Job:
    job = Job(
        tenant_id=enrollment.tenant_id,
        campaign_id=enrollment.campaign_id,
        campaign_enrollment_id=enrollment.id,
        job_type=CALL_JOB_TYPE,
        payload_json={
            "campaign_id": str(enrollment.campaign_id),
            "campaign_enrollment_id": str(enrollment.id),
            "attempt_number": attempt_number,
        },
        idempotency_key=f"{enrollment.id}:attempt:{attempt_number}",
        available_at=available_at,
        max_attempts=5,
    )
    session.add(job)
    return job


async def enqueue_post_call_outcome_if_ready(
    session: AsyncSession,
    attempt: CallAttempt,
    *,
    enrollment: CampaignEnrollment | None = None,
) -> Job | None:
    terminal_statuses = {
        CallAttemptStatus.COMPLETED.value,
        CallAttemptStatus.UNANSWERED.value,
        CallAttemptStatus.BUSY.value,
        CallAttemptStatus.INVALID_NUMBER.value,
        CallAttemptStatus.FAILED.value,
        CallAttemptStatus.CANCELLED.value,
    }
    if attempt.status not in terminal_statuses:
        return None
    if enrollment is None:
        enrollment = (
            await session.execute(
                select(CampaignEnrollment).where(
                    CampaignEnrollment.id == attempt.campaign_enrollment_id,
                    CampaignEnrollment.tenant_id == attempt.tenant_id,
                )
            )
        ).scalar_one_or_none()
    if enrollment is None:
        return None
    outcome = await get_or_create_outcome(session, attempt)
    if outcome.processing_status == "completed":
        return None
    if (
        attempt.status == CallAttemptStatus.COMPLETED.value
        and attempt.artifacts_finalized_at is None
    ):
        return None

    idempotency_key = str(attempt.id)
    job_id = uuid.uuid4()
    await session.execute(
        pg_insert(Job)
        .values(
            id=job_id,
            tenant_id=attempt.tenant_id,
            campaign_id=enrollment.campaign_id,
            campaign_enrollment_id=enrollment.id,
            job_type=POST_CALL_JOB_TYPE,
            status=JobStatus.PENDING.value,
            payload_json={"call_attempt_id": str(attempt.id)},
            idempotency_key=idempotency_key,
            available_at=utcnow(),
            priority=10,
            attempt_count=0,
            max_attempts=3,
        )
        .on_conflict_do_nothing(index_elements=["job_type", "idempotency_key"])
    )
    return (
        await session.execute(
            select(Job).where(
                Job.job_type == POST_CALL_JOB_TYPE,
                Job.idempotency_key == idempotency_key,
            )
        )
    ).scalar_one()


def add_outbox_event(
    session: AsyncSession,
    campaign: Campaign,
    event_type: str,
    payload: dict | None = None,
) -> None:
    session.add(
        OutboxEvent(
            tenant_id=campaign.tenant_id,
            event_type=event_type,
            aggregate_type="campaign",
            aggregate_id=campaign.id,
            payload_json=payload or {},
            available_at=utcnow(),
        )
    )


async def queue_campaign(session: AsyncSession, campaign: Campaign) -> None:
    now = utcnow()
    for enrollment in campaign.enrollments:
        if enrollment.status != EnrollmentStatus.PENDING.value:
            continue
        enrollment.status = EnrollmentStatus.QUEUED.value
        enrollment.next_attempt_at = now
        enqueue_call_job(
            session,
            enrollment,
            attempt_number=enrollment.attempt_count + 1,
            available_at=now,
        )


async def cancel_pending_jobs(
    session: AsyncSession,
    campaign_id: uuid.UUID,
    *,
    enrollment_id: uuid.UUID | None = None,
) -> None:
    statement = update(Job).where(
        Job.campaign_id == campaign_id,
        Job.job_type == CALL_JOB_TYPE,
        Job.status == JobStatus.PENDING.value,
    )
    if enrollment_id is not None:
        statement = statement.where(Job.campaign_enrollment_id == enrollment_id)
    await session.execute(statement.values(status=JobStatus.CANCELLED.value))


async def resume_campaign_jobs(session: AsyncSession, campaign: Campaign) -> None:
    now = utcnow()
    for enrollment in campaign.enrollments:
        if enrollment.status not in {
            EnrollmentStatus.PENDING.value,
            EnrollmentStatus.RETRY_SCHEDULED.value,
        }:
            continue
        enrollment.status = EnrollmentStatus.QUEUED.value
        due_at = max(enrollment.next_attempt_at or now, now)
        enqueue_call_job(
            session,
            enrollment,
            attempt_number=enrollment.attempt_count + 1,
            available_at=due_at,
        )


async def apply_attempt_result(
    session: AsyncSession,
    campaign: Campaign,
    enrollment: CampaignEnrollment,
    attempt: CallAttempt,
    *,
    result_status: str,
    provider_call_id: str | None = None,
    duration_seconds: int | None = None,
    failure_code: str | None = None,
    failure_detail: str | None = None,
    terminal_reason: str | None = None,
) -> None:
    now = utcnow()
    attempt.status = result_status
    attempt.provider_call_id = provider_call_id or attempt.provider_call_id
    attempt.duration_seconds = duration_seconds
    attempt.failure_code = failure_code
    attempt.failure_detail = failure_detail
    attempt.terminal_reason = terminal_reason or attempt.terminal_reason
    enrollment.last_error_code = failure_code

    if result_status == CallAttemptStatus.CONNECTED.value:
        attempt.answered_at = attempt.answered_at or now
        enrollment.status = EnrollmentStatus.CONNECTED.value
        enrollment.next_attempt_at = None
        await cancel_pending_jobs(session, campaign.id, enrollment_id=enrollment.id)
        return

    attempt.ended_at = now
    enrollment.final_call_attempt_id = attempt.id
    if result_status == CallAttemptStatus.COMPLETED.value:
        attempt.answered_at = attempt.answered_at or attempt.started_at or now
        enrollment.status = EnrollmentStatus.COMPLETED.value
        enrollment.next_attempt_at = None
    elif result_status == CallAttemptStatus.INVALID_NUMBER.value:
        enrollment.status = EnrollmentStatus.INVALID_NUMBER.value
        enrollment.next_attempt_at = None
    elif result_status in RETRYABLE_ATTEMPT_STATUSES and attempt.attempt_number <= campaign.retry_limit:
        delay_minutes = int(campaign.retry_policy_json.get("delay_minutes", 15))
        enrollment.status = EnrollmentStatus.RETRY_SCHEDULED.value
        enrollment.next_attempt_at = now + timedelta(minutes=max(0, delay_minutes))
        if campaign.status == CampaignStatus.RUNNING.value:
            enqueue_call_job(
                session,
                enrollment,
                attempt_number=attempt.attempt_number + 1,
                available_at=enrollment.next_attempt_at,
            )
    else:
        enrollment.status = EnrollmentStatus.EXHAUSTED.value
        enrollment.next_attempt_at = None

    await enqueue_post_call_outcome_if_ready(
        session,
        attempt,
        enrollment=enrollment,
    )
    await complete_campaign_if_terminal(session, campaign)


async def complete_campaign_if_terminal(
    session: AsyncSession,
    campaign: Campaign,
) -> None:
    if campaign.status != CampaignStatus.RUNNING.value:
        return
    statuses = (
        await session.execute(
            select(CampaignEnrollment.status).where(
                CampaignEnrollment.campaign_id == campaign.id,
                CampaignEnrollment.tenant_id == campaign.tenant_id,
            )
        )
    ).scalars().all()
    if statuses and all(status in TERMINAL_ENROLLMENT_STATUSES for status in statuses):
        campaign.status = CampaignStatus.COMPLETED.value
        campaign.completed_at = utcnow()
        add_outbox_event(session, campaign, "campaign.completed")


async def claim_call_job(
    session: AsyncSession,
    *,
    worker_id: str,
    lease_seconds: int = 60,
) -> Job | None:
    return await claim_job(
        session,
        worker_id=worker_id,
        lease_seconds=lease_seconds,
        job_types=(CALL_JOB_TYPE,),
    )


async def claim_job(
    session: AsyncSession,
    *,
    worker_id: str,
    lease_seconds: int = 60,
    job_types: tuple[str, ...] = (CALL_JOB_TYPE, POST_CALL_JOB_TYPE),
) -> Job | None:
    now = utcnow()
    exhausted_post_call_jobs = list(
        (
            await session.execute(
                select(Job).where(
                    Job.job_type == POST_CALL_JOB_TYPE,
                    Job.status == JobStatus.LEASED.value,
                    Job.lease_expires_at < now,
                    Job.attempt_count >= Job.max_attempts,
                )
            )
        ).scalars()
    )
    for exhausted_job in exhausted_post_call_jobs:
        try:
            attempt_id = uuid.UUID(
                str(exhausted_job.payload_json.get("call_attempt_id"))
            )
        except (AttributeError, TypeError, ValueError):
            continue
        await mark_outcome_failed(
            session,
            attempt_id=attempt_id,
            tenant_id=exhausted_job.tenant_id,
            error_code="job_lease_exhausted",
        )
    await session.execute(
        update(Job)
        .where(
            Job.status == JobStatus.LEASED.value,
            Job.lease_expires_at < now,
            Job.attempt_count < Job.max_attempts,
        )
        .values(
            status=JobStatus.PENDING.value,
            lease_owner=None,
            lease_expires_at=None,
        )
    )
    await session.execute(
        update(Job)
        .where(
            Job.status == JobStatus.LEASED.value,
            Job.lease_expires_at < now,
            Job.attempt_count >= Job.max_attempts,
        )
        .values(
            status=JobStatus.DEAD_LETTER.value,
            lease_owner=None,
            lease_expires_at=None,
            last_error="job_lease_exhausted",
        )
    )
    statement = (
        select(Job)
        .where(
            Job.job_type.in_(job_types),
            Job.status == JobStatus.PENDING.value,
            Job.available_at <= now,
            Job.attempt_count < Job.max_attempts,
        )
        .order_by(Job.priority.desc(), Job.available_at, Job.id)
        .with_for_update(skip_locked=True)
        .limit(1)
    )
    job = (await session.execute(statement)).scalar_one_or_none()
    if job is None:
        await session.commit()
        return None
    job.status = JobStatus.LEASED.value
    job.lease_owner = worker_id
    job.lease_expires_at = now + timedelta(seconds=lease_seconds)
    job.attempt_count += 1
    await session.commit()
    return job


async def campaign_counts(
    session: AsyncSession,
    campaign_id: uuid.UUID,
) -> dict[str, int]:
    rows = (
        await session.execute(
            select(CampaignEnrollment.status, func.count(CampaignEnrollment.id))
            .where(CampaignEnrollment.campaign_id == campaign_id)
            .group_by(CampaignEnrollment.status)
        )
    ).all()
    return {status: count for status, count in rows}
