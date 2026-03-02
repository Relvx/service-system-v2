from uuid import UUID
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict


class SiteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    client_id: Optional[UUID] = None
    title: str
    address: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    access_notes: Optional[str] = None
    onsite_contact: Optional[str] = None
    service_frequency: Optional[str] = None
    is_active: bool
    is_archived: bool
    created_at: datetime
    updated_at: datetime
    # joined fields
    client_name: Optional[str] = None
    total_visits: Optional[int] = None


class SiteCreate(BaseModel):
    client_id: Optional[UUID] = None
    title: str
    address: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    access_notes: Optional[str] = None
    onsite_contact: Optional[str] = None
    service_frequency: Optional[str] = None


class SiteUpdate(BaseModel):
    client_id: Optional[UUID] = None
    title: Optional[str] = None
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    access_notes: Optional[str] = None
    onsite_contact: Optional[str] = None
    service_frequency: Optional[str] = None
    is_active: Optional[bool] = None
