from uuid import UUID
from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel, ConfigDict


class LogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: Optional[UUID] = None
    action_sysname: Optional[str] = None
    entity_type: str
    entity_id: UUID
    details: Optional[Any] = None
    created_at: datetime
    # Денормализованное имя пользователя (заполняется в роутере)
    user_name: Optional[str] = None
