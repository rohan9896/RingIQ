import asyncio
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import async_sessionmaker

from apps.api.ringiq_api.models.campaigns import (
    CallAttempt,
    CallAttemptStatus,
    CallOutcome,
    CallOutcomeLabel,
    Campaign,
    CampaignEnrollment,
    EnrollmentStatus,
    Job,
    JobStatus,
)
from apps.api.ringiq_api.models.identity import Tenant
from apps.api.ringiq_api.models.knowledge import (
    TenantKnowledgeBase,
    TenantKnowledgeBaseVersion,
)
from apps.api.ringiq_api.models.leads import Lead
from apps.api.ringiq_api.routes.campaigns import _locked_attempt
from apps.api.ringiq_api.services.campaign_operations import (
    POST_CALL_JOB_TYPE,
    claim_job,
    enqueue_post_call_outcome_if_ready,
    utcnow,
)
from apps.api.ringiq_api.services.post_call_outcomes import (
    ExtractedOutcome,
    OutcomeEvidence,
    PostCallOutcomeError,
    QualificationFacts,
    _normalize_callback_at,
    get_or_create_outcome,
    process_post_call_outcome,
)
from tests.api.postgres import create_test_engine, reset_database


class FakeExtractor:
    provider = "test"
    model = "test-outcome-model"

    def __init__(self, result: ExtractedOutcome) -> None:
        self.result = result
        self.calls = 0

    async def extract(self, **_: object) -> ExtractedOutcome:
        self.calls += 1
        return self.result


async def seed_attempt(session, *, status: str, finalized: bool = False):
    tenant = Tenant(clerk_organization_id="org_outcome", name="Outcome Realty", slug="outcome")
    session.add(tenant)
    await session.flush()
    workspace = TenantKnowledgeBase(tenant_id=tenant.id)
    session.add(workspace)
    await session.flush()
    knowledge_version = TenantKnowledgeBaseVersion(
        knowledge_base_id=workspace.id,
        tenant_id=tenant.id,
        version=1,
        title="Outcome KB",
        business_profile_json={"business_name": "Outcome Realty"},
        status="published",
    )
    lead = Lead(
        tenant_id=tenant.id,
        name="Buyer",
        email="buyer@example.com",
        phone_number="9898634500",
        normalized_phone_number="+919898634500",
    )
    session.add_all([knowledge_version, lead])
    await session.flush()
    workspace.active_version_id = knowledge_version.id
    campaign = Campaign(
        tenant_id=tenant.id,
        name="Outcome calls",
        status="running",
        knowledge_base_version_id=knowledge_version.id,
    )
    session.add(campaign)
    await session.flush()
    enrollment = CampaignEnrollment(
        tenant_id=tenant.id,
        campaign_id=campaign.id,
        lead_id=lead.id,
        status=(
            EnrollmentStatus.COMPLETED.value
            if status == CallAttemptStatus.COMPLETED.value
            else EnrollmentStatus.EXHAUSTED.value
        ),
        attempt_count=1,
    )
    session.add(enrollment)
    await session.flush()
    attempt = CallAttempt(
        tenant_id=tenant.id,
        campaign_enrollment_id=enrollment.id,
        attempt_number=1,
        status=status,
        scheduled_at=datetime.now(timezone.utc),
        ended_at=datetime.now(timezone.utc),
        knowledge_base_version_id=knowledge_version.id,
        transcript_json=[
            {"role": "assistant", "text": "When should we call you back?", "interrupted": False},
            {"role": "user", "text": "Please call me tomorrow evening.", "interrupted": False},
        ],
        artifacts_finalized_at=datetime.now(timezone.utc) if finalized else None,
        terminal_reason="qualification_complete" if status == "completed" else status,
    )
    session.add(attempt)
    await session.flush()
    enrollment.final_call_attempt_id = attempt.id
    return tenant, enrollment, attempt


@pytest.mark.parametrize(
    ("status", "expected_label"),
    [
        (CallAttemptStatus.UNANSWERED.value, CallOutcomeLabel.UNANSWERED.value),
        (CallAttemptStatus.INVALID_NUMBER.value, CallOutcomeLabel.INVALID_NUMBER.value),
    ],
)
@pytest.mark.asyncio
async def test_operational_outcomes_do_not_call_extractor(
    status: str,
    expected_label: str,
) -> None:
    engine = create_test_engine()
    try:
        await reset_database(engine)
        factory = async_sessionmaker(engine, expire_on_commit=False)
        async with factory() as session:
            _, _, attempt = await seed_attempt(session, status=status)
            extractor = FakeExtractor(
                ExtractedOutcome(
                    label="hot",
                    confidence=1,
                    rationale="unused",
                    summary="unused",
                )
            )
            outcome = await process_post_call_outcome(
                session,
                attempt,
                tenant_timezone="Asia/Kolkata",
                extractor=extractor,
            )
            assert outcome.label == expected_label
            assert outcome.extractor_provider == "deterministic"
            assert extractor.calls == 0
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_operational_outcome_persists_fallback_terminal_reason() -> None:
    engine = create_test_engine()
    try:
        await reset_database(engine)
        factory = async_sessionmaker(engine, expire_on_commit=False)
        async with factory() as session:
            _, _, attempt = await seed_attempt(
                session, status=CallAttemptStatus.FAILED.value
            )
            attempt.terminal_reason = None
            attempt.failure_code = "outbound_call_start_failed"
            outcome = await process_post_call_outcome(
                session,
                attempt,
                tenant_timezone="Asia/Kolkata",
                extractor=None,
            )
            assert outcome.label == CallOutcomeLabel.NEEDS_REVIEW.value
            assert outcome.terminal_reason == "outbound_call_start_failed"
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_connected_outcome_preserves_ambiguous_callback_without_inventing_time() -> None:
    engine = create_test_engine()
    try:
        await reset_database(engine)
        factory = async_sessionmaker(engine, expire_on_commit=False)
        async with factory() as session:
            _, _, attempt = await seed_attempt(
                session, status=CallAttemptStatus.COMPLETED.value, finalized=True
            )
            extractor = FakeExtractor(
                ExtractedOutcome(
                    label="callback_requested",
                    confidence=0.93,
                    rationale="The customer explicitly requested a callback.",
                    summary="The customer asked to be called tomorrow evening.",
                    qualification_facts=QualificationFacts(),
                    evidence=[
                        OutcomeEvidence(
                            turn_index=1,
                            speaker="user",
                            quote="call me tomorrow evening",
                        )
                    ],
                    callback_original_phrase="Please call me tomorrow evening.",
                    callback_at=None,
                )
            )
            outcome = await process_post_call_outcome(
                session,
                attempt,
                tenant_timezone="Asia/Kolkata",
                extractor=extractor,
            )
            assert outcome.label == CallOutcomeLabel.CALLBACK_REQUESTED.value
            assert outcome.callback_original_phrase == "Please call me tomorrow evening."
            assert outcome.callback_timezone == "Asia/Kolkata"
            assert outcome.callback_at is None
            assert outcome.evidence_json[0]["turn_index"] == 1
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_unsupported_evidence_is_rejected_and_low_confidence_needs_review() -> None:
    engine = create_test_engine()
    try:
        await reset_database(engine)
        factory = async_sessionmaker(engine, expire_on_commit=False)
        async with factory() as session:
            _, _, attempt = await seed_attempt(
                session, status=CallAttemptStatus.COMPLETED.value, finalized=True
            )
            invalid = FakeExtractor(
                ExtractedOutcome(
                    label="hot",
                    confidence=0.95,
                    rationale="High intent.",
                    summary="The customer is ready.",
                    evidence=[OutcomeEvidence(turn_index=1, speaker="user", quote="site visit")],
                )
            )
            with pytest.raises(PostCallOutcomeError, match="evidence_quote_mismatch"):
                await process_post_call_outcome(
                    session,
                    attempt,
                    tenant_timezone="Asia/Kolkata",
                    extractor=invalid,
                )
            low_confidence = FakeExtractor(
                ExtractedOutcome(
                    label="warm",
                    confidence=0.4,
                    rationale="Interest is unclear.",
                    summary="The customer requested a later call.",
                    evidence=[
                        OutcomeEvidence(turn_index=1, speaker="user", quote="tomorrow evening")
                    ],
                )
            )
            outcome = await process_post_call_outcome(
                session,
                attempt,
                tenant_timezone="Asia/Kolkata",
                extractor=low_confidence,
                confidence_threshold=0.6,
            )
            assert outcome.label == CallOutcomeLabel.NEEDS_REVIEW.value
            assert outcome.qualification_facts_json == {}
            assert outcome.callback_at is None
            assert outcome.summary == "Outcome needs review; consult the cited transcript evidence."
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_unsupported_qualification_facts_are_not_persisted() -> None:
    engine = create_test_engine()
    try:
        await reset_database(engine)
        factory = async_sessionmaker(engine, expire_on_commit=False)
        async with factory() as session:
            _, _, attempt = await seed_attempt(
                session, status=CallAttemptStatus.COMPLETED.value, finalized=True
            )
            extractor = FakeExtractor(
                ExtractedOutcome(
                    label="hot",
                    confidence=0.95,
                    rationale="The customer has a large budget.",
                    summary="The customer is ready to buy.",
                    qualification_facts=QualificationFacts(budget="Ten crore"),
                    evidence=[
                        OutcomeEvidence(
                            turn_index=1,
                            speaker="user",
                            quote="tomorrow evening",
                        )
                    ],
                )
            )
            outcome = await process_post_call_outcome(
                session,
                attempt,
                tenant_timezone="Asia/Kolkata",
                extractor=extractor,
            )
            assert outcome.label == CallOutcomeLabel.NEEDS_REVIEW.value
            assert outcome.qualification_facts_json == {}
            assert outcome.rationale == (
                "Outcome requires review: qualification_facts_unsupported."
            )
    finally:
        await engine.dispose()


def test_callback_timestamp_must_match_spoken_time_and_reference_date() -> None:
    reference = datetime(2026, 7, 20, 12, tzinfo=timezone.utc)
    assert _normalize_callback_at(
        "2026-07-21T17:00:00+05:30",
        "Please call tomorrow at 5 pm",
        tenant_timezone="Asia/Kolkata",
        reference_time=reference,
    ) == datetime(2026, 7, 21, 11, 30, tzinfo=timezone.utc)
    assert (
        _normalize_callback_at(
            "2030-01-01T17:00:00+05:30",
            "Please call tomorrow at 5 pm",
            tenant_timezone="Asia/Kolkata",
            reference_time=reference,
        )
        is None
    )
    assert (
        _normalize_callback_at(
            "2026-06-05T16:00:00+05:30",
            "Please call 5/6 at 4 pm",
            tenant_timezone="Asia/Kolkata",
            reference_time=reference,
        )
        is None
    )


@pytest.mark.asyncio
async def test_callback_order_and_duplicates_create_one_job_and_outcome() -> None:
    engine = create_test_engine()
    try:
        await reset_database(engine)
        factory = async_sessionmaker(engine, expire_on_commit=False)
        async with factory() as session:
            _, enrollment, attempt = await seed_attempt(
                session, status=CallAttemptStatus.COMPLETED.value, finalized=False
            )
            assert await enqueue_post_call_outcome_if_ready(
                session, attempt, enrollment=enrollment
            ) is None
            assert await session.scalar(select(func.count(CallOutcome.id))) == 1
            assert await session.scalar(select(func.count(Job.id))) == 0

            attempt.artifacts_finalized_at = datetime.now(timezone.utc)
            first = await enqueue_post_call_outcome_if_ready(
                session, attempt, enrollment=enrollment
            )
            await session.flush()
            repeated = await enqueue_post_call_outcome_if_ready(
                session, attempt, enrollment=enrollment
            )
            assert first is not None
            assert repeated is not None
            assert first.id == repeated.id
            assert await session.scalar(select(func.count(CallOutcome.id))) == 1
            assert await session.scalar(select(func.count(Job.id))) == 1
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_overlapping_result_and_artifact_updates_schedule_one_job() -> None:
    engine = create_test_engine()
    try:
        await reset_database(engine)
        factory = async_sessionmaker(engine, expire_on_commit=False)
        async with factory() as setup_session:
            _, _, seeded_attempt = await seed_attempt(
                setup_session,
                status=CallAttemptStatus.CONNECTED.value,
                finalized=False,
            )
            attempt_id = seeded_attempt.id
            await setup_session.commit()

        result_has_lock = asyncio.Event()
        allow_result_commit = asyncio.Event()

        async def store_result() -> None:
            async with factory() as session:
                attempt = await _locked_attempt(session, attempt_id)
                assert attempt is not None
                attempt.status = CallAttemptStatus.COMPLETED.value
                attempt.ended_at = datetime.now(timezone.utc)
                await enqueue_post_call_outcome_if_ready(session, attempt)
                result_has_lock.set()
                await allow_result_commit.wait()
                await session.commit()

        async def store_artifacts() -> None:
            await result_has_lock.wait()
            async with factory() as session:
                attempt = await _locked_attempt(session, attempt_id)
                assert attempt is not None
                attempt.transcript_json = [
                    {"role": "user", "text": "Call tomorrow at 5 pm."}
                ]
                attempt.artifacts_finalized_at = datetime.now(timezone.utc)
                await enqueue_post_call_outcome_if_ready(session, attempt)
                await session.commit()

        result_task = asyncio.create_task(store_result())
        artifact_task = asyncio.create_task(store_artifacts())
        await result_has_lock.wait()
        await asyncio.sleep(0.05)
        allow_result_commit.set()
        await asyncio.gather(result_task, artifact_task)

        async with factory() as session:
            assert await session.scalar(select(func.count(CallOutcome.id))) == 1
            assert await session.scalar(select(func.count(Job.id))) == 1
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_retry_scheduled_unanswered_attempt_still_gets_outcome_job() -> None:
    engine = create_test_engine()
    try:
        await reset_database(engine)
        factory = async_sessionmaker(engine, expire_on_commit=False)
        async with factory() as session:
            _, enrollment, attempt = await seed_attempt(
                session, status=CallAttemptStatus.UNANSWERED.value
            )
            enrollment.status = EnrollmentStatus.RETRY_SCHEDULED.value
            job = await enqueue_post_call_outcome_if_ready(
                session,
                attempt,
                enrollment=enrollment,
            )
            assert job is not None
            assert job.job_type == POST_CALL_JOB_TYPE
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_exhausted_post_call_lease_marks_outcome_failed() -> None:
    engine = create_test_engine()
    try:
        await reset_database(engine)
        factory = async_sessionmaker(engine, expire_on_commit=False)
        async with factory() as session:
            tenant, enrollment, attempt = await seed_attempt(
                session, status=CallAttemptStatus.COMPLETED.value, finalized=True
            )
            outcome = await get_or_create_outcome(session, attempt)
            outcome.processing_status = "processing"
            session.add(
                Job(
                    tenant_id=tenant.id,
                    campaign_id=enrollment.campaign_id,
                    campaign_enrollment_id=enrollment.id,
                    job_type=POST_CALL_JOB_TYPE,
                    status=JobStatus.LEASED.value,
                    payload_json={"call_attempt_id": str(attempt.id)},
                    idempotency_key=str(attempt.id),
                    available_at=utcnow(),
                    attempt_count=3,
                    max_attempts=3,
                    lease_owner="dead-worker",
                    lease_expires_at=utcnow() - timedelta(seconds=1),
                )
            )
            await session.commit()

            assert await claim_job(session, worker_id="recovery-worker") is None
            stored_outcome = await session.scalar(
                select(CallOutcome).where(CallOutcome.id == outcome.id)
            )
            stored_job = await session.scalar(
                select(Job).where(Job.idempotency_key == str(attempt.id))
            )
            assert stored_outcome is not None
            assert stored_outcome.processing_status == "failed"
            assert stored_outcome.processing_error == "job_lease_exhausted"
            assert stored_job is not None
            assert stored_job.status == JobStatus.DEAD_LETTER.value
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_outcome_tenant_must_match_attempt_tenant() -> None:
    engine = create_test_engine()
    try:
        await reset_database(engine)
        factory = async_sessionmaker(engine, expire_on_commit=False)
        async with factory() as session:
            _, _, attempt = await seed_attempt(
                session, status=CallAttemptStatus.UNANSWERED.value
            )
            other_tenant = Tenant(
                clerk_organization_id="org_outcome_other",
                name="Other Realty",
                slug="outcome-other",
            )
            session.add(other_tenant)
            await session.flush()
            session.add(
                CallOutcome(
                    id=uuid.uuid4(),
                    tenant_id=other_tenant.id,
                    call_attempt_id=attempt.id,
                )
            )
            with pytest.raises(IntegrityError):
                await session.flush()
    finally:
        await engine.dispose()
