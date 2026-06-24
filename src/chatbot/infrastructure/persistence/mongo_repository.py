import datetime
from typing import Any

from bson.objectid import ObjectId
from pymongo import MongoClient

from chatbot.domain.exceptions import PersistenceError


class MongoChatRepository:
    def __init__(self, mongodb_uri: str, database_name: str = "altibbi_db") -> None:
        self._client = MongoClient(mongodb_uri)
        self._messages_col = self._client[database_name]["chat_messages"]

    def log_interaction(
        self,
        session_id: str | None,
        query: str,
        response: str,
        search_params: dict[str, Any] | None = None,
        sources: dict | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> tuple[str, Any]:
        if not session_id:
            session_id = str(ObjectId())

        structured_sources = {str(key): value for key, value in sources.items()} if sources else {}
        structured_search = search_params or {}
        structured_metadata = metadata or {}
        now = datetime.datetime.now(datetime.timezone.utc)

        user_doc = {
            "session_id": session_id,
            "role": "user",
            "timestamp": now,
            "content": query,
            "is_delete": 0,
        }
        model_doc = {
            "session_id": session_id,
            "role": "assistant",
            "timestamp": now,
            "content": response,
            "sources": structured_sources,
            "config": structured_metadata,
            "is_delete": 0,
        }

        try:
            result = self._messages_col.insert_many([user_doc, model_doc])
        except Exception as exc:
            raise PersistenceError(f"Failed to log interaction for session '{session_id}': {exc}") from exc

        return session_id, result.inserted_ids[1]

    def get_all_history(self, limit: int = 20) -> list[dict[str, Any]]:
        try:
            pipeline = [
                {"$match": {"is_delete": {"$ne": 1}}},
                {"$sort": {"timestamp": -1}},
                {
                    "$group": {
                        "_id": "$session_id",
                        "last_active": {"$first": "$timestamp"},
                        "last_preview": {"$first": "$content"},
                        "chat_title": {"$max": "$config.chat_title"},
                    }
                },
                {"$sort": {"last_active": -1}},
                {"$limit": limit},
            ]
            return list(self._messages_col.aggregate(pipeline))
        except Exception as exc:
            print(f"Error fetching history: {exc}")
            return []

    def get_chat_by_id(self, session_id: str) -> list[dict[str, Any]]:
        return list(
            self._messages_col.find({"session_id": session_id, "is_delete": {"$ne": 1}}).sort(
                "timestamp", 1
            )
        )

    def update_eval_scores(self, message_id: Any, ragas_scores: dict[str, Any]) -> None:
        if not message_id:
            return

        try:
            object_id = ObjectId(message_id) if isinstance(message_id, str) else message_id
            self._messages_col.update_one(
                {"_id": object_id},
                {
                    "$set": {
                        "ragas_eval": ragas_scores,
                        "eval_at": datetime.datetime.now(datetime.timezone.utc),
                    }
                },
            )
            print(f"Updated evaluation scores for message document: {message_id}")
        except Exception as exc:
            print(f"Failed to update database: {exc}")

    def delete_chat(self, session_id: str) -> bool:
        result = self._messages_col.update_many(
            {"session_id": session_id},
            {"$set": {"is_delete": 1}},
        )
        print(f"Deleted {result.modified_count} messages for session: {session_id}")
        return True

    def find_session_id_for_message(self, message_id: Any) -> str | None:
        try:
            object_id = ObjectId(message_id) if isinstance(message_id, str) else message_id
            doc = self._messages_col.find_one({"_id": object_id}, {"session_id": 1})
            if not doc:
                return None
            return str(doc.get("session_id"))
        except Exception as exc:
            print(f"Failed to resolve session for message {message_id}: {exc}")
            return None


# Backward-compatible alias
AltibbiDB = MongoChatRepository
