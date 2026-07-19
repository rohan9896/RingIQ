import uuid

from pydantic import BaseModel

from apps.api.ringiq_api.models.identity import PlatformRole
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
