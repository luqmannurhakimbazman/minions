# Claude CLI Agent Integration — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace the placeholder agent container with a working Claude CLI integration that receives tasks, runs Claude Code in non-interactive mode, and creates GitHub PRs with the results.

**Architecture:** The agent Docker image installs Claude CLI (npm) and GitHub CLI. The entrypoint pipes a combined prompt (task description + context) to `claude --print`. The worker's ContainerManager mounts host auth directories (`~/.claude`, `~/.config/gh`, `~/.gitconfig`) read-only into the container.

**Tech Stack:** Docker, bash, Claude CLI (`@anthropic-ai/claude-code`), GitHub CLI (`gh`), Python (docker SDK)

---

### Task 1: Update Dockerfile.agent to install Claude CLI and GitHub CLI

**Files:**
- Modify: `containers/Dockerfile.agent`
- Test: `tests/test_containers.py`

**Step 1: Write failing tests for new Dockerfile requirements**

Add these tests to `tests/test_containers.py` inside the `TestDockerfileAgent` class:

```python
def test_dockerfile_installs_nodejs(self):
    content = (CONTAINERS_DIR / "Dockerfile.agent").read_text()
    assert "nodejs" in content or "node" in content

def test_dockerfile_installs_claude_cli(self):
    content = (CONTAINERS_DIR / "Dockerfile.agent").read_text()
    assert "@anthropic-ai/claude-code" in content

def test_dockerfile_installs_github_cli(self):
    content = (CONTAINERS_DIR / "Dockerfile.agent").read_text()
    assert "gh" in content
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/test_containers.py::TestDockerfileAgent -v`
Expected: 3 FAIL (nodejs, claude-code, gh not in Dockerfile yet)

**Step 3: Update Dockerfile.agent**

Replace the full contents of `containers/Dockerfile.agent` with:

```dockerfile
FROM python:3.13-slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends git curl ripgrep nodejs npm && \
    rm -rf /var/lib/apt/lists/*

# Install Claude CLI
RUN npm install -g @anthropic-ai/claude-code

# Install GitHub CLI
RUN curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg \
      -o /usr/share/keyrings/githubcli-archive-keyring.gpg && \
    echo "deb [signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" \
      > /etc/apt/sources.list.d/github-cli.list && \
    apt-get update && apt-get install -y --no-install-recommends gh && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/test_containers.py::TestDockerfileAgent -v`
Expected: All PASS

**Step 5: Commit**

```
feat(agent): install claude cli and github cli in agent image
```

---

### Task 2: Replace entrypoint.sh placeholder with Claude CLI invocation

**Files:**
- Modify: `containers/entrypoint.sh`
- Test: `tests/test_containers.py`

**Step 1: Write failing tests for new entrypoint behavior**

Add these tests to `tests/test_containers.py` inside the `TestEntrypoint` class:

```python
def test_entrypoint_invokes_claude_cli(self):
    content = (CONTAINERS_DIR / "entrypoint.sh").read_text()
    assert "claude" in content
    assert "--print" in content

def test_entrypoint_skips_permissions(self):
    content = (CONTAINERS_DIR / "entrypoint.sh").read_text()
    assert "--dangerously-skip-permissions" in content

def test_entrypoint_creates_pr(self):
    content = (CONTAINERS_DIR / "entrypoint.sh").read_text()
    assert "gh pr create" in content

def test_entrypoint_checks_for_commits_before_push(self):
    content = (CONTAINERS_DIR / "entrypoint.sh").read_text()
    assert "git diff" in content or "git rev-list" in content or "git status" in content
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/test_containers.py::TestEntrypoint -v`
Expected: 4 FAIL (claude, --print, gh pr create, git diff not in entrypoint yet)

**Step 3: Replace entrypoint.sh**

Replace the full contents of `containers/entrypoint.sh` with:

```bash
#!/usr/bin/env bash
set -e

echo "==> Cloning repository: $REPO_URL"
git clone --depth=1 "$REPO_URL" repo
cd repo

echo "==> Creating branch: $BRANCH_NAME"
git checkout -b "$BRANCH_NAME"

echo "==> Writing context file"
if [ -n "$CONTEXT_FILE" ]; then
    echo "$CONTEXT_FILE" > /tmp/context.json
fi

echo "==> Running task $TASK_ID with Claude CLI"

FULL_PROMPT="$(cat <<EOF
Task: $PROMPT

Repository context (relevant files, tree, and recent git log) is available at /tmp/context.json.
You are working on branch $BRANCH_NAME in a cloned repository.
Make the necessary code changes to complete the task.
Commit your changes when done.
EOF
)"

echo "$FULL_PROMPT" | claude --print \
    --dangerously-skip-permissions \
    --no-session-persistence

echo "==> Checking for changes"
if ! git diff --quiet HEAD origin/HEAD 2>/dev/null; then
    echo "==> Pushing branch: $BRANCH_NAME"
    git push -u origin "$BRANCH_NAME"

    echo "==> Creating pull request"
    EXISTING_PR=$(gh pr list --head "$BRANCH_NAME" --json number --jq '.[0].number' 2>/dev/null || echo "")
    if [ -z "$EXISTING_PR" ]; then
        gh pr create \
            --title "[minions] $PROMPT" \
            --body "Automated PR created by Minions agent for task \`$TASK_ID\`."
    else
        echo "==> PR #$EXISTING_PR already exists for branch $BRANCH_NAME, skipping"
    fi
else
    echo "==> No changes detected, skipping push and PR"
fi

echo "==> Task complete"
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/test_containers.py::TestEntrypoint -v`
Expected: All PASS

**Step 5: Commit**

```
feat(agent): replace placeholder with claude cli invocation and pr creation
```

---

### Task 3: Add volume mounts to ContainerManager for auth

**Files:**
- Modify: `worker/container_manager.py`
- Test: `tests/test_container_manager.py`

**Step 1: Write failing tests for volume mounts**

Add a new test class to `tests/test_container_manager.py`:

```python
from pathlib import Path


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
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/test_container_manager.py::TestRunMountsAuthVolumes -v`
Expected: 2 FAIL (no volumes kwarg passed yet, and no Path import)

**Step 3: Update container_manager.py**

Replace the full contents of `worker/container_manager.py` with:

```python
"""Docker SDK wrapper for spawning agent containers."""

from __future__ import annotations

import json
from pathlib import Path
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

    def _build_volumes(self) -> dict[str, dict[str, str]]:
        """Build volume mounts for host auth directories."""
        home = Path.home()
        mounts: list[tuple[Path, str]] = [
            (home / ".claude", "/root/.claude"),
            (home / ".config" / "gh", "/root/.config/gh"),
            (home / ".gitconfig", "/root/.gitconfig"),
        ]
        volumes: dict[str, dict[str, str]] = {}
        for host_path, container_path in mounts:
            if host_path.exists():
                volumes[str(host_path)] = {"bind": container_path, "mode": "ro"}
        return volumes

    def run(self, task: Task, context: dict[str, Any]) -> dict[str, Any]:
        """Spawn a container, wait for it to finish, and return results.

        Returns a dict with ``exit_code`` (int) and ``logs`` (str).
        """
        client = docker.from_env()
        env = self._build_env(task, context)
        volumes = self._build_volumes()

        container = client.containers.run(
            self._settings.container_image,
            environment=env,
            network_mode=self._settings.container_network_mode,
            volumes=volumes,
            detach=True,
        )

        result = container.wait()
        logs = container.logs().decode("utf-8", errors="replace")
        container.remove()

        return {
            "exit_code": result["StatusCode"],
            "logs": logs,
        }
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/test_container_manager.py -v`
Expected: All PASS (existing tests still pass, new tests pass)

**Step 5: Commit**

```
feat(worker): mount host auth volumes into agent containers
```

---

### Task 4: Run full test suite and verify nothing is broken

**Files:**
- None (verification only)

**Step 1: Run the full test suite**

Run: `pytest -v`
Expected: All tests PASS

**Step 2: Run linter**

Run: `ruff check .`
Expected: No errors

**Step 3: Run formatter check**

Run: `ruff format --check .`
Expected: No changes needed

**Step 4: Commit any lint/format fixes if needed**

```
style: fix lint issues from agent integration
```

---

### Task 5: Verify Docker build works

**Files:**
- None (verification only)

**Step 1: Build the agent image**

Run: `docker build -t minions-agent:latest -f containers/Dockerfile.agent containers/`
Expected: Build completes successfully. Claude CLI and gh are installed.

**Step 2: Verify installed tools**

Run: `docker run --rm minions-agent:latest bash -c "claude --version && gh --version && git --version"`
Expected: Version output for all three tools.

**Step 3: No commit needed** — this is a verification step.
