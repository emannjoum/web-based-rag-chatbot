from typing import Any

from chatbot.application.dependencies import DependencyContainer
from chatbot.domain.exceptions import SearchError
from chatbot.domain.models import ImageHandlingResult, PipelineResult
from chatbot.domain.ports.llm_port import LLMPort


class ChatService:
    """High-level use cases for text queries and image processing workflows."""

    UNSUPPORTED_IMAGE_MESSAGE = (
        "هذا النوع من الصور غير مدعوم. يرجى رفع صورة لتحاليل طبية أو دواء."
    )

    def __init__(self, container: DependencyContainer) -> None:
        self._container = container

    def handle_text_query(
        self,
        query: str,
        chat_history: list[dict[str, Any]],
        session_id: str | None,
        model_choice: str,
        search_method: str,
        *,
        is_drug_profile: bool = False,
    ) -> PipelineResult:
        llm_provider = self._container.create_llm_provider(model_choice)
        search_provider = self._container.create_search_provider(search_method)

        try:
            pipeline_result = self._container.rag_pipeline.execute(
                query,
                chat_history,
                llm_provider,
                search_provider,
                is_drug_profile=is_drug_profile,
                model_label=model_choice,
                search_method_label=search_method,
            )
        except SearchError:
            raise

        new_session_id, message_id = self._container.persist_pipeline_result(
            session_id,
            query,
            pipeline_result,
        )

        if pipeline_result.search_result and pipeline_result.status == "success":
            self._container.query_logger.log(
                query=query,
                last_question=pipeline_result.metadata.get("refined_query", query),
                all_urls=pipeline_result.search_result.raw_urls,
                filtered_sources=pipeline_result.sources,
                raw_context=pipeline_result.search_result.context,
                response=pipeline_result.response,
            )
            self._container.evaluator.trigger_async(
                self._container.repository,
                message_id,
                query,
                pipeline_result.response,
                pipeline_result.search_result.context,
            )

        return PipelineResult(
            response=pipeline_result.response,
            sources=pipeline_result.sources,
            suggestions=pipeline_result.suggestions,
            metadata=pipeline_result.metadata,
            session_id=new_session_id,
            message_id=message_id,
            status=pipeline_result.status,
            refine_result=pipeline_result.refine_result,
            search_result=pipeline_result.search_result,
        )

    def handle_image_upload(
        self,
        image_bytes: bytes,
        filename: str,
        caption: str | None,
        model_choice: str,
    ) -> ImageHandlingResult:
        user_message = f"[Uploaded an Image: {filename}]"
        if caption:
            user_message += f" (Message: {caption})"

        llm_provider = self._container.create_llm_provider(model_choice)
        image_type = self._classify_image(image_bytes, llm_provider)

        if image_type not in {"report", "drug"}:
            return ImageHandlingResult(
                status="unsupported",
                user_message=user_message,
                assistant_response=self.UNSUPPORTED_IMAGE_MESSAGE,
            )

        if image_type == "report":
            report_prompt = self._container.prompt_loader.load_section("image", "report_analysis")
            if caption:
                report_prompt += f"\n\nUser's specific request/question: {caption}"
            
            assistant_response = llm_provider.generate_vision(
                report_prompt,
                image_bytes,
                temperature=0.2,
            )
            return ImageHandlingResult(
                status="report",
                user_message=user_message,
                assistant_response=assistant_response,
            )

        extraction_prompt = self._container.prompt_loader.load_section("image", "drug_extraction")
        drug_query = self._extract_drug_name(image_bytes, llm_provider, extraction_prompt)
        return ImageHandlingResult(
            status="drug",
            user_message=user_message,
            drug_query=drug_query,
        )

    def persist_simple_exchange(
        self,
        session_id: str | None,
        user_message: str,
        assistant_response: str,
        metadata: dict[str, Any],
    ) -> str:
        new_session_id, _ = self._container.repository.log_interaction(
            session_id,
            user_message,
            assistant_response,
            metadata=metadata,
        )
        return new_session_id

    def _classify_image(self, image_bytes: bytes, llm_provider: LLMPort) -> str:
        classification_prompt = self._container.prompt_loader.load_section("image", "classification")
        try:
            return llm_provider.generate_vision(classification_prompt, image_bytes).strip().lower()
        except Exception as exc:
            print(f"Classification Error: {exc}")
            return "unsupported"

    def _extract_drug_name(
        self,
        image_bytes: bytes,
        llm_provider: LLMPort,
        extraction_prompt: str,
    ) -> str:
        try:
            return llm_provider.generate_vision(extraction_prompt, image_bytes).strip()
        except Exception as exc:
            print(f"Extraction Error: {exc}")
            return "Unknown Medication"
