from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.dependencies import get_db, get_current_user
from app.models.attachment import Attachment
from app.models.visit import Visit
from app.models.site import Site
from app.models.client import Client
from app.models.user import User
from app.schemas.attachment import AttachmentOut, AttachmentCreate, AttachmentGalleryPage

router = APIRouter(prefix="/attachments", tags=["attachments"])


@router.get("/gallery", response_model=AttachmentGalleryPage)
async def get_gallery(
    limit: int = 20,
    offset: int = 0,
    site_id: Optional[int] = None,
    client_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    base = (
        select(
            Attachment.id,
            Attachment.file_url,
            Attachment.file_name,
            Attachment.created_at,
            Attachment.visit_id,
            Visit.planned_date.label("visit_date"),
            Site.id.label("site_id"),
            Site.title.label("site_title"),
            Client.id.label("client_id"),
            Client.name.label("client_name"),
        )
        .where(Attachment.kind == "act_photo")
        .outerjoin(Visit, Attachment.visit_id == Visit.id)
        .outerjoin(Site, Visit.site_id == Site.id)
        .outerjoin(Client, Site.client_id == Client.id)
    )
    if site_id is not None:
        base = base.where(Visit.site_id == site_id)
    if client_id is not None:
        base = base.where(Client.id == client_id)

    total_res = await db.execute(select(func.count()).select_from(base.subquery()))
    total = total_res.scalar() or 0

    rows = await db.execute(base.order_by(Attachment.created_at.desc()).offset(offset).limit(limit))
    items = [
        {
            "id": r.id,
            "file_url": r.file_url,
            "file_name": r.file_name,
            "created_at": r.created_at,
            "visit_id": r.visit_id,
            "visit_date": r.visit_date,
            "site_id": r.site_id,
            "site_title": r.site_title,
            "client_id": r.client_id,
            "client_name": r.client_name,
        }
        for r in rows.all()
    ]
    return {"items": items, "total": total}


@router.get("", response_model=List[AttachmentOut])
async def get_attachments(
    visit_id: Optional[int] = None,
    client_id: Optional[int] = None,
    site_id: Optional[int] = None,
    defect_id: Optional[int] = None,
    task_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    stmt = select(Attachment)
    if visit_id is not None:
        stmt = stmt.where(Attachment.visit_id == visit_id)
    if client_id is not None:
        stmt = stmt.where(Attachment.client_id == client_id)
    if site_id is not None:
        stmt = stmt.where(Attachment.site_id == site_id)
    if defect_id is not None:
        stmt = stmt.where(Attachment.defect_id == defect_id)
    if task_id is not None:
        stmt = stmt.where(Attachment.task_id == task_id)
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
        task_id=body.task_id,
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
