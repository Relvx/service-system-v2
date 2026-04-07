from datetime import datetime, date, time
from typing import Optional, Any, List
from pydantic import BaseModel, ConfigDict


class VisitOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    site_id: Optional[int] = None
    assigned_user_id: Optional[int] = None
    planned_date: date
    planned_time_from: Optional[time] = None
    planned_time_to: Optional[time] = None
    visit_type: str
    visit_types: Optional[List[str]] = None  # множественные типы
    priority: str
    status: str
    work_summary: Optional[str] = None
    checklist: Optional[Any] = None
    defects_present: bool
    defects_summary: Optional[str] = None
    recommendations: Optional[str] = None
    completed_at: Optional[datetime] = None
    office_notes: Optional[str] = None
    cost: Optional[float] = None
    contract_id: Optional[int] = None
    is_archived: bool = False
    created_at: datetime
    updated_at: datetime
    # joined fields
    site_title: Optional[str] = None
    site_address: Optional[str] = None
    client_name: Optional[str] = None
    client_id: Optional[int] = None
    master_name: Optional[str] = None
    master_phone: Optional[str] = None
    access_notes: Optional[str] = None
    onsite_contact: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    client_contacts: Optional[str] = None
    act_photos_count: Optional[int] = None
    # многомастерность
    master_ids: List[int] = []
    master_names: List[str] = []

    @property
    def visit_types_list(self) -> List[str]:
        """Возвращает список типов: visit_types если задан, иначе [visit_type]."""
        return self.visit_types if self.visit_types else [self.visit_type]


class VisitCreate(BaseModel):
    site_id: int
    assigned_user_id: Optional[int] = None
    master_ids: Optional[List[int]] = None       # несколько мастеров; если задан, assigned_user_id = master_ids[0]
    planned_date: date
    planned_time_from: Optional[time] = None
    planned_time_to: Optional[time] = None
    visit_type: str = "maintenance"
    visit_types: Optional[List[str]] = None      # несколько типов
    priority: str = "medium"
    status: Optional[str] = None                 # None → 'planned'; 'done' для исторических
    work_summary: Optional[str] = None
    defects_present: Optional[bool] = None
    office_notes: Optional[str] = None
    cost: Optional[float] = None
    contract_id: Optional[int] = None


class VisitUpdate(BaseModel):
    site_id: Optional[int] = None
    assigned_user_id: Optional[int] = None
    master_ids: Optional[List[int]] = None
    planned_date: Optional[date] = None
    planned_time_from: Optional[time] = None
    planned_time_to: Optional[time] = None
    visit_type: Optional[str] = None
    visit_types: Optional[List[str]] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    work_summary: Optional[str] = None
    checklist: Optional[Any] = None
    defects_present: Optional[bool] = None
    defects_summary: Optional[str] = None
    recommendations: Optional[str] = None
    office_notes: Optional[str] = None
    cost: Optional[float] = None
    contract_id: Optional[int] = None


class VisitComplete(BaseModel):
    work_summary: Optional[str] = None
    checklist: Optional[Any] = None
    defects_present: Optional[bool] = False
    defects_summary: Optional[str] = None
    recommendations: Optional[str] = None
