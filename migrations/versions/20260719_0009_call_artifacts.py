"""Add transcripts and recording metadata to call attempts.

Revision ID: 20260719_0009
Revises: 20260718_0008
Create Date: 2026-07-19
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "20260719_0009"
down_revision: str | None = "20260718_0008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.add_column(
        "call_attempts",
        sa.Column("transcript_json", sa.JSON(), server_default=sa.text("'[]'"), nullable=False),
    )
    op.add_column("call_attempts", sa.Column("recording_egress_id", sa.String(255)))
    op.add_column("call_attempts", sa.Column("recording_status", sa.String(32)))
    op.add_column("call_attempts", sa.Column("recording_storage_uri", sa.String(2000)))
    op.add_column("call_attempts", sa.Column("recording_url", sa.String(2000)))


def downgrade() -> None:
    op.drop_column("call_attempts", "recording_url")
    op.drop_column("call_attempts", "recording_storage_uri")
    op.drop_column("call_attempts", "recording_status")
    op.drop_column("call_attempts", "recording_egress_id")
    op.drop_column("call_attempts", "transcript_json")
