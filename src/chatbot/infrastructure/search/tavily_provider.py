from chatbot.domain.exceptions import SearchError
from chatbot.domain.models import SearchResult
from chatbot.domain.services.context_formatter import ContextFormatter
from chatbot.infrastructure.settings import Settings


class TavilySearchProvider:
    def __init__(self, settings: Settings) -> None:
        self._client = settings.tavily_client

    def search(self, query: str) -> SearchResult:
        try:
            response = self._client.search(
                query=query,
                search_depth="advanced",
                include_domains=["altibbi.com"],
                max_results=3,
                include_raw_content=True,
            )
        except Exception as exc:
            raise SearchError(f"Tavily search failed for query '{query}': {exc}") from exc

        indexed_sources: list[tuple[int, str, str]] = []
        raw_urls: list[str] = []
        for index, result in enumerate(response.get("results", []), start=1):
            raw_urls.append(result["url"])
            indexed_sources.append((index, result["url"], result.get("content", "")))

        return ContextFormatter.build_search_result(indexed_sources, raw_urls)
