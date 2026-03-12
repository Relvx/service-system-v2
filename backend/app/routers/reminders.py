from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_

from app.dependencies import get_db, require_groups
from app.models.reminder import Reminder
from app.models.user import User
from app.schemas.reminder import ReminderOut, ReminderCreate

router = APIRouter(prefix="/reminders", tags=["reminders"])


@router.get("", response_model=List[ReminderOut])
async def get_reminders(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_groups("office_group", "admin_group")),
):
    """Return shared reminders + current user's personal reminders."""
    stmt = (
        select(Reminder)
        .where(
            or_(
                Reminder.is_personal == False,
                Reminder.created_by_user_id == current_user.id,
            )
        )
        .order_by(Reminder.is_personal, Reminder.created_at.desc())
    )
    result = await db.execute(stmt)
    reminders = result.scalars().all()

    # Load creators
    user_ids = {r.created_by_user_id for r in reminders}
    creators = {}
    if user_ids:
        ur = await db.execute(select(User).where(User.id.in_(user_ids)))
        for u in ur.scalars().all():
            creators[u.id] = u

    return [
        ReminderOut(
            id=r.id, text=r.text, is_personal=r.is_personal,
            created_by_user_id=r.created_by_user_id,
            created_by_name=creators.get(r.created_by_user_id, {}) and creators[r.created_by_user_id].full_name,
            created_at=r.created_at,
        )
        for r in reminders
    ]


@router.post("", response_model=ReminderOut, status_code=status.HTTP_201_CREATED)
async def create_reminder(
    body: ReminderCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_groups("office_group", "admin_group")),
):
    reminder = Reminder(
        text=body.text,
        is_personal=body.is_personal,
        created_by_user_id=current_user.id,
    )
    db.add(reminder)
    await db.commit()
    await db.refresh(reminder)
    return ReminderOut(
        id=reminder.id, text=reminder.text, is_personal=reminder.is_personal,
        created_by_user_id=reminder.created_by_user_id,
        created_by_name=current_user.full_name,
        created_at=reminder.created_at,
    )


@router.delete("/{reminder_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_reminder(
    reminder_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_groups("office_group", "admin_group")),
):
    result = await db.execute(select(Reminder).where(Reminder.id == reminder_id))
    reminder = result.scalar_one_or_none()
    if reminder is None:
        raise HTTPException(status_code=404, detail="Reminder not found")
    # Personal reminders can only be deleted by their owner
    if reminder.is_personal and reminder.created_by_user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Cannot delete another user's personal reminder")
    await db.delete(reminder)
    await db.commit()
