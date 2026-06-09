import threading
from datasets import Dataset
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy
from langchain_openai import ChatOpenAI
from config import OPENAI_API_KEY

def evaluate_with_ragas(query, response, context):
    try:
        eval_llm = ChatOpenAI(model="gpt-4o-mini", api_key=OPENAI_API_KEY)
        data_sample = {  
            "question": [query],
            "answer": [response],
            "contexts": [[context]] 
        }
        dataset = Dataset.from_dict(data_sample)
        
        result = evaluate(
            dataset,
            metrics=[faithfulness, answer_relevancy],
            llm=eval_llm
        )
        return result.to_pandas().to_dict(orient="records")[0]
    except Exception as e:
        print(f"Ragas Error: {e}")
        return {"faithfulness": 0.0, "answer_relevancy": 0.0}

def process_eval_async(db_instance, chat_id, query, response, context):
    """
    Background worker that runs the evaluation and updates the database.
    """
    try:
        scores = evaluate_with_ragas(query, response, context)
        db_instance.update_eval_scores(chat_id, scores)
    except Exception as e:
        print(f"Async Eval Error: {e}")

def trigger_eval(db_instance, chat_id, query, response, context):
    """
    Entry point to trigger the evaluation in a non-blocking thread.
    """
    eval_thread = threading.Thread(
        target=process_eval_async,
        args=(db_instance, chat_id, query, response, context)
    )
    eval_thread.start()