import threading
from typing import Any

from chatbot.domain.ports.repository_port import ChatRepositoryPort
from chatbot.infrastructure.settings import Settings


class RagasEvaluator:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def evaluate(self, query: str, response: str, context: str) -> dict[str, float] | None:
        if not self._settings.openai_api_key:
            print("Ragas skipped: missing OPENAI_API_KEY")
            return None

        try:
            # Import lazily so missing optional ragas dependencies
            # do not prevent API/container startup.
            from datasets import Dataset
            from langchain_openai import ChatOpenAI
            from ragas import evaluate
            from ragas.metrics import answer_relevancy, faithfulness

            eval_llm = ChatOpenAI(model="gpt-4o-mini", api_key=self._settings.openai_api_key)
            dataset = Dataset.from_dict(
                {
                    "question": [query],
                    "answer": [response],
                    "contexts": [[context]],
                }
            )
            result = evaluate(dataset, metrics=[faithfulness, answer_relevancy], llm=eval_llm)
            return result.to_pandas().to_dict(orient="records")[0]
        except Exception as exc:
            print(f"Ragas Error: {exc}")
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
            print(f"Async Eval Error: {exc}")
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
        )
        eval_thread.start()
