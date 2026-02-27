from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.dependencies import get_db, get_current_user
from app.models.client import Client
from app.models.history import ClientHistory
from app.schemas.client import ClientOut, ClientCreate, ClientUpdate
from app.utils.audit import save_history, save_log
from app.enums import enums

router = APIRouter(prefix="/clients", tags=["clients"])


@router.get("", response_model=List[ClientOut])
async def get_clients(
    search: Optional[str] = None,
    active_only: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    stmt = select(Client)
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


@router.get("/{client_id}", response_model=ClientOut)
async def get_client(client_id: UUID, db: AsyncSession = Depends(get_db), _=Depends(get_current_user)):
    result = await db.execute(select(Client).where(Client.id == client_id))
    client = result.scalar_one_or_none()
    if client is None:
        raise HTTPException(status_code=404, detail="Client not found")
    return client


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
