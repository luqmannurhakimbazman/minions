"""Prometheus metric definitions for the Minions orchestrator."""

from prometheus_client import Counter, Histogram

TASKS_SUBMITTED = Counter(
    "minions_tasks_submitted_total",
    "Total number of tasks submitted to the orchestrator",
)

TASKS_COMPLETED = Counter(
    "minions_tasks_completed_total",
    "Total number of tasks that completed successfully",
)

TASKS_FAILED = Counter(
    "minions_tasks_failed_total",
    "Total number of tasks that failed after all retries",
)

RETRIES_TOTAL = Counter(
    "minions_retries_total",
    "Total number of task retry attempts",
)

TASK_DURATION_SECONDS = Histogram(
    "minions_task_duration_seconds",
    "Time spent executing a task from start to finish",
)

CONTAINER_SPAWN_SECONDS = Histogram(
    "minions_container_spawn_seconds",
    "Time spent spawning an agent container",
)
