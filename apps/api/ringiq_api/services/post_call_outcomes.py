import json
import re
import uuid
from datetime import date, datetime, timedelta, timezone
from typing import Protocol
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from openai import AsyncOpenAI
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.ringiq_api.config import AppSettings
from apps.api.ringiq_api.models.campaigns import (
    CallAttempt,
    CallAttemptStatus,
    CallOutcome,
    CallOutcomeLabel,
    CallOutcomeStatus,
)

EXTRACTOR_VERSION = "v1"


class PostCallOutcomeError(RuntimeError):
    """Safe, retryable post-call processing error."""


class QualificationFacts(BaseModel):
    model_config = ConfigDict(extra="forbid")

    area: str | None = Field(default=None, max_length=500)
    budget: str | None = Field(default=None, max_length=500)
    property_type: str | None = Field(default=None, max_length=500)
    intent: str | None = Field(default=None, max_length=500)
    timeline: str | None = Field(default=None, max_length=500)


class OutcomeEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid")

    turn_index: int = Field(ge=0)
    speaker: str = Field(pattern="^(user|assistant)$")
    quote: str = Field(min_length=1, max_length=2000)


class ExtractedOutcome(BaseModel):
    model_config = ConfigDict(extra="forbid")

    label: CallOutcomeLabel
    confidence: float = Field(ge=0, le=1)
    rationale: str = Field(min_length=1, max_length=2000)
    summary: str = Field(min_length=1, max_length=4000)
    qualification_facts: QualificationFacts = Field(default_factory=QualificationFacts)
    evidence: list[OutcomeEvidence] = Field(default_factory=list, max_length=20)
    callback_original_phrase: str | None = Field(default=None, max_length=1000)
    callback_at: str | None = Field(default=None, max_length=100)


class OutcomeExtractor(Protocol):
    provider: str
    model: str

    async def extract(
        self,
        *,
        transcript: list[dict],
        tenant_timezone: str,
        terminal_reason: str | None,
    ) -> ExtractedOutcome: ...


class GroqOutcomeExtractor:
    provider = "groq"

    def __init__(self, settings: AppSettings) -> None:
        if not settings.post_call_outcome_api_key:
            raise PostCallOutcomeError("extractor_not_configured")
        self.model = settings.post_call_outcome_model
        self._client = AsyncOpenAI(
            api_key=settings.post_call_outcome_api_key,
            base_url=settings.post_call_outcome_base_url,
            timeout=settings.post_call_outcome_timeout_seconds,
        )

    async def extract(
        self,
        *,
        transcript: list[dict],
        tenant_timezone: str,
        terminal_reason: str | None,
    ) -> ExtractedOutcome:
        numbered_transcript = [
            {
                "turn_index": index,
                "speaker": turn.get("role"),
                "text": turn.get("text"),
            }
            for index, turn in enumerate(transcript)
        ]
        system_prompt = """You extract a read-only post-call qualification outcome from a transcript.
Use only the transcript and terminal reason. Return one JSON object and no prose.
Allowed labels: hot, warm, cold, callback_requested, not_interested, needs_review.
Every evidence item must copy an exact quote from the cited turn and preserve its speaker.
Never invent a fact, summary detail, callback phrase, date, or time. Use null for unknown facts.
Every classification, summary statement, rationale statement, and qualification fact must be
supported by at least one returned evidence quote.
For a callback, preserve the customer's original phrase. Set callback_at only when the customer
gave an unambiguous date, time, and timezone; otherwise set it to null. callback_at must be ISO-8601
with an explicit UTC offset. Use needs_review when evidence is ambiguous or insufficient.
The JSON keys are: label, confidence, rationale, summary, qualification_facts
(area, budget, property_type, intent, timeline), evidence (turn_index, speaker, quote),
callback_original_phrase, callback_at."""
        try:
            response = await self._client.chat.completions.create(
                model=self.model,
                temperature=0,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": json.dumps(
                            {
                                "tenant_timezone": tenant_timezone,
                                "terminal_reason": terminal_reason,
                                "transcript": numbered_transcript,
                            },
                            ensure_ascii=False,
                        ),
                    },
                ],
            )
            content = response.choices[0].message.content
            if not content:
                raise PostCallOutcomeError("extractor_empty_response")
            return ExtractedOutcome.model_validate_json(content)
        except PostCallOutcomeError:
            raise
        except Exception as exc:
            raise PostCallOutcomeError("extractor_request_failed") from exc


async def get_or_create_outcome(
    session: AsyncSession,
    attempt: CallAttempt,
) -> CallOutcome:
    outcome = (
        await session.execute(
            select(CallOutcome).where(
                CallOutcome.call_attempt_id == attempt.id,
                CallOutcome.tenant_id == attempt.tenant_id,
            )
        )
    ).scalar_one_or_none()
    if outcome is None:
        await session.execute(
            pg_insert(CallOutcome)
            .values(
                id=uuid.uuid4(),
                tenant_id=attempt.tenant_id,
                call_attempt_id=attempt.id,
                terminal_reason=attempt.terminal_reason,
            )
            .on_conflict_do_nothing(index_elements=["call_attempt_id"])
        )
        outcome = (
            await session.execute(
                select(CallOutcome).where(
                    CallOutcome.call_attempt_id == attempt.id,
                    CallOutcome.tenant_id == attempt.tenant_id,
                )
            )
        ).scalar_one()
    elif attempt.terminal_reason and not outcome.terminal_reason:
        outcome.terminal_reason = attempt.terminal_reason
    return outcome


def _validate_evidence(
    transcript: list[dict],
    evidence: list[OutcomeEvidence],
) -> list[dict]:
    validated: list[dict] = []
    for item in evidence:
        if item.turn_index >= len(transcript):
            raise PostCallOutcomeError("evidence_turn_not_found")
        turn = transcript[item.turn_index]
        if turn.get("role") != item.speaker:
            raise PostCallOutcomeError("evidence_speaker_mismatch")
        text = turn.get("text")
        if not isinstance(text, str) or item.quote not in text:
            raise PostCallOutcomeError("evidence_quote_mismatch")
        validated.append(item.model_dump())
    return validated


def _spoken_callback_time(phrase: str) -> tuple[int, int] | None:
    twenty_four_hour = re.search(
        r"\b(?P<hour>[01]?\d|2[0-3]):(?P<minute>[0-5]\d)\b",
        phrase,
    )
    if twenty_four_hour:
        return int(twenty_four_hour.group("hour")), int(
            twenty_four_hour.group("minute")
        )
    twelve_hour = re.search(
        r"\b(?P<hour>1[0-2]|0?[1-9])(?:[:.](?P<minute>[0-5]\d))?\s*(?P<period>am|pm)\b",
        phrase,
    )
    if not twelve_hour:
        return None
    hour = int(twelve_hour.group("hour")) % 12
    if twelve_hour.group("period") == "pm":
        hour += 12
    return hour, int(twelve_hour.group("minute") or 0)


def _spoken_callback_date(
    phrase: str,
    *,
    reference_time: datetime | None,
    tenant_zone: ZoneInfo,
) -> date | None:
    iso_date = re.search(r"\b\d{4}-\d{2}-\d{2}\b", phrase)
    if iso_date:
        try:
            return date.fromisoformat(iso_date.group(0))
        except ValueError:
            return None

    relative_date = re.search(r"\b(today|tomorrow)\b", phrase)
    if relative_date:
        if reference_time is None or reference_time.tzinfo is None:
            return None
        local_reference = reference_time.astimezone(tenant_zone).date()
        return local_reference + timedelta(
            days=1 if relative_date.group(1) == "tomorrow" else 0
        )

    month_date = re.search(
        r"\b(?P<month>jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|"
        r"jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|"
        r"nov(?:ember)?|dec(?:ember)?)\s+(?P<day>\d{1,2})(?:,)?\s+(?P<year>\d{4})\b",
        phrase,
    )
    if month_date:
        try:
            return datetime.strptime(
                f"{month_date.group('month')} {month_date.group('day')} {month_date.group('year')}",
                "%B %d %Y",
            ).date()
        except ValueError:
            try:
                return datetime.strptime(
                    f"{month_date.group('month')} {month_date.group('day')} {month_date.group('year')}",
                    "%b %d %Y",
                ).date()
            except ValueError:
                return None
    return None


def _normalize_callback_at(
    value: str | None,
    phrase: str | None,
    *,
    tenant_timezone: str,
    reference_time: datetime | None,
) -> datetime | None:
    if not value or not phrase:
        return None
    normalized_phrase = phrase.casefold()
    spoken_time = _spoken_callback_time(normalized_phrase)
    try:
        tenant_zone = ZoneInfo(tenant_timezone)
    except ZoneInfoNotFoundError:
        return None
    spoken_date = _spoken_callback_date(
        normalized_phrase,
        reference_time=reference_time,
        tenant_zone=tenant_zone,
    )
    if spoken_date is None or spoken_time is None:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        return None
    local_value = parsed.astimezone(tenant_zone)
    if (
        local_value.date() != spoken_date
        or (local_value.hour, local_value.minute) != spoken_time
    ):
        return None
    normalized_local = datetime.combine(
        spoken_date,
        datetime.min.time().replace(
            hour=spoken_time[0],
            minute=spoken_time[1],
        ),
        tzinfo=tenant_zone,
    )
    return normalized_local.astimezone(timezone.utc)


def _callback_phrase_is_grounded(transcript: list[dict], phrase: str | None) -> bool:
    if not phrase:
        return False
    return any(
        turn.get("role") == "user"
        and isinstance(turn.get("text"), str)
        and phrase in turn["text"]
        for turn in transcript
    )


def _qualification_facts_are_grounded(
    transcript: list[dict],
    facts: QualificationFacts,
) -> bool:
    transcript_text = [
        turn["text"].casefold()
        for turn in transcript
        if isinstance(turn.get("text"), str)
    ]
    return all(
        value is None
        or any(value.casefold() in turn_text for turn_text in transcript_text)
        for value in facts.model_dump().values()
    )


def _complete_deterministic_outcome(
    outcome: CallOutcome,
    attempt: CallAttempt,
) -> bool:
    label_by_status = {
        CallAttemptStatus.UNANSWERED.value: CallOutcomeLabel.UNANSWERED.value,
        CallAttemptStatus.INVALID_NUMBER.value: CallOutcomeLabel.INVALID_NUMBER.value,
    }
    label = label_by_status.get(attempt.status)
    if label is None and attempt.status in {
        CallAttemptStatus.BUSY.value,
        CallAttemptStatus.FAILED.value,
        CallAttemptStatus.CANCELLED.value,
    }:
        label = CallOutcomeLabel.NEEDS_REVIEW.value
    if label is None:
        return False

    reason = attempt.terminal_reason or attempt.failure_code or attempt.status
    outcome.processing_status = CallOutcomeStatus.COMPLETED.value
    outcome.processing_error = None
    outcome.processed_at = datetime.now(timezone.utc)
    outcome.label = label
    outcome.confidence = 1.0 if label != CallOutcomeLabel.NEEDS_REVIEW.value else 0.0
    outcome.rationale = f"Operational call result: {reason}."
    outcome.summary = f"Call ended with operational status {attempt.status.replace('_', ' ')}."
    outcome.qualification_facts_json = {}
    outcome.evidence_json = []
    outcome.callback_original_phrase = None
    outcome.callback_timezone = None
    outcome.callback_at = None
    outcome.terminal_reason = reason
    outcome.extractor_provider = "deterministic"
    outcome.extractor_model = None
    outcome.extractor_version = EXTRACTOR_VERSION
    return True


async def process_post_call_outcome(
    session: AsyncSession,
    attempt: CallAttempt,
    *,
    tenant_timezone: str,
    extractor: OutcomeExtractor | None,
    confidence_threshold: float = 0.6,
) -> CallOutcome:
    outcome = await get_or_create_outcome(session, attempt)
    if outcome.processing_status == CallOutcomeStatus.COMPLETED.value:
        return outcome

    outcome.processing_status = CallOutcomeStatus.PROCESSING.value
    outcome.processing_attempts += 1
    outcome.processing_error = None
    outcome.terminal_reason = attempt.terminal_reason
    await session.flush()

    if _complete_deterministic_outcome(outcome, attempt):
        return outcome
    if attempt.status != CallAttemptStatus.COMPLETED.value:
        raise PostCallOutcomeError("attempt_not_ready")
    if attempt.artifacts_finalized_at is None:
        raise PostCallOutcomeError("artifacts_not_finalized")
    if extractor is None:
        raise PostCallOutcomeError("extractor_not_configured")

    extracted = await extractor.extract(
        transcript=attempt.transcript_json,
        tenant_timezone=tenant_timezone,
        terminal_reason=attempt.terminal_reason,
    )
    validated_evidence = _validate_evidence(attempt.transcript_json, extracted.evidence)
    label = extracted.label.value
    review_reason: str | None = None
    if label in {
        CallOutcomeLabel.UNANSWERED.value,
        CallOutcomeLabel.INVALID_NUMBER.value,
    }:
        label = CallOutcomeLabel.NEEDS_REVIEW.value
        review_reason = "connected_extractor_returned_operational_label"
    phrase_grounded = _callback_phrase_is_grounded(
        attempt.transcript_json, extracted.callback_original_phrase
    )
    if extracted.callback_original_phrase and not phrase_grounded:
        raise PostCallOutcomeError("callback_phrase_mismatch")
    facts_grounded = _qualification_facts_are_grounded(
        attempt.transcript_json,
        extracted.qualification_facts,
    )
    if extracted.confidence < confidence_threshold:
        label = CallOutcomeLabel.NEEDS_REVIEW.value
        review_reason = "confidence_below_threshold"
    elif label != CallOutcomeLabel.NEEDS_REVIEW.value and not validated_evidence:
        label = CallOutcomeLabel.NEEDS_REVIEW.value
        review_reason = "supporting_evidence_missing"
    elif not facts_grounded:
        label = CallOutcomeLabel.NEEDS_REVIEW.value
        review_reason = "qualification_facts_unsupported"
    if label == CallOutcomeLabel.CALLBACK_REQUESTED.value and not phrase_grounded:
        label = CallOutcomeLabel.NEEDS_REVIEW.value
        review_reason = "callback_phrase_missing"
    if label == CallOutcomeLabel.NEEDS_REVIEW.value and review_reason is None:
        review_reason = "extractor_marked_needs_review"

    needs_review = label == CallOutcomeLabel.NEEDS_REVIEW.value
    normalized_callback_at = _normalize_callback_at(
        extracted.callback_at,
        extracted.callback_original_phrase,
        tenant_timezone=tenant_timezone,
        reference_time=attempt.ended_at,
    )

    outcome.processing_status = CallOutcomeStatus.COMPLETED.value
    outcome.processing_error = None
    outcome.processed_at = datetime.now(timezone.utc)
    outcome.label = label
    outcome.confidence = extracted.confidence
    outcome.rationale = (
        f"Outcome requires review: {review_reason}."
        if needs_review
        else extracted.rationale
    )
    outcome.summary = (
        "Outcome needs review; consult the cited transcript evidence."
        if needs_review
        else extracted.summary
    )
    outcome.qualification_facts_json = (
        {} if needs_review else extracted.qualification_facts.model_dump()
    )
    outcome.evidence_json = validated_evidence
    outcome.callback_original_phrase = extracted.callback_original_phrase
    outcome.callback_timezone = tenant_timezone if extracted.callback_original_phrase else None
    outcome.callback_at = None if needs_review else normalized_callback_at
    outcome.extractor_provider = extractor.provider
    outcome.extractor_model = extractor.model
    outcome.extractor_version = EXTRACTOR_VERSION
    return outcome


async def mark_outcome_failed(
    session: AsyncSession,
    *,
    attempt_id: uuid.UUID,
    tenant_id: uuid.UUID,
    error_code: str,
) -> None:
    outcome = (
        await session.execute(
            select(CallOutcome).where(
                CallOutcome.call_attempt_id == attempt_id,
                CallOutcome.tenant_id == tenant_id,
            )
        )
    ).scalar_one_or_none()
    if outcome is not None and outcome.processing_status != CallOutcomeStatus.COMPLETED.value:
        outcome.processing_status = CallOutcomeStatus.FAILED.value
        outcome.processing_error = error_code[:500]


def extractor_from_settings(settings: AppSettings) -> GroqOutcomeExtractor:
    return GroqOutcomeExtractor(settings)
