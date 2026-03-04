from datetime import datetime, date
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, ConfigDict


class PurchaseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    defect_id: Optional[int] = None
    site_id: Optional[int] = None
    item: str
    qty: Decimal
    status: str
    due_date: Optional[date] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    # joined fields
    defect_title: Optional[str] = None
    site_title: Optional[str] = None


class PurchaseCreate(BaseModel):
    defect_id: Optional[int] = None
    site_id: Optional[int] = None
    item: str
    qty: Decimal = Decimal("1")
    due_date: Optional[date] = None
    notes: Optional[str] = None


class PurchaseUpdate(BaseModel):
    item: Optional[str] = None
    qty: Optional[Decimal] = None
    status: Optional[str] = None
    due_date: Optional[date] = None
    notes: Optional[str] = None
