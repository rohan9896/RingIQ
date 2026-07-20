"""Add persisted post-call qualification outcomes.

Revision ID: 20260720_0010
Revises: 20260719_0009
Create Date: 2026-07-20
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "20260720_0010"
down_revision: str | None = "20260719_0009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.add_column("call_attempts", sa.Column("terminal_reason", sa.String(100)))
    op.add_column(
        "call_attempts", sa.Column("artifacts_finalized_at", sa.DateTime(timezone=True))
    )
    op.create_unique_constraint(
        "uq_call_attempts_tenant_id",
        "call_attempts",
        ["tenant_id", "id"],
    )
    op.create_table(
        "call_outcomes",
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("call_attempt_id", sa.Uuid(), nullable=False),
        sa.Column("processing_status", sa.String(20), server_default="pending", nullable=False),
        sa.Column("processing_attempts", sa.Integer(), server_default="0", nullable=False),
        sa.Column("processing_error", sa.String(500)),
        sa.Column("processed_at", sa.DateTime(timezone=True)),
        sa.Column("label", sa.String(32)),
        sa.Column("confidence", sa.Float()),
        sa.Column("rationale", sa.String(2000)),
        sa.Column("summary", sa.String(4000)),
        sa.Column("qualification_facts_json", sa.JSON(), server_default=sa.text("'{}'"), nullable=False),
        sa.Column("evidence_json", sa.JSON(), server_default=sa.text("'[]'"), nullable=False),
        sa.Column("callback_original_phrase", sa.String(1000)),
        sa.Column("callback_timezone", sa.String(100)),
        sa.Column("callback_at", sa.DateTime(timezone=True)),
        sa.Column("terminal_reason", sa.String(100)),
        sa.Column("extractor_provider", sa.String(50)),
        sa.Column("extractor_model", sa.String(255)),
        sa.Column("extractor_version", sa.String(50)),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.CheckConstraint(
            "processing_status IN ('pending', 'processing', 'completed', 'failed')",
            name="ck_call_outcomes_processing_status_valid",
        ),
        sa.CheckConstraint(
            "label IS NULL OR label IN ('hot', 'warm', 'cold', 'callback_requested', "
            "'not_interested', 'unanswered', 'invalid_number', 'needs_review')",
            name="ck_call_outcomes_label_valid",
        ),
        sa.CheckConstraint(
            "confidence IS NULL OR (confidence >= 0 AND confidence <= 1)",
            name="ck_call_outcomes_confidence_valid",
        ),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "call_attempt_id"],
            ["call_attempts.tenant_id", "call_attempts.id"],
            ondelete="CASCADE",
            name="fk_call_outcomes_tenant_attempt",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("call_attempt_id"),
    )
    op.create_index("ix_call_outcomes_tenant_id", "call_outcomes", ["tenant_id"])
    op.create_index(
        "ix_call_outcomes_tenant_label_created",
        "call_outcomes",
        ["tenant_id", "label", "created_at"],
    )
    op.create_index(
        "ix_call_outcomes_tenant_processing",
        "call_outcomes",
        ["tenant_id", "processing_status", "updated_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_call_outcomes_tenant_processing", table_name="call_outcomes")
    op.drop_index("ix_call_outcomes_tenant_label_created", table_name="call_outcomes")
    op.drop_index("ix_call_outcomes_tenant_id", table_name="call_outcomes")
    op.drop_table("call_outcomes")
    op.drop_constraint("uq_call_attempts_tenant_id", "call_attempts", type_="unique")
    op.drop_column("call_attempts", "artifacts_finalized_at")
    op.drop_column("call_attempts", "terminal_reason")
