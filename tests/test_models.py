"""Tests for common.models — TaskStatus enum and Task model."""

from datetime import datetime
from uuid import UUID

from common.models import Task, TaskStatus


class TestTaskStatus:
    def test_all_values_exist(self):
        expected = {
            "PENDING",
            "PREFETCHING",
            "RUNNING",
            "TESTING",
            "RETRYING",
            "COMPLETED",
            "FAILED",
            "CANCELLED",
        }
        actual = {s.value for s in TaskStatus}
        assert actual == expected

    def test_status_is_string(self):
        assert isinstance(TaskStatus.PENDING, str)
        assert TaskStatus.PENDING == "PENDING"


class TestTask:
    def test_minimal_creation(self):
        task = Task(description="Fix the login bug", repo="acme/webapp")
        assert task.description == "Fix the login bug"
        assert task.repo == "acme/webapp"
        assert task.status == TaskStatus.PENDING

    def test_id_is_uuid(self):
        task = Task(description="d", repo="r")
        assert isinstance(task.id, UUID)

    def test_two_tasks_have_different_ids(self):
        t1 = Task(description="d", repo="r")
        t2 = Task(description="d", repo="r")
        assert t1.id != t2.id

    def test_json_roundtrip(self):
        task = Task(description="roundtrip", repo="org/repo")
        data = task.model_dump_json()
        restored = Task.model_validate_json(data)
        assert restored.id == task.id
        assert restored.description == task.description
        assert restored.status == task.status

    def test_default_context_is_empty_dict(self):
        task = Task(description="d", repo="r")
        assert task.context == {}

    def test_default_logs_is_empty_list(self):
        task = Task(description="d", repo="r")
        assert task.logs == []

    def test_default_retries_is_zero(self):
        task = Task(description="d", repo="r")
        assert task.retries == 0

    def test_timestamps_are_set(self):
        task = Task(description="d", repo="r")
        assert isinstance(task.created_at, datetime)
        assert isinstance(task.updated_at, datetime)

    def test_optional_fields_default_none(self):
        task = Task(description="d", repo="r")
        assert task.worktree_path is None
        assert task.branch_name is None
        assert task.pr_url is None
