"""Tests for worker.pipeline — BlueprintPipeline orchestration."""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from common.config import Settings
from common.models import Task, TaskStatus
from worker.pipeline import BlueprintPipeline


@pytest.fixture
def settings():
    return Settings(max_retries=3)


@pytest.fixture
def task_store():
    store = AsyncMock()
    return store


@pytest.fixture
def container_manager():
    return MagicMock()


@pytest.fixture
def pipeline(task_store, container_manager, settings):
    return BlueprintPipeline(task_store, container_manager, settings)


@pytest.fixture
def task():
    return Task(
        id=uuid4(),
        description="Add dark mode support",
        repo="https://github.com/example/repo.git",
    )


class TestProcessTaskSuccess:
    @pytest.mark.asyncio
    async def test_task_ends_up_completed(self, pipeline, task, task_store, container_manager):
        with patch(
            "worker.pipeline.prefetch",
            return_value={
                "tree": [],
                "relevant_files": [],
                "git_log": [],
            },
        ):
            container_manager.run.return_value = {"exit_code": 0, "logs": "ok"}
            await pipeline.process_task(task)

        # Final status should be COMPLETED
        task_store.save.assert_called()
        last_saved_task = task_store.save.call_args_list[-1][0][0]
        assert last_saved_task.status == TaskStatus.COMPLETED


class TestFailureTriggersRetry:
    @pytest.mark.asyncio
    async def test_task_retries_on_failure(self, pipeline, task, task_store, container_manager):
        task.retries = 0
        with patch(
            "worker.pipeline.prefetch",
            return_value={
                "tree": [],
                "relevant_files": [],
                "git_log": [],
            },
        ):
            container_manager.run.return_value = {"exit_code": 1, "logs": "error"}
            await pipeline.process_task(task)

        last_saved_task = task_store.save.call_args_list[-1][0][0]
        assert last_saved_task.status == TaskStatus.RETRYING
        assert last_saved_task.retries == 1


class TestExhaustsRetries:
    @pytest.mark.asyncio
    async def test_task_fails_when_retries_exhausted(
        self,
        pipeline,
        task,
        task_store,
        container_manager,
        settings,
    ):
        task.retries = settings.max_retries
        with patch(
            "worker.pipeline.prefetch",
            return_value={
                "tree": [],
                "relevant_files": [],
                "git_log": [],
            },
        ):
            container_manager.run.return_value = {"exit_code": 1, "logs": "error"}
            await pipeline.process_task(task)

        last_saved_task = task_store.save.call_args_list[-1][0][0]
        assert last_saved_task.status == TaskStatus.FAILED


class TestStatusTransitions:
    @pytest.mark.asyncio
    async def test_prefetching_and_running_statuses_are_set(
        self,
        pipeline,
        task,
        task_store,
        container_manager,
    ):
        statuses_seen: list[TaskStatus] = []

        async def capture_save(t: Task) -> None:
            statuses_seen.append(t.status)

        task_store.save.side_effect = capture_save

        with patch(
            "worker.pipeline.prefetch",
            return_value={
                "tree": [],
                "relevant_files": [],
                "git_log": [],
            },
        ):
            container_manager.run.return_value = {"exit_code": 0, "logs": "ok"}
            await pipeline.process_task(task)

        assert TaskStatus.PREFETCHING in statuses_seen
        assert TaskStatus.RUNNING in statuses_seen
        assert TaskStatus.COMPLETED in statuses_seen


class TestMetricsInstrumentation:
    @pytest.mark.asyncio
    async def test_completed_counter_incremented(
        self,
        pipeline,
        task,
        task_store,
        container_manager,
    ):
        from monitoring.metrics import TASKS_COMPLETED

        before = TASKS_COMPLETED._value.get()
        with patch(
            "worker.pipeline.prefetch",
            return_value={
                "tree": [],
                "relevant_files": [],
                "git_log": [],
            },
        ):
            container_manager.run.return_value = {"exit_code": 0, "logs": "ok"}
            await pipeline.process_task(task)
        after = TASKS_COMPLETED._value.get()
        assert after - before == 1

    @pytest.mark.asyncio
    async def test_failed_counter_incremented(
        self,
        pipeline,
        task,
        task_store,
        container_manager,
        settings,
    ):
        from monitoring.metrics import TASKS_FAILED

        task.retries = settings.max_retries
        before = TASKS_FAILED._value.get()
        with patch(
            "worker.pipeline.prefetch",
            return_value={
                "tree": [],
                "relevant_files": [],
                "git_log": [],
            },
        ):
            container_manager.run.return_value = {"exit_code": 1, "logs": "error"}
            await pipeline.process_task(task)
        after = TASKS_FAILED._value.get()
        assert after - before == 1

    @pytest.mark.asyncio
    async def test_retry_counter_incremented(self, pipeline, task, task_store, container_manager):
        from monitoring.metrics import RETRIES_TOTAL

        task.retries = 0
        before = RETRIES_TOTAL._value.get()
        with patch(
            "worker.pipeline.prefetch",
            return_value={
                "tree": [],
                "relevant_files": [],
                "git_log": [],
            },
        ):
            container_manager.run.return_value = {"exit_code": 1, "logs": "error"}
            await pipeline.process_task(task)
        after = RETRIES_TOTAL._value.get()
        assert after - before == 1
