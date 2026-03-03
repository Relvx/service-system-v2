from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.dependencies import get_db, get_current_user, require_groups
from app.models.site import Site
from app.models.client import Client
from app.models.visit import Visit
from app.models.defect import Defect
from app.models.user import User
from app.models.history import SiteHistory
from app.schemas.site import SiteOut, SiteDetailOut, SiteCreate, SiteUpdate
from app.utils.audit import save_history, save_log
from app.enums import enums

router = APIRouter(prefix="/sites", tags=["sites"])


@router.get("", response_model=List[SiteOut])
async def get_sites(
    client_id: Optional[UUID] = None,
    search: Optional[str] = None,
    active_only: Optional[bool] = None,
    show_archived: bool = False,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    visit_count = (
        select(func.count()).where(Visit.site_id == Site.id).correlate(Site).scalar_subquery()
    )

    stmt = (
        select(Site, Client.name.label("client_name"), visit_count.label("total_visits"))
        .outerjoin(Client, Site.client_id == Client.id)
    )

    if not show_archived:
        stmt = stmt.where(Site.is_archived == False)
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


@router.get("/{site_id}", response_model=SiteDetailOut)
async def get_site(site_id: UUID, db: AsyncSession = Depends(get_db), _=Depends(get_current_user)):
    # Base site + client name
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
    obj = SiteDetailOut.model_validate(site)
    obj.client_name = row[1]

    # Total visits count
    visit_count_res = await db.execute(
        select(func.count()).where(Visit.site_id == site_id)
    )
    obj.total_visits = visit_count_res.scalar()

    # Active defects (not fixed/cancelled)
    defects_stmt = (
        select(Defect)
        .where(
            Defect.site_id == site_id,
            Defect.status != enums.defect_statuses.fixed,
        )
        .order_by(Defect.created_at.desc())
    )
    defects_res = await db.execute(defects_stmt)
    defects = defects_res.scalars().all()
    obj.active_defects = [
        {
            "id": str(d.id),
            "title": d.title,
            "priority": d.priority,
            "status": d.status,
            "action_type": d.action_type,
            "description": d.description,
            "created_at": d.created_at.isoformat(),
        }
        for d in defects
    ]

    # Recent visits (last 10)
    visits_stmt = (
        select(Visit, User.full_name.label("master_name"))
        .outerjoin(User, Visit.assigned_user_id == User.id)
        .where(Visit.site_id == site_id)
        .order_by(Visit.planned_date.desc())
        .limit(10)
    )
    visits_res = await db.execute(visits_stmt)
    visits_rows = visits_res.all()
    obj.recent_visits = [
        {
            "id": str(v[0].id),
            "planned_date": str(v[0].planned_date),
            "visit_type": v[0].visit_type,
            "priority": v[0].priority,
            "status": v[0].status,
            "master_name": v[1],
            "work_summary": v[0].work_summary,
            "cost": v[0].cost,
        }
        for v in visits_rows
    ]

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
    await save_log(db, current_user.id, enums.log_actions.site_create, "site", site.id)
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

    changed = body.model_dump(exclude_unset=True)
    await save_history(db, SiteHistory, site, current_user.id,
                       method="update", new_values=changed)

    for field, value in changed.items():
        setattr(site, field, value)

    await save_log(db, current_user.id, enums.log_actions.site_update, "site", site_id,
                   details={"changed": list(changed.keys())})
    await db.commit()
    await db.refresh(site)
    return SiteOut.model_validate(site)


@router.patch("/{site_id}/archive", response_model=SiteOut)
async def archive_site(
    site_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = await db.execute(select(Site).where(Site.id == site_id))
    site = result.scalar_one_or_none()
    if site is None:
        raise HTTPException(status_code=404, detail="Site not found")

    site.is_archived = True
    await save_log(db, current_user.id, enums.log_actions.site_delete, "site", site_id,
                   details={"title": site.title, "action": "archive"})
    await db.commit()
    await db.refresh(site)
    return SiteOut.model_validate(site)


@router.patch("/{site_id}/unarchive", response_model=SiteOut)
async def unarchive_site(
    site_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_groups("admin_group")),
):
    result = await db.execute(select(Site).where(Site.id == site_id))
    site = result.scalar_one_or_none()
    if site is None:
        raise HTTPException(status_code=404, detail="Site not found")

    site.is_archived = False
    await save_log(db, current_user.id, enums.log_actions.site_update, "site", site_id,
                   details={"title": site.title, "action": "unarchive"})
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
    await save_log(db, current_user.id, enums.log_actions.site_delete, "site", site_id,
                   details={"title": site.title})
    await db.delete(site)
    await db.commit()
