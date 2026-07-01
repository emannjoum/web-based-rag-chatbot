from chatbot.domain.models import SearchResult
from chatbot.domain.services.context_formatter import ContextFormatter
from chatbot.infrastructure.search.scraper import WebScraper


class LinkProcessor:
    MAX_SOURCES = 3

    def __init__(self, serper_api_key: str) -> None:
        self._serper_api_key = serper_api_key
        self._scraper = WebScraper()

    def process(
        self,
        links: list[str],
        organic_results_map: dict[str, str] | None = None,
    ) -> SearchResult:
        indexed_sources: list[tuple[int, str, str]] = []
        snippet_map = organic_results_map or {}
        valid_count = 1

        for link in links:
            if not self._scraper.is_trusted_source(link) or valid_count > self.MAX_SOURCES:
                continue

            full_content = self._scraper.scrape_with_serper(link, self._serper_api_key)
            final_content = full_content if len(full_content) > 100 else snippet_map.get(link, "")
            indexed_sources.append((valid_count, link, final_content))
            valid_count += 1

        return ContextFormatter.build_search_result(indexed_sources, list(links))
