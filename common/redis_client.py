"""Redis-backed task store with CRUD, queue, and log operations."""

from __future__ import annotations

import json
from typing import Optional

from redis.asyncio import Redis

from common.models import Task, TaskStatus

TASK_KEY_PREFIX = "minions:task:"
TASK_INDEX_KEY = "minions:tasks"
QUEUE_KEY = "minions:queue"


class TaskStore:
    """Wraps async Redis to provide task persistence and a simple work queue."""

    def __init__(self, redis: Redis) -> None:
        self._r = redis

    # ---- CRUD ----

    async def save(self, task: Task) -> None:
        """Persist a task as a Redis hash and add its id to the index set."""
        key = f"{TASK_KEY_PREFIX}{task.id}"
        await self._r.set(key, task.model_dump_json())
        await self._r.sadd(TASK_INDEX_KEY, str(task.id))

    async def get(self, task_id: str) -> Optional[Task]:
        """Retrieve a task by id, or None if not found."""
        key = f"{TASK_KEY_PREFIX}{task_id}"
        data = await self._r.get(key)
        if data is None:
            return None
        return Task.model_validate_json(data)

    async def list_tasks(self) -> list[Task]:
        """Return all stored tasks."""
        ids = await self._r.smembers(TASK_INDEX_KEY)
        tasks = []
        for task_id in ids:
            task = await self.get(task_id)
            if task is not None:
                tasks.append(task)
        return tasks

    async def update_status(self, task_id: str, status: TaskStatus) -> None:
        """Update only the status field of an existing task."""
        task = await self.get(task_id)
        if task is None:
            raise KeyError(f"Task {task_id} not found")
        task.status = status
        await self.save(task)

    # ---- Queue (Redis List) ----

    async def enqueue(self, task_id: str) -> None:
        """Push a task id onto the work queue."""
        await self._r.lpush(QUEUE_KEY, task_id)

    async def dequeue(self) -> Optional[str]:
        """Pop the next task id from the work queue, or None if empty."""
        result = await self._r.rpop(QUEUE_KEY)
        return result

    # ---- Logs ----

    async def append_log(self, task_id: str, message: str) -> None:
        """Append a log line to a task's logs list."""
        task = await self.get(task_id)
        if task is None:
            raise KeyError(f"Task {task_id} not found")
        task.logs.append(message)
        await self.save(task)
