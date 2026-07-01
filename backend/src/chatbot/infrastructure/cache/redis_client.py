"""Redis client factory with graceful degradation when Redis is unavailable."""

from __future__ import annotations

import logging

import redis

logger = logging.getLogger(__name__)


def create_redis_client(redis_url: str) -> redis.Redis | None:
    try:
        client = redis.Redis.from_url(
            redis_url,
            decode_responses=True,
            socket_connect_timeout=2,
            socket_timeout=2,
        )
        client.ping()
        logger.info("Connected to Redis at %s", redis_url)
        return client
    except Exception as exc:
        logger.warning("Redis unavailable (%s). Continuing without cache.", exc)
        return None
