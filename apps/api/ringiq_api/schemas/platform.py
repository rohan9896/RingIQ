import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from apps.api.ringiq_api.models.identity import PlatformInvitationStatus, PlatformRole
from apps.api.ringiq_api.schemas.catalog import CategoryResponse, CategoryTemplateVersionResponse


class PlatformMeResponse(BaseModel):
    user_id: uuid.UUID
    clerk_user_id: str
    primary_email: str | None
    display_name: str | None
    role: PlatformRole


class PlatformOverviewCounts(BaseModel):
    organizations: int
    active_organizations: int
    suspended_organizations: int
    tenant_users: int
    platform_users: int
    categories: int
    active_categories: int
    draft_templates: int
    published_templates: int


class PlatformOverviewResponse(BaseModel):
    counts: PlatformOverviewCounts
    first_template_seeded: bool


class PlatformStarterSeedResponse(BaseModel):
    category: CategoryResponse
    template_version: CategoryTemplateVersionResponse
    created_category: bool
    created_template: bool


class PlatformManagedUser(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    clerk_user_id: str
    primary_email: str | None
    display_name: str | None
    platform_role: PlatformRole
    status: str
    created_at: datetime
    updated_at: datetime


class PlatformInvitation(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    display_name: str | None
    platform_role: PlatformRole
    status: PlatformInvitationStatus
    expires_at: datetime
    created_at: datetime
    accepted_user_id: uuid.UUID | None


class CreatePlatformInvitationRequest(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    display_name: str | None = Field(default=None, max_length=255)
    role: PlatformRole

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        normalized = value.strip().lower()
        local, separator, domain = normalized.partition("@")
        if not separator or not local or "." not in domain or domain.startswith("."):
            raise ValueError("invalid email address")
        return normalized
