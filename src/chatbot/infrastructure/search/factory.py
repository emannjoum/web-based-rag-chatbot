from chatbot.infrastructure.search.manual_provider import ManualSearchProvider
from chatbot.infrastructure.search.protocol import SearchProvider
from chatbot.infrastructure.search.serper_provider import SerperSearchProvider
from chatbot.infrastructure.search.tavily_provider import TavilySearchProvider
from chatbot.infrastructure.settings import Settings

SERPER = "Serper"
TAVILY = "Tavily"
MANUAL_SCRAPING = "Manual Scraping"


class SearchProviderFactory:
    @classmethod
    def create(cls, method: str, settings: Settings) -> SearchProvider:
        providers: dict[str, SearchProvider] = {
            SERPER: SerperSearchProvider(settings),
            TAVILY: TavilySearchProvider(settings),
            MANUAL_SCRAPING: ManualSearchProvider(settings),
        }
        return providers.get(method, SerperSearchProvider(settings))
