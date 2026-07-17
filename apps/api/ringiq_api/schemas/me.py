import uuid

from pydantic import BaseModel


class MeResponse(BaseModel):
    tenant_id: uuid.UUID
    user_id: uuid.UUID
    membership_id: uuid.UUID
    clerk_organization_id: str
    clerk_user_id: str
    clerk_membership_id: str
    tenant_name: str
    tenant_slug: str
    timezone: str
