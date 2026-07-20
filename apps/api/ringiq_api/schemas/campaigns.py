import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from apps.api.ringiq_api.models.campaigns import (
    CallAttemptStatus,
    CampaignStatus,
    EnrollmentStatus,
)


class CampaignCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    lead_ids: list[uuid.UUID] = Field(min_length=1, max_length=10_000)
    source_import_id: uuid.UUID | None = None
    retry_limit: int = Field(default=3, ge=0, le=10)


class CampaignReadinessResponse(BaseModel):
    is_ready: bool
    blockers: list[str]


class CampaignKnowledgeBaseResponse(BaseModel):
    id: uuid.UUID
    title: str
    version: int
    status: str
    category_id: uuid.UUID | None
    is_pinned: bool


class CampaignProgressResponse(BaseModel):
    total: int
    pending: int = 0
    queued: int = 0
    calling: int = 0
    connected: int = 0
    retry_scheduled: int = 0
    completed: int = 0
    invalid_number: int = 0
    exhausted: int = 0
    cancelled: int = 0


class QualificationFactsResponse(BaseModel):
    area: str | None = None
    budget: str | None = None
    property_type: str | None = None
    intent: str | None = None
    timeline: str | None = None


class OutcomeEvidenceResponse(BaseModel):
    turn_index: int
    speaker: Literal["user", "assistant"]
    quote: str


class CallOutcomeResponse(BaseModel):
    id: uuid.UUID
    processing_status: Literal["pending", "processing", "completed", "failed"]
    processing_error: str | None
    processed_at: datetime | None
    label: Literal[
        "hot",
        "warm",
        "cold",
        "callback_requested",
        "not_interested",
        "unanswered",
        "invalid_number",
        "needs_review",
    ] | None
    confidence: float | None
    rationale: str | None
    summary: str | None
    qualification_facts: QualificationFactsResponse
    evidence: list[OutcomeEvidenceResponse]
    callback_original_phrase: str | None
    callback_timezone: str | None
    callback_at: datetime | None
    terminal_reason: str | None


class CallAttemptResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    attempt_number: int
    status: CallAttemptStatus
    scheduled_at: datetime
    started_at: datetime | None
    answered_at: datetime | None
    ended_at: datetime | None
    duration_seconds: int | None
    provider: str | None
    provider_call_id: str | None
    livekit_room_name: str | None
    failure_code: str | None
    failure_detail: str | None
    terminal_reason: str | None
    artifacts_finalized_at: datetime | None
    outcome: CallOutcomeResponse | None = None


class CampaignEnrollmentResponse(BaseModel):
    id: uuid.UUID
    lead_id: uuid.UUID
    lead_name: str
    lead_email: str
    lead_phone_number: str
    status: EnrollmentStatus
    attempt_count: int
    next_attempt_at: datetime | None
    last_error_code: str | None
    attempts: list[CallAttemptResponse]


class CampaignResponse(BaseModel):
    id: uuid.UUID
    name: str
    status: CampaignStatus
    source_import_id: uuid.UUID | None
    knowledge_base_version_id: uuid.UUID | None
    knowledge_base: CampaignKnowledgeBaseResponse | None
    retry_limit: int
    retry_policy_json: dict[str, Any]
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime
    readiness: CampaignReadinessResponse
    progress: CampaignProgressResponse


class CampaignDetailResponse(CampaignResponse):
    enrollments: list[CampaignEnrollmentResponse]


class CallAttemptResultRequest(BaseModel):
    status: Literal[
        "connected",
        "completed",
        "unanswered",
        "busy",
        "invalid_number",
        "failed",
    ]
    provider_call_id: str | None = Field(default=None, max_length=255)
    duration_seconds: int | None = Field(default=None, ge=0)
    failure_code: str | None = Field(default=None, max_length=100)
    failure_detail: str | None = Field(default=None, max_length=2000)
    terminal_reason: str | None = Field(default=None, max_length=100)


class TranscriptTurn(BaseModel):
    role: Literal["user", "assistant"]
    text: str = Field(min_length=1, max_length=10_000)
    interrupted: bool = False


class CallArtifactsUpdateRequest(BaseModel):
    transcript: list[TranscriptTurn] | None = Field(default=None, max_length=500)
    recording_egress_id: str | None = Field(default=None, max_length=255)
    recording_status: Literal["recording", "available", "failed"] | None = None
    recording_storage_uri: str | None = Field(default=None, max_length=2000)
    recording_url: str | None = Field(default=None, max_length=2000)


class CallActivityResponse(BaseModel):
    id: uuid.UUID
    lead_id: uuid.UUID
    lead_name: str
    lead_phone_number: str
    campaign_id: uuid.UUID
    campaign_name: str
    attempt_number: int
    status: CallAttemptStatus
    started_at: datetime | None
    answered_at: datetime | None
    ended_at: datetime | None
    duration_seconds: int | None
    transcript: list[TranscriptTurn]
    recording_status: str | None
    recording_url: str | None
    terminal_reason: str | None
    outcome: CallOutcomeResponse | None


class CampaignLeadHistoryResponse(BaseModel):
    campaign_id: uuid.UUID
    campaign_name: str
    campaign_status: CampaignStatus
    enrollment_id: uuid.UUID
    enrollment_status: EnrollmentStatus
    attempt_count: int
    attempts: list[CallAttemptResponse]
