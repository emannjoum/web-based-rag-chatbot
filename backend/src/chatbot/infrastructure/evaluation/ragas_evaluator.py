import logging
import threading
import time
from typing import Any

from chatbot.domain.ports.repository_port import ChatRepositoryPort
from chatbot.infrastructure.settings import Settings

logger = logging.getLogger(__name__)


class RagasEvaluator:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def evaluate(self, query: str, response: str, context: str) -> dict[str, float] | None:
        if not self._settings.openai_api_key:
            logger.info("Ragas skipped: missing OPENAI_API_KEY")
            return None

        # Large contexts and transient OpenAI errors can cause intermittent failures.
        # Keep evaluation resilient with bounded context and retries.
        bounded_context = context[:12000] if context else ""
        max_attempts = 3
        backoff_seconds = 1.5

        for attempt in range(1, max_attempts + 1):
            try:
                from datasets import Dataset
                from langchain_openai import ChatOpenAI, OpenAIEmbeddings
                from ragas import evaluate
                from ragas.embeddings import LangchainEmbeddingsWrapper
                from ragas.llms import LangchainLLMWrapper
                from ragas.metrics import answer_relevancy, faithfulness

                llm = LangchainLLMWrapper(
                    ChatOpenAI(
                        model="gpt-4o-mini",
                        api_key=self._settings.openai_api_key,
                        timeout=45,
                    )
                )
                embeddings = LangchainEmbeddingsWrapper(
                    OpenAIEmbeddings(
                        model="text-embedding-3-small",
                        api_key=self._settings.openai_api_key,
                    )
                )
                dataset = Dataset.from_dict(
                    {
                        "question": [query],
                        "answer": [response],
                        "contexts": [[bounded_context]],
                    }
                )
                result = evaluate(
                    dataset,
                    metrics=[faithfulness, answer_relevancy],
                    llm=llm,
                    embeddings=embeddings,
                )
                return result.to_pandas().to_dict(orient="records")[0]
            except Exception:
                logger.warning(
                    "Ragas evaluation failed (attempt %s/%s).",
                    attempt,
                    max_attempts,
                    exc_info=True,
                )
                if attempt < max_attempts:
                    time.sleep(backoff_seconds * attempt)
                    continue
                return None

    def process_async(
        self,
        repository: ChatRepositoryPort,
        message_id: Any,
        query: str,
        response: str,
        context: str,
    ) -> None:
        try:
            scores = self.evaluate(query, response, context)
            if scores is None:
                repository.update_eval_scores(message_id, None, "failed")
            else:
                repository.update_eval_scores(message_id, scores, "success")
        except Exception as exc:
            logger.warning("Async Ragas evaluation failed: %s", exc)
            repository.update_eval_scores(message_id, None, "failed")

    def trigger_async(
        self,
        repository: ChatRepositoryPort,
        message_id: Any,
        query: str,
        response: str,
        context: str,
    ) -> None:
        eval_thread = threading.Thread(
            target=self.process_async,
            args=(repository, message_id, query, response, context),
            daemon=True,
        )
        eval_thread.start()
