"""Create category starter template tables.

Revision ID: 20260717_0003
Revises: 20260717_0002
Create Date: 2026-07-17
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "20260717_0003"
down_revision: str | None = "20260717_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "categories",
        sa.Column("key", sa.String(length=100), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.String(length=1000), nullable=True),
        sa.Column("status", sa.String(length=20), server_default="active", nullable=False),
        sa.Column("created_by_user_id", sa.Uuid(), nullable=True),
        sa.Column("updated_by_user_id", sa.Uuid(), nullable=True),
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
        sa.CheckConstraint(
            "status IN ('active', 'inactive')",
            name="ck_categories_status_valid",
        ),
        sa.ForeignKeyConstraint(
            ["created_by_user_id"],
            ["users.id"],
            name="fk_categories_created_by_user_id_users",
        ),
        sa.ForeignKeyConstraint(
            ["updated_by_user_id"],
            ["users.id"],
            name="fk_categories_updated_by_user_id_users",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_categories"),
        sa.UniqueConstraint("key", name="uq_categories_key"),
    )
    op.create_index("ix_categories_status", "categories", ["status"])

    op.create_table(
        "category_template_versions",
        sa.Column("category_id", sa.Uuid(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.String(length=1000), nullable=True),
        sa.Column("status", sa.String(length=20), server_default="draft", nullable=False),
        sa.Column("lead_schema_json", sa.JSON(), server_default=sa.text("'{}'"), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("published_by_user_id", sa.Uuid(), nullable=True),
        sa.Column("created_by_user_id", sa.Uuid(), nullable=True),
        sa.Column("updated_by_user_id", sa.Uuid(), nullable=True),
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
        sa.CheckConstraint(
            "status IN ('draft', 'published', 'archived')",
            name="ck_category_template_versions_status_valid",
        ),
        sa.ForeignKeyConstraint(
            ["category_id"],
            ["categories.id"],
            name="fk_category_template_versions_category_id_categories",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["created_by_user_id"],
            ["users.id"],
            name="fk_category_template_versions_created_by_user_id_users",
        ),
        sa.ForeignKeyConstraint(
            ["published_by_user_id"],
            ["users.id"],
            name="fk_category_template_versions_published_by_user_id_users",
        ),
        sa.ForeignKeyConstraint(
            ["updated_by_user_id"],
            ["users.id"],
            name="fk_category_template_versions_updated_by_user_id_users",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_category_template_versions"),
        sa.UniqueConstraint(
            "category_id",
            "version",
            name="uq_category_template_versions_category_id_version",
        ),
    )
    op.create_index(
        "ix_category_template_versions_category_id_status",
        "category_template_versions",
        ["category_id", "status"],
    )
    op.create_index(
        "ix_category_template_versions_status",
        "category_template_versions",
        ["status"],
    )

    op.create_table(
        "qna_questions",
        sa.Column("category_template_version_id", sa.Uuid(), nullable=False),
        sa.Column("key", sa.String(length=100), nullable=False),
        sa.Column("label", sa.String(length=500), nullable=False),
        sa.Column("help_text", sa.String(length=1000), nullable=True),
        sa.Column("answer_type", sa.String(length=30), nullable=False),
        sa.Column("required", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("display_order", sa.Integer(), nullable=False),
        sa.Column("validation_json", sa.JSON(), server_default=sa.text("'{}'"), nullable=False),
        sa.Column("options_json", sa.JSON(), nullable=True),
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
        sa.CheckConstraint(
            "answer_type IN ('short_text', 'long_text', 'number', 'boolean', "
            "'single_select', 'multi_select', 'date')",
            name="ck_qna_questions_answer_type_valid",
        ),
        sa.CheckConstraint(
            "display_order >= 0",
            name="ck_qna_questions_display_order_non_negative",
        ),
        sa.ForeignKeyConstraint(
            ["category_template_version_id"],
            ["category_template_versions.id"],
            name="fk_qna_questions_template_version_id",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_qna_questions"),
        sa.UniqueConstraint(
            "category_template_version_id",
            "display_order",
            name="uq_qna_questions_category_template_version_id_display_order",
        ),
        sa.UniqueConstraint(
            "category_template_version_id",
            "key",
            name="uq_qna_questions_category_template_version_id_key",
        ),
    )
    op.create_index(
        "ix_qna_questions_template_order",
        "qna_questions",
        ["category_template_version_id", "display_order"],
    )


def downgrade() -> None:
    op.drop_index("ix_qna_questions_template_order", table_name="qna_questions")
    op.drop_table("qna_questions")
    op.drop_index(
        "ix_category_template_versions_status",
        table_name="category_template_versions",
    )
    op.drop_index(
        "ix_category_template_versions_category_id_status",
        table_name="category_template_versions",
    )
    op.drop_table("category_template_versions")
    op.drop_index("ix_categories_status", table_name="categories")
    op.drop_table("categories")
