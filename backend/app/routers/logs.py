"""Роутер аудит-лога — просмотр истории действий (admin + office)."""

from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.dependencies import get_db, require_groups
from app.models.log import Log
from app.models.user import User
from app.schemas.log import LogOut

router = APIRouter(prefix="/logs", tags=["logs"])

_office_or_admin = Depends(require_groups("admin_group", "office_group"))


@router.get("", response_model=List[LogOut])
async def get_logs(
    entity_type: Optional[str] = None,
    entity_id: Optional[UUID] = None,
    action_sysname: Optional[str] = None,
    user_id: Optional[UUID] = None,
    limit: int = Query(default=100, le=500),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    _=_office_or_admin,
):
    """Вернуть список записей аудит-лога с опциональной фильтрацией."""
    stmt = (
        select(Log, User.full_name.label("user_name"))
        .outerjoin(User, Log.user_id == User.id)
        .order_by(desc(Log.created_at))
        .limit(limit)
        .offset(offset)
    )

    if entity_type:
        stmt = stmt.where(Log.entity_type == entity_type)
    if entity_id:
        stmt = stmt.where(Log.entity_id == entity_id)
    if action_sysname:
        stmt = stmt.where(Log.action_sysname == action_sysname)
    if user_id:
        stmt = stmt.where(Log.user_id == user_id)

    result = await db.execute(stmt)
    rows = result.all()

    out = []
    for row in rows:
        log = row[0]
        obj = LogOut.model_validate(log)
        obj.user_name = row[1]
        out.append(obj)
    return out
