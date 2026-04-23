from datetime import datetime
from pydantic import BaseModel, ConfigDict


class TaskCreate(BaseModel):
    title: str
    description: str | None = None


class TaskUpdate(BaseModel):
    title: str | None = None
    description: str | None = None


class TaskStatusUpdate(BaseModel):
    status: str


class TaskAssign(BaseModel):
    user_id: int


class TaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str | None
    status: str

    owner_id: int
    assignee_id: int | None

    created_at: datetime
    updated_at: datetime