import io
from typing import Any

import google.generativeai as genai
from PIL import Image

from chatbot.infrastructure.settings import Settings


class GeminiProvider:
    def __init__(self, settings: Settings, model: str = "gemini-2.5-flash") -> None:
        settings.configure_gemini()
        self._model_name = model

    def generate_text(
        self,
        prompt: str,
        *,
        is_json: bool = False,
        temperature: float = 0.0,
        system_prompt: str | None = None,
        history: list[dict[str, Any]] | None = None,
    ) -> str:
        gemini_history: list[dict[str, Any]] = []
        if history:
            for message in history:
                role = "user" if message["role"] == "user" else "model"
                if not gemini_history or gemini_history[-1]["role"] != role:
                    gemini_history.append({"role": role, "parts": [message["content"]]})
                else:
                    gemini_history[-1]["parts"][0] += f"\n\n{message['content']}"

        model = genai.GenerativeModel(model_name=self._model_name, system_instruction=system_prompt)
        chat = model.start_chat(history=gemini_history)
        kwargs: dict[str, Any] = {"temperature": temperature}
        if is_json:
            kwargs["response_mime_type"] = "application/json"

        return chat.send_message(prompt, generation_config=kwargs).text or ""

    def generate_vision(
        self,
        prompt: str,
        image_bytes: bytes,
        *,
        temperature: float = 0.0,
    ) -> str:
        image = Image.open(io.BytesIO(image_bytes))
        model = genai.GenerativeModel(self._model_name)
        response = model.generate_content(
            [prompt, image],
            generation_config={"temperature": temperature},
        )
        return response.text or ""
