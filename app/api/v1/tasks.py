from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth import get_current_user
from app.core.database import get_db
from app.models.task import Task
from app.models.user import User
from app.schemas.task import (
    TaskAssign,
    TaskCreate,
    TaskResponse,
    TaskStatusUpdate,
    TaskUpdate,
)
from app.services.task_service import TaskService
from app.utils.pagination import PaginatedResponse

router = APIRouter(prefix="/api/v1/tasks", tags=["tasks"])


def can_edit_task(task: Task, user: User) -> bool:
    return user.role == "admin" or task.owner_id == user.id


def can_assign_task(user: User) -> bool:
    return user.role in {"admin", "manager"}


def can_change_status(task: Task, user: User) -> bool:
    return (
        user.role == "admin"
        or task.owner_id == user.id
        or task.assignee_id == user.id
    )


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    payload: TaskCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = TaskService(db)
    return await service.create(current_user, payload)


@router.get("", response_model=PaginatedResponse[TaskResponse])
async def list_tasks(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    status_filter: str | None = Query(None, alias="status"),
    owner_id: int | None = Query(None),
    assignee_id: int | None = Query(None),
    mine: bool = Query(False),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = TaskService(db)
    items, total = await service.list(
        page=page,
        size=size,
        status_filter=status_filter,
        owner_id=owner_id,
        assignee_id=assignee_id,
        mine=mine,
        current_user=current_user,
    )

    return {
        "items": items,
        "total": total,
        "page": page,
        "size": size,
    }


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    task = await db.scalar(select(Task).where(Task.id == task_id))

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    return task


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

    if not can_edit_task(task, current_user):
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    service = TaskService(db)
    return await service.update(task, payload)


@router.patch("/{task_id}/status", response_model=TaskResponse)
async def update_task_status(
    task_id: int,
    payload: TaskStatusUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    task = await db.scalar(select(Task).where(Task.id == task_id))

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if not can_change_status(task, current_user):
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    service = TaskService(db)
    return await service.update_status(task, payload.status)


@router.patch("/{task_id}/assign", response_model=TaskResponse)
async def assign_task(
    task_id: int,
    payload: TaskAssign,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    task = await db.scalar(select(Task).where(Task.id == task_id))
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if not can_assign_task(current_user):
        raise HTTPException(status_code=403, detail="Only manager or admin can assign tasks")

    assignee = await db.scalar(select(User).where(User.id == payload.user_id))
    if not assignee:
        raise HTTPException(status_code=404, detail="Assignee user not found")

    service = TaskService(db)
    return await service.assign(task, assignee)