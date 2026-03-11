from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class AttachmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    visit_id: Optional[int] = None
    client_id: Optional[int] = None
    site_id: Optional[int] = None
    defect_id: Optional[int] = None
    kind: str
    file_url: str
    file_name: Optional[str] = None
    created_by_user_id: Optional[int] = None
    created_at: datetime


class AttachmentCreate(BaseModel):
    visit_id: Optional[int] = None
    client_id: Optional[int] = None
    site_id: Optional[int] = None
    defect_id: Optional[int] = None
    kind: str = "document"
    file_url: str
    file_name: Optional[str] = None
