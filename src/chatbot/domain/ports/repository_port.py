from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class ChatRepositoryPort(Protocol):
    def log_interaction(
        self,
        session_id: str | None,
        query: str,
        response: str,
        search_params: dict[str, Any] | None = None,
        sources: dict | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> tuple[str, Any]: ...

    def get_all_history(self, limit: int = 20) -> list[dict[str, Any]]: ...

    def get_chat_by_id(self, session_id: str) -> list[dict[str, Any]]: ...

    def update_eval_scores(self, message_id: Any, ragas_scores: dict[str, Any]) -> None: ...

    def delete_chat(self, session_id: str) -> bool: ...
