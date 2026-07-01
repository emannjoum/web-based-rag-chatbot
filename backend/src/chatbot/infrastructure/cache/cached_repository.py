"""Repository decorator that caches recent chat histories in Redis."""

from __future__ import annotations

import logging
from typing import Any

from chatbot.infrastructure.cache.serialization import (
    deserialize_documents,
    history_cache_key,
    serialize_documents,
    session_cache_key,
)

logger = logging.getLogger(__name__)


class CachedChatRepository:
    """Read-through cache for session lists and individual session messages."""

    def __init__(
        self,
        repository: Any,
        redis_client: Any | None,
        *,
        ttl_seconds: int = 300,
        enabled: bool = True,
    ) -> None:
        self._repository = repository
        self._redis = redis_client
        self._ttl_seconds = ttl_seconds
        self._enabled = enabled and redis_client is not None

    def log_interaction(
        self,
        session_id: str | None,
        query: str,
        response: str,
        user_id: int,
        search_params: dict[str, Any] | None = None,
        sources: dict | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> tuple[str, Any]:
        new_session_id, message_id = self._repository.log_interaction(
            session_id,
            query,
            response,
            user_id,
            search_params,
            sources,
            metadata,
        )
        self._invalidate_session(new_session_id)
        self._invalidate_history_lists(user_id)
        return new_session_id, message_id

    def get_all_history(self, user_id: int, limit: int = 20) -> list[dict[str, Any]]:
        if not self._enabled:
            return self._repository.get_all_history(user_id=user_id, limit=limit)

        cache_key = history_cache_key(user_id, limit)
        try:
            cached = self._redis.get(cache_key)
            if cached is not None:
                return deserialize_documents(cached)
        except Exception as exc:
            logger.warning("Redis read failed for %s: %s", cache_key, exc)

        history = self._repository.get_all_history(user_id=user_id, limit=limit)
        self._cache_history(user_id, limit, history)
        return history

    def get_chat_by_id(self, session_id: str, user_id: int) -> list[dict[str, Any]]:
        if not self._enabled:
            return self._repository.get_chat_by_id(session_id, user_id)

        cache_key = session_cache_key(session_id)
        try:
            cached = self._redis.get(cache_key)
            if cached is not None:
                return deserialize_documents(cached)
        except Exception as exc:
            logger.warning("Redis read failed for %s: %s", cache_key, exc)

        messages = self._repository.get_chat_by_id(session_id, user_id)
        self._cache_session(session_id, messages)
        return messages

    def update_eval_scores(
        self,
        message_id: Any,
        ragas_scores: dict[str, Any] | None,
        eval_status: str = "success",
    ) -> None:
        self._repository.update_eval_scores(message_id, ragas_scores, eval_status)
        if not self._enabled:
            return

        try:
            session_id = self._find_session_id_for_message(message_id)
            if session_id:
                self._invalidate_session(session_id)
        except Exception as exc:
            logger.warning("Failed to invalidate cache after eval update: %s", exc)

    def delete_chat(self, session_id: str, user_id: int) -> bool:
        deleted = self._repository.delete_chat(session_id, user_id)
        self._invalidate_session(session_id)
        self._invalidate_history_lists(user_id)
        return deleted

    def session_belongs_to_user(self, session_id: str, user_id: int) -> bool:
        return self._repository.session_belongs_to_user(session_id, user_id)

    def _cache_session(self, session_id: str, messages: list[dict[str, Any]]) -> None:
        if not self._enabled:
            return
        try:
            self._redis.setex(
                session_cache_key(session_id),
                self._ttl_seconds,
                serialize_documents(messages),
            )
        except Exception as exc:
            logger.warning("Redis write failed for session %s: %s", session_id, exc)

    def _cache_history(self, user_id: int, limit: int, history: list[dict[str, Any]]) -> None:
        if not self._enabled:
            return
        try:
            self._redis.setex(
                history_cache_key(user_id, limit),
                self._ttl_seconds,
                serialize_documents(history),
            )
        except Exception as exc:
            logger.warning("Redis write failed for history limit %s: %s", limit, exc)

    def _invalidate_session(self, session_id: str) -> None:
        if not self._enabled or not session_id:
            return
        try:
            self._redis.delete(session_cache_key(session_id))
        except Exception as exc:
            logger.warning("Redis delete failed for session %s: %s", session_id, exc)

    def _invalidate_history_lists(self, user_id: int) -> None:
        if not self._enabled:
            return
        try:
            prefix = f"{history_cache_key(user_id, 0).rsplit(':', 1)[0]}:"
            for key in self._redis.scan_iter(f"{prefix}*"):
                self._redis.delete(key)
        except Exception as exc:
            logger.warning("Redis history invalidation failed: %s", exc)

    def _find_session_id_for_message(self, message_id: Any) -> str | None:
        if hasattr(self._repository, "find_session_id_for_message"):
            return self._repository.find_session_id_for_message(message_id)
        return None
