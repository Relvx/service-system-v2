from uuid import UUID
from datetime import datetime
from typing import Optional
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
