from uuid import UUID
from datetime import datetime, date
from typing import Optional
from pydantic import BaseModel, ConfigDict


class DefectOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    visit_id: Optional[UUID] = None
    site_id: Optional[UUID] = None
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
    visit_date: Optional[date] = None
    visit_type: Optional[str] = None


class DefectCreate(BaseModel):
    visit_id: Optional[UUID] = None
    site_id: Optional[UUID] = None
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
