# Minions

An autonomous software engineering orchestrator that takes task descriptions, prefetches repository context, spawns AI agent containers, and manages the full lifecycle from submission to pull request.

## Architecture

Minions is composed of 6 services that work together:

- **API** (FastAPI) -- REST interface for task CRUD, cancellation, and Prometheus metrics. Runs on port 8000.
- **Redis** -- Persistence layer for tasks and the work queue.
- **Worker** -- Polls the Redis queue, runs the prefetch-then-container pipeline, and handles retries.
- **Dashboard** (Streamlit) -- Real-time web UI showing task status, logs, and progress. Runs on port 8501.
- **Prometheus** -- Scrapes metrics from the API and worker. Runs on port 9090.
- **Grafana** -- Dashboards and alerting built on Prometheus data. Runs on port 3000.

### Task Lifecycle

1. A task is submitted via the CLI or API (`POST /tasks`).
2. The worker dequeues the task and transitions it through statuses: `PENDING` -> `PREFETCHING` -> `RUNNING` -> `COMPLETED` (or `RETRYING` -> `FAILED`).
3. During prefetching, the repo tree is scanned and relevant files are collected based on keyword matching.
4. An agent Docker container is spawned with the task context. Inside the container, Claude CLI runs in non-interactive mode (`--print`) to make code changes, then pushes the branch and creates a GitHub PR.
5. On success the task is marked `COMPLETED`. On failure it is retried up to `max_retries` times before being marked `FAILED`.

## Prerequisites

The agent container uses [Claude CLI](https://docs.anthropic.com/en/docs/claude-code) and [GitHub CLI](https://cli.github.com/) via host-mounted credentials. Before starting:

1. **Claude CLI** -- log in on your host machine (`claude auth`). The worker mounts `~/.claude` read-only into agent containers.
2. **GitHub CLI** -- log in on your host machine (`gh auth login`). The worker mounts `~/.config/gh` and `~/.gitconfig` read-only into agent containers.
3. **Docker** -- Docker Desktop or Docker Engine must be running.

```bash
# Build the agent image
docker build -t minions-agent:latest -f containers/Dockerfile.agent containers/
```

## Quick Start

```bash
# Clone the repository
git clone <repo-url> && cd minions

# Build the agent image
docker build -t minions-agent:latest -f containers/Dockerfile.agent containers/

# Start all services with Docker Compose
docker compose up --build -d

# Verify services are running
docker compose ps
```

The following endpoints will be available:

| Service     | URL                        |
|-------------|----------------------------|
| API         | http://localhost:8000      |
| Dashboard   | http://localhost:8501      |
| Prometheus  | http://localhost:9090      |
| Grafana     | http://localhost:3000      |

Grafana default credentials: `admin` / `admin`.

## CLI Usage

```bash
# Install the project (includes the CLI)
uv pip install -e ".[dev]"

# Submit a task
minion run "Fix the login bug" https://github.com/org/repo

# List all tasks
minion status

# View task logs
minion logs <task-id>

# Cancel a task
minion cancel <task-id>
```

## Local Development

```bash
# Create a virtual environment and install dev dependencies
uv venv
source .venv/bin/activate
uv pip install -e ".[dev]"

# Run tests
pytest -v

# Lint and format
ruff check .
ruff format .
```

## Project Structure

```
minions/
  api/
    app.py            # FastAPI application factory
    routes.py         # Task CRUD endpoints
    deps.py           # Dependency injection
  worker/
    main.py           # Worker polling loop
    pipeline.py       # BlueprintPipeline orchestration
    container_manager.py  # Docker SDK wrapper
    run.py            # Async entrypoint for docker compose
  prefetcher/
    tree.py           # Repository tree scanner
    keywords.py       # Keyword extraction and file matching
    git_context.py    # Git log context
    collect.py        # Prefetch orchestrator
  cli/
    main.py           # Typer CLI application
  dashboard/
    app.py            # Streamlit dashboard
  common/
    models.py         # Pydantic domain models
    config.py         # Settings with env var overrides
    redis_client.py   # TaskStore (Redis wrapper)
  monitoring/
    metrics.py        # Prometheus metric definitions
    prometheus.yml    # Prometheus scrape config
    grafana/          # Grafana provisioning
  containers/
    Dockerfile.agent  # Agent container image (Claude CLI + gh)
    entrypoint.sh     # Agent entrypoint: clone, run Claude CLI, push, PR
  tests/              # Pytest test suite
  Dockerfile          # Container image for API/worker/dashboard
  docker-compose.yml  # Full stack orchestration
  pyproject.toml      # Project metadata and dependencies
```

## Monitoring

Prometheus metrics are exposed at `GET /metrics` on the API service. Key metrics include:

- `minions_tasks_submitted_total` -- tasks submitted
- `minions_tasks_completed_total` -- tasks completed successfully
- `minions_tasks_failed_total` -- tasks failed after all retries
- `minions_retries_total` -- retry attempts
- `minions_task_duration_seconds` -- task execution time histogram
- `minions_container_spawn_seconds` -- container spawn time histogram
