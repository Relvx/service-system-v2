from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.dependencies import get_db, get_current_user
from app.models.attachment import Attachment
from app.models.user import User
from app.schemas.attachment import AttachmentOut, AttachmentCreate

router = APIRouter(prefix="/attachments", tags=["attachments"])


@router.get("", response_model=List[AttachmentOut])
async def get_attachments(
    visit_id: Optional[int] = None,
    client_id: Optional[int] = None,
    site_id: Optional[int] = None,
    defect_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    stmt = select(Attachment)
    if visit_id is not None:
        stmt = stmt.where(Attachment.visit_id == visit_id)
    elif client_id is not None:
        stmt = stmt.where(Attachment.client_id == client_id)
    elif site_id is not None:
        stmt = stmt.where(Attachment.site_id == site_id)
    elif defect_id is not None:
        stmt = stmt.where(Attachment.defect_id == defect_id)
    stmt = stmt.order_by(Attachment.created_at)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("", response_model=AttachmentOut, status_code=status.HTTP_201_CREATED)
async def upload_attachment(
    body: AttachmentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    att = Attachment(
        visit_id=body.visit_id,
        client_id=body.client_id,
        site_id=body.site_id,
        defect_id=body.defect_id,
        kind=body.kind,
        file_url=body.file_url,
        file_name=body.file_name,
        created_by_user_id=current_user.id,
    )
    db.add(att)
    await db.commit()
    await db.refresh(att)
    return att


@router.delete("/{attachment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_attachment(
    attachment_id: int,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    result = await db.execute(select(Attachment).where(Attachment.id == attachment_id))
    att = result.scalar_one_or_none()
    if att is None:
        raise HTTPException(status_code=404, detail="Attachment not found")
    await db.delete(att)
    await db.commit()
