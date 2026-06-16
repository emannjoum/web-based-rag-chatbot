import threading
from typing import Any

from datasets import Dataset
from langchain_openai import ChatOpenAI
from ragas import evaluate
from ragas.metrics import answer_relevancy, faithfulness

from chatbot.domain.ports.repository_port import ChatRepositoryPort
from chatbot.infrastructure.settings import Settings


class RagasEvaluator:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def evaluate(self, query: str, response: str, context: str) -> dict[str, float]:
        try:
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
            return {"faithfulness": 0.0, "answer_relevancy": 0.0}

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
            repository.update_eval_scores(message_id, scores)
        except Exception as exc:
            print(f"Async Eval Error: {exc}")

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
