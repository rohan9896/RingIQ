"""Request and response schemas."""
from apps.api.ringiq_api.schemas.catalog import (
    CategoryCreateRequest,
    CategoryResponse,
    CategoryTemplateVersionResponse,
    CategoryUpdateRequest,
    QnaQuestionResponse,
    QnaQuestionWrite,
    TemplateQuestionsReplaceRequest,
    TemplateVersionCreateRequest,
    TemplateVersionUpdateRequest,
)
from apps.api.ringiq_api.schemas.me import MeResponse
from apps.api.ringiq_api.schemas.platform import PlatformMeResponse

__all__ = [
    "CategoryCreateRequest",
    "CategoryResponse",
    "CategoryTemplateVersionResponse",
    "CategoryUpdateRequest",
    "MeResponse",
    "PlatformMeResponse",
    "QnaQuestionResponse",
    "QnaQuestionWrite",
    "TemplateQuestionsReplaceRequest",
    "TemplateVersionCreateRequest",
    "TemplateVersionUpdateRequest",
]
