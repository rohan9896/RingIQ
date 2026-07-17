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
    with op.batch_alter_table("users") as batch_op:
        batch_op.add_column(
            sa.Column("realm", sa.String(length=20), server_default="tenant", nullable=False)
        )
        batch_op.add_column(
            sa.Column("platform_role", sa.String(length=40), nullable=True)
        )
        batch_op.create_check_constraint(
            "ck_users_realm_valid",
            "realm IN ('tenant', 'platform')",
        )
        batch_op.create_check_constraint(
            "ck_users_realm_role_valid",
            "(realm = 'tenant' AND platform_role IS NULL) OR "
            "(realm = 'platform' AND platform_role IS NOT NULL AND platform_role IN "
            "('platform_super_admin', 'platform_operations', 'template_manager'))",
        )
        batch_op.create_index("ix_users_realm", ["realm"])
        batch_op.create_index("ix_users_platform_role", ["platform_role"])


def downgrade() -> None:
    with op.batch_alter_table("users") as batch_op:
        batch_op.drop_index("ix_users_platform_role")
        batch_op.drop_index("ix_users_realm")
        batch_op.drop_constraint("ck_users_realm_role_valid", type_="check")
        batch_op.drop_constraint("ck_users_realm_valid", type_="check")
        batch_op.drop_column("platform_role")
        batch_op.drop_column("realm")
