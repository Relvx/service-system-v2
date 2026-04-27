"""API для расписания обслуживания по договорам."""

from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.dependencies import get_db, get_current_user
from app.models.contract_schedule import ContractSchedule
from app.models.contract import Contract, ContractSite
from app.models.client import Client
from app.models.client_contact import ClientContact
from app.models.site import Site
from app.models.visit import Visit
from app.models.user import User

router = APIRouter(prefix="/schedule", tags=["schedule"])


# ---------- Schemas ----------

class ScheduleCell(BaseModel):
    contract_id: int
    contract_number: str
    client_name: str
    year: int
    month: int
    note: str
    contact_name: Optional[str] = None
    contact_phone: Optional[str] = None
    site_addresses: List[str] = []


class ScheduleRow(BaseModel):
    contract_id: int
    client_id: Optional[int]
    contract_number: str
    client_name: str
    cells: dict[int, str]  # month → note


class VisitComment(BaseModel):
    visit_id: int
    planned_date: str
    master_name: Optional[str]
    work_summary: Optional[str]
    recommendations: Optional[str]
    defects_summary: Optional[str]
    defects_present: bool


class ContractVisitsOut(BaseModel):
    contract_id: int
    contract_number: str
    client_name: str
    visits: List[VisitComment]


class ScheduleYearOut(BaseModel):
    year: int
    rows: List[ScheduleRow]


class ScheduleMonthOut(BaseModel):
    year: int
    month: int
    items: List[ScheduleCell]


class ScheduleNoteUpdate(BaseModel):
    note: Optional[str] = None


class ContractYearCells(BaseModel):
    year: int
    cells: dict[int, Optional[str]]  # month → note (None = entry exists, no note)


# ---------- Endpoints ----------

@router.get("/year/{year}", response_model=ScheduleYearOut)
async def get_schedule_year(
    year: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Всё расписание за год: строки = договоры, столбцы = месяцы 1–12."""
    result = await db.execute(
        select(ContractSchedule, Contract.contract_number, Client.name, Client.id)
        .join(Contract, ContractSchedule.contract_id == Contract.id)
        .join(Client, Contract.client_id == Client.id)
        .where(ContractSchedule.year == year)
        .order_by(Client.name, Contract.contract_number)
    )
    rows_raw = result.all()

    # Группируем по договору
    contract_rows: dict[int, ScheduleRow] = {}
    for sched, contract_number, client_name, client_id in rows_raw:
        if sched.contract_id not in contract_rows:
            contract_rows[sched.contract_id] = ScheduleRow(
                contract_id=sched.contract_id,
                client_id=client_id,
                contract_number=contract_number or "",
                client_name=client_name or "",
                cells={},
            )
        if sched.note:
            contract_rows[sched.contract_id].cells[sched.month] = sched.note

    return ScheduleYearOut(year=year, rows=list(contract_rows.values()))


@router.get("/month/{year}/{month}", response_model=ScheduleMonthOut)
async def get_schedule_month(
    year: int,
    month: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Все договоры с непустыми заметками в конкретном месяце."""
    if not 1 <= month <= 12:
        raise HTTPException(status_code=400, detail="month must be 1–12")

    result = await db.execute(
        select(
            ContractSchedule,
            Contract.contract_number,
            Client.name,
            ClientContact.full_name,
            ClientContact.phone,
        )
        .join(Contract, ContractSchedule.contract_id == Contract.id)
        .join(Client, Contract.client_id == Client.id)
        .outerjoin(
            ClientContact,
            (ClientContact.client_id == Client.id) & (ClientContact.is_primary == True),
        )
        .where(ContractSchedule.year == year, ContractSchedule.month == month)
        .where(ContractSchedule.note.isnot(None), ContractSchedule.note != "")
        .order_by(Client.name, Contract.contract_number)
    )
    all_rows = result.all()

    # Дедупликация: один договор — одна строка (JOIN с контактами может дать дубли)
    seen_contracts: set[int] = set()
    rows = []
    for row in all_rows:
        if row[0].contract_id not in seen_contracts:
            seen_contracts.add(row[0].contract_id)
            rows.append(row)

    contract_ids = [s.contract_id for s, *_ in rows]

    # Адреса объектов по договорам
    sites_map: dict[int, list[str]] = {}
    if contract_ids:
        sites_result = await db.execute(
            select(ContractSite.contract_id, Site.address)
            .join(Site, ContractSite.site_id == Site.id)
            .where(ContractSite.contract_id.in_(contract_ids), Site.is_archived == False)
            .order_by(ContractSite.contract_id, Site.address)
        )
        for contract_id, address in sites_result.all():
            if address:
                sites_map.setdefault(contract_id, []).append(address)

    items = [
        ScheduleCell(
            contract_id=s.contract_id,
            contract_number=cn or "",
            client_name=cl or "",
            year=year,
            month=month,
            note=s.note,
            contact_name=contact_name or None,
            contact_phone=contact_phone or None,
            site_addresses=sites_map.get(s.contract_id, []),
        )
        for s, cn, cl, contact_name, contact_phone in rows
    ]
    return ScheduleMonthOut(year=year, month=month, items=items)


@router.put("/{contract_id}/{year}/{month}", response_model=ScheduleCell)
async def upsert_schedule_cell(
    contract_id: int,
    year: int,
    month: int,
    body: ScheduleNoteUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Создать или обновить заметку расписания для договора+месяц."""
    if not 1 <= month <= 12:
        raise HTTPException(status_code=400, detail="month must be 1–12")

    # Проверяем что договор существует
    contract_result = await db.execute(
        select(Contract, Client.name)
        .join(Client, Contract.client_id == Client.id)
        .where(Contract.id == contract_id)
    )
    row = contract_result.first()
    if not row:
        raise HTTPException(status_code=404, detail="Contract not found")
    contract, client_name = row

    stmt = (
        pg_insert(ContractSchedule)
        .values(
            contract_id=contract_id,
            year=year,
            month=month,
            note=body.note,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        .on_conflict_do_update(
            constraint="uq_contract_schedule",
            set_={"note": body.note, "updated_at": datetime.now()},
        )
    )
    await db.execute(stmt)
    await db.commit()

    return ScheduleCell(
        contract_id=contract_id,
        contract_number=contract.contract_number or "",
        client_name=client_name or "",
        year=year,
        month=month,
        note=body.note or "",
    )


@router.delete("/{contract_id}/{year}/{month}", status_code=204)
async def delete_schedule_cell(
    contract_id: int,
    year: int,
    month: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Удалить заметку расписания."""
    result = await db.execute(
        select(ContractSchedule).where(
            ContractSchedule.contract_id == contract_id,
            ContractSchedule.year == year,
            ContractSchedule.month == month,
        )
    )
    cell = result.scalar_one_or_none()
    if not cell:
        raise HTTPException(status_code=404, detail="Not found")
    await db.delete(cell)
    await db.commit()


@router.get("/contract/{contract_id}", response_model=ContractYearCells)
async def get_contract_schedule(
    contract_id: int,
    year: int = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Ячейки расписания конкретного договора за год."""
    result = await db.execute(
        select(ContractSchedule)
        .where(ContractSchedule.contract_id == contract_id, ContractSchedule.year == year)
    )
    rows = result.scalars().all()
    cells = {r.month: r.note for r in rows}
    return ContractYearCells(year=year, cells=cells)


@router.get("/visits/{contract_id}", response_model=ContractVisitsOut)
async def get_contract_visits(
    contract_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Завершённые выезды по договору с комментариями мастера."""
    contract_result = await db.execute(
        select(Contract, Client.name)
        .join(Client, Contract.client_id == Client.id)
        .where(Contract.id == contract_id)
    )
    row = contract_result.first()
    if not row:
        raise HTTPException(status_code=404, detail="Contract not found")
    contract, client_name = row

    # Собираем site_id для данного договора
    site_ids_result = await db.execute(
        select(ContractSite.site_id).where(ContractSite.contract_id == contract_id)
    )
    site_ids = [r.site_id for r in site_ids_result.all()]

    # Ищем завершённые выезды:
    # - явно привязанные к договору (contract_id == X)
    # - ИЛИ без привязки (contract_id IS NULL) у объектов этого договора
    from sqlalchemy import or_, and_
    visit_filter = [Visit.status == "done"]
    if site_ids:
        visit_filter.append(or_(
            Visit.contract_id == contract_id,
            and_(Visit.contract_id.is_(None), Visit.site_id.in_(site_ids)),
        ))
    else:
        visit_filter.append(Visit.contract_id == contract_id)

    visits_result = await db.execute(
        select(Visit, User.full_name)
        .outerjoin(User, Visit.assigned_user_id == User.id)
        .where(*visit_filter)
        .order_by(Visit.planned_date.desc())
        .limit(50)
    )
    visits_raw = visits_result.all()

    visits = [
        VisitComment(
            visit_id=v.id,
            planned_date=str(v.planned_date),
            master_name=master_name or v.master_name_raw,
            work_summary=v.work_summary,
            recommendations=v.recommendations,
            defects_summary=v.defects_summary,
            defects_present=v.defects_present,
        )
        for v, master_name in visits_raw
    ]

    return ContractVisitsOut(
        contract_id=contract_id,
        contract_number=contract.contract_number or "",
        client_name=client_name or "",
        visits=visits,
    )
