from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel

from app.dependencies import get_db, get_current_user, require_groups
from app.models.client import Client
from app.models.client_contact import ClientContact
from app.models.client_legal import ClientLegal
from app.models.site import Site
from app.models.visit import Visit
from app.models.contract import Contract
from app.models.user import User
from app.models.history import ClientHistory
from app.schemas.client import (
    ClientOut, ClientCreate, ClientUpdate, ClientDetailOut,
    ClientContactOut, ClientContactCreate, ClientContactUpdate,
    ClientLegalOut, ClientLegalUpdate,
    ClientSiteShort, ClientVisitShort,
)
from app.utils.audit import save_history, save_log
from app.enums import enums

router = APIRouter(prefix="/clients", tags=["clients"])

DEFAULT_LIMIT = 50


class ClientPage(BaseModel):
    items: List[ClientOut]
    total: int
    limit: int
    offset: int

# ─── HELPER FUNCTIONS ─────────────────────────────────────────────────────

async def _get_client(db: AsyncSession, client_id: int) -> Client:
    """Получить клиента с проверкой существования."""
    result = await db.execute(select(Client).where(Client.id == client_id))
    client = result.scalar_one_or_none()
    if client is None:
        raise HTTPException(status_code=404, detail="Client not found")
    return client


async def _get_client_contact(
    db: AsyncSession, client_id: int, contact_id: int
) -> ClientContact:
    """Получить контакт клиента с проверкой."""
    result = await db.execute(
        select(ClientContact).where(
            ClientContact.id == contact_id,
            ClientContact.client_id == client_id,
        )
    )
    contact = result.scalar_one_or_none()
    if contact is None:
        raise HTTPException(status_code=404, detail="Contact not found")
    return contact


def _client_out_with_counts(client: Client, sites_count: int, visits_count: int, contracts_count: int, primary_contact: str | None = None) -> ClientOut:
    """Создать ClientOut с дополнительными счетчиками."""
    obj = ClientOut.model_validate(client)
    obj.sites_count = sites_count
    obj.visits_count = visits_count
    obj.contracts_count = contracts_count
    obj.primary_contact = primary_contact
    return obj



@router.get("", response_model=ClientPage)
async def get_clients(
    search: Optional[str] = None,
    active_only: Optional[bool] = None,
    inactive_only: Optional[bool] = None,
    show_archived: bool = False,
    limit: int = Query(DEFAULT_LIMIT, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    sites_count_sq = (
        select(func.count())
        .where(Site.client_id == Client.id, Site.is_archived == False)
        .correlate(Client)
        .scalar_subquery()
    )
    visits_count_sq = (
        select(func.count())
        .select_from(Visit)
        .join(Site, Visit.site_id == Site.id)
        .where(Site.client_id == Client.id, Visit.is_archived == False)
        .correlate(Client)
        .scalar_subquery()
    )
    contracts_count_sq = (
        select(func.count())
        .where(Contract.client_id == Client.id, Contract.is_archived == False)
        .correlate(Client)
        .scalar_subquery()
    )

    primary_contact_sq = (
        select(ClientContact.full_name)
        .where(ClientContact.client_id == Client.id, ClientContact.is_primary == True)
        .limit(1)
        .correlate(Client)
        .scalar_subquery()
    )

    stmt = select(
        Client,
        sites_count_sq.label("sites_count"),
        visits_count_sq.label("visits_count"),
        contracts_count_sq.label("contracts_count"),
        primary_contact_sq.label("primary_contact"),
    )
    if show_archived:
        stmt = stmt.where(Client.is_archived == True)
    else:
        stmt = stmt.where(Client.is_archived == False)
    if active_only:
        stmt = stmt.where(Client.is_active == True)
    if inactive_only:
        stmt = stmt.where(Client.is_active == False)
    if search:
        stmt = stmt.where(
            Client.name.ilike(f"%{search}%")
            | Client.inn.ilike(f"%{search}%")
        )
    stmt = stmt.order_by(Client.name)

    total_stmt = select(func.count()).select_from(stmt.subquery())
    total_result = await db.execute(total_stmt)
    total = total_result.scalar() or 0

    paginated_stmt = stmt.offset(offset).limit(limit)
    result = await db.execute(paginated_stmt)
    
    items = [
        _client_out_with_counts(client, s_cnt, v_cnt, c_cnt, pc)
        for client, s_cnt, v_cnt, c_cnt, pc in result.all()
    ]
    return ClientPage(items=items, total=total, limit=limit, offset=offset)



@router.get("/{client_id}", response_model=ClientDetailOut)
async def get_client(client_id: int, db: AsyncSession = Depends(get_db), _=Depends(get_current_user)):
    # Клиент
    client = await _get_client(db, client_id)

    # Контакты
    contacts_res = await db.execute(
        select(ClientContact)
        .where(ClientContact.client_id == client_id)
        .order_by(ClientContact.is_primary.desc(), ClientContact.created_at)
    )
    contacts = [ClientContactOut.model_validate(c) for c in contacts_res.scalars().all()]
    
    # Реквизиты
    legal_res = await db.execute(
        select(ClientLegal).where(ClientLegal.client_id == client_id)
    )
    _legal_obj = legal_res.scalar_one_or_none()
    legal = ClientLegalOut.model_validate(_legal_obj) if _legal_obj else None

    # Объекты клиента (не архивные)
    sites_res = await db.execute(
        select(Site)
        .where(Site.client_id == client_id, Site.is_archived == False)
        .order_by(Site.title)
    )
    sites = [ClientSiteShort.model_validate(s) for s in sites_res.scalars().all()]

    # История выездов по всем объектам клиента (последние 20)
    site_ids = [s.id for s in sites]
    recent_visits = []
    if sites:
        site_ids = [s.id for s in sites]
        visits_result = await db.execute(
            select(Visit, Site, User)
            .join(Site, Visit.site_id == Site.id)
            .join(User, Visit.assigned_user_id == User.id, isouter=True)
            .where(Visit.site_id.in_(site_ids), Visit.is_archived == False)
            .order_by(Visit.planned_date.desc())
            .limit(20)
        )
        recent_visits = [
            ClientVisitShort(
                id=visit.id,
                site_id=visit.site_id,
                site_title=site.title,
                planned_date=visit.planned_date,
                status=visit.status,
                visit_type=visit.visit_type,
                priority=visit.priority,
                master_name=user.full_name if user else None,
            )
            for visit, site, user in visits_result.all()
        ]

    return ClientDetailOut(
        **ClientOut.model_validate(client).model_dump(),
        contact_persons=contacts,
        legal=legal,
        sites=sites,
        recent_visits=recent_visits,
    )


@router.post("", response_model=ClientOut, status_code=status.HTTP_201_CREATED)
async def create_client(
    body: ClientCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    client = Client(**body.model_dump())
    db.add(client)
    await db.flush()
    await save_log(db, current_user.id, enums.log_actions.client_create, "client", client.id)
    await db.commit()
    await db.refresh(client)
    return client


@router.put("/{client_id}", response_model=ClientOut)
async def update_client(
    client_id: int,
    body: ClientUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = await db.execute(select(Client).where(Client.id == client_id))
    client = result.scalar_one_or_none()
    if client is None:
        raise HTTPException(status_code=404, detail="Client not found")

    changed = body.model_dump(exclude_none=True)
    await save_history(db, ClientHistory, client, current_user.id,
                       method="update", new_values=changed)

    for field, value in changed.items():
        setattr(client, field, value)

    action = (
        enums.log_actions.client_change_status
        if "is_active" in changed
        else enums.log_actions.client_update
    )
    await save_log(db, current_user.id, action, "client", client_id,
                   details={"changed": list(changed.keys())})
    await db.commit()
    await db.refresh(client)
    return client


@router.patch("/{client_id}/archive", response_model=ClientOut)
async def archive_client(
    client_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = await db.execute(select(Client).where(Client.id == client_id))
    client = result.scalar_one_or_none()
    if client is None:
        raise HTTPException(status_code=404, detail="Client not found")

    client.is_archived = True
    await save_log(db, current_user.id, enums.log_actions.client_delete, "client", client_id,
                   details={"name": client.name, "action": "archive"})
    await db.commit()
    await db.refresh(client)
    return client


@router.patch("/{client_id}/unarchive", response_model=ClientOut)
async def unarchive_client(
    client_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_groups("admin_group", "office_group")),
):
    result = await db.execute(select(Client).where(Client.id == client_id))
    client = result.scalar_one_or_none()
    if client is None:
        raise HTTPException(status_code=404, detail="Client not found")

    client.is_archived = False
    await save_log(db, current_user.id, enums.log_actions.client_update, "client", client_id,
                   details={"name": client.name, "action": "unarchive"})
    await db.commit()
    await db.refresh(client)
    return client


@router.delete("/{client_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_client(
    client_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_groups("admin_group", "office_group")),
):
    result = await db.execute(select(Client).where(Client.id == client_id))
    client = result.scalar_one_or_none()
    if client is None:
        raise HTTPException(status_code=404, detail="Client not found")

    await save_log(db, current_user.id, enums.log_actions.client_delete, "client", client_id,
                   details={"name": client.name})
    await db.delete(client)
    await db.commit()


# ── Контакты ──────────────────────────────────────────────────────────────

@router.post("/{client_id}/contacts", response_model=ClientContactOut, status_code=status.HTTP_201_CREATED)
async def add_contact(
    client_id: int,
    body: ClientContactCreate,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    result = await db.execute(select(Client).where(Client.id == client_id))
    if result.scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail="Client not found")

    contact = ClientContact(client_id=client_id, **body.model_dump())
    db.add(contact)
    await db.commit()
    await db.refresh(contact)
    return contact


@router.put("/{client_id}/contacts/{contact_id}", response_model=ClientContactOut)
async def update_contact(
    client_id: int,
    contact_id: int,
    body: ClientContactUpdate,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    contact = await _get_client_contact(db, client_id, contact_id)
    
    changed = body.model_dump(exclude_none=True)
    if not changed:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    for field, value in changed.items():
        setattr(contact, field, value)
    
    await db.commit()
    await db.refresh(contact)
    return ClientContactOut.model_validate(contact)


@router.delete("/{client_id}/contacts/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_contact(
    client_id: int,
    contact_id: int,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    contact = await _get_client_contact(db, client_id, contact_id)
    await db.delete(contact)
    await db.commit()


# ── Юридические реквизиты ─────────────────────────────────────────────────

@router.put("/{client_id}/legal", response_model=ClientLegalOut)
async def upsert_legal(
    client_id: int,
    body: ClientLegalUpdate,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    await _get_client(db, client_id)
    
    legal_result = await db.execute(
        select(ClientLegal).where(ClientLegal.client_id == client_id)
    )
    legal = legal_result.scalar_one_or_none()
    
    changed = body.model_dump(exclude_none=True)
    if not changed:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    if legal is None:
        legal = ClientLegal(client_id=client_id, **changed)
        db.add(legal)
    else:
        for field, value in changed.items():
            setattr(legal, field, value)
    
    await db.commit()
    await db.refresh(legal)
    return ClientLegalOut.model_validate(legal)