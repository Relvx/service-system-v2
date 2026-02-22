from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.dependencies import get_db, get_current_user
from app.models.client import Client
from app.schemas.client import ClientOut, ClientCreate, ClientUpdate

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
async def create_client(body: ClientCreate, db: AsyncSession = Depends(get_db), _=Depends(get_current_user)):
    client = Client(**body.model_dump())
    db.add(client)
    await db.commit()
    await db.refresh(client)
    return client


@router.put("/{client_id}", response_model=ClientOut)
async def update_client(
    client_id: UUID,
    body: ClientUpdate,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    result = await db.execute(select(Client).where(Client.id == client_id))
    client = result.scalar_one_or_none()
    if client is None:
        raise HTTPException(status_code=404, detail="Client not found")

    for field, value in body.model_dump(exclude_none=True).items():
        setattr(client, field, value)

    await db.commit()
    await db.refresh(client)
    return client


@router.delete("/{client_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_client(client_id: UUID, db: AsyncSession = Depends(get_db), _=Depends(get_current_user)):
    result = await db.execute(select(Client).where(Client.id == client_id))
    client = result.scalar_one_or_none()
    if client is None:
        raise HTTPException(status_code=404, detail="Client not found")
    await db.delete(client)
    await db.commit()
