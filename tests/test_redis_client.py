"""Tests for common.redis_client — TaskStore with Redis CRUD and queue."""

import pytest
import fakeredis.aioredis

from common.models import Task, TaskStatus
from common.redis_client import TaskStore


@pytest.fixture
async def store():
    redis = fakeredis.aioredis.FakeRedis(decode_responses=True)
    s = TaskStore(redis)
    yield s
    await redis.aclose()


@pytest.fixture
def sample_task():
    return Task(description="Fix login bug", repo="acme/webapp")


class TestTaskStoreCRUD:
    async def test_save_and_get(self, store, sample_task):
        await store.save(sample_task)
        retrieved = await store.get(str(sample_task.id))
        assert retrieved is not None
        assert retrieved.id == sample_task.id
        assert retrieved.description == sample_task.description
        assert retrieved.repo == sample_task.repo

    async def test_get_nonexistent_returns_none(self, store):
        result = await store.get("00000000-0000-0000-0000-000000000000")
        assert result is None

    async def test_list_tasks(self, store):
        t1 = Task(description="task 1", repo="r")
        t2 = Task(description="task 2", repo="r")
        await store.save(t1)
        await store.save(t2)
        tasks = await store.list_tasks()
        ids = {t.id for t in tasks}
        assert t1.id in ids
        assert t2.id in ids
        assert len(tasks) == 2

    async def test_update_status(self, store, sample_task):
        await store.save(sample_task)
        await store.update_status(str(sample_task.id), TaskStatus.RUNNING)
        retrieved = await store.get(str(sample_task.id))
        assert retrieved.status == TaskStatus.RUNNING


class TestTaskStoreQueue:
    async def test_enqueue_and_dequeue(self, store, sample_task):
        await store.save(sample_task)
        await store.enqueue(str(sample_task.id))
        task_id = await store.dequeue()
        assert task_id == str(sample_task.id)

    async def test_dequeue_empty_returns_none(self, store):
        result = await store.dequeue()
        assert result is None


class TestTaskStoreLogs:
    async def test_append_log(self, store, sample_task):
        await store.save(sample_task)
        await store.append_log(str(sample_task.id), "Step 1 done")
        await store.append_log(str(sample_task.id), "Step 2 done")
        retrieved = await store.get(str(sample_task.id))
        assert retrieved.logs == ["Step 1 done", "Step 2 done"]
