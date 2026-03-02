"""API route definitions for task management."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from api.deps import get_task_store
from common.models import Task
from common.redis_client import TaskStore

router = APIRouter()


class CreateTaskRequest(BaseModel):
    description: str
    repo: str


@router.post("/tasks", status_code=201)
async def create_task(
    request: CreateTaskRequest,
    store: TaskStore = Depends(get_task_store),
) -> Task:
    task = Task(description=request.description, repo=request.repo)
    await store.save(task)
    await store.enqueue(str(task.id))
    return task


@router.get("/tasks")
async def list_tasks(store: TaskStore = Depends(get_task_store)) -> list[Task]:
    return await store.list_tasks()


@router.get("/tasks/{task_id}")
async def get_task(task_id: str, store: TaskStore = Depends(get_task_store)) -> Task:
    task = await store.get(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task
