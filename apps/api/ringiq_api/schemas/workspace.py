import uuid
from datetime import datetime

from pydantic import BaseModel


class WorkspaceCategoryResponse(BaseModel):
    id: uuid.UUID
    key: str
    name: str


class WorkspaceUpdateRequest(BaseModel):
    primary_category_id: uuid.UUID


class WorkspaceResponse(BaseModel):
    tenant_id: uuid.UUID
    name: str
    timezone: str
    category: WorkspaceCategoryResponse | None
    has_active_knowledge_base: bool
    is_call_ready: bool
    readiness_blockers: list[str]


class DashboardTotalsResponse(BaseModel):
    leads: int
    campaigns: int
    call_attempts: int
    connected: int
    completed: int
    failed: int


class DashboardRecentCallResponse(BaseModel):
    attempt_id: uuid.UUID
    lead_id: uuid.UUID
    lead_name: str
    campaign_id: uuid.UUID
    campaign_name: str
    status: str
    started_at: datetime | None
    ended_at: datetime | None
    duration_seconds: int | None
    failure_code: str | None
    failure_detail: str | None


class DashboardResponse(BaseModel):
    workspace: WorkspaceResponse
    totals: DashboardTotalsResponse
    recent_calls: list[DashboardRecentCallResponse]
