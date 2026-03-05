import redis
import json
from typing import Any, Optional

# Initialize Redis connection
# Using db=1 to separate from Celery (which uses db=0)
redis_client = redis.Redis(
    host='localhost',
    port=6379,
    db=1,
    decode_responses=True  # Return strings instead of bytes
)


def get_device_state(entity_name: str) -> Optional[dict]:
    """Get cached device state"""
    data = redis_client.hgetall(f"device:{entity_name}")
    return data if data else None


def set_device_state(entity_name: str, state: dict, expire_seconds: int = 300) -> None:
    """Cache device state with optional expiration"""
    key = f"device:{entity_name}"
    redis_client.hset(key, mapping=state)
    if expire_seconds:
        redis_client.expire(key, expire_seconds)


def add_command_history(command: str, max_history: int = 100) -> None:
    """Add command to history list"""
    redis_client.lpush("command_history", command)
    redis_client.ltrim("command_history", 0, max_history - 1)


def get_command_history(count: int = 10) -> list:
    """Get recent commands"""
    return redis_client.lrange("command_history", 0, count - 1)


def cache_llm_response(command: str, response: dict, expire_seconds: int = 3600) -> None:
    """Cache LLM response to avoid duplicate API calls"""
    key = f"llm_cache:{hash(command)}"
    redis_client.set(key, json.dumps(response), ex=expire_seconds)


def get_cached_llm_response(command: str) -> Optional[dict]:
    """Get cached LLM response if exists"""
    key = f"llm_cache:{hash(command)}"
    data = redis_client.get(key)
    return json.loads(data) if data else None
