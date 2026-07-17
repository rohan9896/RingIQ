import uuid
from enum import StrEnum

from sqlalchemy import CheckConstraint, ForeignKey, Index, String, UniqueConstraint, text
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
