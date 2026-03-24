"""Глобальный поиск по клиентам, объектам и договорам."""

from typing import List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from app.dependencies import get_db, get_current_user
from app.models.client import Client
from app.models.site import Site
from app.models.contract import Contract

router = APIRouter(prefix="/search", tags=["search"])


class SearchResult(BaseModel):
    type: str        # "client" | "site" | "contract"
    id: int
    title: str
    subtitle: str | None = None
    url: str


@router.get("", response_model=List[SearchResult])
async def global_search(
    q: str = Query(..., min_length=2),
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    results = []
    pattern = f"%{q}%"

    # Клиенты
    clients = await db.execute(
        select(Client)
        .where(
            Client.is_archived == False,
            Client.name.ilike(pattern) |
            Client.inn.ilike(pattern) |
            Client.contacts.ilike(pattern)
        )
        .limit(5)
    )
    for c in clients.scalars():
        results.append(SearchResult(
            type="client",
            id=c.id,
            title=c.name,
            subtitle=f"ИНН: {c.inn}" if c.inn else None,
            url=f"/clients/{c.id}",
        ))

    # Объекты
    sites = await db.execute(
        select(Site)
        .where(
            Site.is_archived == False,
            Site.address.ilike(pattern) |
            Site.title.ilike(pattern)
        )
        .limit(5)
    )
    for s in sites.scalars():
        results.append(SearchResult(
            type="site",
            id=s.id,
            title=s.address,
            subtitle=s.title if s.title != s.address else None,
            url=f"/sites/{s.id}",
        ))

    # Договоры
    contracts = await db.execute(
        select(Contract)
        .where(
            Contract.is_archived == False,
            Contract.contract_number.ilike(pattern) |
            Contract.subject.ilike(pattern)
        )
        .limit(5)
    )
    for c in contracts.scalars():
        results.append(SearchResult(
            type="contract",
            id=c.id,
            title=c.contract_number or "Без номера",
            subtitle=c.subject,
            url=f"/contracts/{c.id}",
        ))

    return results
