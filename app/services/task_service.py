from sqlalchemy import select, func
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
        user: User,
        page: int = 1,
        size: int = 10,
        status: str | None = None,
    ):
        query = select(Task)

        if status:
            query = query.where(Task.status == status)

        total = await self.db.scalar(select(func.count()).select_from(query.subquery()))

        query = query.offset((page - 1) * size).limit(size)

        result = await self.db.scalars(query)
        items = result.all()

        return items, total

    async def update(self, task: Task, payload: TaskUpdate):
        if payload.title is not None:
            task.title = payload.title
        if payload.description is not None:
            task.description = payload.description

        await self.db.commit()
        await self.db.refresh(task)
        return task