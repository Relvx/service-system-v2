from datetime import datetime, date
from typing import Optional
from pydantic import BaseModel, ConfigDict


class TaskOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: Optional[str] = None
    deadline: Optional[date] = None
    is_done: bool
    created_by_user_id: Optional[int] = None
    created_by_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    deadline: Optional[date] = None


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    deadline: Optional[date] = None
    is_done: Optional[bool] = None
