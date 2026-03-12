from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import extract, select

from app.dependencies import get_db, require_groups
from app.models.calendar_note import CalendarNote
from app.models.user import User
from app.schemas.calendar_note import CalendarNoteCreate, CalendarNoteOut, CalendarNoteUpdate

router = APIRouter(prefix="/calendar-notes", tags=["calendar-notes"])


@router.get("", response_model=List[CalendarNoteOut])
async def get_calendar_notes(
    year: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_groups("office_group", "admin_group")),
):
    stmt = select(CalendarNote).order_by(CalendarNote.date)
    if year:
        stmt = stmt.where(extract("year", CalendarNote.date) == year)
    result = await db.execute(stmt)
    notes = result.scalars().all()

    user_ids = {n.created_by_user_id for n in notes}
    creators = {}
    if user_ids:
        ur = await db.execute(select(User).where(User.id.in_(user_ids)))
        for u in ur.scalars().all():
            creators[u.id] = u

    return [
        CalendarNoteOut(
            id=n.id, date=n.date, text=n.text,
            created_by_user_id=n.created_by_user_id,
            created_by_name=creators.get(n.created_by_user_id) and creators[n.created_by_user_id].full_name,
            created_at=n.created_at,
        )
        for n in notes
    ]


@router.post("", response_model=CalendarNoteOut, status_code=status.HTTP_201_CREATED)
async def create_calendar_note(
    body: CalendarNoteCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_groups("office_group", "admin_group")),
):
    note = CalendarNote(
        date=body.date,
        text=body.text,
        created_by_user_id=current_user.id,
    )
    db.add(note)
    await db.commit()
    await db.refresh(note)
    return CalendarNoteOut(
        id=note.id, date=note.date, text=note.text,
        created_by_user_id=note.created_by_user_id,
        created_by_name=current_user.full_name,
        created_at=note.created_at,
    )


@router.put("/{note_id}", response_model=CalendarNoteOut)
async def update_calendar_note(
    note_id: int,
    body: CalendarNoteUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_groups("office_group", "admin_group")),
):
    result = await db.execute(select(CalendarNote).where(CalendarNote.id == note_id))
    note = result.scalar_one_or_none()
    if note is None:
        raise HTTPException(status_code=404, detail="Note not found")
    note.text = body.text
    await db.commit()
    await db.refresh(note)
    return CalendarNoteOut(
        id=note.id, date=note.date, text=note.text,
        created_by_user_id=note.created_by_user_id,
        created_by_name=current_user.full_name,
        created_at=note.created_at,
    )


@router.delete("/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_calendar_note(
    note_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_groups("office_group", "admin_group")),
):
    result = await db.execute(select(CalendarNote).where(CalendarNote.id == note_id))
    note = result.scalar_one_or_none()
    if note is None:
        raise HTTPException(status_code=404, detail="Note not found")
    await db.delete(note)
    await db.commit()
