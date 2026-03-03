from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.dependencies import get_db, get_current_user
from app.models.attachment import Attachment
from app.models.user import User
from app.schemas.attachment import AttachmentOut, AttachmentCreate

router = APIRouter(prefix="/attachments", tags=["attachments"])


@router.get("", response_model=List[AttachmentOut])
async def get_attachments(
    visit_id: int,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    result = await db.execute(
        select(Attachment).where(Attachment.visit_id == visit_id).order_by(Attachment.created_at)
    )
    return result.scalars().all()


@router.post("", response_model=AttachmentOut, status_code=status.HTTP_201_CREATED)
async def upload_attachment(
    body: AttachmentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    att = Attachment(
        visit_id=body.visit_id,
        kind=body.kind,
        file_url=body.file_url,
        created_by_user_id=current_user.id,
    )
    db.add(att)
    await db.commit()
    await db.refresh(att)
    return att
