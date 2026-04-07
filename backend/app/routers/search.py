"""Глобальный поиск по клиентам, объектам и договорам."""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel

from app.dependencies import get_db, get_current_user
from app.models.client import Client
from app.models.site import Site
from app.models.contract import Contract

router = APIRouter(prefix="/search", tags=["search"])

PREVIEW_LIMIT = 5  # кол-во результатов в выпадающем попапе


class SearchResult(BaseModel):
    type: str        # "client" | "site" | "contract"
    id: int
    title: str
    subtitle: str | None = None
    url: str


class SearchResponse(BaseModel):
    results: List[SearchResult]
    clients_total: int
    sites_total: int
    contracts_total: int
    limit: int
    offset: int


@router.get("", response_model=SearchResponse)
async def global_search(
    q: str = Query(..., min_length=1),
    limit: int = Query(PREVIEW_LIMIT, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    results = []
    pattern = f"%{q}%"

    # ── Клиенты ──────────────────────────────────────────────────────────
    client_filter = (
        Client.is_archived == False,
        Client.name.ilike(pattern) |
        Client.inn.ilike(pattern) |
        Client.contacts.ilike(pattern)
    )
    clients_total_res = await db.execute(
        select(func.count()).where(*client_filter)
    )
    clients_total = clients_total_res.scalar() or 0

    clients = await db.execute(
        select(Client).where(*client_filter).offset(offset).limit(limit)
    )
    for c in clients.scalars():
        results.append(SearchResult(
            type="client",
            id=c.id,
            title=c.name,
            subtitle=f"ИНН: {c.inn}" if c.inn else None,
            url=f"/clients/{c.id}",
        ))

    # ── Объекты ──────────────────────────────────────────────────────────
    site_filter = (
        Site.is_archived == False,
        Site.address.ilike(pattern) |
        Site.title.ilike(pattern)
    )
    sites_total_res = await db.execute(
        select(func.count()).where(*site_filter)
    )
    sites_total = sites_total_res.scalar() or 0

    sites = await db.execute(
        select(Site).where(*site_filter).offset(offset).limit(limit)
    )
    for s in sites.scalars():
        results.append(SearchResult(
            type="site",
            id=s.id,
            title=s.address,
            subtitle=s.title if s.title != s.address else None,
            url=f"/sites/{s.id}",
        ))

    # ── Договоры ─────────────────────────────────────────────────────────
    contract_filter = (
        Contract.is_archived == False,
        Contract.contract_number.ilike(pattern) |
        Contract.subject.ilike(pattern)
    )
    contracts_total_res = await db.execute(
        select(func.count()).where(*contract_filter)
    )
    contracts_total = contracts_total_res.scalar() or 0

    contracts = await db.execute(
        select(Contract).where(*contract_filter).offset(offset).limit(limit)
    )
    for c in contracts.scalars():
        results.append(SearchResult(
            type="contract",
            id=c.id,
            title=c.contract_number or "Без номера",
            subtitle=c.subject,
            url=f"/contracts/{c.id}",
        ))

    return SearchResponse(
        results=results,
        clients_total=clients_total,
        sites_total=sites_total,
        contracts_total=contracts_total,
        limit=limit,
        offset=offset,
    )
