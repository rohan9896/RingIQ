"""Create campaign and durable call operation tables.

Revision ID: 20260718_0007
Revises: 20260718_0006
Create Date: 2026-07-18
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "20260718_0007"
down_revision: str | None = "20260718_0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | None = None


def _timestamps() -> tuple[sa.Column, sa.Column, sa.Column]:
    return (
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
    )


def upgrade() -> None:
    op.create_table(
        "campaigns",
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=20), server_default="draft", nullable=False),
        sa.Column("source_import_id", sa.Uuid(), nullable=True),
        sa.Column("knowledge_base_version_id", sa.Uuid(), nullable=True),
        sa.Column("retry_limit", sa.Integer(), server_default="3", nullable=False),
        sa.Column("retry_policy_json", sa.JSON(), server_default=sa.text("'{}'"), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by_user_id", sa.Uuid(), nullable=True),
        sa.Column("updated_by_user_id", sa.Uuid(), nullable=True),
        *_timestamps(),
        sa.CheckConstraint(
            "status IN ('draft', 'ready', 'running', 'paused', 'completed', "
            "'cancelled', 'failed')",
            name="ck_campaigns_status_valid",
        ),
        sa.CheckConstraint("retry_limit BETWEEN 0 AND 10", name="ck_campaigns_retry_limit_valid"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], name="fk_campaigns_tenant_id", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["source_import_id"], ["lead_imports.id"], name="fk_campaigns_source_import_id", ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["knowledge_base_version_id"], ["tenant_knowledge_base_versions.id"], name="fk_campaigns_kb_version_id", ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], name="fk_campaigns_created_by_user_id"),
        sa.ForeignKeyConstraint(["updated_by_user_id"], ["users.id"], name="fk_campaigns_updated_by_user_id"),
        sa.PrimaryKeyConstraint("id", name="pk_campaigns"),
    )
    op.create_index("ix_campaigns_tenant_id", "campaigns", ["tenant_id"])
    op.create_index("ix_campaigns_tenant_status_created", "campaigns", ["tenant_id", "status", "created_at"])

    op.create_table(
        "campaign_enrollments",
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("campaign_id", sa.Uuid(), nullable=False),
        sa.Column("lead_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(length=24), server_default="pending", nullable=False),
        sa.Column("attempt_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("next_attempt_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("final_call_attempt_id", sa.Uuid(), nullable=True),
        sa.Column("last_error_code", sa.String(length=100), nullable=True),
        *_timestamps(),
        sa.CheckConstraint(
            "status IN ('pending', 'queued', 'calling', 'connected', 'retry_scheduled', "
            "'completed', 'invalid_number', 'exhausted', 'cancelled')",
            name="ck_campaign_enrollments_status_valid",
        ),
        sa.CheckConstraint("attempt_count >= 0", name="ck_campaign_enrollments_attempt_count_non_negative"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], name="fk_campaign_enrollments_tenant_id", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["campaign_id"], ["campaigns.id"], name="fk_campaign_enrollments_campaign_id", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["lead_id"], ["leads.id"], name="fk_campaign_enrollments_lead_id", ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id", name="pk_campaign_enrollments"),
        sa.UniqueConstraint("campaign_id", "lead_id", name="uq_campaign_enrollments_campaign_lead"),
    )
    op.create_index("ix_campaign_enrollments_tenant_id", "campaign_enrollments", ["tenant_id"])
    op.create_index("ix_campaign_enrollments_campaign_status", "campaign_enrollments", ["tenant_id", "campaign_id", "status"])
    op.create_index("ix_campaign_enrollments_due", "campaign_enrollments", ["tenant_id", "status", "next_attempt_at"])
    op.create_index("ix_campaign_enrollments_lead", "campaign_enrollments", ["tenant_id", "lead_id", "created_at"])

    op.create_table(
        "call_attempts",
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("campaign_enrollment_id", sa.Uuid(), nullable=False),
        sa.Column("attempt_number", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=20), server_default="queued", nullable=False),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("answered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("duration_seconds", sa.Integer(), nullable=True),
        sa.Column("provider", sa.String(length=50), nullable=True),
        sa.Column("provider_call_id", sa.String(length=255), nullable=True),
        sa.Column("livekit_room_name", sa.String(length=255), nullable=True),
        sa.Column("knowledge_base_version_id", sa.Uuid(), nullable=False),
        sa.Column("context_snapshot_json", sa.JSON(), server_default=sa.text("'{}'"), nullable=False),
        sa.Column("failure_code", sa.String(length=100), nullable=True),
        sa.Column("failure_detail", sa.String(length=2000), nullable=True),
        *_timestamps(),
        sa.CheckConstraint(
            "status IN ('queued', 'dialing', 'ringing', 'connected', 'completed', "
            "'unanswered', 'busy', 'invalid_number', 'failed', 'cancelled')",
            name="ck_call_attempts_status_valid",
        ),
        sa.CheckConstraint("attempt_number >= 1", name="ck_call_attempts_attempt_number_positive"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], name="fk_call_attempts_tenant_id", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["campaign_enrollment_id"], ["campaign_enrollments.id"], name="fk_call_attempts_enrollment_id", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["knowledge_base_version_id"], ["tenant_knowledge_base_versions.id"], name="fk_call_attempts_kb_version_id", ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id", name="pk_call_attempts"),
        sa.UniqueConstraint("campaign_enrollment_id", "attempt_number", name="uq_call_attempts_enrollment_attempt"),
    )
    op.create_index("ix_call_attempts_tenant_id", "call_attempts", ["tenant_id"])
    op.create_index("ix_call_attempts_tenant_status_scheduled", "call_attempts", ["tenant_id", "status", "scheduled_at"])
    op.create_index("ix_call_attempts_provider_call", "call_attempts", ["provider", "provider_call_id"])
    op.create_foreign_key(
        "fk_campaign_enrollments_final_attempt_id",
        "campaign_enrollments",
        "call_attempts",
        ["final_call_attempt_id"],
        ["id"],
        ondelete="SET NULL",
    )

    op.create_table(
        "jobs",
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("campaign_id", sa.Uuid(), nullable=True),
        sa.Column("campaign_enrollment_id", sa.Uuid(), nullable=True),
        sa.Column("job_type", sa.String(length=100), nullable=False),
        sa.Column("status", sa.String(length=20), server_default="pending", nullable=False),
        sa.Column("payload_json", sa.JSON(), nullable=False),
        sa.Column("idempotency_key", sa.String(length=255), nullable=False),
        sa.Column("available_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("priority", sa.Integer(), server_default="0", nullable=False),
        sa.Column("attempt_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("max_attempts", sa.Integer(), server_default="5", nullable=False),
        sa.Column("lease_owner", sa.String(length=255), nullable=True),
        sa.Column("lease_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error", sa.String(length=2000), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        *_timestamps(),
        sa.CheckConstraint(
            "status IN ('pending', 'leased', 'completed', 'cancelled', 'dead_letter')",
            name="ck_jobs_status_valid",
        ),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], name="fk_jobs_tenant_id", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["campaign_id"], ["campaigns.id"], name="fk_jobs_campaign_id", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["campaign_enrollment_id"], ["campaign_enrollments.id"], name="fk_jobs_enrollment_id", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name="pk_jobs"),
        sa.UniqueConstraint("job_type", "idempotency_key", name="uq_jobs_type_idempotency"),
    )
    op.create_index("ix_jobs_tenant_id", "jobs", ["tenant_id"])
    op.create_index("ix_jobs_campaign_id", "jobs", ["campaign_id"])
    op.create_index("ix_jobs_campaign_enrollment_id", "jobs", ["campaign_enrollment_id"])
    op.create_index("ix_jobs_claimable", "jobs", ["status", "priority", "available_at"])
    op.create_index("ix_jobs_lease_expiry", "jobs", ["status", "lease_expires_at"])

    op.create_table(
        "outbox_events",
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("event_type", sa.String(length=100), nullable=False),
        sa.Column("aggregate_type", sa.String(length=100), nullable=False),
        sa.Column("aggregate_id", sa.Uuid(), nullable=False),
        sa.Column("payload_json", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(length=20), server_default="pending", nullable=False),
        sa.Column("available_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("attempt_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error", sa.String(length=2000), nullable=True),
        *_timestamps(),
        sa.CheckConstraint("status IN ('pending', 'published', 'failed')", name="ck_outbox_events_status_valid"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], name="fk_outbox_events_tenant_id", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name="pk_outbox_events"),
    )
    op.create_index("ix_outbox_events_tenant_id", "outbox_events", ["tenant_id"])
    op.create_index("ix_outbox_pending", "outbox_events", ["status", "available_at"])


def downgrade() -> None:
    op.drop_index("ix_outbox_pending", table_name="outbox_events")
    op.drop_index("ix_outbox_events_tenant_id", table_name="outbox_events")
    op.drop_table("outbox_events")
    op.drop_index("ix_jobs_lease_expiry", table_name="jobs")
    op.drop_index("ix_jobs_claimable", table_name="jobs")
    op.drop_index("ix_jobs_campaign_enrollment_id", table_name="jobs")
    op.drop_index("ix_jobs_campaign_id", table_name="jobs")
    op.drop_index("ix_jobs_tenant_id", table_name="jobs")
    op.drop_table("jobs")
    op.drop_constraint("fk_campaign_enrollments_final_attempt_id", "campaign_enrollments", type_="foreignkey")
    op.drop_index("ix_call_attempts_provider_call", table_name="call_attempts")
    op.drop_index("ix_call_attempts_tenant_status_scheduled", table_name="call_attempts")
    op.drop_index("ix_call_attempts_tenant_id", table_name="call_attempts")
    op.drop_table("call_attempts")
    op.drop_index("ix_campaign_enrollments_lead", table_name="campaign_enrollments")
    op.drop_index("ix_campaign_enrollments_due", table_name="campaign_enrollments")
    op.drop_index("ix_campaign_enrollments_campaign_status", table_name="campaign_enrollments")
    op.drop_index("ix_campaign_enrollments_tenant_id", table_name="campaign_enrollments")
    op.drop_table("campaign_enrollments")
    op.drop_index("ix_campaigns_tenant_status_created", table_name="campaigns")
    op.drop_index("ix_campaigns_tenant_id", table_name="campaigns")
    op.drop_table("campaigns")
