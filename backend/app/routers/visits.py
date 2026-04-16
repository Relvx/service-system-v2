from typing import List, Optional
from datetime import date, datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, exists
from pydantic import BaseModel

from app.dependencies import get_db, get_current_user, require_groups
from app.models.visit import Visit, VisitMaster
from app.models.site import Site
from app.models.client import Client
from app.models.client_contact import ClientContact
from app.models.contract import Contract, ContractSite
from sqlalchemy import or_, and_
from app.models.user import User
from app.models.attachment import Attachment
from app.models.history import VisitHistory
from app.schemas.visit import VisitOut, VisitCreate, VisitUpdate, VisitComplete
from app.utils.notifications import create_notification, notify_users_by_group
from app.utils.audit import save_history, save_log
from app.enums import enums

router = APIRouter(prefix="/visits", tags=["visits"])

DEFAULT_LIMIT = 50


class VisitPage(BaseModel):
    items: List[VisitOut]
    total: int
    limit: int
    offset: int


def _build_visit_query(
    master_id=None, site_id=None, status_=None, date_from=None, date_to=None, priority=None
):
    act_count = (
        select(func.count())
        .where(Attachment.visit_id == Visit.id, Attachment.kind == "act_photo")
        .correlate(Visit)
        .scalar_subquery()
    )

    # Subqueries for multiple masters
    master_ids_subq = (
        select(func.array_agg(VisitMaster.user_id))
        .where(VisitMaster.visit_id == Visit.id)
        .correlate(Visit)
        .scalar_subquery()
    )

    master_names_subq = (
        select(func.array_agg(User.full_name))
        .join(VisitMaster, VisitMaster.user_id == User.id)
        .where(VisitMaster.visit_id == Visit.id)
        .correlate(Visit)
        .scalar_subquery()
    )

    primary_contact_subq = (
        select(
            func.concat_ws(
                ", ",
                func.nullif(ClientContact.full_name, ""),
                func.nullif(ClientContact.phone, ""),
            )
        )
        .where(
            ClientContact.client_id == Client.id,
            ClientContact.is_primary == True,
        )
        .limit(1)
        .correlate(Client)
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
            primary_contact_subq.label("client_contacts"),
            User.full_name.label("master_name"),
            User.phone.label("master_phone"),
            act_count.label("act_photos_count"),
            Client.id.label("client_id"),
            master_ids_subq.label("master_ids"),
            master_names_subq.label("master_names"),
            Contract.contract_number.label("contract_number"),
        )
        .outerjoin(Site, Visit.site_id == Site.id)
        .outerjoin(Client, Site.client_id == Client.id)
        .outerjoin(User, Visit.assigned_user_id == User.id)
        .outerjoin(Contract, Visit.contract_id == Contract.id)
    )

    if master_id:
        stmt = stmt.where(
            exists().where(
                VisitMaster.visit_id == Visit.id,
                VisitMaster.user_id == master_id,
            )
        )
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
    obj.client_id = row[12]
    obj.master_ids = list(row[13]) if row[13] else []
    obj.master_names = list(row[14]) if row[14] else []
    obj.contract_number = row[15]
    return obj


async def _sync_visit_masters(db: AsyncSession, visit_id: int, master_ids: List[int]):
    """Синхронизирует таблицу visit_masters для выезда."""
    await db.execute(
        VisitMaster.__table__.delete().where(VisitMaster.visit_id == visit_id)
    )
    for uid in master_ids:
        db.add(VisitMaster(visit_id=visit_id, user_id=uid))
    await db.flush()


@router.get("", response_model=VisitPage)
async def get_visits(
    master_id: Optional[int] = None,
    site_id: Optional[int] = None,
    contract_id: Optional[int] = None,
    status: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    priority: Optional[str] = None,
    show_archived: bool = False,
    limit: int = Query(DEFAULT_LIMIT, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    stmt = _build_visit_query(master_id, site_id, status, date_from, date_to, priority)
    if not show_archived:
        stmt = stmt.where(Visit.is_archived == False)

    # Фильтр по договору: прямая привязка ИЛИ выезды без договора на объектах этого договора
    if contract_id is not None:
        site_ids_res = await db.execute(
            select(ContractSite.site_id).where(ContractSite.contract_id == contract_id)
        )
        site_ids = [r.site_id for r in site_ids_res.all()]
        if site_ids:
            stmt = stmt.where(or_(
                Visit.contract_id == contract_id,
                and_(Visit.contract_id.is_(None), Visit.site_id.in_(site_ids)),
            ))
        else:
            stmt = stmt.where(Visit.contract_id == contract_id)

    stmt = stmt.order_by(Visit.planned_date.desc(), Visit.planned_time_from)

    total_res = await db.execute(select(func.count()).select_from(stmt.subquery()))
    total = total_res.scalar() or 0

    result = await db.execute(stmt.offset(offset).limit(limit))
    return VisitPage(items=[_row_to_visit_out(r) for r in result.all()], total=total, limit=limit, offset=offset)


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
    data = body.model_dump(exclude={"master_ids", "visit_types"})

    # Определяем мастеров
    master_ids = body.master_ids or ([body.assigned_user_id] if body.assigned_user_id else [])
    if master_ids:
        data["assigned_user_id"] = master_ids[0]  # первый = основной

    # Определяем типы выезда
    visit_types = body.visit_types or [body.visit_type or "maintenance"]
    data["visit_type"] = visit_types[0]
    data["visit_types"] = visit_types

    # Статус по умолчанию
    if not data.get("status"):
        data["status"] = "planned"

    visit = Visit(**data)

    # Автоподстановка стоимости из объекта
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

    # Синхронизируем мастеров
    if master_ids:
        await _sync_visit_masters(db, visit.id, master_ids)

    # Уведомления (для исторических не нужны)
    if visit.status != "done":
        for uid in master_ids:
            await create_notification(
                db,
                user_id=uid,
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

    changed = body.model_dump(exclude_unset=True, exclude={"master_ids", "visit_types"})

    # Обработка мастеров
    if body.master_ids is not None:
        master_ids = body.master_ids
        if master_ids:
            changed["assigned_user_id"] = master_ids[0]
        await _sync_visit_masters(db, visit_id, master_ids)

    # Обработка типов
    if body.visit_types is not None:
        visit_types = body.visit_types
        if visit_types:
            changed["visit_type"] = visit_types[0]
        changed["visit_types"] = visit_types

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

    user_groups = {g.sysname for g in current_user.groups}
    is_office_admin = bool(user_groups & {"office_group", "admin_group"})
    if not is_office_admin and visit.assigned_user_id != current_user.id:
        raise HTTPException(status_code=403, detail="You can only complete your own assigned visit")

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
    visit.completed_at = datetime.now(timezone.utc).replace(tzinfo=None)

    await save_log(db, current_user.id, enums.log_actions.visit_complete, "visit", visit_id)

    site_res = await db.execute(select(Site).where(Site.id == visit.site_id))
    site_obj = site_res.scalar_one_or_none()
    site_title = site_obj.title if site_obj else f"объект #{visit.site_id}"
    await notify_users_by_group(
        db,
        group_sysnames=["office_group", "admin_group"],
        exclude_user_id=current_user.id,
        type_="visit_completed",
        title="Выезд завершён мастером",
        message=f"Мастер {current_user.full_name} завершил выезд на «{site_title}»",
        related_visit_id=visit_id,
    )
    await db.commit()

    stmt = _build_visit_query()
    stmt = stmt.where(Visit.id == visit_id)
    result = await db.execute(stmt)
    return _row_to_visit_out(result.first())


@router.patch("/{visit_id}/cancel", response_model=VisitOut)
async def cancel_visit(
    visit_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_groups("office_group", "admin_group")),
):
    result = await db.execute(select(Visit).where(Visit.id == visit_id))
    visit = result.scalar_one_or_none()
    if visit is None:
        raise HTTPException(status_code=404, detail="Visit not found")
    if visit.status == enums.visit_statuses.closed:
        raise HTTPException(status_code=400, detail="Cannot cancel a completed visit")
    if visit.status == enums.visit_statuses.cancelled:
        raise HTTPException(status_code=400, detail="Visit is already cancelled")

    await save_history(db, VisitHistory, visit, current_user.id,
                       method="update", new_values={"status": enums.visit_statuses.cancelled})
    visit.status = enums.visit_statuses.cancelled
    await save_log(db, current_user.id, enums.log_actions.visit_change_status, "visit", visit_id,
                   details={"status": "cancelled"})
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
    current_user=Depends(require_groups("admin_group", "office_group")),
):
    result = await db.execute(select(Visit).where(Visit.id == visit_id))
    visit = result.scalar_one_or_none()
    if visit is None:
        raise HTTPException(status_code=404, detail="Visit not found")

    await save_log(db, current_user.id, enums.log_actions.visit_delete, "visit", visit_id,
                   details={"site_id": visit.site_id, "planned_date": str(visit.planned_date)})
    await db.delete(visit)
    await db.commit()
