from chatbot.domain.models import SearchResult


class ContextFormatter:
    @classmethod
    def format_source_block(cls, source_id: int, url: str, content: str) -> str:
        return f"Source [{source_id}]\nURL: {url}\nContent: {content}\n\n"

    @classmethod
    def build_search_result(
        cls,
        indexed_sources: list[tuple[int, str, str]],
        raw_urls: list[str],
    ) -> SearchResult:
        context = "".join(
            cls.format_source_block(source_id, url, content)
            for source_id, url, content in indexed_sources
        )
        sources = {source_id: url for source_id, url, _ in indexed_sources}
        return SearchResult(context=context, sources=sources, raw_urls=raw_urls)
