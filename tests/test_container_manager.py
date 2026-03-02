"""Tests for worker.container_manager — Docker SDK wrapper."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from common.config import Settings
from common.models import Task
from worker.container_manager import ContainerManager


@pytest.fixture
def settings():
    return Settings(container_image="minions-agent:latest", container_network_mode="host")


@pytest.fixture
def manager(settings):
    return ContainerManager(settings)


@pytest.fixture
def task():
    return Task(
        id=uuid4(),
        description="Fix the login bug",
        repo="https://github.com/example/repo.git",
    )


class TestGenerateBranchName:
    def test_starts_with_minions_prefix(self, manager, task):
        name = manager.generate_branch_name(str(task.id))
        assert name.startswith("minions/")

    def test_uses_first_eight_chars_of_task_id(self, manager, task):
        name = manager.generate_branch_name(str(task.id))
        expected = f"minions/{str(task.id)[:8]}"
        assert name == expected


class TestBuildEnv:
    def test_returns_correct_env_vars(self, manager, task):
        context = {"tree": ["src/main.py"], "relevant_files": [], "git_log": []}
        env = manager._build_env(task, context)

        assert env["TASK_ID"] == str(task.id)
        assert env["REPO_URL"] == task.repo
        assert "BRANCH_NAME" in env
        assert env["PROMPT"] == task.description
        assert "CONTEXT_FILE" in env
        # Context should be JSON-serializable string
        parsed = json.loads(env["CONTEXT_FILE"])
        assert parsed["tree"] == ["src/main.py"]


class TestRun:
    @patch("worker.container_manager.docker")
    def test_run_calls_docker_and_returns_result(self, mock_docker, manager, task):
        context = {"tree": [], "relevant_files": [], "git_log": []}

        mock_container = MagicMock()
        mock_container.wait.return_value = {"StatusCode": 0}
        mock_container.logs.return_value = b"All done\n"

        mock_client = MagicMock()
        mock_client.containers.run.return_value = mock_container
        mock_docker.from_env.return_value = mock_client

        result = manager.run(task, context)

        mock_client.containers.run.assert_called_once()
        mock_container.wait.assert_called_once()
        mock_container.logs.assert_called_once()
        mock_container.remove.assert_called_once()

        assert result["exit_code"] == 0
        assert result["logs"] == "All done\n"

    @patch("worker.container_manager.docker")
    def test_run_captures_nonzero_exit_code(self, mock_docker, manager, task):
        context = {"tree": [], "relevant_files": [], "git_log": []}

        mock_container = MagicMock()
        mock_container.wait.return_value = {"StatusCode": 1}
        mock_container.logs.return_value = b"Error occurred\n"

        mock_client = MagicMock()
        mock_client.containers.run.return_value = mock_container
        mock_docker.from_env.return_value = mock_client

        result = manager.run(task, context)

        assert result["exit_code"] == 1
        assert result["logs"] == "Error occurred\n"


class TestRunMountsAuthVolumes:
    @patch("worker.container_manager.docker")
    @patch("worker.container_manager.Path.home")
    def test_mounts_claude_dir_when_exists(self, mock_home, mock_docker, manager, task):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            (tmp_path / ".claude").mkdir()
            (tmp_path / ".config" / "gh").mkdir(parents=True)
            (tmp_path / ".gitconfig").touch()
            mock_home.return_value = tmp_path

            mock_container = MagicMock()
            mock_container.wait.return_value = {"StatusCode": 0}
            mock_container.logs.return_value = b"ok"
            mock_client = MagicMock()
            mock_client.containers.run.return_value = mock_container
            mock_docker.from_env.return_value = mock_client

            context = {"tree": [], "relevant_files": [], "git_log": []}
            manager.run(task, context)

            call_kwargs = mock_client.containers.run.call_args
            volumes = call_kwargs.kwargs.get("volumes") or call_kwargs[1].get("volumes", {})
            assert str(tmp_path / ".claude") in volumes

    @patch("worker.container_manager.docker")
    @patch("worker.container_manager.Path.home")
    def test_skips_missing_auth_dirs(self, mock_home, mock_docker, manager, task):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            # No .claude, .config/gh, or .gitconfig created
            mock_home.return_value = tmp_path

            mock_container = MagicMock()
            mock_container.wait.return_value = {"StatusCode": 0}
            mock_container.logs.return_value = b"ok"
            mock_client = MagicMock()
            mock_client.containers.run.return_value = mock_container
            mock_docker.from_env.return_value = mock_client

            context = {"tree": [], "relevant_files": [], "git_log": []}
            manager.run(task, context)

            call_kwargs = mock_client.containers.run.call_args
            volumes = call_kwargs.kwargs.get("volumes") or call_kwargs[1].get("volumes", {})
            assert volumes == {}
