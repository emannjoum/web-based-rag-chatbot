import requests

from chatbot.domain.exceptions import SearchError
from chatbot.domain.models import SearchResult
from chatbot.domain.services.context_formatter import ContextFormatter
from chatbot.infrastructure.search.link_processor import LinkProcessor
from chatbot.infrastructure.settings import Settings


class SerperSearchProvider:
    def __init__(self, settings: Settings) -> None:
        self._api_key = settings.serper_api_key
        self._link_processor = LinkProcessor(settings.serper_api_key)

    def search(self, query: str) -> SearchResult:
        try:
            url = "https://google.serper.dev/search"
            payload = {"q": f"{query} site:altibbi.com", "gl": "jo", "hl": "ar", "num": 3}
            headers = {"X-API-KEY": self._api_key, "Content-Type": "application/json"}
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            search_results = response.json()
        except Exception as exc:
            raise SearchError(f"Serper search failed for query '{query}': {exc}") from exc

        all_retrieved_urls: list[str] = []
        snippet_map: dict[str, str] = {}
        for result in search_results.get("organic", []):
            link = result.get("link")
            if not link:
                continue
            all_retrieved_urls.append(link)
            snippet_map[link] = result.get("snippet", "")

        return self._link_processor.process(all_retrieved_urls, snippet_map)
