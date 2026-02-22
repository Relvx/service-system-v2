from uuid import UUID
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class AttachmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    visit_id: Optional[UUID] = None
    kind: str
    file_url: str
    created_by_user_id: Optional[UUID] = None
    created_at: datetime


class AttachmentCreate(BaseModel):
    visit_id: UUID
    kind: str = "act_photo"
    file_url: str
