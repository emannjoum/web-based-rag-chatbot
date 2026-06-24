"""Redis-backed cache helpers for chat history."""

from __future__ import annotations

import datetime
import json
import logging
from typing import Any

from bson.objectid import ObjectId

logger = logging.getLogger(__name__)

SESSION_KEY_PREFIX = "chat:session:"
HISTORY_KEY_PREFIX = "chat:history:"


def _json_default(value: Any) -> Any:
    if isinstance(value, ObjectId):
        return str(value)
    if isinstance(value, datetime.datetime):
        return value.isoformat()
    raise TypeError(f"Object of type {type(value)!r} is not JSON serializable")


def serialize_documents(documents: list[dict[str, Any]]) -> str:
    return json.dumps(documents, default=_json_default)


def deserialize_documents(payload: str) -> list[dict[str, Any]]:
    return json.loads(payload)


def session_cache_key(session_id: str) -> str:
    return f"{SESSION_KEY_PREFIX}{session_id}"


def history_cache_key(limit: int) -> str:
    return f"{HISTORY_KEY_PREFIX}{limit}"
