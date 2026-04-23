from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.task import Task
from app.models.user import User
from app.schemas.task import TaskCreate, TaskUpdate


class TaskService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, user: User, payload: TaskCreate) -> Task:
        task = Task(
            title=payload.title,
            description=payload.description,
            owner_id=user.id,
        )
        self.db.add(task)
        await self.db.commit()
        await self.db.refresh(task)
        return task

    async def list(
        self,
        *,
        page: int = 1,
        size: int = 10,
        status_filter: str | None = None,
        owner_id: int | None = None,
        assignee_id: int | None = None,
        mine: bool = False,
        current_user: User,
    ) -> tuple[list[Task], int]:
        query = select(Task)

        if status_filter:
            query = query.where(Task.status == status_filter)

        if owner_id is not None:
            query = query.where(Task.owner_id == owner_id)

        if assignee_id is not None:
            query = query.where(Task.assignee_id == assignee_id)

        if mine:
            query = query.where(
                (Task.owner_id == current_user.id) | (Task.assignee_id == current_user.id)
            )

        total = await self.db.scalar(
            select(func.count()).select_from(query.subquery())
        )

        query = query.order_by(Task.id.desc()).offset((page - 1) * size).limit(size)

        result = await self.db.scalars(query)
        items = result.all()

        return items, int(total or 0)

    async def update(self, task: Task, payload: TaskUpdate) -> Task:
        if payload.title is not None:
            task.title = payload.title
        if payload.description is not None:
            task.description = payload.description

        await self.db.commit()
        await self.db.refresh(task)
        return task

    async def update_status(self, task: Task, new_status: str) -> Task:
        allowed_statuses = {"todo", "in_progress", "done"}

        if new_status not in allowed_statuses:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status. Allowed: {', '.join(sorted(allowed_statuses))}",
            )

        task.status = new_status
        await self.db.commit()
        await self.db.refresh(task)
        return task

    async def assign(self, task: Task, assignee: User) -> Task:
        task.assignee_id = assignee.id
        await self.db.commit()
        await self.db.refresh(task)
        return task