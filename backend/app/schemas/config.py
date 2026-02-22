from pydantic import BaseModel, ConfigDict


class RoleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    code: str
    display_name: str
    default_redirect: str


class VisitStatusOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    code: str
    display_name: str
    color: str


class VisitTypeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    code: str
    display_name: str


class PriorityOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    code: str
    display_name: str
    color: str
    sort_order: int


class DefectStatusOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    code: str
    display_name: str
    color: str


class DefectActionTypeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    code: str
    display_name: str


class AttachmentKindOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    code: str
    display_name: str


class PurchaseStatusOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    code: str
    display_name: str
    color: str


class ServiceFrequencyOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    code: str
    display_name: str


class NotificationTypeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    code: str
    display_name: str
