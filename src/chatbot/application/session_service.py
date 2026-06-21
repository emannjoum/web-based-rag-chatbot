import datetime
from typing import Any

from chatbot.domain.ports.repository_port import ChatRepositoryPort


class SessionService:
    def __init__(self, repository: ChatRepositoryPort) -> None:
        self._repository = repository

    def list_sessions(self, limit: int = 30) -> list[dict[str, Any]]:
        sessions: list[dict[str, Any]] = []
        for chat in self._repository.get_all_history(limit=limit) or []:
            title = chat.get("chat_title") or chat.get("last_preview") or "New Chat"
            preview = chat.get("last_preview") or ""
            last_active = chat.get("last_active")
            if isinstance(last_active, datetime.datetime) and last_active.tzinfo is None:
                last_active = last_active.replace(tzinfo=datetime.timezone.utc)

            sessions.append(
                {
                    "id": str(chat["_id"]),
                    "title": str(title)[:80],
                    "preview": str(preview)[:120],
                    "last_active": last_active or datetime.datetime.now(datetime.timezone.utc),
                }
            )
        return sessions

    def get_session_messages(self, session_id: str) -> list[dict[str, Any]]:
        raw_messages = self._repository.get_chat_by_id(session_id) or []
        return self._normalize_messages(raw_messages)

    def delete_session(self, session_id: str) -> bool:
        return self._repository.delete_chat(session_id)

    def delete_all_sessions(self) -> int:
        sessions = self._repository.get_all_history(limit=500) or []
        deleted = 0
        for chat in sessions:
            if self._repository.delete_chat(str(chat["_id"])):
                deleted += 1
        return deleted

    @staticmethod
    def _normalize_messages(raw_messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
        normalized: list[dict[str, Any]] = []
        for doc in raw_messages:
            role = doc.get("role")
            if role not in {"user", "assistant"}:
                continue

            entry: dict[str, Any] = {
                "role": role,
                "content": doc.get("content", ""),
            }
            if role == "assistant":
                sources = doc.get("sources") or {}
                entry["sources"] = {str(key): str(value) for key, value in sources.items()}
            normalized.append(entry)
        return normalized
