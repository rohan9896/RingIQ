from fastapi import APIRouter, Depends

from apps.api.ringiq_api.auth.context import (
    PlatformContext,
    get_current_platform_context,
)
from apps.api.ringiq_api.schemas.platform import PlatformMeResponse

router = APIRouter(prefix="/v1/platform", tags=["platform"])


@router.get("/me", response_model=PlatformMeResponse)
async def get_platform_me(
    context: PlatformContext = Depends(get_current_platform_context),
) -> PlatformMeResponse:
    return PlatformMeResponse(**context.__dict__)
