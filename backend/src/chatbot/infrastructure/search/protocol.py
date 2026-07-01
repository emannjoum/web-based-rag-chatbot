from typing import Protocol, runtime_checkable

from chatbot.domain.models import SearchResult


@runtime_checkable
class SearchProvider(Protocol):
    def search(self, query: str) -> SearchResult: ...
