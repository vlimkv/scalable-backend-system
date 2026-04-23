from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth import get_current_user
from app.core.database import get_db
from app.models.task import Task
from app.models.user import User
from app.schemas.task import (
    TaskCreate,
    TaskResponse,
    TaskUpdate,
)
from app.services.task_service import TaskService
from app.utils.pagination import PaginatedResponse

router = APIRouter(prefix="/api/v1/tasks", tags=["tasks"])


@router.post("", response_model=TaskResponse)
async def create_task(
    payload: TaskCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = TaskService(db)
    return await service.create(current_user, payload)


@router.get("", response_model=PaginatedResponse[TaskResponse])
async def list_tasks(
    page: int = Query(1),
    size: int = Query(10),
    status: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = TaskService(db)
    items, total = await service.list(current_user, page, size, status)

    return {
        "items": items,
        "total": total,
        "page": page,
        "size": size,
    }


@router.patch("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: int,
    payload: TaskUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    task = await db.scalar(select(Task).where(Task.id == task_id))

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    service = TaskService(db)
    return await service.update(task, payload)