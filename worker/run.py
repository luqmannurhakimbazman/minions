"""Async entrypoint for the worker process."""

import asyncio

from redis.asyncio import Redis

from common.config import get_settings
from common.redis_client import TaskStore
from worker.container_manager import ContainerManager
from worker.main import Worker
from worker.pipeline import BlueprintPipeline


async def main():
    settings = get_settings()
    redis = Redis.from_url(settings.redis_url)
    store = TaskStore(redis)
    container_mgr = ContainerManager(settings)
    pipeline = BlueprintPipeline(store, container_mgr, settings)
    worker = Worker(store, pipeline)
    try:
        await worker.run()
    finally:
        await redis.aclose()


if __name__ == "__main__":
    asyncio.run(main())
