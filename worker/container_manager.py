"""Docker SDK wrapper for spawning agent containers."""

from __future__ import annotations

import json
from typing import Any

import docker

from common.config import Settings
from common.models import Task


class ContainerManager:
    """Manages the lifecycle of agent Docker containers."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def generate_branch_name(self, task_id: str) -> str:
        """Return a Git branch name derived from the task id."""
        return f"minions/{task_id[:8]}"

    def _build_env(self, task: Task, context: dict[str, Any]) -> dict[str, str]:
        """Build the environment variable dict passed into the container."""
        return {
            "TASK_ID": str(task.id),
            "REPO_URL": task.repo,
            "BRANCH_NAME": self.generate_branch_name(str(task.id)),
            "CONTEXT_FILE": json.dumps(context),
            "PROMPT": task.description,
        }

    def run(self, task: Task, context: dict[str, Any]) -> dict[str, Any]:
        """Spawn a container, wait for it to finish, and return results.

        Returns a dict with ``exit_code`` (int) and ``logs`` (str).
        """
        client = docker.from_env()
        env = self._build_env(task, context)

        container = client.containers.run(
            self._settings.container_image,
            environment=env,
            network_mode=self._settings.container_network_mode,
            detach=True,
        )

        result = container.wait()
        logs = container.logs().decode("utf-8", errors="replace")
        container.remove()

        return {
            "exit_code": result["StatusCode"],
            "logs": logs,
        }
