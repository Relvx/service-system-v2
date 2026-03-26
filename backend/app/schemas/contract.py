from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, ConfigDict


class ContractSiteShort(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    address: str
    is_archived: bool


class ContractOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    client_id: Optional[int] = None
    client_name: Optional[str] = None
    contract_number: Optional[str] = None
    contract_date: Optional[date] = None
    subject: Optional[str] = None
    amount: Optional[Decimal] = None
    act_amount: Optional[Decimal] = None
    status: str
    notes: Optional[str] = None
    description: Optional[str] = None
    raw_visit_history: Optional[str] = None
    is_archived: bool
    created_at: datetime
    updated_at: datetime
    # joined counter
    sites_count: Optional[int] = None


class ContractDetailOut(ContractOut):
    sites: List[ContractSiteShort] = []


class ContractCreate(BaseModel):
    client_id: Optional[int] = None
    contract_number: Optional[str] = None
    contract_date: Optional[date] = None
    subject: Optional[str] = None
    amount: Optional[Decimal] = None
    act_amount: Optional[Decimal] = None
    status: str = "active"
    notes: Optional[str] = None


class ContractUpdate(BaseModel):
    contract_number: Optional[str] = None
    contract_date: Optional[date] = None
    subject: Optional[str] = None
    amount: Optional[Decimal] = None
    act_amount: Optional[Decimal] = None
    status: Optional[str] = None
    notes: Optional[str] = None
    description: Optional[str] = None
    raw_visit_history: Optional[str] = None
    is_archived: Optional[bool] = None


# ── Для списка договоров в карточке клиента ───────────────────────────────

class ClientContractShort(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    contract_number: Optional[str] = None
    contract_date: Optional[date] = None
    subject: Optional[str] = None
    amount: Optional[Decimal] = None
    status: str
    sites_count: int = 0
