from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class LLMPort(Protocol):
    def generate_text(
        self,
        prompt: str,
        *,
        is_json: bool = False,
        temperature: float = 0.0,
        system_prompt: str | None = None,
        history: list[dict[str, Any]] | None = None,
    ) -> str: ...

    def generate_vision(
        self,
        prompt: str,
        image_bytes: bytes,
        *,
        temperature: float = 0.0,
    ) -> str: ...
