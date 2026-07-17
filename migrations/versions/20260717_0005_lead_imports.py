"""Create tenant lead and import tables.

Revision ID: 20260717_0005
Revises: 20260717_0004
Create Date: 2026-07-17
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "20260717_0005"
down_revision: str | None = "20260717_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.create_table("leads", sa.Column("tenant_id", sa.Uuid(), nullable=False), sa.Column("name", sa.String(length=255), nullable=False), sa.Column("email", sa.String(length=320), nullable=False), sa.Column("phone_number", sa.String(length=32), nullable=False), sa.Column("normalized_phone_number", sa.String(length=20), nullable=False), sa.Column("attributes_json", sa.JSON(), server_default=sa.text("'{}'"), nullable=False), sa.Column("created_by_user_id", sa.Uuid(), nullable=True), sa.Column("updated_by_user_id", sa.Uuid(), nullable=True), sa.Column("id", sa.Uuid(), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False), sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], name="fk_leads_tenant_id_tenants", ondelete="CASCADE"), sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], name="fk_leads_created_by_user_id_users"), sa.ForeignKeyConstraint(["updated_by_user_id"], ["users.id"], name="fk_leads_updated_by_user_id_users"), sa.PrimaryKeyConstraint("id", name="pk_leads"), sa.UniqueConstraint("tenant_id", "normalized_phone_number", name="uq_leads_tenant_id_normalized_phone_number"))
    op.create_index("ix_leads_tenant_id", "leads", ["tenant_id"])
    op.create_index("ix_leads_tenant_created_at", "leads", ["tenant_id", "created_at"])
    op.create_table("lead_imports", sa.Column("tenant_id", sa.Uuid(), nullable=False), sa.Column("filename", sa.String(length=255), nullable=False), sa.Column("status", sa.String(length=20), server_default="completed", nullable=False), sa.Column("total_rows", sa.Integer(), server_default="0", nullable=False), sa.Column("imported_rows", sa.Integer(), server_default="0", nullable=False), sa.Column("invalid_rows", sa.Integer(), server_default="0", nullable=False), sa.Column("duplicate_rows", sa.Integer(), server_default="0", nullable=False), sa.Column("column_mapping_json", sa.JSON(), server_default=sa.text("'{}'"), nullable=False), sa.Column("created_by_user_id", sa.Uuid(), nullable=True), sa.Column("id", sa.Uuid(), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False), sa.CheckConstraint("status IN ('completed')", name="ck_lead_imports_status_valid"), sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], name="fk_lead_imports_tenant_id_tenants", ondelete="CASCADE"), sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], name="fk_lead_imports_created_by_user_id_users"), sa.PrimaryKeyConstraint("id", name="pk_lead_imports"))
    op.create_index("ix_lead_imports_tenant_id", "lead_imports", ["tenant_id"])
    op.create_index("ix_lead_imports_tenant_created_at", "lead_imports", ["tenant_id", "created_at"])
    op.create_table("lead_import_rows", sa.Column("tenant_id", sa.Uuid(), nullable=False), sa.Column("lead_import_id", sa.Uuid(), nullable=False), sa.Column("lead_id", sa.Uuid(), nullable=True), sa.Column("row_number", sa.Integer(), nullable=False), sa.Column("status", sa.String(length=20), nullable=False), sa.Column("error_code", sa.String(length=100), nullable=True), sa.Column("error_message", sa.String(length=1000), nullable=True), sa.Column("raw_data_json", sa.JSON(), nullable=False), sa.Column("id", sa.Uuid(), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False), sa.CheckConstraint("status IN ('imported', 'invalid', 'duplicate')", name="ck_lead_import_rows_status_valid"), sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], name="fk_lead_import_rows_tenant_id_tenants", ondelete="CASCADE"), sa.ForeignKeyConstraint(["lead_import_id"], ["lead_imports.id"], name="fk_lead_import_rows_lead_import_id_lead_imports", ondelete="CASCADE"), sa.ForeignKeyConstraint(["lead_id"], ["leads.id"], name="fk_lead_import_rows_lead_id_leads", ondelete="SET NULL"), sa.PrimaryKeyConstraint("id", name="pk_lead_import_rows"), sa.UniqueConstraint("lead_import_id", "row_number", name="uq_lead_import_rows_lead_import_id_row_number"))
    op.create_index("ix_lead_import_rows_tenant_id", "lead_import_rows", ["tenant_id"])
    op.create_index("ix_lead_import_rows_import_status", "lead_import_rows", ["lead_import_id", "status"])


def downgrade() -> None:
    op.drop_index("ix_lead_import_rows_import_status", table_name="lead_import_rows")
    op.drop_index("ix_lead_import_rows_tenant_id", table_name="lead_import_rows")
    op.drop_table("lead_import_rows")
    op.drop_index("ix_lead_imports_tenant_created_at", table_name="lead_imports")
    op.drop_index("ix_lead_imports_tenant_id", table_name="lead_imports")
    op.drop_table("lead_imports")
    op.drop_index("ix_leads_tenant_created_at", table_name="leads")
    op.drop_index("ix_leads_tenant_id", table_name="leads")
    op.drop_table("leads")
