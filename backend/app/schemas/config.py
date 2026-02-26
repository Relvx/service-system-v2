from typing import List, Optional
from pydantic import BaseModel, ConfigDict


class RoleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    sysname: str
    display_name: str
    default_redirect: str


class VisitStatusOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    sysname: str
    display_name: str


class VisitTypeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    sysname: str
    display_name: str


class PriorityOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    sysname: str
    display_name: str
    sort_order: int


class DefectStatusOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    sysname: str
    display_name: str


class DefectActionTypeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    sysname: str
    display_name: str


class AttachmentKindOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    sysname: str
    display_name: str


class PurchaseStatusOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    sysname: str
    display_name: str


class ServiceFrequencyOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    sysname: str
    display_name: str


class NotificationTypeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    sysname: str
    display_name: str


# ─── Permission / Group schemas ─────────────────────────────────────────────

class PermissionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    sysname: str
    display_name: str
    resource: str
    action: str


class PermissionGroupOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    sysname: str
    display_name: str
    default_redirect: str
    permissions: List[PermissionOut] = []


# ─── Config CRUD input schemas ──────────────────────────────────────────────

class ConfigItemCreate(BaseModel):
    sysname: str
    display_name: str
    sort_order: Optional[int] = None
    default_redirect: Optional[str] = None


class ConfigItemUpdate(BaseModel):
    display_name: Optional[str] = None
    sort_order: Optional[int] = None
    default_redirect: Optional[str] = None
