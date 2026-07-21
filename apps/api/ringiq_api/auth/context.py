import logging
import uuid
from dataclasses import dataclass

from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.ringiq_api.auth.clerk import (
    ClerkPrincipal,
    require_clerk_principal,
    require_tenant_principal,
)
from apps.api.ringiq_api.db.session import get_db_session
from apps.api.ringiq_api.models.identity import (
    PlatformRole,
    RecordStatus,
    Tenant,
    TenantMembership,
    User,
    UserRealm,
)

logger = logging.getLogger("ringiq.api.auth")


@dataclass(frozen=True)
class TenantContext:
    tenant_id: uuid.UUID
    user_id: uuid.UUID
    membership_id: uuid.UUID
    clerk_organization_id: str
    clerk_user_id: str
    clerk_membership_id: str
    tenant_name: str
    tenant_slug: str
    timezone: str


@dataclass(frozen=True)
class PlatformContext:
    user_id: uuid.UUID
    clerk_user_id: str
    primary_email: str | None
    display_name: str | None
    role: PlatformRole


async def get_current_tenant_context(
    principal: ClerkPrincipal = Depends(require_tenant_principal),
    session: AsyncSession = Depends(get_db_session),
) -> TenantContext:
    statement = (
        select(TenantMembership, Tenant, User)
        .join(Tenant, Tenant.id == TenantMembership.tenant_id)
        .join(User, User.id == TenantMembership.user_id)
        .where(
            Tenant.clerk_organization_id == principal.organization_id,
            User.clerk_user_id == principal.user_id,
            User.realm == UserRealm.TENANT.value,
            Tenant.status == RecordStatus.ACTIVE.value,
            User.status == RecordStatus.ACTIVE.value,
            TenantMembership.status == RecordStatus.ACTIVE.value,
        )
    )
    try:
        row = (await session.execute(statement)).one_or_none()
    except SQLAlchemyError as exc:
        logger.exception(
            "tenant_context.lookup_failed clerk_user_id=%s clerk_organization_id=%s",
            principal.user_id,
            principal.organization_id,
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="identity_store_unavailable",
        ) from exc

    if row is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="tenant_membership_not_provisioned",
        )

    membership, tenant, user = row
    return TenantContext(
        tenant_id=tenant.id,
        user_id=user.id,
        membership_id=membership.id,
        clerk_organization_id=tenant.clerk_organization_id,
        clerk_user_id=user.clerk_user_id,
        clerk_membership_id=membership.clerk_membership_id,
        tenant_name=tenant.name,
        tenant_slug=tenant.slug,
        timezone=tenant.timezone,
    )


async def get_current_platform_context(
    principal: ClerkPrincipal = Depends(require_clerk_principal),
    session: AsyncSession = Depends(get_db_session),
) -> PlatformContext:
    if principal.organization_id is not None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="platform_identity_has_active_organization",
        )

    statement = select(User).where(
        User.clerk_user_id == principal.user_id,
        User.realm == UserRealm.PLATFORM.value,
    )
    try:
        user = (await session.execute(statement)).scalar_one_or_none()
    except SQLAlchemyError as exc:
        logger.exception(
            "platform_context.lookup_failed clerk_user_id=%s",
            principal.user_id,
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="identity_store_unavailable",
        ) from exc

    if user is None or user.platform_role is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="platform_access_not_provisioned",
        )
    if user.status != RecordStatus.ACTIVE.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="platform_identity_inactive",
        )

    return PlatformContext(
        user_id=user.id,
        clerk_user_id=user.clerk_user_id,
        primary_email=user.primary_email,
        display_name=user.display_name,
        role=PlatformRole(user.platform_role),
    )
