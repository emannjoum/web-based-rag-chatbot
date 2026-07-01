from typing import Any

from openai import OpenAI

from chatbot.shared.image_encoder import ImageEncoder


class OpenAIProvider:
    def __init__(self, client: OpenAI, model: str = "gpt-4o-mini") -> None:
        self._client = client
        self._model = model

    def generate_text(
        self,
        prompt: str,
        *,
        is_json: bool = False,
        temperature: float = 0.0,
        system_prompt: str | None = None,
        history: list[dict[str, Any]] | None = None,
    ) -> str:
        messages: list[dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        if history:
            messages.extend({"role": m["role"], "content": m["content"]} for m in history)
        messages.append({"role": "user", "content": prompt})

        kwargs: dict[str, Any] = {"temperature": temperature}
        if is_json:
            kwargs["response_format"] = {"type": "json_object"}

        response = self._client.chat.completions.create(
            model=self._model,
            messages=messages,
            **kwargs,
        )
        return response.choices[0].message.content or ""

    def generate_vision(
        self,
        prompt: str,
        image_bytes: bytes,
        *,
        temperature: float = 0.0,
    ) -> str:
        base64_img = ImageEncoder.encode(image_bytes)
        response = self._client.chat.completions.create(
            model=self._model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{base64_img}"},
                        },
                    ],
                }
            ],
            temperature=temperature,
        )
        return response.choices[0].message.content or ""
