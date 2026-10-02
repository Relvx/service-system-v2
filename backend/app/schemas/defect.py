from datetime import datetime, date
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator


class DefectOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    visit_id: Optional[int] = None
    site_id: Optional[int] = None
    title: str
    description: Optional[str] = None
    priority: str
    action_type: str
    suggested_parts: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime
    # joined fields
    site_title: Optional[str] = None
    address: Optional[str] = None
    client_name: Optional[str] = None
    client_id: Optional[int] = None
    visit_date: Optional[date] = None
    visit_type: Optional[str] = None


class DefectCreate(BaseModel):
    visit_id: Optional[int] = None
    site_id: Optional[int] = None
    title: str
    description: Optional[str] = None
    priority: str = "medium"
    action_type: str = "repair"
    suggested_parts: Optional[str] = None


class DefectUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[str] = None
    action_type: Optional[str] = None
    suggested_parts: Optional[str] = None
    status: Optional[str] = None


class DefectCommentCreate(BaseModel):
    text: str = Field(min_length=1, max_length=10000)

    @field_validator("text")
    @classmethod
    def trim_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Введите комментарий")
        return value


class DefectCommentOut(BaseModel):
    id: int
    defect_id: int
    user_id: Optional[int] = None
    author_name: str
    text: str
    created_at: datetime
