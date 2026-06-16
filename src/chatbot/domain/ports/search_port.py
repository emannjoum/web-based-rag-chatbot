from typing import Protocol, runtime_checkable

from chatbot.domain.models import SearchResult


@runtime_checkable
class SearchPort(Protocol):
    def search(self, query: str) -> SearchResult: ...
