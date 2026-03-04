from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict


class SiteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    client_id: Optional[int] = None
    title: str
    address: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    access_notes: Optional[str] = None
    onsite_contact: Optional[str] = None
    service_frequency: Optional[str] = None
    price_maintenance: Optional[float] = None
    price_repair: Optional[float] = None
    price_emergency: Optional[float] = None
    is_active: bool
    is_archived: bool
    created_at: datetime
    updated_at: datetime
    # joined fields
    client_name: Optional[str] = None
    total_visits: Optional[int] = None


class SiteDetailOut(SiteOut):
    """Расширенная карточка объекта для страницы /sites/:id."""
    active_defects: List[dict] = []
    recent_visits: List[dict] = []


class SiteCreate(BaseModel):
    client_id: Optional[int] = None
    title: str
    address: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    access_notes: Optional[str] = None
    onsite_contact: Optional[str] = None
    service_frequency: Optional[str] = None
    price_maintenance: Optional[float] = None
    price_repair: Optional[float] = None
    price_emergency: Optional[float] = None


class SiteUpdate(BaseModel):
    client_id: Optional[int] = None
    title: Optional[str] = None
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    access_notes: Optional[str] = None
    onsite_contact: Optional[str] = None
    service_frequency: Optional[str] = None
    price_maintenance: Optional[float] = None
    price_repair: Optional[float] = None
    price_emergency: Optional[float] = None
    is_active: Optional[bool] = None
