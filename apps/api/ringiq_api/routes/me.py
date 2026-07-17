from fastapi import APIRouter, Depends

from apps.api.ringiq_api.auth.context import TenantContext, get_current_tenant_context
from apps.api.ringiq_api.schemas.me import MeResponse

router = APIRouter(prefix="/v1", tags=["identity"])


@router.get("/me", response_model=MeResponse)
async def get_me(
    context: TenantContext = Depends(get_current_tenant_context),
) -> MeResponse:
    return MeResponse(**context.__dict__)
