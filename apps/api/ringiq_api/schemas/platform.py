import uuid

from pydantic import BaseModel

from apps.api.ringiq_api.models.identity import PlatformRole


class PlatformMeResponse(BaseModel):
    user_id: uuid.UUID
    clerk_user_id: str
    primary_email: str | None
    display_name: str | None
    role: PlatformRole
