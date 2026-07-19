import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.ringiq_api.auth.clerk import ClerkPrincipal, require_tenant_principal
from apps.api.ringiq_api.db.session import get_db_session
from apps.api.ringiq_api.schemas.me import MeResponse
from apps.api.ringiq_api.services.clerk_directory import (
    ClerkDirectory,
    ClerkDirectoryUnavailable,
    ClerkMembershipNotFound,
    get_clerk_directory,
)
from apps.api.ringiq_api.services.tenant_provisioning import (
    TenantProvisioningConflict,
    TenantProvisioningUnavailable,
    provision_tenant_membership,
)

logger = logging.getLogger("ringiq.api.onboarding")
router = APIRouter(prefix="/v1/onboarding", tags=["onboarding"])


@router.post("/bootstrap", response_model=MeResponse)
async def bootstrap_tenant_membership(
    principal: ClerkPrincipal = Depends(require_tenant_principal),
    session: AsyncSession = Depends(get_db_session),
    clerk_directory: ClerkDirectory = Depends(get_clerk_directory),
) -> MeResponse:
    assert principal.organization_id is not None
    try:
        clerk_membership = await clerk_directory.get_tenant_membership(
            user_id=principal.user_id,
            organization_id=principal.organization_id,
        )
        context = await provision_tenant_membership(
            session,
            principal,
            clerk_membership,
        )
    except ClerkMembershipNotFound as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="clerk_organization_membership_required",
        ) from exc
    except ClerkDirectoryUnavailable as exc:
        logger.exception("onboarding.clerk_directory_unavailable")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="clerk_directory_unavailable",
        ) from exc
    except TenantProvisioningConflict as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="tenant_identity_conflict",
        ) from exc
    except TenantProvisioningUnavailable as exc:
        logger.exception("onboarding.tenant_provisioning_unavailable")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="tenant_provisioning_unavailable",
        ) from exc

    return MeResponse(**context.__dict__)
