import re


class CitationFilter:
    CITATION_PATTERN = re.compile(r"\[(\d+)\]")

    @classmethod
    def extract_cited_ids(cls, response: str) -> set[str]:
        return set(cls.CITATION_PATTERN.findall(response))

    @classmethod
    def filter_sources(cls, sources: dict[int, str], response: str) -> dict[int, str]:
        cited_ids = cls.extract_cited_ids(response)
        return {key: value for key, value in sources.items() if str(key) in cited_ids}
