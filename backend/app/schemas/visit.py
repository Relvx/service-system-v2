from uuid import UUID
from datetime import datetime, date, time
from typing import Optional, Any
from pydantic import BaseModel, ConfigDict


class VisitOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    site_id: Optional[UUID] = None
    assigned_user_id: Optional[UUID] = None
    planned_date: date
    planned_time_from: Optional[time] = None
    planned_time_to: Optional[time] = None
    visit_type: str
    priority: str
    status: str
    work_summary: Optional[str] = None
    checklist: Optional[Any] = None
    defects_present: bool
    defects_summary: Optional[str] = None
    recommendations: Optional[str] = None
    completed_at: Optional[datetime] = None
    office_notes: Optional[str] = None
    is_archived: bool = False
    created_at: datetime
    updated_at: datetime
    # joined fields
    site_title: Optional[str] = None
    site_address: Optional[str] = None
    client_name: Optional[str] = None
    master_name: Optional[str] = None
    master_phone: Optional[str] = None
    access_notes: Optional[str] = None
    onsite_contact: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    client_contacts: Optional[str] = None
    act_photos_count: Optional[int] = None


class VisitCreate(BaseModel):
    site_id: UUID
    assigned_user_id: UUID
    planned_date: date
    planned_time_from: Optional[time] = None
    planned_time_to: Optional[time] = None
    visit_type: str = "maintenance"
    priority: str = "medium"
    work_summary: Optional[str] = None
    office_notes: Optional[str] = None


class VisitUpdate(BaseModel):
    site_id: Optional[UUID] = None
    assigned_user_id: Optional[UUID] = None
    planned_date: Optional[date] = None
    planned_time_from: Optional[time] = None
    planned_time_to: Optional[time] = None
    visit_type: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    work_summary: Optional[str] = None
    checklist: Optional[Any] = None
    defects_present: Optional[bool] = None
    defects_summary: Optional[str] = None
    recommendations: Optional[str] = None
    office_notes: Optional[str] = None


class VisitComplete(BaseModel):
    work_summary: Optional[str] = None
    checklist: Optional[Any] = None
    defects_present: Optional[bool] = False
    defects_summary: Optional[str] = None
    recommendations: Optional[str] = None
