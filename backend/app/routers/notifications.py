from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.dependencies import get_db, get_current_user
from app.models.notification import Notification
from app.models.user import User
from app.schemas.notification import NotificationOut

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=List[NotificationOut])
async def get_notifications(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Notification)
        .where(Notification.user_id == current_user.id)
        .order_by(Notification.created_at.desc())
        .limit(50)
    )
    return result.scalars().all()


@router.put("/{notif_id}/read")
async def mark_read(
    notif_id: UUID,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    result = await db.execute(select(Notification).where(Notification.id == notif_id))
    n = result.scalar_one_or_none()
    if n is None:
        raise HTTPException(status_code=404, detail="Notification not found")
    n.is_read = True
    await db.commit()
    return {"message": "Marked as read"}


@router.put("/{notif_id}/unread")
async def mark_unread(
    notif_id: UUID,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    result = await db.execute(select(Notification).where(Notification.id == notif_id))
    n = result.scalar_one_or_none()
    if n is None:
        raise HTTPException(status_code=404, detail="Notification not found")
    n.is_read = False
    await db.commit()
    return {"message": "Marked as unread"}
