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
        self.chats = self.db["chat_histories"]

    def log_interaction(self, chat_id, query, response, search_params=None, sources=None, metadata=None):
        """
        Saves interaction with structured JSON objects.
        search_params: dict (e.g., {"query": "...", "filters": [...]})
        sources: dict or list of dicts
        metadata: dict (e.g., {"model": "gpt-4", "latency": 1.2})
        """
        
        structured_sources = {str(k): v for k, v in sources.items()} if sources else {}
        structured_search = search_params if search_params else {}
        structured_metadata = metadata if metadata else {}

        now = datetime.datetime.now(datetime.timezone.utc)

        new_messages = [
            {
                "role": "user", 
                "content": query, 
                "timestamp": now
            },
            {
                "role": "assistant", 
                "content": response, 
                "sources": structured_sources, # nested obj
                "search_context": structured_search, # nested obj
                "timestamp": now
            }
        ]

        if chat_id:
            self.chats.update_one(
                {"_id": ObjectId(chat_id)},
                {
                    "$push": {"history": {"$each": new_messages}},
                    "$inc": {"summary.interaction_count": 1}
                    }
            )
            return chat_id
        else:
            chat_doc = {
                "timestamp": now,
                "summary": {
                    "last_query": query,
                    "interaction_count": 1
                },
                "config": structured_metadata,
                "history": new_messages
            }
            result = self.chats.insert_one(chat_doc)
            return str(result.inserted_id)
    
    def get_all_history(self, limit=20):
        try:
            return list(self.chats.find().sort("timestamp", -1).limit(limit))
        except Exception as e:
            print(f"Error fetching history: {e}")
            return []
    
    def get_chat_by_id(self, chat_id):
        try:
            return self.chats.find_one({"_id": ObjectId(chat_id)})
        except Exception as e:
            print(f"Error fetching specific chat: {e}")
            return None
        
    def update_eval_scores(self, chat_id, ragas_scores):
        try:
            if not chat_id:
                return
                
            if isinstance(chat_id, str):
                chat_id = ObjectId(chat_id)
                
            # current length of the history array to target the last element
            chat = self.chats.find_one({"_id": chat_id}, {"history": 1})
            if not chat or "history" not in chat:
                return

            last_index = len(chat["history"]) - 1
            
            self.chats.update_one(
                {"_id": chat_id},
                {
                    "$set": {
                        f"history.{last_index}.ragas_eval": ragas_scores,
                        f"history.{last_index}.eval_at": datetime.datetime.now(datetime.timezone.utc)
                    }
                }
            )
            print(f"updated scores for message index {last_index} in chat: {chat_id}")
        except Exception as e:
            print(f"Failed to update database: {e}")
# cache to only create 1 instance of the class
@st.cache_resource
def get_db_instance():
    return AltibbiDB()