from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class ReminderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    text: str
    is_personal: bool
    created_by_user_id: int
    created_by_name: Optional[str] = None
    created_at: datetime


class ReminderCreate(BaseModel):
    text: str
    is_personal: bool = False
