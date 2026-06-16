from dataclasses import dataclass, field
from typing import Any, Literal

Role = Literal["user", "assistant"]
PipelineStatus = Literal["success", "fallback", "unsupported", "report"]


@dataclass(frozen=True)
class RefineResult:
    refined_query: str
    language: str
    chat_title: str


@dataclass(frozen=True)
class SearchResult:
    context: str
    sources: dict[int, str]
    raw_urls: list[str]

    @property
    def has_sources(self) -> bool:
        return bool(self.sources)


@dataclass
class ChatMessage:
    role: Role
    content: str
    sources: dict[int, str] = field(default_factory=dict)
    suggestions: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class PipelineResult:
    response: str
    sources: dict[int, str]
    suggestions: list[str]
    metadata: dict[str, Any]
    session_id: str | None
    message_id: str | None
    status: PipelineStatus
    refine_result: RefineResult | None = None
    search_result: SearchResult | None = None


@dataclass(frozen=True)
class ImageHandlingResult:
    status: Literal["unsupported", "report", "drug"]
    user_message: str
    assistant_response: str | None = None
    drug_query: str | None = None
