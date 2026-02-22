from typing import List
from pydantic import BaseModel


class DefectPriorityCount(BaseModel):
    priority: str
    count: int


class DashboardStats(BaseModel):
    visits_today: int
    visits_this_week: int
    open_defects: List[DefectPriorityCount]
    active_purchases: int
