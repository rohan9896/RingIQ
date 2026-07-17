import uuid
from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from apps.api.ringiq_api.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class TenantKnowledgeBase(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "tenant_knowledge_bases"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    active_version_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("tenant_knowledge_base_versions.id", use_alter=True),
        nullable=True,
    )

    versions: Mapped[list["TenantKnowledgeBaseVersion"]] = relationship(
        back_populates="knowledge_base",
        foreign_keys="TenantKnowledgeBaseVersion.knowledge_base_id",
        cascade="all, delete-orphan",
    )
    active_version: Mapped["TenantKnowledgeBaseVersion | None"] = relationship(
        foreign_keys=[active_version_id],
        post_update=True,
    )


class TenantKnowledgeBaseVersion(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "tenant_knowledge_base_versions"
    __table_args__ = (
        UniqueConstraint("knowledge_base_id", "version"),
        CheckConstraint(
            "status IN ('draft', 'published', 'archived')",
            name="status_valid",
        ),
        Index("ix_tenant_kb_versions_tenant_status", "tenant_id", "status"),
    )

    knowledge_base_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tenant_knowledge_bases.id", ondelete="CASCADE"),
        nullable=False,
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    category_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("categories.id", ondelete="SET NULL"),
    )
    source_template_version_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("category_template_versions.id", ondelete="SET NULL"),
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    business_profile_json: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
        server_default=text("'{}'"),
    )
    additional_notes: Mapped[str | None] = mapped_column(String(10000))
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="draft",
        server_default=text("'draft'"),
        index=True,
    )
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    published_by_user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    created_by_user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    updated_by_user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))

    knowledge_base: Mapped[TenantKnowledgeBase] = relationship(
        back_populates="versions",
        foreign_keys=[knowledge_base_id],
    )
    questions: Mapped[list["TenantKnowledgeQuestion"]] = relationship(
        back_populates="knowledge_base_version",
        cascade="all, delete-orphan",
        order_by="TenantKnowledgeQuestion.display_order",
    )


class TenantKnowledgeQuestion(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "tenant_knowledge_questions"
    __table_args__ = (
        UniqueConstraint("tenant_knowledge_base_version_id", "key"),
        UniqueConstraint("tenant_knowledge_base_version_id", "display_order"),
        CheckConstraint(
            "answer_type IN ('short_text', 'long_text', 'number', 'boolean', "
            "'single_select', 'multi_select', 'date')",
            name="answer_type_valid",
        ),
        CheckConstraint("display_order >= 0", name="display_order_non_negative"),
        Index(
            "ix_tenant_kb_questions_version_order",
            "tenant_knowledge_base_version_id",
            "display_order",
        ),
    )

    tenant_knowledge_base_version_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tenant_knowledge_base_versions.id", ondelete="CASCADE"),
        nullable=False,
    )
    key: Mapped[str] = mapped_column(String(100), nullable=False)
    label: Mapped[str] = mapped_column(String(500), nullable=False)
    help_text: Mapped[str | None] = mapped_column(String(1000))
    answer_type: Mapped[str] = mapped_column(String(30), nullable=False)
    required: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=text("1"),
    )
    display_order: Mapped[int] = mapped_column(Integer, nullable=False)
    validation_json: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
        server_default=text("'{}'"),
    )
    options_json: Mapped[list | None] = mapped_column(JSON)
    answer_value_json: Mapped[object | None] = mapped_column(JSON)

    knowledge_base_version: Mapped[TenantKnowledgeBaseVersion] = relationship(
        back_populates="questions"
    )
