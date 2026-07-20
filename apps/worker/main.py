import argparse
import asyncio
import json
import logging
import socket
import uuid
from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from apps.api.ringiq_api.config import get_app_settings, get_voice_settings
from apps.api.ringiq_api.db.session import get_session_factory
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
from apps.api.ringiq_api.models.leads import Lead
from apps.api.ringiq_api.models.identity import Tenant
from apps.api.ringiq_api.models.knowledge import TenantKnowledgeBaseVersion
from apps.api.ringiq_api.services.campaign_operations import (
    apply_attempt_result,
    POST_CALL_JOB_TYPE,
    claim_job,
    load_campaign,
    utcnow,
)
from apps.api.ringiq_api.services.post_call_outcomes import (
    PostCallOutcomeError,
    extractor_from_settings,
    get_or_create_outcome,
    process_post_call_outcome,
)
from apps.api.ringiq_api.services.livekit_calls import (
    LiveKitCallService,
    LiveKitCallServiceError,
)

logger = logging.getLogger("ringiq.background_worker")
JOB_LEASE_SECONDS = 180


async def process_next_call_job(worker_id: str) -> bool:
    session_factory = get_session_factory()
    async with session_factory() as session:
        job = await claim_job(
            session,
            worker_id=worker_id,
            lease_seconds=JOB_LEASE_SECONDS,
        )
    if job is None:
        return False

    async with session_factory() as session:
        job = await session.get(Job, job.id)
        if job is None:
            return True
        if job.job_type == POST_CALL_JOB_TYPE:
            attempt_id_value = job.payload_json.get("call_attempt_id")
            try:
                attempt_id = uuid.UUID(str(attempt_id_value))
            except (TypeError, ValueError):
                job.status = JobStatus.DEAD_LETTER.value
                job.last_error = "invalid_call_attempt_id"
                await session.commit()
                return True
            attempt = (
                await session.execute(
                    select(CallAttempt).where(
                        CallAttempt.id == attempt_id,
                        CallAttempt.tenant_id == job.tenant_id,
                    )
                )
            ).scalar_one_or_none()
            tenant = await session.get(Tenant, job.tenant_id)
            if attempt is None or tenant is None:
                job.status = JobStatus.DEAD_LETTER.value
                job.last_error = "call_attempt_or_tenant_not_found"
                await session.commit()
                return True
            settings = get_app_settings()
            try:
                extractor = (
                    extractor_from_settings(settings)
                    if attempt.status == CallAttemptStatus.COMPLETED.value
                    else None
                )
                await process_post_call_outcome(
                    session,
                    attempt,
                    tenant_timezone=tenant.timezone,
                    extractor=extractor,
                    confidence_threshold=settings.post_call_outcome_confidence_threshold,
                )
                job.status = JobStatus.COMPLETED.value
                job.completed_at = utcnow()
                job.last_error = None
                job.lease_owner = None
                job.lease_expires_at = None
            except Exception as exc:
                error_code = (
                    str(exc)
                    if isinstance(exc, PostCallOutcomeError)
                    else "outcome_processing_failed"
                )
                logger.warning(
                    "post_call_outcome.failed attempt_id=%s error_code=%s",
                    attempt.id,
                    error_code,
                )
                outcome = await get_or_create_outcome(session, attempt)
                outcome.processing_error = error_code[:500]
                job.last_error = error_code[:2000]
                job.lease_owner = None
                job.lease_expires_at = None
                if job.attempt_count >= job.max_attempts:
                    outcome.processing_status = "failed"
                    job.status = JobStatus.DEAD_LETTER.value
                else:
                    outcome.processing_status = "pending"
                    job.status = JobStatus.PENDING.value
                    job.available_at = utcnow() + timedelta(
                        seconds=min(300, 15 * (2 ** max(0, job.attempt_count - 1)))
                    )
            await session.commit()
            return True
        enrollment = (
            await session.execute(
                select(CampaignEnrollment)
                .options(selectinload(CampaignEnrollment.attempts))
                .where(
                    CampaignEnrollment.id == job.campaign_enrollment_id,
                    CampaignEnrollment.tenant_id == job.tenant_id,
                )
            )
        ).scalar_one_or_none()
        campaign = await load_campaign(session, job.tenant_id, job.campaign_id) if job.campaign_id else None
        if enrollment is None or campaign is None:
            job.status = JobStatus.DEAD_LETTER.value
            job.last_error = "campaign_or_enrollment_not_found"
            await session.commit()
            return True
        if campaign.status == CampaignStatus.PAUSED.value:
            job.status = JobStatus.PENDING.value
            job.attempt_count = max(0, job.attempt_count - 1)
            job.lease_owner = None
            job.lease_expires_at = None
            job.available_at = utcnow() + timedelta(seconds=30)
            await session.commit()
            return True
        if campaign.status != CampaignStatus.RUNNING.value:
            job.status = JobStatus.CANCELLED.value
            await session.commit()
            return True
        if enrollment.status not in {
            EnrollmentStatus.QUEUED.value,
            EnrollmentStatus.RETRY_SCHEDULED.value,
        }:
            job.status = JobStatus.COMPLETED.value
            job.completed_at = utcnow()
            await session.commit()
            return True
        if campaign.knowledge_base_version_id is None:
            job.status = JobStatus.DEAD_LETTER.value
            job.last_error = "campaign_knowledge_base_version_missing"
            campaign.status = CampaignStatus.FAILED.value
            await session.commit()
            return True

        lead = (
            await session.execute(
                select(Lead).where(
                    Lead.id == enrollment.lead_id,
                    Lead.tenant_id == enrollment.tenant_id,
                )
            )
        ).scalar_one()
        knowledge_version = (
            await session.execute(
                select(TenantKnowledgeBaseVersion)
                .options(selectinload(TenantKnowledgeBaseVersion.questions))
                .where(
                    TenantKnowledgeBaseVersion.id == campaign.knowledge_base_version_id,
                    TenantKnowledgeBaseVersion.tenant_id == enrollment.tenant_id,
                )
            )
        ).scalar_one()
        tenant = await session.get(Tenant, enrollment.tenant_id)
        agent_context = {
            "organization_name": tenant.name if tenant else "the business",
            "lead": {"name": lead.name, "attributes": lead.attributes_json},
            "knowledge_base": {
                "title": knowledge_version.title,
                "business_profile": knowledge_version.business_profile_json,
                "additional_notes": knowledge_version.additional_notes,
                "answers": [
                    {"question": question.label, "answer": question.answer_value_json}
                    for question in knowledge_version.questions
                    if question.answer_value_json is not None
                ],
            },
        }
        attempt_number = int(job.payload_json["attempt_number"])
        attempt = next(
            (item for item in enrollment.attempts if item.attempt_number == attempt_number),
            None,
        )
        if attempt is None:
            attempt = CallAttempt(
                tenant_id=enrollment.tenant_id,
                campaign_enrollment_id=enrollment.id,
                attempt_number=attempt_number,
                status=CallAttemptStatus.QUEUED.value,
                scheduled_at=job.available_at,
                knowledge_base_version_id=campaign.knowledge_base_version_id,
                context_snapshot_json={
                    "campaign_id": str(campaign.id),
                    "campaign_name": campaign.name,
                    "lead_id": str(lead.id),
                    "lead_name": lead.name,
                    "lead_phone_number": lead.normalized_phone_number,
                    "lead_attributes": lead.attributes_json,
                    "agent_context": agent_context,
                },
            )
            session.add(attempt)
            await session.flush()
        attempt.status = CallAttemptStatus.DIALING.value
        attempt.started_at = attempt.started_at or utcnow()
        enrollment.status = EnrollmentStatus.CALLING.value
        enrollment.attempt_count = max(enrollment.attempt_count, attempt_number)
        enrollment.next_attempt_at = None
        await session.commit()

        service = LiveKitCallService(get_voice_settings())
        try:
            response = await service.create_campaign_call(
                phone_number=lead.normalized_phone_number,
                room_name=f"ringiq-call-{attempt.id.hex[:12]}",
                metadata={
                    "call_id": str(attempt.id),
                    "tenant_id": str(enrollment.tenant_id),
                    "campaign_id": str(campaign.id),
                    "campaign_enrollment_id": str(enrollment.id),
                    "call_attempt_id": str(attempt.id),
                    "knowledge_base_version_id": str(campaign.knowledge_base_version_id),
                    "lead_id": str(lead.id),
                    "lead_name": lead.name,
                    "agent_context_json": json.dumps(agent_context, default=str),
                },
            )
            attempt.status = CallAttemptStatus.DIALING.value
            attempt.provider = "livekit_vobiz"
            attempt.provider_call_id = response.livekit_sip_call_id
            attempt.livekit_room_name = response.room_name
            job.status = JobStatus.COMPLETED.value
            job.completed_at = utcnow()
            job.lease_owner = None
            job.lease_expires_at = None
        except LiveKitCallServiceError as exc:
            await apply_attempt_result(
                session,
                campaign,
                enrollment,
                attempt,
                result_status=CallAttemptStatus.FAILED.value,
                failure_code="outbound_call_start_failed",
                failure_detail=str(exc),
                terminal_reason="outbound_call_start_failed",
            )
            job.status = JobStatus.DEAD_LETTER.value
            job.last_error = str(exc)
        await session.commit()
        return True


async def run_worker(*, once: bool, poll_seconds: float = 2.0) -> None:
    worker_id = f"{socket.gethostname()}:{uuid.uuid4().hex[:8]}"
    logger.info("background_worker.started worker_id=%s", worker_id)
    while True:
        processed = await process_next_call_job(worker_id)
        if once:
            return
        if not processed:
            await asyncio.sleep(poll_seconds)


def main() -> None:
    parser = argparse.ArgumentParser(description="RingIQ PostgreSQL-backed job worker")
    parser.add_argument("--once", action="store_true", help="Process at most one due job")
    parser.add_argument("--poll-seconds", type=float, default=2.0)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run_worker(once=args.once, poll_seconds=args.poll_seconds))


if __name__ == "__main__":
    main()
