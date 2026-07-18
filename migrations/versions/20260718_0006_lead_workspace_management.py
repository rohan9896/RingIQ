"""Add lead workspace management fields.

Revision ID: 20260718_0006
Revises: 20260717_0005
Create Date: 2026-07-18
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "20260718_0006"
down_revision: str | None = "20260717_0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.add_column(
        "leads",
        sa.Column("status", sa.String(length=20), server_default="active", nullable=False),
    )
    op.add_column(
        "leads",
        sa.Column("manual_status", sa.String(length=20), server_default="new", nullable=False),
    )
    op.add_column("leads", sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True))
    op.create_check_constraint(
        "ck_leads_status_valid", "leads", "status IN ('active', 'archived')"
    )
    op.create_check_constraint(
        "ck_leads_manual_status_valid",
        "leads",
        "manual_status IN ('new', 'in_progress', 'follow_up', 'closed')",
    )
    op.create_index("ix_leads_tenant_status", "leads", ["tenant_id", "status"])


def downgrade() -> None:
    op.drop_index("ix_leads_tenant_status", table_name="leads")
    op.drop_constraint("ck_leads_manual_status_valid", "leads", type_="check")
    op.drop_constraint("ck_leads_status_valid", "leads", type_="check")
    op.drop_column("leads", "archived_at")
    op.drop_column("leads", "manual_status")
    op.drop_column("leads", "status")
