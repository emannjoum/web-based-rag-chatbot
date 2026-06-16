from chatbot.infrastructure.llm.gemini_provider import GeminiProvider
from chatbot.infrastructure.llm.openai_provider import OpenAIProvider
from chatbot.infrastructure.llm.protocol import LLMProvider
from chatbot.infrastructure.settings import Settings

GPT4O_MINI = "GPT-4o mini"
GEMINI_FLASH_LITE = "Gemini 2.5 Flash Lite"


class LLMProviderFactory:
    @classmethod
    def create(cls, model_choice: str, settings: Settings) -> LLMProvider:
        if model_choice == GPT4O_MINI:
            return OpenAIProvider(settings.openai_client)
        return GeminiProvider(settings)
