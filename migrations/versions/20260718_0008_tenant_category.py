"""Assign a primary category to tenant organizations.

Revision ID: 20260718_0008
Revises: 20260718_0007
Create Date: 2026-07-18
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "20260718_0008"
down_revision: str | None = "20260718_0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.add_column("tenants", sa.Column("primary_category_id", sa.Uuid(), nullable=True))
    op.create_foreign_key(
        "fk_tenants_primary_category_id",
        "tenants",
        "categories",
        ["primary_category_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_tenants_primary_category_id", "tenants", ["primary_category_id"])


def downgrade() -> None:
    op.drop_index("ix_tenants_primary_category_id", table_name="tenants")
    op.drop_constraint("fk_tenants_primary_category_id", "tenants", type_="foreignkey")
    op.drop_column("tenants", "primary_category_id")
