from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel

from app.dependencies import get_db, get_current_user
from app.models.contract import Contract, ContractSite
from app.models.client import Client
from app.models.site import Site
from app.schemas.contract import (
    ContractOut, ContractDetailOut, ContractCreate, ContractUpdate,
    ContractSiteShort, ClientContractShort,
)

router = APIRouter(prefix="/contracts", tags=["contracts"])

DEFAULT_LIMIT = 50


class ContractPage(BaseModel):
    items: List[ContractOut]
    total: int
    limit: int
    offset: int


@router.get("", response_model=ContractPage)
async def get_contracts(
    client_id: Optional[int] = None,
    site_id: Optional[int] = None,
    status: Optional[str] = None,
    search: Optional[str] = None,
    show_archived: bool = False,
    limit: int = Query(DEFAULT_LIMIT, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    sites_count_sq = (
        select(func.count())
        .where(ContractSite.contract_id == Contract.id)
        .correlate(Contract).scalar_subquery()
    )
    stmt = (
        select(Contract, Client.name.label("client_name"), sites_count_sq.label("sites_count"))
        .outerjoin(Client, Contract.client_id == Client.id)
    )
    if not show_archived:
        stmt = stmt.where(Contract.is_archived == False)
    if client_id:
        stmt = stmt.where(Contract.client_id == client_id)
    if site_id:
        stmt = stmt.where(
            Contract.id.in_(
                select(ContractSite.contract_id).where(ContractSite.site_id == site_id)
            )
        )
    if status:
        stmt = stmt.where(Contract.status == status)
    if search:
        stmt = stmt.where(
            Contract.contract_number.ilike(f"%{search}%")
            | Contract.subject.ilike(f"%{search}%")
            | Client.name.ilike(f"%{search}%")
        )
    stmt = stmt.order_by(Contract.created_at.desc())

    total_res = await db.execute(select(func.count()).select_from(stmt.subquery()))
    total = total_res.scalar() or 0

    result = await db.execute(stmt.offset(offset).limit(limit))
    out = []
    for row in result.all():
        c, client_name, s_cnt = row[0], row[1], row[2]
        obj = ContractOut.model_validate(c)
        obj.client_name = client_name
        obj.sites_count = s_cnt
        out.append(obj)
    return ContractPage(items=out, total=total, limit=limit, offset=offset)


@router.get("/{contract_id}", response_model=ContractDetailOut)
async def get_contract(
    contract_id: int,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    result = await db.execute(select(Contract).where(Contract.id == contract_id))
    contract = result.scalar_one_or_none()
    if contract is None:
        raise HTTPException(status_code=404, detail="Contract not found")

    client_name = None
    if contract.client_id:
        r = await db.execute(select(Client).where(Client.id == contract.client_id))
        cl = r.scalar_one_or_none()
        client_name = cl.name if cl else None

    # Объекты договора
    stmt = (
        select(Site)
        .join(ContractSite, ContractSite.site_id == Site.id)
        .where(ContractSite.contract_id == contract_id)
        .order_by(Site.title)
    )
    sites_result = await db.execute(stmt)
    sites = sites_result.scalars().all()

    out = ContractDetailOut.model_validate(contract)
    out.client_name = client_name
    out.sites = [ContractSiteShort.model_validate(s) for s in sites]
    return out


@router.post("", response_model=ContractOut, status_code=201)
async def create_contract(
    data: ContractCreate,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    now = datetime.now()
    contract = Contract(
        **data.model_dump(),
        created_at=now,
        updated_at=now,
    )
    db.add(contract)
    await db.commit()
    await db.refresh(contract)
    out = ContractOut.model_validate(contract)
    if contract.client_id:
        r = await db.execute(select(Client).where(Client.id == contract.client_id))
        cl = r.scalar_one_or_none()
        out.client_name = cl.name if cl else None
    return out


@router.patch("/{contract_id}", response_model=ContractOut)
async def update_contract(
    contract_id: int,
    data: ContractUpdate,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    result = await db.execute(select(Contract).where(Contract.id == contract_id))
    contract = result.scalar_one_or_none()
    if contract is None:
        raise HTTPException(status_code=404, detail="Contract not found")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(contract, field, value)
    contract.updated_at = datetime.now()
    await db.commit()
    await db.refresh(contract)

    out = ContractOut.model_validate(contract)
    if contract.client_id:
        r = await db.execute(select(Client).where(Client.id == contract.client_id))
        cl = r.scalar_one_or_none()
        out.client_name = cl.name if cl else None
    return out


# ── Объекты в договоре ────────────────────────────────────────────────────

@router.post("/{contract_id}/sites/{site_id}", status_code=201)
async def add_site_to_contract(
    contract_id: int,
    site_id: int,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    # Проверяем существование
    r = await db.execute(select(Contract).where(Contract.id == contract_id))
    if r.scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail="Contract not found")
    r = await db.execute(select(Site).where(Site.id == site_id))
    if r.scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail="Site not found")

    # Проверяем дубли
    r = await db.execute(
        select(ContractSite).where(
            ContractSite.contract_id == contract_id,
            ContractSite.site_id == site_id,
        )
    )
    if r.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Site already linked to this contract")

    db.add(ContractSite(contract_id=contract_id, site_id=site_id))
    await db.commit()
    return {"ok": True}


@router.delete("/{contract_id}/sites/{site_id}", status_code=200)
async def remove_site_from_contract(
    contract_id: int,
    site_id: int,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    r = await db.execute(
        select(ContractSite).where(
            ContractSite.contract_id == contract_id,
            ContractSite.site_id == site_id,
        )
    )
    link = r.scalar_one_or_none()
    if link is None:
        raise HTTPException(status_code=404, detail="Link not found")
    await db.delete(link)
    await db.commit()
    return {"ok": True}


# ── Договоры клиента (для карточки клиента) ───────────────────────────────

@router.get("/by-client/{client_id}", response_model=List[ClientContractShort])
async def get_contracts_by_client(
    client_id: int,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    stmt = (
        select(Contract)
        .where(Contract.client_id == client_id, Contract.is_archived == False)
        .order_by(Contract.contract_date.desc().nullslast(), Contract.created_at.desc())
    )
    result = await db.execute(stmt)
    contracts = result.scalars().all()

    out = []
    for c in contracts:
        count_result = await db.execute(
            select(func.count()).where(ContractSite.contract_id == c.id)
        )
        sites_count = count_result.scalar() or 0
        row = ClientContractShort.model_validate(c)
        row.sites_count = sites_count
        out.append(row)
    return out
