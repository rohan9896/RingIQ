"""Create tenant-owned knowledge base versions.

Revision ID: 20260717_0004
Revises: 20260717_0003
Create Date: 2026-07-17
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "20260717_0004"
down_revision: str | None = "20260717_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.create_table(
        "tenant_knowledge_bases",
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("active_version_id", sa.Uuid(), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], name="fk_tenant_knowledge_bases_tenant_id_tenants", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name="pk_tenant_knowledge_bases"),
        sa.UniqueConstraint("tenant_id", name="uq_tenant_knowledge_bases_tenant_id"),
    )
    op.create_table(
        "tenant_knowledge_base_versions",
        sa.Column("knowledge_base_id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("category_id", sa.Uuid(), nullable=True),
        sa.Column("source_template_version_id", sa.Uuid(), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("business_profile_json", sa.JSON(), server_default=sa.text("'{}'"), nullable=False),
        sa.Column("additional_notes", sa.String(length=10000), nullable=True),
        sa.Column("status", sa.String(length=20), server_default="draft", nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("published_by_user_id", sa.Uuid(), nullable=True),
        sa.Column("created_by_user_id", sa.Uuid(), nullable=True),
        sa.Column("updated_by_user_id", sa.Uuid(), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.CheckConstraint("status IN ('draft', 'published', 'archived')", name="ck_tenant_kb_versions_status_valid"),
        sa.ForeignKeyConstraint(["knowledge_base_id"], ["tenant_knowledge_bases.id"], name="fk_tenant_kb_versions_knowledge_base_id_tenant_knowledge_bases", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], name="fk_tenant_kb_versions_tenant_id_tenants", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["category_id"], ["categories.id"], name="fk_tenant_kb_versions_category_id_categories", ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["source_template_version_id"], ["category_template_versions.id"], name="fk_tenant_kb_versions_source_template_id", ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["published_by_user_id"], ["users.id"], name="fk_tenant_kb_versions_published_by_user_id_users"),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], name="fk_tenant_kb_versions_created_by_user_id_users"),
        sa.ForeignKeyConstraint(["updated_by_user_id"], ["users.id"], name="fk_tenant_kb_versions_updated_by_user_id_users"),
        sa.PrimaryKeyConstraint("id", name="pk_tenant_knowledge_base_versions"),
        sa.UniqueConstraint("knowledge_base_id", "version", name="uq_tenant_kb_versions_knowledge_base_id_version"),
    )
    op.create_index("ix_tenant_knowledge_base_versions_tenant_id", "tenant_knowledge_base_versions", ["tenant_id"])
    op.create_index("ix_tenant_knowledge_base_versions_status", "tenant_knowledge_base_versions", ["status"])
    op.create_index("ix_tenant_kb_versions_tenant_status", "tenant_knowledge_base_versions", ["tenant_id", "status"])
    op.create_foreign_key(
        "fk_tenant_kb_active_version_id",
        "tenant_knowledge_bases",
        "tenant_knowledge_base_versions",
        ["active_version_id"],
        ["id"],
    )
    op.create_table(
        "tenant_knowledge_questions",
        sa.Column("tenant_knowledge_base_version_id", sa.Uuid(), nullable=False),
        sa.Column("key", sa.String(length=100), nullable=False),
        sa.Column("label", sa.String(length=500), nullable=False),
        sa.Column("help_text", sa.String(length=1000), nullable=True),
        sa.Column("answer_type", sa.String(length=30), nullable=False),
        sa.Column("required", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("display_order", sa.Integer(), nullable=False),
        sa.Column("validation_json", sa.JSON(), server_default=sa.text("'{}'"), nullable=False),
        sa.Column("options_json", sa.JSON(), nullable=True),
        sa.Column("answer_value_json", sa.JSON(), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.CheckConstraint("answer_type IN ('short_text', 'long_text', 'number', 'boolean', 'single_select', 'multi_select', 'date')", name="ck_tenant_kb_questions_answer_type_valid"),
        sa.CheckConstraint("display_order >= 0", name="ck_tenant_kb_questions_display_order_non_negative"),
        sa.ForeignKeyConstraint(["tenant_knowledge_base_version_id"], ["tenant_knowledge_base_versions.id"], name="fk_tenant_kb_questions_version_id", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name="pk_tenant_knowledge_questions"),
        sa.UniqueConstraint("tenant_knowledge_base_version_id", "key", name="uq_tenant_kb_questions_version_key"),
        sa.UniqueConstraint("tenant_knowledge_base_version_id", "display_order", name="uq_tenant_kb_questions_version_display_order"),
    )
    op.create_index("ix_tenant_kb_questions_version_order", "tenant_knowledge_questions", ["tenant_knowledge_base_version_id", "display_order"])


def downgrade() -> None:
    op.drop_index("ix_tenant_kb_questions_version_order", table_name="tenant_knowledge_questions")
    op.drop_table("tenant_knowledge_questions")
    op.drop_constraint(
        "fk_tenant_kb_active_version_id",
        "tenant_knowledge_bases",
        type_="foreignkey",
    )
    op.drop_index("ix_tenant_kb_versions_tenant_status", table_name="tenant_knowledge_base_versions")
    op.drop_index("ix_tenant_knowledge_base_versions_status", table_name="tenant_knowledge_base_versions")
    op.drop_index("ix_tenant_knowledge_base_versions_tenant_id", table_name="tenant_knowledge_base_versions")
    op.drop_table("tenant_knowledge_base_versions")
    op.drop_table("tenant_knowledge_bases")
