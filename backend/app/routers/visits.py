from typing import List, Optional
from datetime import date, datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.dependencies import get_db, get_current_user, require_groups
from app.models.visit import Visit
from app.models.site import Site
from app.models.client import Client
from app.models.user import User
from app.models.attachment import Attachment
from app.models.history import VisitHistory
from app.schemas.visit import VisitOut, VisitCreate, VisitUpdate, VisitComplete
from app.utils.notifications import create_notification
from app.utils.audit import save_history, save_log
from app.enums import enums

router = APIRouter(prefix="/visits", tags=["visits"])


def _build_visit_query(
    master_id=None, site_id=None, status_=None, date_from=None, date_to=None, priority=None
):
    act_count = (
        select(func.count())
        .where(Attachment.visit_id == Visit.id, Attachment.kind == "act_photo")
        .correlate(Visit)
        .scalar_subquery()
    )

    stmt = (
        select(
            Visit,
            Site.title.label("site_title"),
            Site.address.label("site_address"),
            Site.latitude,
            Site.longitude,
            Site.access_notes,
            Site.onsite_contact,
            Client.name.label("client_name"),
            Client.contacts.label("client_contacts"),
            User.full_name.label("master_name"),
            User.phone.label("master_phone"),
            act_count.label("act_photos_count"),
        )
        .outerjoin(Site, Visit.site_id == Site.id)
        .outerjoin(Client, Site.client_id == Client.id)
        .outerjoin(User, Visit.assigned_user_id == User.id)
    )

    if master_id:
        stmt = stmt.where(Visit.assigned_user_id == master_id)
    if site_id:
        stmt = stmt.where(Visit.site_id == site_id)
    if status_:
        if status_ == enums.visit_statuses.closed:
            stmt = stmt.where(Visit.status.in_(["done", enums.visit_statuses.closed]))
        else:
            stmt = stmt.where(Visit.status == status_)
    if priority:
        stmt = stmt.where(Visit.priority == priority)
    if date_from:
        stmt = stmt.where(Visit.planned_date >= date_from)
    if date_to:
        stmt = stmt.where(Visit.planned_date <= date_to)

    return stmt


def _row_to_visit_out(row) -> VisitOut:
    visit = row[0]
    obj = VisitOut.model_validate(visit)
    obj.site_title = row[1]
    obj.site_address = row[2]
    obj.latitude = row[3]
    obj.longitude = row[4]
    obj.access_notes = row[5]
    obj.onsite_contact = row[6]
    obj.client_name = row[7]
    obj.client_contacts = row[8]
    obj.master_name = row[9]
    obj.master_phone = row[10]
    obj.act_photos_count = row[11]
    return obj


@router.get("", response_model=List[VisitOut])
async def get_visits(
    master_id: Optional[int] = None,
    site_id: Optional[int] = None,
    status: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    priority: Optional[str] = None,
    show_archived: bool = False,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    stmt = _build_visit_query(master_id, site_id, status, date_from, date_to, priority)
    if not show_archived:
        stmt = stmt.where(Visit.is_archived == False)
    stmt = stmt.order_by(Visit.planned_date.desc(), Visit.planned_time_from)
    result = await db.execute(stmt)
    return [_row_to_visit_out(r) for r in result.all()]


@router.get("/calendar", response_model=List[VisitOut])
async def get_calendar(
    start: date,
    end: date,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    stmt = _build_visit_query(date_from=start, date_to=end)
    stmt = stmt.order_by(Visit.planned_date, Visit.planned_time_from)
    result = await db.execute(stmt)
    return [_row_to_visit_out(r) for r in result.all()]


@router.get("/{visit_id}", response_model=VisitOut)
async def get_visit(visit_id: int, db: AsyncSession = Depends(get_db), _=Depends(get_current_user)):
    stmt = _build_visit_query()
    stmt = stmt.where(Visit.id == visit_id)
    result = await db.execute(stmt)
    row = result.first()
    if row is None:
        raise HTTPException(status_code=404, detail="Visit not found")
    return _row_to_visit_out(row)


@router.post("", response_model=VisitOut, status_code=status.HTTP_201_CREATED)
async def create_visit(
    body: VisitCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    visit = Visit(**body.model_dump())

    # Автоподстановка стоимости из объекта, если не задана явно
    if visit.cost is None and visit.site_id:
        site_res = await db.execute(select(Site).where(Site.id == visit.site_id))
        site = site_res.scalar_one_or_none()
        if site:
            price_map = {
                enums.visit_types.maintenance: site.price_maintenance,
                enums.visit_types.repair: site.price_repair,
                enums.visit_types.emergency: site.price_emergency,
            }
            visit.cost = price_map.get(visit.visit_type)

    db.add(visit)
    await db.flush()

    await create_notification(
        db,
        user_id=body.assigned_user_id,
        type_="visit_assigned",
        title="Новый выезд",
        message=f"Вам назначен новый выезд на {body.planned_date}",
        related_visit_id=visit.id,
    )

    await save_log(db, current_user.id, enums.log_actions.visit_create, "visit", visit.id)

    await db.commit()
    await db.refresh(visit)

    stmt = _build_visit_query()
    stmt = stmt.where(Visit.id == visit.id)
    result = await db.execute(stmt)
    return _row_to_visit_out(result.first())


@router.put("/{visit_id}", response_model=VisitOut)
async def update_visit(
    visit_id: int,
    body: VisitUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = await db.execute(select(Visit).where(Visit.id == visit_id))
    visit = result.scalar_one_or_none()
    if visit is None:
        raise HTTPException(status_code=404, detail="Visit not found")

    changed = body.model_dump(exclude_unset=True)
    await save_history(db, VisitHistory, visit, current_user.id,
                       method="update", new_values=changed)

    old_master = visit.assigned_user_id
    old_date = visit.planned_date

    for field, value in changed.items():
        setattr(visit, field, value)

    new_master = visit.assigned_user_id
    new_date = visit.planned_date

    if new_master and (old_master != new_master or old_date != new_date):
        message = "Выезд переназначен вам" if old_master != new_master else f"Дата выезда изменена на {new_date}"
        await create_notification(
            db, user_id=new_master, type_="visit_updated",
            title="Изменение выезда", message=message, related_visit_id=visit_id,
        )

    # Выбираем наиболее специфичное действие
    if "assigned_user_id" in changed:
        action = enums.log_actions.visit_assign
    elif "status" in changed:
        action = enums.log_actions.visit_change_status
    else:
        action = enums.log_actions.visit_update

    await save_log(db, current_user.id, action, "visit", visit_id,
                   details={"changed": list(changed.keys())})
    await db.commit()

    stmt = _build_visit_query()
    stmt = stmt.where(Visit.id == visit_id)
    result = await db.execute(stmt)
    return _row_to_visit_out(result.first())


@router.post("/{visit_id}/complete", response_model=VisitOut)
async def complete_visit(
    visit_id: int,
    body: VisitComplete,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = await db.execute(select(Visit).where(Visit.id == visit_id))
    visit = result.scalar_one_or_none()
    if visit is None:
        raise HTTPException(status_code=404, detail="Visit not found")

    complete_vals = {"status": enums.visit_statuses.closed, "work_summary": body.work_summary,
                     "checklist": body.checklist, "defects_present": body.defects_present or False,
                     "defects_summary": body.defects_summary, "recommendations": body.recommendations}
    await save_history(db, VisitHistory, visit, current_user.id,
                       method="update", new_values=complete_vals)

    visit.status = enums.visit_statuses.closed
    visit.work_summary = body.work_summary
    visit.checklist = body.checklist
    visit.defects_present = body.defects_present or False
    visit.defects_summary = body.defects_summary
    visit.recommendations = body.recommendations
    visit.completed_at = datetime.utcnow()

    await save_log(db, current_user.id, enums.log_actions.visit_complete, "visit", visit_id)
    await db.commit()

    stmt = _build_visit_query()
    stmt = stmt.where(Visit.id == visit_id)
    result = await db.execute(stmt)
    return _row_to_visit_out(result.first())


@router.patch("/{visit_id}/archive", response_model=VisitOut)
async def archive_visit(
    visit_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = await db.execute(select(Visit).where(Visit.id == visit_id))
    visit = result.scalar_one_or_none()
    if visit is None:
        raise HTTPException(status_code=404, detail="Visit not found")

    visit.is_archived = True
    await save_log(db, current_user.id, enums.log_actions.visit_delete, "visit", visit_id,
                   details={"action": "archive", "planned_date": str(visit.planned_date)})
    await db.commit()

    stmt = _build_visit_query()
    stmt = stmt.where(Visit.id == visit_id)
    result = await db.execute(stmt)
    return _row_to_visit_out(result.first())


@router.patch("/{visit_id}/unarchive", response_model=VisitOut)
async def unarchive_visit(
    visit_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_groups("admin_group")),
):
    result = await db.execute(select(Visit).where(Visit.id == visit_id))
    visit = result.scalar_one_or_none()
    if visit is None:
        raise HTTPException(status_code=404, detail="Visit not found")

    visit.is_archived = False
    await save_log(db, current_user.id, enums.log_actions.visit_update, "visit", visit_id,
                   details={"action": "unarchive", "planned_date": str(visit.planned_date)})
    await db.commit()

    stmt = _build_visit_query()
    stmt = stmt.where(Visit.id == visit_id)
    result = await db.execute(stmt)
    return _row_to_visit_out(result.first())


@router.delete("/{visit_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_visit(
    visit_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = await db.execute(select(Visit).where(Visit.id == visit_id))
    visit = result.scalar_one_or_none()
    if visit is None:
        raise HTTPException(status_code=404, detail="Visit not found")

    await save_log(db, current_user.id, enums.log_actions.visit_delete, "visit", visit_id,
                   details={"site_id": visit.site_id, "planned_date": str(visit.planned_date)})
    await db.delete(visit)
    await db.commit()
