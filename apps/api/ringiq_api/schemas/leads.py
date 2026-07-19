import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from apps.api.ringiq_api.models.leads import (
    LeadImportRowStatus,
    LeadImportStatus,
    LeadManualStatus,
    LeadStatus,
)


class LeadImportCreateRequest(BaseModel):
    filename: str = Field(min_length=1, max_length=255)
    csv_content: str = Field(min_length=1, max_length=5_000_000)
    column_mapping: dict[str, str] = Field(default_factory=dict)


class LeadResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    email: str
    phone_number: str
    normalized_phone_number: str
    attributes_json: dict[str, Any]
    status: LeadStatus
    manual_status: LeadManualStatus
    archived_at: datetime | None
    created_at: datetime
    updated_at: datetime


class LeadCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    email: str = Field(min_length=3, max_length=320)
    phone_number: str = Field(min_length=5, max_length=32)
    attributes_json: dict[str, Any] = Field(default_factory=dict)


class LeadUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    email: str | None = Field(default=None, min_length=3, max_length=320)
    phone_number: str | None = Field(default=None, min_length=5, max_length=32)
    attributes_json: dict[str, Any] | None = None
    manual_status: LeadManualStatus | None = None


class LeadImportRowResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    lead_id: uuid.UUID | None
    row_number: int
    status: LeadImportRowStatus
    error_code: str | None
    error_message: str | None
    raw_data_json: dict[str, Any]
    created_at: datetime


class LeadImportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    filename: str
    status: LeadImportStatus
    total_rows: int
    imported_rows: int
    invalid_rows: int
    duplicate_rows: int
    column_mapping_json: dict[str, Any]
    created_at: datetime


class LeadImportDetailResponse(LeadImportResponse):
    rows: list[LeadImportRowResponse]
