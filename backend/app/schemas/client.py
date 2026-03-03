from uuid import UUID
from datetime import datetime, date
from typing import Optional, List
from pydantic import BaseModel, ConfigDict


class ClientOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    inn: Optional[str] = None
    kpp: Optional[str] = None
    contacts: Optional[str] = None
    contact_person: Optional[str] = None
    notes: Optional[str] = None
    is_active: bool
    is_archived: bool
    created_at: datetime
    updated_at: datetime


class ClientCreate(BaseModel):
    name: str
    inn: Optional[str] = None
    kpp: Optional[str] = None
    contacts: Optional[str] = None
    contact_person: Optional[str] = None
    notes: Optional[str] = None


class ClientUpdate(BaseModel):
    name: Optional[str] = None
    inn: Optional[str] = None
    kpp: Optional[str] = None
    contacts: Optional[str] = None
    contact_person: Optional[str] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None


# ── Контакты ──────────────────────────────────────────────────────────────

class ClientContactOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    client_id: UUID
    full_name: str
    position: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    is_primary: bool
    created_at: datetime


class ClientContactCreate(BaseModel):
    full_name: str
    position: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    is_primary: bool = False


class ClientContactUpdate(BaseModel):
    full_name: Optional[str] = None
    position: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    is_primary: Optional[bool] = None


# ── Юридические реквизиты ─────────────────────────────────────────────────

class ClientLegalOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    client_id: UUID
    legal_address: Optional[str] = None
    bank: Optional[str] = None
    bik: Optional[str] = None
    account: Optional[str] = None


class ClientLegalUpdate(BaseModel):
    legal_address: Optional[str] = None
    bank: Optional[str] = None
    bik: Optional[str] = None
    account: Optional[str] = None


# ── Детальная карточка клиента ────────────────────────────────────────────

class ClientSiteShort(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    address: str
    service_frequency: Optional[str] = None
    is_archived: bool


class ClientVisitShort(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    site_id: Optional[UUID] = None
    site_title: Optional[str] = None
    planned_date: date
    status: str
    visit_type: str
    priority: str
    master_name: Optional[str] = None


class ClientDetailOut(ClientOut):
    contact_persons: List[ClientContactOut] = []
    legal: Optional[ClientLegalOut] = None
    sites: List[ClientSiteShort] = []
    recent_visits: List[ClientVisitShort] = []
