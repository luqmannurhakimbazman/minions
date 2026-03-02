"""Tests for the Typer CLI."""

import uuid

import httpx
import respx
from typer.testing import CliRunner

from cli.main import app
from common.config import Settings

runner = CliRunner()
BASE_URL = Settings().api_base_url


class TestRunCommand:
    @respx.mock
    def test_run_posts_task_and_prints_id(self):
        task_id = str(uuid.uuid4())
        respx.post(f"{BASE_URL}/tasks").mock(
            return_value=httpx.Response(
                201,
                json={
                    "id": task_id,
                    "description": "Fix bug",
                    "repo": "org/repo",
                    "status": "PENDING",
                },
            )
        )
        result = runner.invoke(app, ["run", "Fix bug", "org/repo"])
        assert result.exit_code == 0
        assert task_id in result.output
        assert "PENDING" in result.output


class TestStatusCommand:
    @respx.mock
    def test_status_prints_table(self):
        task_id = str(uuid.uuid4())
        respx.get(f"{BASE_URL}/tasks").mock(
            return_value=httpx.Response(
                200,
                json=[
                    {
                        "id": task_id,
                        "description": "Fix bug",
                        "repo": "org/repo",
                        "status": "RUNNING",
                        "retries": 0,
                        "pr_url": None,
                        "logs": [],
                    }
                ],
            )
        )
        result = runner.invoke(app, ["status"])
        assert result.exit_code == 0
        assert "org/repo" in result.output
        assert "RUNNING" in result.output


class TestCancelCommand:
    @respx.mock
    def test_cancel_prints_confirmation(self):
        task_id = str(uuid.uuid4())
        respx.post(f"{BASE_URL}/tasks/{task_id}/cancel").mock(
            return_value=httpx.Response(
                200,
                json={
                    "id": task_id,
                    "description": "Fix bug",
                    "repo": "org/repo",
                    "status": "CANCELLED",
                },
            )
        )
        result = runner.invoke(app, ["cancel", task_id])
        assert result.exit_code == 0
        assert "CANCELLED" in result.output


class TestLogsCommand:
    @respx.mock
    def test_logs_prints_task_logs(self):
        task_id = str(uuid.uuid4())
        respx.get(f"{BASE_URL}/tasks/{task_id}").mock(
            return_value=httpx.Response(
                200,
                json={
                    "id": task_id,
                    "description": "Fix bug",
                    "repo": "org/repo",
                    "status": "RUNNING",
                    "logs": ["Step 1 done", "Step 2 done"],
                },
            )
        )
        result = runner.invoke(app, ["logs", task_id])
        assert result.exit_code == 0
        assert "Step 1 done" in result.output
        assert "Step 2 done" in result.output
