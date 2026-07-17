import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from apps.api.ringiq_api.models.catalog import QuestionAnswerType, TemplateStatus


class StarterTemplateQuestionResponse(BaseModel):
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


class StarterTemplateResponse(BaseModel):
    id: uuid.UUID
    category_id: uuid.UUID
    category_key: str
    category_name: str
    title: str
    description: str | None
    lead_schema_json: dict[str, Any]
    qna_questions: list[StarterTemplateQuestionResponse]


class TenantKnowledgeQuestionWrite(BaseModel):
    key: str = Field(min_length=1, max_length=100)
    label: str = Field(min_length=1, max_length=500)
    help_text: str | None = Field(default=None, max_length=1000)
    answer_type: QuestionAnswerType
    required: bool = True
    display_order: int = Field(ge=0)
    validation_json: dict[str, Any] = Field(default_factory=dict)
    options_json: list[Any] | None = None
    answer_value_json: Any | None = None


class TenantKnowledgeQuestionResponse(TenantKnowledgeQuestionWrite):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class TenantKnowledgeVersionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    knowledge_base_id: uuid.UUID
    tenant_id: uuid.UUID
    category_id: uuid.UUID | None
    source_template_version_id: uuid.UUID | None
    version: int
    title: str
    business_profile_json: dict[str, Any]
    additional_notes: str | None
    status: TemplateStatus
    published_at: datetime | None
    created_at: datetime
    updated_at: datetime
    questions: list[TenantKnowledgeQuestionResponse] = Field(default_factory=list)


class TenantKnowledgeBaseResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    active_version: TenantKnowledgeVersionResponse | None
    draft_version: TenantKnowledgeVersionResponse | None


class CreateKnowledgeBaseDraftRequest(BaseModel):
    starter_template_version_id: uuid.UUID | None = None


class UpdateKnowledgeBaseDraftRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    business_profile_json: dict[str, Any] | None = None
    additional_notes: str | None = Field(default=None, max_length=10000)


class ReplaceTenantKnowledgeQuestionsRequest(BaseModel):
    questions: list[TenantKnowledgeQuestionWrite]
