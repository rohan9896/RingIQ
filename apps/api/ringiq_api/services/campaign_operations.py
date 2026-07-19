import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select, update
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

CALL_JOB_TYPE = "campaign.outbound_call"
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
            )
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
) -> None:
    now = utcnow()
    attempt.status = result_status
    attempt.provider_call_id = provider_call_id or attempt.provider_call_id
    attempt.duration_seconds = duration_seconds
    attempt.failure_code = failure_code
    attempt.failure_detail = failure_detail
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
    now = utcnow()
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
            Job.job_type == CALL_JOB_TYPE,
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
