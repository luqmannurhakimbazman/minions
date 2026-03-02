"""FastAPI dependency providers."""

from redis.asyncio import Redis

from common.config import get_settings
from common.redis_client import TaskStore


async def get_task_store() -> TaskStore:
    """Provide a TaskStore instance backed by the configured Redis."""
    settings = get_settings()
    redis = Redis.from_url(settings.redis_url, decode_responses=True)
    return TaskStore(redis)
