from uuid import UUID
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class NotificationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    type: str
    title: str
    message: str
    related_visit_id: Optional[UUID] = None
    is_read: bool
    created_at: datetime
