import logging

from functools import lru_cache
from typing import Any

from chatbot.application.auth_service import AuthService
from chatbot.domain.ports.llm_port import LLMPort
from chatbot.domain.ports.repository_port import ChatRepositoryPort
from chatbot.domain.ports.search_port import SearchPort
from chatbot.domain.prompts.loader import PromptLoader
from chatbot.domain.services.query_refiner import QueryRefiner
from chatbot.domain.services.rag_pipeline import RAGPipeline
from chatbot.infrastructure.cache.cached_repository import CachedChatRepository
from chatbot.infrastructure.cache.redis_client import create_redis_client
from chatbot.infrastructure.evaluation.ragas_evaluator import RagasEvaluator
from chatbot.infrastructure.llm.factory import LLMProviderFactory
from chatbot.infrastructure.logging.query_logger import QueryLogger
from chatbot.infrastructure.persistence.mongo_repository import MongoChatRepository
from chatbot.infrastructure.persistence.mysql.database import create_session_factory
from chatbot.infrastructure.persistence.mysql.migrations import run_migrations
from chatbot.infrastructure.persistence.mysql.user_repository import MySQLUserRepository
from chatbot.infrastructure.search.factory import SearchProviderFactory
from chatbot.infrastructure.settings import Settings

logger = logging.getLogger(__name__)


class DependencyContainer:
    """Provisions and caches concrete infrastructure adapters for application services."""

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or Settings.from_env()
        self._prompt_loader = PromptLoader()
        self._query_refiner = QueryRefiner(self._prompt_loader)
        self._rag_pipeline = RAGPipeline(self._query_refiner, self._prompt_loader)
        mongo_repository = MongoChatRepository(self._settings.mongodb_uri)
        redis_client = (
            create_redis_client(self._settings.redis_url)
            if self._settings.redis_cache_enabled
            else None
        )
        self._repository = CachedChatRepository(
            mongo_repository,
            redis_client,
            ttl_seconds=self._settings.redis_cache_ttl_seconds,
            enabled=self._settings.redis_cache_enabled,
        )
        self._query_logger = QueryLogger()
        self._evaluator = RagasEvaluator(self._settings)
        run_migrations(self._settings.mysql_url)
        self._db_session_factory = create_session_factory(self._settings.mysql_url)
        self._user_repository = MySQLUserRepository(self._db_session_factory)
        self._auth_service = AuthService(self._user_repository, self._settings)

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

    @property
    def auth_service(self) -> AuthService:
        return self._auth_service

    def create_llm_provider(self, model_choice: str) -> LLMPort:
        return LLMProviderFactory.create(model_choice, self._settings)

    def create_search_provider(self, search_method: str) -> SearchPort:
        return SearchProviderFactory.create(search_method, self._settings)

    def persist_pipeline_result(
        self,
        session_id: str | None,
        user_id: int,
        user_query: str,
        pipeline_result: Any,
    ) -> tuple[str, Any]:
        search_params = {"query": pipeline_result.metadata.get("refined_query", user_query)}
        new_session_id, message_id = self._repository.log_interaction(
            session_id,
            user_query,
            pipeline_result.response,
            user_id,
            search_params,
            pipeline_result.sources,
            pipeline_result.metadata,
        )
        return new_session_id, message_id
