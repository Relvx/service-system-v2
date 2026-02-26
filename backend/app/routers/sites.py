from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text

from app.dependencies import get_db, get_current_user
from app.models.site import Site
from app.models.client import Client
from app.models.visit import Visit
from app.models.history import SiteHistory
from app.schemas.site import SiteOut, SiteCreate, SiteUpdate
from app.utils.audit import save_history, save_log

router = APIRouter(prefix="/sites", tags=["sites"])


@router.get("", response_model=List[SiteOut])
async def get_sites(
    client_id: Optional[UUID] = None,
    search: Optional[str] = None,
    active_only: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    from sqlalchemy.orm import aliased

    # subquery for total_visits
    visit_count = (
        select(func.count()).where(Visit.site_id == Site.id).correlate(Site).scalar_subquery()
    )

    stmt = (
        select(
            Site,
            Client.name.label("client_name"),
            visit_count.label("total_visits"),
        )
        .outerjoin(Client, Site.client_id == Client.id)
    )

    if active_only:
        stmt = stmt.where(Site.is_active == True)
    if client_id:
        stmt = stmt.where(Site.client_id == client_id)
    if search:
        stmt = stmt.where(
            Site.title.ilike(f"%{search}%") | Site.address.ilike(f"%{search}%")
        )

    stmt = stmt.order_by(Site.title)
    result = await db.execute(stmt)
    rows = result.all()

    out = []
    for row in rows:
        site = row[0]
        obj = SiteOut.model_validate(site)
        obj.client_name = row[1]
        obj.total_visits = row[2]
        out.append(obj)
    return out


@router.get("/{site_id}", response_model=SiteOut)
async def get_site(site_id: UUID, db: AsyncSession = Depends(get_db), _=Depends(get_current_user)):
    stmt = (
        select(Site, Client.name.label("client_name"))
        .outerjoin(Client, Site.client_id == Client.id)
        .where(Site.id == site_id)
    )
    result = await db.execute(stmt)
    row = result.first()
    if row is None:
        raise HTTPException(status_code=404, detail="Site not found")
    site = row[0]
    obj = SiteOut.model_validate(site)
    obj.client_name = row[1]
    return obj


@router.post("", response_model=SiteOut, status_code=status.HTTP_201_CREATED)
async def create_site(
    body: SiteCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    site = Site(**body.model_dump())
    db.add(site)
    await db.flush()
    await save_log(db, current_user.id, "create", "site", site.id)
    await db.commit()
    await db.refresh(site)
    return SiteOut.model_validate(site)


@router.put("/{site_id}", response_model=SiteOut)
async def update_site(
    site_id: UUID,
    body: SiteUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = await db.execute(select(Site).where(Site.id == site_id))
    site = result.scalar_one_or_none()
    if site is None:
        raise HTTPException(status_code=404, detail="Site not found")

    await save_history(db, SiteHistory, site, current_user.id)

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(site, field, value)

    await save_log(db, current_user.id, "update", "site", site_id)
    await db.commit()
    await db.refresh(site)
    return SiteOut.model_validate(site)


@router.delete("/{site_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_site(
    site_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = await db.execute(select(Site).where(Site.id == site_id))
    site = result.scalar_one_or_none()
    if site is None:
        raise HTTPException(status_code=404, detail="Site not found")
    await save_log(db, current_user.id, "delete", "site", site_id,
                   details={"title": site.title})
    await db.delete(site)
    await db.commit()
