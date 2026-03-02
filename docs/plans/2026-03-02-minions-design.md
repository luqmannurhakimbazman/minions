# Minions — Personal Coding Agent Orchestrator

## Purpose

Fire-and-forget coding agents that take a task description, write code, pass checks, and open a PR. Built as a microservice system for personal productivity and as a portfolio showcase.

Inspired by Stripe's Minions architecture. The core principle: **the model does not run the system — the system runs the model.** The LLM only controls the code-writing step. Everything else is deterministic.

## Architecture

```
┌─────────┐     ┌─────────────┐     ┌───────────┐
│   CLI   │────▶│  API Server  │────▶│   Redis   │
└─────────┘     │  (FastAPI)   │     │  (Queue +  │
                └──────┬───────┘     │   State)   │
┌─────────┐            │             └─────┬──────┘
│Dashboard│◀───▶       │                   │
│(Streamlit)    ┌──────▼───────┐    ┌──────▼──────┐
└─────────┘     │  Prefetcher  │    │   Workers   │
                │ (Deterministic│    │  (Spawns    │
┌─────────┐     │  Context)    │    │  Agent      │
│Grafana +│     └──────────────┘    │  Containers)│
│Prometheus│◀──metrics──────────────└─────────────┘
└─────────┘
```

## Services

| Service | Tech | Port | Role |
|---------|------|------|------|
| API | FastAPI | 8000 | Task CRUD, WebSocket status |
| Redis | Redis | 6379 | Queue, state, logs, pub/sub |
| Worker | Python + Docker SDK | — | Orchestrates agent containers |
| Dashboard | Streamlit | 8501 | Task management, log viewing |
| Prometheus | Prometheus | 9090 | Metrics collection |
| Grafana | Grafana | 3000 | Operational dashboards |

## Blueprint Pipeline

The core execution flow per task. Each worker picks a task, prefetches context, spawns an isolated Docker container, and collects results.

```
Worker process:                    Agent container:
  1. Pick task from Redis
  2. Run prefetcher
  3. Spawn container ──────────▶  4. Receive context + prompt
                                  5. claude CLI writes code
                                  6. Lint + type-check
                                     └─ fail → retry step 5
                                  7. Run tests
                                     └─ fail → retry step 5
                                  8. git commit + push
                                  9. gh pr create
  10. Collect results ◀──────────
  11. Update Redis
  12. Destroy container
```

- 2 retry cap on test/lint failures.
- LLM only controls step 5. Everything else is deterministic.

## Agent Container Isolation

Each agent run gets its own Docker container:

- Fresh repo clone per run
- Pre-warmed base images per language stack (claude CLI, git, gh, linters baked in)
- Restricted network: GitHub access only, no Redis/API/internet
- No host filesystem access
- Prefetched context mounted as read-only files
- Destroyed after results are collected

## Prefetcher

Deterministic context gathering. No LLM involved.

**Inputs:** task description + repo path

**Collects:**
1. Ripgrep task keywords against repo to find relevant files (top 10-15)
2. CLAUDE.md / .cursorrules from discovered directories
3. Git log for recent commits touching discovered files
4. Repo directory tree (depth-limited)
5. Content from any URLs in task description

## Task Lifecycle

```
PENDING → PREFETCHING → RUNNING → TESTING → COMPLETED
                                      ↓
                                  RETRYING (max 2)
                                      ↓
                                   FAILED
```

### Task Schema

```json
{
  "id": "uuid",
  "description": "fix the off-by-one error in the executor",
  "repo": "/path/to/repo",
  "status": "PENDING",
  "worktree_path": null,
  "branch_name": null,
  "pr_url": null,
  "retries": 0,
  "context": {},
  "logs": [],
  "created_at": "...",
  "updated_at": "..."
}
```

## CLI

```
minion run "description"   — submit task
minion status              — list all tasks
minion logs <id>           — tail logs
minion cancel <id>         — cancel task
```

Built with Typer. Thin HTTP client hitting the API.

## Monitoring

- Workers emit Prometheus metrics: tasks completed, retry rates, container spinup latency, failure rate by repo
- Grafana dashboards for operational visibility
- First-class component, not a stretch goal

## Project Structure

```
minions/
├── api/           # FastAPI server
├── worker/        # Blueprint runner + Docker SDK
├── prefetcher/    # Context gathering
├── dashboard/     # Streamlit app
├── cli/           # CLI client (Typer)
├── common/        # Shared models, Redis client, config
├── containers/    # Dockerfiles for agent base images
├── monitoring/    # Prometheus config, Grafana dashboards
└── docker-compose.yml
```

## Tech Stack

- Python, FastAPI, Streamlit, Typer
- Redis (Streams + Hash + Pub/Sub)
- Docker SDK for Python
- Prometheus + Grafana
- Claude Code CLI as the core agent

## Key Design Decisions

1. **Claude Code as the agent** — No custom agent, wraps the existing CLI
2. **Docker isolation from day one** — Each agent run in its own container with restricted networking
3. **Deterministic prefetching** — No LLM in context gathering, pure code
4. **Blueprint pattern** — LLM only writes code, everything else is hardcoded pipeline steps
5. **2-round retry cap** — Prevents runaway compute, flags hard tasks for humans
6. **Microservice architecture** — Learning goal alongside productivity goal
