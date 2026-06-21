from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"
    service: str = "altibbi-chatbot-api"


class ModelOptionSchema(BaseModel):
    id: str
    label: str
    provider_value: str


class ConfigResponse(BaseModel):
    models: list[ModelOptionSchema]
    search_methods: list[str]
    default_model_id: str
    default_search_method: str


class SessionSummarySchema(BaseModel):
    id: str
    title: str
    preview: str
    last_active: datetime


class SessionListResponse(BaseModel):
    sessions: list[SessionSummarySchema]


class ChatMessageSchema(BaseModel):
    role: Literal["user", "assistant"]
    content: str
    sources: dict[str, str] = Field(default_factory=dict)
    suggestions: list[str] = Field(default_factory=list)
    ragas_eval: dict[str, float] | None = Field(default=None)
    thoughtDurationSeconds: float | None = None

class SessionDetailResponse(BaseModel):
    session_id: str
    messages: list[ChatMessageSchema]


class ChatCompletionRequest(BaseModel):
    message: str = Field(min_length=1, max_length=8000)
    session_id: str | None = None
    model_id: str
    search_method: str | None = None
    is_drug_profile: bool = False


class ChatCompletionResponse(BaseModel):
    session_id: str
    status: str
    user_message: ChatMessageSchema
    assistant_message: ChatMessageSchema


class DeleteSessionResponse(BaseModel):
    deleted: bool
    session_id: str


class DeleteAllSessionsResponse(BaseModel):
    deleted_count: int


class ErrorResponse(BaseModel):
    detail: str
    code: str | None = None


class ImageUploadResponse(BaseModel):
    session_id: str
    status: str
    user_message: ChatMessageSchema
    assistant_message: ChatMessageSchema | None = None
    drug_query: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
