from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.dependencies import get_db, get_current_user, require_groups
from app.models.client import Client
from app.models.client_contact import ClientContact
from app.models.client_legal import ClientLegal
from app.models.site import Site
from app.models.visit import Visit
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


@router.get("", response_model=List[ClientOut])
async def get_clients(
    search: Optional[str] = None,
    active_only: Optional[bool] = None,
    show_archived: bool = False,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    stmt = select(Client)
    if not show_archived:
        stmt = stmt.where(Client.is_archived == False)
    if active_only:
        stmt = stmt.where(Client.is_active == True)
    if search:
        stmt = stmt.where(
            Client.name.ilike(f"%{search}%")
            | Client.inn.ilike(f"%{search}%")
            | Client.contact_person.ilike(f"%{search}%")
        )
    stmt = stmt.order_by(Client.name)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/{client_id}", response_model=ClientDetailOut)
async def get_client(client_id: UUID, db: AsyncSession = Depends(get_db), _=Depends(get_current_user)):
    # Клиент
    result = await db.execute(select(Client).where(Client.id == client_id))
    client = result.scalar_one_or_none()
    if client is None:
        raise HTTPException(status_code=404, detail="Client not found")

    # Контакты
    contacts_res = await db.execute(
        select(ClientContact)
        .where(ClientContact.client_id == client_id)
        .order_by(ClientContact.is_primary.desc(), ClientContact.created_at)
    )
    contacts = contacts_res.scalars().all()

    # Реквизиты
    legal_res = await db.execute(
        select(ClientLegal).where(ClientLegal.client_id == client_id)
    )
    legal = legal_res.scalar_one_or_none()

    # Объекты клиента (не архивные)
    sites_res = await db.execute(
        select(Site)
        .where(Site.client_id == client_id, Site.is_archived == False)
        .order_by(Site.title)
    )
    sites = sites_res.scalars().all()

    # История выездов по всем объектам клиента (последние 20)
    site_ids = [s.id for s in sites]
    recent_visits = []
    if site_ids:
        visits_res = await db.execute(
            select(Visit, Site, User)
            .join(Site, Visit.site_id == Site.id, isouter=True)
            .join(User, Visit.assigned_user_id == User.id, isouter=True)
            .where(Visit.site_id.in_(site_ids), Visit.is_archived == False)
            .order_by(Visit.planned_date.desc())
            .limit(20)
        )
        for visit, site, user in visits_res.all():
            recent_visits.append(ClientVisitShort(
                id=visit.id,
                site_id=visit.site_id,
                site_title=site.title if site else None,
                planned_date=visit.planned_date,
                status=visit.status,
                visit_type=visit.visit_type,
                priority=visit.priority,
                master_name=user.full_name if user else None,
            ))

    return ClientDetailOut(
        **ClientOut.model_validate(client).model_dump(),
        contact_persons=[ClientContactOut.model_validate(c) for c in contacts],
        legal=ClientLegalOut.model_validate(legal) if legal else None,
        sites=[ClientSiteShort.model_validate(s) for s in sites],
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
    client_id: UUID,
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
    client_id: UUID,
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
    client_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_groups("admin_group")),
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
    client_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
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
    client_id: UUID,
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
    client_id: UUID,
    contact_id: UUID,
    body: ClientContactUpdate,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    result = await db.execute(
        select(ClientContact).where(
            ClientContact.id == contact_id,
            ClientContact.client_id == client_id,
        )
    )
    contact = result.scalar_one_or_none()
    if contact is None:
        raise HTTPException(status_code=404, detail="Contact not found")

    for field, value in body.model_dump(exclude_none=True).items():
        setattr(contact, field, value)

    await db.commit()
    await db.refresh(contact)
    return contact


@router.delete("/{client_id}/contacts/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_contact(
    client_id: UUID,
    contact_id: UUID,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    result = await db.execute(
        select(ClientContact).where(
            ClientContact.id == contact_id,
            ClientContact.client_id == client_id,
        )
    )
    contact = result.scalar_one_or_none()
    if contact is None:
        raise HTTPException(status_code=404, detail="Contact not found")

    await db.delete(contact)
    await db.commit()


# ── Юридические реквизиты ─────────────────────────────────────────────────

@router.put("/{client_id}/legal", response_model=ClientLegalOut)
async def upsert_legal(
    client_id: UUID,
    body: ClientLegalUpdate,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    result = await db.execute(select(Client).where(Client.id == client_id))
    if result.scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail="Client not found")

    legal_res = await db.execute(
        select(ClientLegal).where(ClientLegal.client_id == client_id)
    )
    legal = legal_res.scalar_one_or_none()

    if legal is None:
        legal = ClientLegal(client_id=client_id, **body.model_dump(exclude_none=True))
        db.add(legal)
    else:
        for field, value in body.model_dump(exclude_none=True).items():
            setattr(legal, field, value)

    await db.commit()
    await db.refresh(legal)
    return legal
