import uuid
from enum import StrEnum

from sqlalchemy import (
    JSON,
    CheckConstraint,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from apps.api.ringiq_api.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class LeadImportStatus(StrEnum):
    COMPLETED = "completed"


class LeadImportRowStatus(StrEnum):
    IMPORTED = "imported"
    INVALID = "invalid"
    DUPLICATE = "duplicate"


class Lead(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "leads"
    __table_args__ = (
        UniqueConstraint("tenant_id", "normalized_phone_number"),
        Index("ix_leads_tenant_created_at", "tenant_id", "created_at"),
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(320), nullable=False)
    phone_number: Mapped[str] = mapped_column(String(32), nullable=False)
    normalized_phone_number: Mapped[str] = mapped_column(String(20), nullable=False)
    attributes_json: Mapped[dict] = mapped_column(
        JSON, nullable=False, default=dict, server_default=text("'{}'")
    )
    created_by_user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    updated_by_user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))


class LeadImport(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "lead_imports"
    __table_args__ = (
        CheckConstraint("status IN ('completed')", name="status_valid"),
        Index("ix_lead_imports_tenant_created_at", "tenant_id", "created_at"),
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=LeadImportStatus.COMPLETED.value,
        server_default=text("'completed'"),
    )
    total_rows: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    imported_rows: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    invalid_rows: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    duplicate_rows: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    column_mapping_json: Mapped[dict] = mapped_column(
        JSON, nullable=False, default=dict, server_default=text("'{}'")
    )
    created_by_user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))


class LeadImportRow(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "lead_import_rows"
    __table_args__ = (
        UniqueConstraint("lead_import_id", "row_number"),
        CheckConstraint(
            "status IN ('imported', 'invalid', 'duplicate')", name="status_valid"
        ),
        Index("ix_lead_import_rows_import_status", "lead_import_id", "status"),
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    lead_import_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("lead_imports.id", ondelete="CASCADE"), nullable=False
    )
    lead_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("leads.id", ondelete="SET NULL")
    )
    row_number: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    error_code: Mapped[str | None] = mapped_column(String(100))
    error_message: Mapped[str | None] = mapped_column(String(1000))
    raw_data_json: Mapped[dict] = mapped_column(JSON, nullable=False)
