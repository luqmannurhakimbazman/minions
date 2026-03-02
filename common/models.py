"""Shared domain models for the Minions orchestrator."""

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class TaskStatus(StrEnum):
    PENDING = "PENDING"
    PREFETCHING = "PREFETCHING"
    RUNNING = "RUNNING"
    TESTING = "TESTING"
    RETRYING = "RETRYING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class Task(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    description: str
    repo: str
    status: TaskStatus = TaskStatus.PENDING
    worktree_path: str | None = None
    branch_name: str | None = None
    pr_url: str | None = None
    retries: int = 0
    context: dict[str, Any] = Field(default_factory=dict)
    logs: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
