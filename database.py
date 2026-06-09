import os
import datetime
from pymongo import MongoClient
import streamlit as st
from dotenv import load_dotenv
from bson.objectid import ObjectId

load_dotenv()

class AltibbiDB:
    def __init__(self):
        uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
        self.client = MongoClient(uri)
        self.db = self.client["altibbi_db"]
        self.messages_col = self.db["chat_messages"]

    def log_interaction(self, session_id, query, response, search_params=None, sources=None, metadata=None):
        if not session_id:
            session_id = str(ObjectId())

        structured_sources = {str(k): v for k, v in sources.items()} if sources else {}
        structured_search = search_params if search_params else {}
        structured_metadata = metadata if metadata else {}

        now = datetime.datetime.now(datetime.timezone.utc)

        user_doc = {
            "session_id": session_id,
            "role": "user",
            "timestamp": now,
            "content": query,
            "is_delete": 0
        }

        model_doc = {
            "session_id": session_id,
            "role": "assistant",
            "timestamp": now,
            "content": response,
            "sources": structured_sources,
            "config": structured_metadata, # language + chat_title
            "extra": {},
            "is_delete": 0
        }

        result = self.messages_col.insert_many([user_doc, model_doc])
        return session_id, result.inserted_ids[1] # sesh id + unique id of assitant's message
    
    def get_all_history(self, limit=20):
        try:
            pipeline = [
                {"$match": {"is_delete": {"$ne": 1}}},
                {"$sort": {"timestamp": -1}},
                {
                    "$group": {
                        "_id": "$session_id",
                        "last_active": {"$first": "$timestamp"},
                        "last_preview": {"$first": "$content"},
                        "chat_title": {"$max": "$config.chat_title"} 
                    }
                },
                {"$sort": {"last_active": -1}},
                {"$limit": limit}
            ]
            return list(self.messages_col.aggregate(pipeline))
        except Exception as e:
            print(f"Error fetching history: {e}")
            return []
    
    def get_chat_by_id(self, session_id):
            return list(self.messages_col.find({
                "session_id": session_id,
                "is_delete": {"$ne": 1} 
            }).sort("timestamp", 1))
        
    def update_eval_scores(self, message_id, ragas_scores):
        try:
            if not message_id:
                return

            self.messages_col.update_one(
                {"_id": ObjectId(message_id) if isinstance(message_id, str) else message_id},
                {
                    "$set": {
                        "ragas_eval": ragas_scores,
                        "eval_at": datetime.datetime.now(datetime.timezone.utc)
                    }
                }
            )
            print(f"Updated evaluation scores for message document: {message_id}")
        except Exception as e:
            print(f"Failed to update database: {e}")

    def delete_chat(self, session_id):
            result = self.messages_col.update_many(
                {"session_id": session_id},
                {"$set": {"is_delete": 1}}
            )
            print(f"Deleted {result.modified_count} messages for session: {session_id}")
            return True

@st.cache_resource
def get_db_instance():
    return AltibbiDB()