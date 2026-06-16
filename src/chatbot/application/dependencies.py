from functools import lru_cache
from typing import Any

from chatbot.domain.ports.llm_port import LLMPort
from chatbot.domain.ports.repository_port import ChatRepositoryPort
from chatbot.domain.ports.search_port import SearchPort
from chatbot.domain.prompts.loader import PromptLoader
from chatbot.domain.services.query_refiner import QueryRefiner
from chatbot.domain.services.rag_pipeline import RAGPipeline
from chatbot.infrastructure.evaluation.ragas_evaluator import RagasEvaluator
from chatbot.infrastructure.llm.factory import LLMProviderFactory
from chatbot.infrastructure.logging.query_logger import QueryLogger
from chatbot.infrastructure.persistence.mongo_repository import MongoChatRepository
from chatbot.infrastructure.search.factory import SearchProviderFactory
from chatbot.infrastructure.settings import Settings


class DependencyContainer:
    """Provisions and caches concrete infrastructure adapters for application services."""

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or Settings.from_env()
        self._prompt_loader = PromptLoader()
        self._query_refiner = QueryRefiner(self._prompt_loader)
        self._rag_pipeline = RAGPipeline(self._query_refiner, self._prompt_loader)
        self._repository = MongoChatRepository(self._settings.mongodb_uri)
        self._query_logger = QueryLogger()
        self._evaluator = RagasEvaluator(self._settings)

    @classmethod
    @lru_cache(maxsize=1)
    def default(cls) -> "DependencyContainer":
        return cls()

    @property
    def settings(self) -> Settings:
        return self._settings

    @property
    def prompt_loader(self) -> PromptLoader:
        return self._prompt_loader

    @property
    def rag_pipeline(self) -> RAGPipeline:
        return self._rag_pipeline

    @property
    def repository(self) -> ChatRepositoryPort:
        return self._repository

    @property
    def query_logger(self) -> QueryLogger:
        return self._query_logger

    @property
    def evaluator(self) -> RagasEvaluator:
        return self._evaluator

    def create_llm_provider(self, model_choice: str) -> LLMPort:
        return LLMProviderFactory.create(model_choice, self._settings)

    def create_search_provider(self, search_method: str) -> SearchPort:
        return SearchProviderFactory.create(search_method, self._settings)

    def persist_pipeline_result(
        self,
        session_id: str | None,
        user_query: str,
        pipeline_result: Any,
    ) -> tuple[str, Any]:
        search_params = {"query": pipeline_result.metadata.get("refined_query", user_query)}
        new_session_id, message_id = self._repository.log_interaction(
            session_id,
            user_query,
            pipeline_result.response,
            search_params,
            pipeline_result.sources,
            pipeline_result.metadata,
        )
        return new_session_id, message_id
