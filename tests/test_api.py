"""Tests for the API server."""

import httpx
import pytest
from fakeredis import aioredis as fakeredis_aio

from api.app import create_app
from api.deps import get_task_store
from common.redis_client import TaskStore


@pytest.fixture
def fake_store():
    """Create a TaskStore backed by fakeredis."""
    redis = fakeredis_aio.FakeRedis(decode_responses=True)
    return TaskStore(redis)


@pytest.fixture
def app(fake_store):
    application = create_app()
    application.dependency_overrides[get_task_store] = lambda: fake_store
    return application


@pytest.fixture
async def client(app):
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac


class TestHealthCheck:
    async def test_health_returns_200(self, client):
        resp = await client.get("/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}


class TestCreateTask:
    async def test_create_task_returns_201(self, client):
        resp = await client.post("/tasks", json={"description": "Fix bug", "repo": "org/repo"})
        assert resp.status_code == 201
        data = resp.json()
        assert data["description"] == "Fix bug"
        assert data["repo"] == "org/repo"
        assert data["status"] == "PENDING"
        assert "id" in data

    async def test_create_task_is_persisted(self, client):
        resp = await client.post("/tasks", json={"description": "Fix bug", "repo": "org/repo"})
        task_id = resp.json()["id"]
        get_resp = await client.get(f"/tasks/{task_id}")
        assert get_resp.status_code == 200
        assert get_resp.json()["id"] == task_id


class TestListTasks:
    async def test_list_tasks_empty(self, client):
        resp = await client.get("/tasks")
        assert resp.status_code == 200
        assert resp.json() == []

    async def test_list_tasks_after_create(self, client):
        await client.post("/tasks", json={"description": "Task 1", "repo": "org/a"})
        await client.post("/tasks", json={"description": "Task 2", "repo": "org/b"})
        resp = await client.get("/tasks")
        assert resp.status_code == 200
        assert len(resp.json()) == 2


class TestGetTask:
    async def test_get_task_found(self, client):
        create_resp = await client.post(
            "/tasks", json={"description": "Fix bug", "repo": "org/repo"}
        )
        task_id = create_resp.json()["id"]
        resp = await client.get(f"/tasks/{task_id}")
        assert resp.status_code == 200
        assert resp.json()["description"] == "Fix bug"

    async def test_get_task_not_found(self, client):
        resp = await client.get("/tasks/00000000-0000-0000-0000-000000000000")
        assert resp.status_code == 404


class TestCancelTask:
    async def test_cancel_task_returns_200(self, client):
        create_resp = await client.post(
            "/tasks", json={"description": "Fix bug", "repo": "org/repo"}
        )
        task_id = create_resp.json()["id"]
        resp = await client.post(f"/tasks/{task_id}/cancel")
        assert resp.status_code == 200
        assert resp.json()["status"] == "CANCELLED"

    async def test_cancel_task_not_found(self, client):
        resp = await client.post("/tasks/00000000-0000-0000-0000-000000000000/cancel")
        assert resp.status_code == 404
