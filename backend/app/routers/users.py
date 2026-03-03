from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.dependencies import get_db, get_current_user, require_groups
from app.models.user import User
from app.models.config_tables import PermissionGroup, UserPermissionGroup
from app.schemas.user import UserOut, UserCreate, UserUpdate, MasterOut
from app.utils.auth import hash_password

router = APIRouter(prefix="/users", tags=["users"])


def _user_out(user: User) -> UserOut:
    obj = UserOut.model_validate(user)
    obj.groups = [g.sysname for g in user.groups]
    return obj


@router.get("/masters", response_model=List[MasterOut])
async def get_masters(db: AsyncSession = Depends(get_db), _=Depends(get_current_user)):
    result = await db.execute(
        select(User)
        .join(UserPermissionGroup, UserPermissionGroup.user_id == User.id)
        .join(PermissionGroup, PermissionGroup.id == UserPermissionGroup.group_id)
        .where(PermissionGroup.sysname == "master_group", User.is_active == True)
        .order_by(User.full_name)
    )
    return result.scalars().all()


@router.get("", response_model=List[UserOut])
async def get_users(
    group: Optional[str] = None,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_groups("office_group", "admin_group")),
):
    stmt = select(User)
    if group:
        stmt = (
            stmt
            .join(UserPermissionGroup, UserPermissionGroup.user_id == User.id)
            .join(PermissionGroup, PermissionGroup.id == UserPermissionGroup.group_id)
            .where(PermissionGroup.sysname == group)
        )
    if search:
        stmt = stmt.where(
            (User.full_name.ilike(f"%{search}%")) | (User.email.ilike(f"%{search}%"))
        )
    stmt = stmt.order_by(User.full_name)
    result = await db.execute(stmt)
    users = result.scalars().all()
    return [_user_out(u) for u in users]


@router.post("", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def create_user(
    body: UserCreate,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_groups("admin_group")),
):
    existing = await db.execute(select(User).where(User.email == body.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already exists")

    user = User(
        email=body.email,
        password_hash=hash_password(body.password),
        full_name=body.full_name,
        phone=body.phone,
    )
    db.add(user)
    await db.flush()

    # Assign requested groups
    for group_sysname in body.groups:
        grp_result = await db.execute(
            select(PermissionGroup).where(PermissionGroup.sysname == group_sysname)
        )
        grp = grp_result.scalar_one_or_none()
        if grp:
            db.add(UserPermissionGroup(user_id=user.id, group_id=grp.id))

    await db.commit()
    await db.refresh(user)
    return _user_out(user)


@router.put("/{user_id}", response_model=UserOut)
async def update_user(
    user_id: int,
    body: UserUpdate,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_groups("admin_group")),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    if body.full_name is not None:
        user.full_name = body.full_name
    if body.phone is not None:
        user.phone = body.phone
    if body.is_active is not None:
        user.is_active = body.is_active

    await db.commit()
    await db.refresh(user)
    return _user_out(user)
