import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from apps.api.ringiq_api.models.catalog import (
    CategoryStatus,
    QuestionAnswerType,
    TemplateStatus,
)


class QnaQuestionWrite(BaseModel):
    key: str = Field(min_length=1, max_length=100)
    label: str = Field(min_length=1, max_length=500)
    help_text: str | None = Field(default=None, max_length=1000)
    answer_type: QuestionAnswerType
    required: bool = True
    display_order: int = Field(ge=0)
    validation_json: dict[str, Any] = Field(default_factory=dict)
    options_json: list[Any] | None = None


class QnaQuestionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    key: str
    label: str
    help_text: str | None
    answer_type: QuestionAnswerType
    required: bool
    display_order: int
    validation_json: dict[str, Any]
    options_json: list[Any] | None
    created_at: datetime
    updated_at: datetime


class CategoryCreateRequest(BaseModel):
    key: str = Field(min_length=1, max_length=100, pattern=r"^[a-z0-9][a-z0-9_]*$")
    name: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=1000)
    status: CategoryStatus = CategoryStatus.ACTIVE


class CategoryUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=1000)
    status: CategoryStatus | None = None


class CategoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    key: str
    name: str
    description: str | None
    status: CategoryStatus
    created_at: datetime
    updated_at: datetime


class TemplateVersionCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=1000)
    lead_schema_json: dict[str, Any] = Field(default_factory=dict)
    qna_questions: list[QnaQuestionWrite] = Field(default_factory=list)


class TemplateVersionUpdateRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=1000)
    lead_schema_json: dict[str, Any] | None = None


class TemplateQuestionsReplaceRequest(BaseModel):
    qna_questions: list[QnaQuestionWrite]


class CategoryTemplateVersionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    category_id: uuid.UUID
    version: int
    title: str
    description: str | None
    status: TemplateStatus
    lead_schema_json: dict[str, Any]
    published_at: datetime | None
    published_by_user_id: uuid.UUID | None
    created_at: datetime
    updated_at: datetime
    qna_questions: list[QnaQuestionResponse] = Field(default_factory=list)
