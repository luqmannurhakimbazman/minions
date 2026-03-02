"""Shared domain models for the Minions orchestrator."""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
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
    worktree_path: Optional[str] = None
    branch_name: Optional[str] = None
    pr_url: Optional[str] = None
    retries: int = 0
    context: dict[str, Any] = Field(default_factory=dict)
    logs: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
