from datetime import datetime, date
from typing import Optional, List
from pydantic import BaseModel, ConfigDict


class AttachmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    visit_id: Optional[int] = None
    client_id: Optional[int] = None
    site_id: Optional[int] = None
    defect_id: Optional[int] = None
    task_id: Optional[int] = None
    kind: str
    file_url: str
    file_name: Optional[str] = None
    created_by_user_id: Optional[int] = None
    created_at: datetime


class AttachmentGalleryItem(BaseModel):
    id: int
    file_url: str
    file_name: Optional[str] = None
    created_at: datetime
    visit_id: Optional[int] = None
    visit_date: Optional[date] = None
    site_id: Optional[int] = None
    site_title: Optional[str] = None
    client_id: Optional[int] = None
    client_name: Optional[str] = None


class AttachmentGalleryPage(BaseModel):
    items: List[AttachmentGalleryItem]
    total: int


class AttachmentCreate(BaseModel):
    visit_id: Optional[int] = None
    client_id: Optional[int] = None
    site_id: Optional[int] = None
    defect_id: Optional[int] = None
    task_id: Optional[int] = None
    kind: str = "document"
    file_url: str
    file_name: Optional[str] = None
