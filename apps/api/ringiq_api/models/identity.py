import uuid
from datetime import datetime
from enum import StrEnum

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, String, UniqueConstraint, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from apps.api.ringiq_api.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class RecordStatus(StrEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"


class UserRealm(StrEnum):
    TENANT = "tenant"
    PLATFORM = "platform"


class PlatformRole(StrEnum):
    SUPER_ADMIN = "platform_super_admin"
    OPERATIONS = "platform_operations"
    TEMPLATE_MANAGER = "template_manager"


class PlatformInvitationStatus(StrEnum):
    CREATING = "creating"
    PENDING = "pending"
    ACCEPTED = "accepted"
    REVOKED = "revoked"
    EXPIRED = "expired"
    FAILED = "failed"


class WebhookReceiptStatus(StrEnum):
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"


class Tenant(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "tenants"
    __table_args__ = (
        CheckConstraint(
            "status IN ('active', 'inactive', 'suspended')",
            name="status_valid",
        ),
    )

    clerk_organization_id: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    primary_category_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("categories.id", ondelete="SET NULL"), index=True
    )
    timezone: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        default="Asia/Kolkata",
        server_default="Asia/Kolkata",
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=RecordStatus.ACTIVE.value,
        server_default=text("'active'"),
        index=True,
    )

    memberships: Mapped[list["TenantMembership"]] = relationship(
        back_populates="tenant",
        cascade="all, delete-orphan",
    )


class User(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint(
            "status IN ('active', 'inactive', 'suspended')",
            name="status_valid",
        ),
        CheckConstraint(
            "realm IN ('tenant', 'platform')",
            name="realm_valid",
        ),
        CheckConstraint(
            "(realm = 'tenant' AND platform_role IS NULL) OR "
            "(realm = 'platform' AND platform_role IS NOT NULL AND platform_role IN "
            "('platform_super_admin', 'platform_operations', 'template_manager'))",
            name="realm_role_valid",
        ),
    )

    clerk_user_id: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    primary_email: Mapped[str | None] = mapped_column(String(320))
    display_name: Mapped[str | None] = mapped_column(String(255))
    realm: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=UserRealm.TENANT.value,
        server_default=text("'tenant'"),
        index=True,
    )
    platform_role: Mapped[str | None] = mapped_column(String(40), index=True)
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=RecordStatus.ACTIVE.value,
        server_default=text("'active'"),
        index=True,
    )

    memberships: Mapped[list["TenantMembership"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )


class PlatformUserInvitation(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "platform_user_invitations"
    __table_args__ = (
        CheckConstraint("email = lower(btrim(email))", name="email_normalized"),
        CheckConstraint(
            "platform_role IN ('platform_super_admin', 'platform_operations', 'template_manager')",
            name="platform_role_valid",
        ),
        CheckConstraint(
            "status IN ('creating', 'pending', 'accepted', 'revoked', 'expired', 'failed')",
            name="status_valid",
        ),
        Index(
            "uq_platform_user_invitations_open_email",
            "email",
            unique=True,
            postgresql_where=text("status IN ('creating', 'pending')"),
        ),
    )

    email: Mapped[str] = mapped_column(String(320), nullable=False, index=True)
    display_name: Mapped[str | None] = mapped_column(String(255))
    platform_role: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    clerk_invitation_id: Mapped[str | None] = mapped_column(
        String(64), unique=True, index=True
    )
    invited_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), index=True
    )
    accepted_user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), unique=True, index=True
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=PlatformInvitationStatus.CREATING.value,
        server_default=text("'creating'"),
        index=True,
    )
    failure_reason: Mapped[str | None] = mapped_column(String(500))


class WebhookReceipt(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "webhook_receipts"
    __table_args__ = (
        UniqueConstraint("provider", "delivery_id"),
        CheckConstraint(
            "status IN ('processing', 'processed', 'failed')",
            name="status_valid",
        ),
    )

    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    delivery_id: Mapped[str] = mapped_column(String(255), nullable=False)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=WebhookReceiptStatus.PROCESSING.value,
        server_default=text("'processing'"),
        index=True,
    )
    payload_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    error: Mapped[str | None] = mapped_column(String(1000))


class TenantMembership(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "tenant_memberships"
    __table_args__ = (
        UniqueConstraint("tenant_id", "user_id"),
        CheckConstraint(
            "status IN ('active', 'inactive', 'suspended')",
            name="status_valid",
        ),
        Index("ix_tenant_memberships_user_id_status", "user_id", "status"),
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    clerk_membership_id: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=RecordStatus.ACTIVE.value,
        server_default=text("'active'"),
        index=True,
    )
    role_key: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        default="member",
        server_default=text("'member'"),
    )

    tenant: Mapped[Tenant] = relationship(back_populates="memberships")
    user: Mapped[User] = relationship(back_populates="memberships")
