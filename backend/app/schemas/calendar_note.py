from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class CalendarNoteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    date: date
    text: str
    created_by_user_id: int
    created_by_name: Optional[str] = None
    created_at: datetime


class CalendarNoteCreate(BaseModel):
    date: date
    text: str


class CalendarNoteUpdate(BaseModel):
    text: str
