import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from apps.api.ringiq_api.models.leads import LeadImportRowStatus, LeadImportStatus


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
    created_at: datetime
    updated_at: datetime


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
