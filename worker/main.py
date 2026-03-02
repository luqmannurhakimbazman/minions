"""Worker main loop — polls Redis queue and dispatches tasks to the pipeline."""

from __future__ import annotations

import asyncio
import logging

from common.redis_client import TaskStore
from worker.pipeline import BlueprintPipeline

logger = logging.getLogger(__name__)


class Worker:
    """Continuously polls the task queue and processes tasks."""

    def __init__(self, task_store: TaskStore, pipeline: BlueprintPipeline) -> None:
        self._store = task_store
        self._pipeline = pipeline
        self._running = False

    async def poll_once(self) -> bool:
        """Dequeue and process a single task.

        Returns ``True`` if a task was processed, ``False`` if the queue was empty.
        """
        task_id = await self._store.dequeue()
        if task_id is None:
            return False

        task = await self._store.get(task_id)
        if task is None:
            logger.warning("Dequeued task %s but it was not found in store", task_id)
            return False

        await self._pipeline.process_task(task)
        return True

    async def run(self) -> None:
        """Run the worker loop until ``stop()`` is called."""
        self._running = True
        logger.info("Worker started")
        while self._running:
            try:
                found = await self.poll_once()
                if not found:
                    await asyncio.sleep(0.5)
            except Exception:
                logger.exception("Error processing task")
                await asyncio.sleep(1.0)
        logger.info("Worker stopped")

    def stop(self) -> None:
        """Signal the worker loop to exit."""
        self._running = False
