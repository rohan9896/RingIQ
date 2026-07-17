import uuid
from datetime import datetime
from enum import StrEnum

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


class CategoryStatus(StrEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class TemplateStatus(StrEnum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class QuestionAnswerType(StrEnum):
    SHORT_TEXT = "short_text"
    LONG_TEXT = "long_text"
    NUMBER = "number"
    BOOLEAN = "boolean"
    SINGLE_SELECT = "single_select"
    MULTI_SELECT = "multi_select"
    DATE = "date"


class Category(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "categories"
    __table_args__ = (
        CheckConstraint(
            "status IN ('active', 'inactive')",
            name="status_valid",
        ),
    )

    key: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(String(1000))
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=CategoryStatus.ACTIVE.value,
        server_default=text("'active'"),
        index=True,
    )
    created_by_user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    updated_by_user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))

    template_versions: Mapped[list["CategoryTemplateVersion"]] = relationship(
        back_populates="category",
        cascade="all, delete-orphan",
    )


class CategoryTemplateVersion(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "category_template_versions"
    __table_args__ = (
        UniqueConstraint("category_id", "version"),
        CheckConstraint(
            "status IN ('draft', 'published', 'archived')",
            name="status_valid",
        ),
        Index("ix_category_template_versions_category_id_status", "category_id", "status"),
    )

    category_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("categories.id", ondelete="CASCADE"),
        nullable=False,
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(String(1000))
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=TemplateStatus.DRAFT.value,
        server_default=text("'draft'"),
        index=True,
    )
    lead_schema_json: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
        server_default=text("'{}'"),
    )
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    published_by_user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    created_by_user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    updated_by_user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))

    category: Mapped[Category] = relationship(back_populates="template_versions")
    qna_questions: Mapped[list["QnaQuestion"]] = relationship(
        back_populates="template_version",
        cascade="all, delete-orphan",
        order_by="QnaQuestion.display_order",
    )


class QnaQuestion(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "qna_questions"
    __table_args__ = (
        UniqueConstraint("category_template_version_id", "key"),
        UniqueConstraint("category_template_version_id", "display_order"),
        CheckConstraint(
            "answer_type IN ('short_text', 'long_text', 'number', 'boolean', "
            "'single_select', 'multi_select', 'date')",
            name="answer_type_valid",
        ),
        CheckConstraint("display_order >= 0", name="display_order_non_negative"),
        Index(
            "ix_qna_questions_template_order",
            "category_template_version_id",
            "display_order",
        ),
    )

    category_template_version_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("category_template_versions.id", ondelete="CASCADE"),
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

    template_version: Mapped[CategoryTemplateVersion] = relationship(
        back_populates="qna_questions"
    )
