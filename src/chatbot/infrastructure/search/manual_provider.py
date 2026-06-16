from ddgs import DDGS

from chatbot.domain.exceptions import SearchError
from chatbot.domain.models import SearchResult
from chatbot.infrastructure.search.link_processor import LinkProcessor
from chatbot.infrastructure.settings import Settings


class ManualSearchProvider:
    def __init__(self, settings: Settings) -> None:
        self._link_processor = LinkProcessor(settings.serper_api_key)

    def search(self, query: str) -> SearchResult:
        try:
            target_query = f"{query} site:altibbi.com"
            all_retrieved_urls: list[str] = []
            with DDGS() as ddgs:
                results = ddgs.text(target_query, max_results=3)
                if results:
                    all_retrieved_urls = [result["href"] for result in results]
            return self._link_processor.process(all_retrieved_urls)
        except Exception as exc:
            raise SearchError(f"Manual search failed for query '{query}': {exc}") from exc
