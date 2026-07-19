from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.ringiq_api.auth.clerk import ClerkPrincipal
from apps.api.ringiq_api.auth.context import TenantContext
from apps.api.ringiq_api.models.identity import (
    RecordStatus,
    Tenant,
    TenantMembership,
    User,
    UserRealm,
)
from apps.api.ringiq_api.services.clerk_directory import ClerkTenantMembership


class TenantProvisioningConflict(Exception):
    pass


class TenantProvisioningUnavailable(Exception):
    pass


async def provision_tenant_membership(
    session: AsyncSession,
    principal: ClerkPrincipal,
    clerk_membership: ClerkTenantMembership,
) -> TenantContext:
    if principal.organization_id != clerk_membership.organization_id:
        raise TenantProvisioningConflict
    if principal.user_id != clerk_membership.user_id:
        raise TenantProvisioningConflict

    try:
        user = await session.scalar(
            select(User).where(User.clerk_user_id == clerk_membership.user_id)
        )
        if user is not None and user.realm != UserRealm.TENANT.value:
            raise TenantProvisioningConflict
        if user is None:
            user = User(
                clerk_user_id=clerk_membership.user_id,
                primary_email=clerk_membership.primary_email,
                display_name=clerk_membership.display_name,
                realm=UserRealm.TENANT.value,
            )
            session.add(user)
        else:
            user.primary_email = clerk_membership.primary_email
            user.display_name = clerk_membership.display_name
            user.status = RecordStatus.ACTIVE.value

        tenant = await session.scalar(
            select(Tenant).where(
                Tenant.clerk_organization_id == clerk_membership.organization_id
            )
        )
        if tenant is None:
            tenant = Tenant(
                clerk_organization_id=clerk_membership.organization_id,
                name=clerk_membership.organization_name,
                slug=clerk_membership.organization_slug,
            )
            session.add(tenant)
        else:
            tenant.name = clerk_membership.organization_name
            tenant.slug = clerk_membership.organization_slug
            tenant.status = RecordStatus.ACTIVE.value

        await session.flush()
        membership = await session.scalar(
            select(TenantMembership).where(
                TenantMembership.tenant_id == tenant.id,
                TenantMembership.user_id == user.id,
            )
        )
        if membership is None:
            membership = TenantMembership(
                tenant_id=tenant.id,
                user_id=user.id,
                clerk_membership_id=clerk_membership.membership_id,
                role_key=clerk_membership.role,
            )
            session.add(membership)
        else:
            membership.clerk_membership_id = clerk_membership.membership_id
            membership.role_key = clerk_membership.role
            membership.status = RecordStatus.ACTIVE.value

        await session.commit()
    except TenantProvisioningConflict:
        await session.rollback()
        raise
    except IntegrityError as exc:
        await session.rollback()
        raise TenantProvisioningConflict from exc
    except SQLAlchemyError as exc:
        await session.rollback()
        raise TenantProvisioningUnavailable from exc

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
