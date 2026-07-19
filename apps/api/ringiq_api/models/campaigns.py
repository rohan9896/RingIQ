import uuid
from datetime import datetime
from enum import StrEnum

from sqlalchemy import (
    JSON,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from apps.api.ringiq_api.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class CampaignStatus(StrEnum):
    DRAFT = "draft"
    READY = "ready"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"


class EnrollmentStatus(StrEnum):
    PENDING = "pending"
    QUEUED = "queued"
    CALLING = "calling"
    CONNECTED = "connected"
    RETRY_SCHEDULED = "retry_scheduled"
    COMPLETED = "completed"
    INVALID_NUMBER = "invalid_number"
    EXHAUSTED = "exhausted"
    CANCELLED = "cancelled"


class CallAttemptStatus(StrEnum):
    QUEUED = "queued"
    DIALING = "dialing"
    RINGING = "ringing"
    CONNECTED = "connected"
    COMPLETED = "completed"
    UNANSWERED = "unanswered"
    BUSY = "busy"
    INVALID_NUMBER = "invalid_number"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobStatus(StrEnum):
    PENDING = "pending"
    LEASED = "leased"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    DEAD_LETTER = "dead_letter"


class OutboxStatus(StrEnum):
    PENDING = "pending"
    PUBLISHED = "published"
    FAILED = "failed"


class Campaign(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "campaigns"
    __table_args__ = (
        CheckConstraint(
            "status IN ('draft', 'ready', 'running', 'paused', 'completed', "
            "'cancelled', 'failed')",
            name="status_valid",
        ),
        CheckConstraint("retry_limit BETWEEN 0 AND 10", name="retry_limit_valid"),
        Index("ix_campaigns_tenant_status_created", "tenant_id", "status", "created_at"),
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=CampaignStatus.DRAFT.value, server_default="draft"
    )
    source_import_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("lead_imports.id", ondelete="SET NULL")
    )
    knowledge_base_version_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("tenant_knowledge_base_versions.id", ondelete="SET NULL")
    )
    retry_limit: Mapped[int] = mapped_column(Integer, nullable=False, default=3, server_default="3")
    retry_policy_json: Mapped[dict] = mapped_column(
        JSON, nullable=False, default=dict, server_default=text("'{}'")
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_by_user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    updated_by_user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))

    enrollments: Mapped[list["CampaignEnrollment"]] = relationship(
        back_populates="campaign", cascade="all, delete-orphan"
    )


class CampaignEnrollment(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "campaign_enrollments"
    __table_args__ = (
        UniqueConstraint("campaign_id", "lead_id"),
        CheckConstraint(
            "status IN ('pending', 'queued', 'calling', 'connected', 'retry_scheduled', "
            "'completed', 'invalid_number', 'exhausted', 'cancelled')",
            name="status_valid",
        ),
        CheckConstraint("attempt_count >= 0", name="attempt_count_non_negative"),
        Index("ix_campaign_enrollments_campaign_status", "tenant_id", "campaign_id", "status"),
        Index("ix_campaign_enrollments_due", "tenant_id", "status", "next_attempt_at"),
        Index("ix_campaign_enrollments_lead", "tenant_id", "lead_id", "created_at"),
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    campaign_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False
    )
    lead_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("leads.id", ondelete="RESTRICT"), nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(24), nullable=False, default=EnrollmentStatus.PENDING.value, server_default="pending"
    )
    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    next_attempt_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    final_call_attempt_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("call_attempts.id", use_alter=True, ondelete="SET NULL")
    )
    last_error_code: Mapped[str | None] = mapped_column(String(100))

    campaign: Mapped[Campaign] = relationship(back_populates="enrollments")
    attempts: Mapped[list["CallAttempt"]] = relationship(
        back_populates="enrollment",
        foreign_keys="CallAttempt.campaign_enrollment_id",
        order_by="CallAttempt.attempt_number",
    )


class CallAttempt(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "call_attempts"
    __table_args__ = (
        UniqueConstraint("campaign_enrollment_id", "attempt_number"),
        CheckConstraint(
            "status IN ('queued', 'dialing', 'ringing', 'connected', 'completed', "
            "'unanswered', 'busy', 'invalid_number', 'failed', 'cancelled')",
            name="status_valid",
        ),
        CheckConstraint("attempt_number >= 1", name="attempt_number_positive"),
        Index("ix_call_attempts_tenant_status_scheduled", "tenant_id", "status", "scheduled_at"),
        Index("ix_call_attempts_provider_call", "provider", "provider_call_id"),
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    campaign_enrollment_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("campaign_enrollments.id", ondelete="CASCADE"), nullable=False
    )
    attempt_number: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=CallAttemptStatus.QUEUED.value, server_default="queued"
    )
    scheduled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    answered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    duration_seconds: Mapped[int | None] = mapped_column(Integer)
    provider: Mapped[str | None] = mapped_column(String(50))
    provider_call_id: Mapped[str | None] = mapped_column(String(255))
    livekit_room_name: Mapped[str | None] = mapped_column(String(255))
    knowledge_base_version_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tenant_knowledge_base_versions.id", ondelete="RESTRICT"), nullable=False
    )
    context_snapshot_json: Mapped[dict] = mapped_column(
        JSON, nullable=False, default=dict, server_default=text("'{}'")
    )
    transcript_json: Mapped[list] = mapped_column(
        JSON, nullable=False, default=list, server_default=text("'[]'")
    )
    recording_egress_id: Mapped[str | None] = mapped_column(String(255))
    recording_status: Mapped[str | None] = mapped_column(String(32))
    recording_storage_uri: Mapped[str | None] = mapped_column(String(2000))
    recording_url: Mapped[str | None] = mapped_column(String(2000))
    failure_code: Mapped[str | None] = mapped_column(String(100))
    failure_detail: Mapped[str | None] = mapped_column(String(2000))

    enrollment: Mapped[CampaignEnrollment] = relationship(
        back_populates="attempts", foreign_keys=[campaign_enrollment_id]
    )


class Job(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "jobs"
    __table_args__ = (
        UniqueConstraint("job_type", "idempotency_key"),
        CheckConstraint(
            "status IN ('pending', 'leased', 'completed', 'cancelled', 'dead_letter')",
            name="status_valid",
        ),
        Index("ix_jobs_claimable", "status", "priority", "available_at"),
        Index("ix_jobs_lease_expiry", "status", "lease_expires_at"),
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    campaign_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("campaigns.id", ondelete="CASCADE"), index=True
    )
    campaign_enrollment_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("campaign_enrollments.id", ondelete="CASCADE"), index=True
    )
    job_type: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=JobStatus.PENDING.value, server_default="pending"
    )
    payload_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(255), nullable=False)
    available_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    max_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=5, server_default="5")
    lease_owner: Mapped[str | None] = mapped_column(String(255))
    lease_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_error: Mapped[str | None] = mapped_column(String(2000))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class OutboxEvent(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "outbox_events"
    __table_args__ = (
        CheckConstraint("status IN ('pending', 'published', 'failed')", name="status_valid"),
        Index("ix_outbox_pending", "status", "available_at"),
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    aggregate_type: Mapped[str] = mapped_column(String(100), nullable=False)
    aggregate_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    payload_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=OutboxStatus.PENDING.value, server_default="pending"
    )
    available_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_error: Mapped[str | None] = mapped_column(String(2000))
