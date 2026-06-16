import json
from typing import Any

from chatbot.domain.language import LanguageResolver
from chatbot.domain.models import RefineResult
from chatbot.domain.prompts.loader import PromptLoader
from chatbot.domain.ports.llm_port import LLMPort
from chatbot.shared.json_parser import JsonParser


class QueryRefiner:
    def __init__(self, prompt_loader: PromptLoader) -> None:
        self._prompt_loader = prompt_loader

    def refine(
        self,
        user_query: str,
        chat_history: list[dict[str, Any]],
        llm_provider: LLMPort,
    ) -> RefineResult:
        history_str = (
            "\n".join(f"{message['role']}: {message['content']}" for message in chat_history[-3:])
            if chat_history
            else "No previous history."
        )
        prompt = self._prompt_loader.build_refine_prompt(history_str, user_query)
        content = llm_provider.generate_text(prompt, is_json=True, temperature=0.0)

        default = {
            "refined_query": user_query,
            "language": "ar",
            "chat_title": user_query[:30],
        }
        try:
            parsed_json = JsonParser.safe_parse(content, default=default)
        except json.JSONDecodeError:
            parsed_json = default

        print("\nExtracted JSON (Query Refiner)")
        print(json.dumps(parsed_json, indent=2, ensure_ascii=False))

        return RefineResult(
            chat_title=parsed_json.get("chat_title", user_query[:30]),
            refined_query=parsed_json.get("refined_query", user_query),
            language=parsed_json.get("language", "ar"),
        )
