from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.dependencies import get_db, get_current_user, require_roles
from app.models.user import User
from app.schemas.user import UserOut, UserCreate, UserUpdate, MasterOut
from app.utils.auth import hash_password

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/masters", response_model=List[MasterOut])
async def get_masters(db: AsyncSession = Depends(get_db), _=Depends(get_current_user)):
    result = await db.execute(
        select(User).where(User.role == "master", User.is_active == True).order_by(User.full_name)
    )
    return result.scalars().all()


@router.get("", response_model=List[UserOut])
async def get_users(
    role: Optional[str] = None,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("office", "admin")),
):
    stmt = select(User)
    if role:
        stmt = stmt.where(User.role == role)
    if search:
        stmt = stmt.where(
            (User.full_name.ilike(f"%{search}%")) | (User.email.ilike(f"%{search}%"))
        )
    stmt = stmt.order_by(User.full_name)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def create_user(
    body: UserCreate,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_roles("admin")),
):
    existing = await db.execute(select(User).where(User.email == body.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already exists")

    user = User(
        email=body.email,
        password_hash=hash_password(body.password),
        full_name=body.full_name,
        phone=body.phone,
        role=body.role,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@router.put("/{user_id}", response_model=UserOut)
async def update_user(
    user_id: UUID,
    body: UserUpdate,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_roles("admin")),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    if body.full_name is not None:
        user.full_name = body.full_name
    if body.phone is not None:
        user.phone = body.phone
    if body.role is not None:
        user.role = body.role
    if body.is_active is not None:
        user.is_active = body.is_active

    await db.commit()
    await db.refresh(user)
    return user
