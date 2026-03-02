"""Tests for worker.main — Worker polling loop."""

from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from common.models import Task
from worker.main import Worker


@pytest.fixture
def task_store():
    return AsyncMock()


@pytest.fixture
def pipeline():
    return AsyncMock()


@pytest.fixture
def worker(task_store, pipeline):
    return Worker(task_store, pipeline)


class TestPollOnce:
    @pytest.mark.asyncio
    async def test_processes_queued_task(self, worker, task_store, pipeline):
        task_id = str(uuid4())
        task = Task(id=task_id, description="Do something", repo="https://github.com/x/y.git")

        task_store.dequeue.return_value = task_id
        task_store.get.return_value = task

        result = await worker.poll_once()

        assert result is True
        task_store.dequeue.assert_awaited_once()
        task_store.get.assert_awaited_once_with(task_id)
        pipeline.process_task.assert_awaited_once_with(task)

    @pytest.mark.asyncio
    async def test_returns_false_when_queue_empty(self, worker, task_store, pipeline):
        task_store.dequeue.return_value = None

        result = await worker.poll_once()

        assert result is False
        pipeline.process_task.assert_not_awaited()
