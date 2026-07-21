"""Add platform user invitations and webhook receipts.

Revision ID: 20260721_0011
Revises: 20260720_0010
Create Date: 2026-07-21
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "20260721_0011"
down_revision: str | None = "20260720_0010"
branch_labels: str | Sequence[str] | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.create_table(
        "platform_user_invitations",
        sa.Column("email", sa.String(320), nullable=False),
        sa.Column("display_name", sa.String(255)),
        sa.Column("platform_role", sa.String(40), nullable=False),
        sa.Column("clerk_invitation_id", sa.String(64)),
        sa.Column("invited_by_user_id", sa.Uuid()),
        sa.Column("accepted_user_id", sa.Uuid()),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(20), server_default="creating", nullable=False),
        sa.Column("failure_reason", sa.String(500)),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint(
            "email = lower(btrim(email))",
            name="ck_platform_user_invitations_email_normalized",
        ),
        sa.CheckConstraint(
            "platform_role IN ('platform_super_admin', 'platform_operations', 'template_manager')",
            name="ck_platform_user_invitations_platform_role_valid",
        ),
        sa.CheckConstraint(
            "status IN ('creating', 'pending', 'accepted', 'revoked', 'expired', 'failed')",
            name="ck_platform_user_invitations_status_valid",
        ),
        sa.ForeignKeyConstraint(["invited_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["accepted_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("accepted_user_id"),
        sa.UniqueConstraint("clerk_invitation_id"),
    )
    op.create_index("ix_platform_user_invitations_email", "platform_user_invitations", ["email"])
    op.create_index("ix_platform_user_invitations_platform_role", "platform_user_invitations", ["platform_role"])
    op.create_index("ix_platform_user_invitations_status", "platform_user_invitations", ["status"])
    op.create_index("ix_platform_user_invitations_clerk_invitation_id", "platform_user_invitations", ["clerk_invitation_id"])
    op.create_index("ix_platform_user_invitations_invited_by_user_id", "platform_user_invitations", ["invited_by_user_id"])
    op.create_index("ix_platform_user_invitations_accepted_user_id", "platform_user_invitations", ["accepted_user_id"])
    op.create_index(
        "uq_platform_user_invitations_open_email",
        "platform_user_invitations",
        ["email"],
        unique=True,
        postgresql_where=sa.text("status IN ('creating', 'pending')"),
    )

    op.create_table(
        "webhook_receipts",
        sa.Column("provider", sa.String(50), nullable=False),
        sa.Column("delivery_id", sa.String(255), nullable=False),
        sa.Column("event_type", sa.String(100), nullable=False),
        sa.Column("received_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("processed_at", sa.DateTime(timezone=True)),
        sa.Column("status", sa.String(20), server_default="processing", nullable=False),
        sa.Column("payload_hash", sa.String(64), nullable=False),
        sa.Column("error", sa.String(1000)),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint(
            "status IN ('processing', 'processed', 'failed')",
            name="ck_webhook_receipts_status_valid",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("provider", "delivery_id"),
    )
    op.create_index("ix_webhook_receipts_event_type", "webhook_receipts", ["event_type"])
    op.create_index("ix_webhook_receipts_status", "webhook_receipts", ["status"])


def downgrade() -> None:
    op.drop_index("ix_webhook_receipts_status", table_name="webhook_receipts")
    op.drop_index("ix_webhook_receipts_event_type", table_name="webhook_receipts")
    op.drop_table("webhook_receipts")
    op.drop_index("uq_platform_user_invitations_open_email", table_name="platform_user_invitations")
    op.drop_index("ix_platform_user_invitations_accepted_user_id", table_name="platform_user_invitations")
    op.drop_index("ix_platform_user_invitations_invited_by_user_id", table_name="platform_user_invitations")
    op.drop_index("ix_platform_user_invitations_clerk_invitation_id", table_name="platform_user_invitations")
    op.drop_index("ix_platform_user_invitations_status", table_name="platform_user_invitations")
    op.drop_index("ix_platform_user_invitations_platform_role", table_name="platform_user_invitations")
    op.drop_index("ix_platform_user_invitations_email", table_name="platform_user_invitations")
    op.drop_table("platform_user_invitations")
