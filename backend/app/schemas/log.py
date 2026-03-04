from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel, ConfigDict


class LogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: Optional[int] = None
    action_sysname: Optional[str] = None
    entity_type: str
    entity_id: int
    details: Optional[Any] = None
    created_at: datetime
    # Денормализованное имя пользователя (заполняется в роутере)
    user_name: Optional[str] = None
