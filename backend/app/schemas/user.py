from typing import Optional, List, Any
from pydantic import BaseModel, ConfigDict, field_validator


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    full_name: str
    phone: Optional[str] = None
    is_active: bool
    groups: List[str] = []

    @field_validator("groups", mode="before")
    @classmethod
    def coerce_groups(cls, v: Any) -> List[str]:
        """Accept both list[str] and list[PermissionGroup] objects."""
        result = []
        for item in v:
            if isinstance(item, str):
                result.append(item)
            else:
                result.append(item.sysname)
        return result


class UserCreate(BaseModel):
    email: str
    password: str
    full_name: str
    phone: Optional[str] = None
    groups: List[str] = []


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    is_active: Optional[bool] = None


class MasterOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    full_name: str
    phone: Optional[str] = None
