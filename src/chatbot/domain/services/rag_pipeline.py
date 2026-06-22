import json
from typing import Any

from chatbot.domain.exceptions import SearchError
from chatbot.domain.language import LanguageResolver
from chatbot.domain.models import PipelineResult, RefineResult, SearchResult
from chatbot.domain.prompts.loader import PromptLoader
from chatbot.domain.services.citation_filter import CitationFilter
from chatbot.domain.services.query_refiner import QueryRefiner
from chatbot.domain.ports.llm_port import LLMPort
from chatbot.domain.ports.search_port import SearchPort
from chatbot.shared.json_parser import JsonParser
from chatbot.shared.text_cleaner import TextCleaner


class RAGPipeline:
    def __init__(
        self,
        query_refiner: QueryRefiner,
        prompt_loader: PromptLoader,
    ) -> None:
        self._query_refiner = query_refiner
        self._prompt_loader = prompt_loader

    def execute(
        self,
        query: str,
        chat_history: list[dict[str, Any]],
        llm_provider: LLMPort,
        search_provider: SearchPort,
        *,
        is_drug_profile: bool = False,
        model_label: str = "",
        search_method_label: str = "",
    ) -> PipelineResult:
        refine_result = self._query_refiner.refine(query, chat_history, llm_provider)

        metadata = self._build_metadata(
            refine_result=refine_result,
            model_label=model_label,
            search_method_label=search_method_label,
        )

        if not refine_result.needs_search:
            search_result = SearchResult(
                context="The user is asking a follow-up question regarding the conversation history or an uploaded image. Please answer based strictly on the provided history.",
                sources={},
                raw_urls=[]
            )
        else:
            try:
                search_result = search_provider.search(refine_result.refined_query)
            except SearchError as exc:
                raise exc

            if not search_result.has_sources:
                fallback_response = self._generate_fallback(query, refine_result.language, llm_provider)
                metadata["status"] = "fallback"
                return PipelineResult(
                    response=fallback_response,
                    sources={},
                    suggestions=[],
                    metadata=metadata,
                    session_id=None,
                    message_id=None,
                    status="fallback",
                    refine_result=refine_result,
                    search_result=search_result,
                )

        target_lang = LanguageResolver.resolve_target_language(refine_result.language)
        system_prompt = self._prompt_loader.build_system_prompt(
            TextCleaner.clean(search_result.context),
            refine_result.language,
            target_lang,
        )
        user_prompt = (
            self._prompt_loader.build_drug_prompt(query, refine_result.language)
            if is_drug_profile
            else f"Please provide medical information about: {query}"
        )

        ai_reply = llm_provider.generate_text(
            user_prompt,
            system_prompt=system_prompt,
            history=chat_history,
        )
        used_sources = CitationFilter.filter_sources(search_result.sources, ai_reply)
        suggestions = self._generate_follow_ups(query, ai_reply, refine_result.language, llm_provider)
        metadata["status"] = "success"

        return PipelineResult(
            response=ai_reply,
            sources=used_sources,
            suggestions=suggestions,
            metadata=metadata,
            session_id=None,
            message_id=None,
            status="success",
            refine_result=refine_result,
            search_result=search_result,
        )

    def _build_metadata(
        self,
        refine_result: RefineResult,
        model_label: str,
        search_method_label: str,
    ) -> dict[str, Any]:
        return {
            "model": model_label,
            "method": search_method_label,
            "chat_title": refine_result.chat_title,
            "language": refine_result.language,
            "refined_query": refine_result.refined_query,
        }

    def _generate_fallback(
        self,
        user_query: str,
        language: str,
        llm_provider: LLMPort,
    ) -> str:
        target_lang = LanguageResolver.resolve_bilingual_language(language)
        system_prompt = self._prompt_loader.build_fallback_prompt(target_lang)
        user_prompt = f"USER'S QUERY: {user_query}"
        try:
            return llm_provider.generate_text(
                user_prompt,
                temperature=0.6,
                system_prompt=system_prompt,
            )
        except Exception:
            if "ar" in target_lang.lower():
                return (
                    f"لم أتمكن من العثور على معلومات محددة حول '{user_query}' في الطبي حالياً. "
                    "هل يمكنك إخباري بالمزيد من التفاصيل أو الأعراض المرافقة لمساعدتك بشكل أفضل؟"
                )
            return (
                f"I couldn't find matching articles for '{user_query}' right now. "
                "Could you share more details or symptoms so I can better assist you?"
            )

    def _generate_follow_ups(
        self,
        user_query: str,
        ai_response: str,
        language: str,
        llm_provider: LLMPort,
    ) -> list[str]:
        target_lang = LanguageResolver.resolve_bilingual_language(language)
        prompt = self._prompt_loader.build_follow_ups_prompt(user_query, ai_response, target_lang)
        try:
            content = llm_provider.generate_text(prompt, is_json=True, temperature=0.6)
            parsed_data = JsonParser.safe_parse(JsonParser.strip_fences(content))
            suggestions = parsed_data.get("suggestions", [])
            if isinstance(suggestions, list):
                return suggestions[:3]
            return []
        except Exception as exc:
            print(f"Follow-up Error: {exc}")
            return []
