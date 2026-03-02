"""BlueprintPipeline — orchestrates prefetch, container spawn, and retry logic."""

from __future__ import annotations

from common.config import Settings
from common.models import Task, TaskStatus
from common.redis_client import TaskStore
from prefetcher.collect import prefetch
from worker.container_manager import ContainerManager


class BlueprintPipeline:
    """Runs the full task lifecycle: prefetch -> container -> status update."""

    def __init__(
        self,
        task_store: TaskStore,
        container_manager: ContainerManager,
        settings: Settings,
    ) -> None:
        self._store = task_store
        self._cm = container_manager
        self._settings = settings

    async def process_task(self, task: Task) -> None:
        """Execute the full pipeline for a single task."""
        # 1. Prefetch context
        task.status = TaskStatus.PREFETCHING
        await self._store.save(task)

        context = prefetch(task.repo, task.description)

        # 2. Run agent container
        task.status = TaskStatus.RUNNING
        await self._store.save(task)

        result = self._cm.run(task, context)

        # 3. Handle outcome
        if result["exit_code"] == 0:
            task.status = TaskStatus.COMPLETED
            await self._store.save(task)
        else:
            await self._handle_failure(task)

    async def _handle_failure(self, task: Task) -> None:
        """Retry the task or mark it as failed."""
        if task.retries >= self._settings.max_retries:
            task.status = TaskStatus.FAILED
        else:
            task.retries += 1
            task.status = TaskStatus.RETRYING
        await self._store.save(task)
