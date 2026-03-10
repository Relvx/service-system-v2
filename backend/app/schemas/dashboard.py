from datetime import date
from typing import List, Optional
from pydantic import BaseModel


class DefectPriorityCount(BaseModel):
    priority: str
    count: int


class VisitShort(BaseModel):
    id: int
    planned_date: date
    status: str
    visit_type: str
    site_title: Optional[str] = None
    client_name: Optional[str] = None
    master_name: Optional[str] = None


class DashboardStats(BaseModel):
    visits_today: int
    visits_this_week: int
    open_defects: List[DefectPriorityCount]
    active_purchases: int
    today_visits: List[VisitShort]
    recent_completed: List[VisitShort]
