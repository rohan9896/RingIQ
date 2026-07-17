"""Add platform user realm and roles.

Revision ID: 20260717_0002
Revises: 20260717_0001
Create Date: 2026-07-17
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "20260717_0002"
down_revision: str | None = "20260717_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("realm", sa.String(length=20), server_default="tenant", nullable=False),
    )
    op.add_column("users", sa.Column("platform_role", sa.String(length=40), nullable=True))
    op.create_check_constraint("ck_users_realm_valid", "users", "realm IN ('tenant', 'platform')")
    op.create_check_constraint(
        "ck_users_realm_role_valid",
        "users",
        "(realm = 'tenant' AND platform_role IS NULL) OR "
        "(realm = 'platform' AND platform_role IS NOT NULL AND platform_role IN "
        "('platform_super_admin', 'platform_operations', 'template_manager'))",
    )
    op.create_index("ix_users_realm", "users", ["realm"])
    op.create_index("ix_users_platform_role", "users", ["platform_role"])


def downgrade() -> None:
    op.drop_index("ix_users_platform_role", table_name="users")
    op.drop_index("ix_users_realm", table_name="users")
    op.drop_constraint("ck_users_realm_role_valid", "users", type_="check")
    op.drop_constraint("ck_users_realm_valid", "users", type_="check")
    op.drop_column("users", "platform_role")
    op.drop_column("users", "realm")
