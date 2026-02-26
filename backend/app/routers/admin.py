"""Admin router — user management, permission groups, and permission assignments."""

from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from app.dependencies import get_db, require_groups
from app.models.user import User
from app.models.config_tables import (
    PermissionGroup, Permission,
    PermissionGroupPermission, UserPermissionGroup,
)
from app.schemas.user import UserOut, UserCreate, UserUpdate
from app.schemas.config import PermissionGroupOut, PermissionOut, ConfigItemCreate, ConfigItemUpdate
from app.utils.auth import hash_password

router = APIRouter(prefix="/admin", tags=["admin"])

_admin = Depends(require_groups("admin_group"))


def _user_out(user: User) -> UserOut:
    obj = UserOut.model_validate(user)
    obj.groups = [g.sysname for g in user.groups]
    return obj


# ─── Users ────────────────────────────────────────────────────────────────

@router.get("/users", response_model=List[UserOut])
async def admin_get_users(db: AsyncSession = Depends(get_db), _=_admin):
    result = await db.execute(select(User).order_by(User.full_name))
    return [_user_out(u) for u in result.scalars().all()]


@router.post("/users", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def admin_create_user(
    body: UserCreate,
    db: AsyncSession = Depends(get_db),
    _=_admin,
):
    existing = await db.execute(select(User).where(User.email == body.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Email already exists")

    user = User(
        email=body.email,
        password_hash=hash_password(body.password),
        full_name=body.full_name,
        phone=body.phone,
    )
    db.add(user)
    await db.flush()

    for group_sysname in body.groups:
        grp = await db.execute(
            select(PermissionGroup).where(PermissionGroup.sysname == group_sysname)
        )
        grp = grp.scalar_one_or_none()
        if grp:
            db.add(UserPermissionGroup(user_id=user.id, group_id=grp.id))

    await db.commit()
    await db.refresh(user)
    return _user_out(user)


@router.put("/users/{user_id}", response_model=UserOut)
async def admin_update_user(
    user_id: UUID,
    body: UserUpdate,
    db: AsyncSession = Depends(get_db),
    _=_admin,
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


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def admin_delete_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    _=_admin,
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    await db.delete(user)
    await db.commit()


# ─── User ↔ Group assignments ─────────────────────────────────────────────

@router.post("/users/{user_id}/groups/{group_sysname}", status_code=status.HTTP_201_CREATED)
async def add_user_to_group(
    user_id: UUID,
    group_sysname: str,
    db: AsyncSession = Depends(get_db),
    _=_admin,
):
    user = (await db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    grp = (await db.execute(
        select(PermissionGroup).where(PermissionGroup.sysname == group_sysname)
    )).scalar_one_or_none()
    if grp is None:
        raise HTTPException(status_code=404, detail="Group not found")

    existing = (await db.execute(
        select(UserPermissionGroup).where(
            UserPermissionGroup.user_id == user_id,
            UserPermissionGroup.group_id == grp.id,
        )
    )).scalar_one_or_none()
    if not existing:
        db.add(UserPermissionGroup(user_id=user_id, group_id=grp.id))
        await db.commit()

    return {"message": "User added to group"}


@router.delete("/users/{user_id}/groups/{group_sysname}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_user_from_group(
    user_id: UUID,
    group_sysname: str,
    db: AsyncSession = Depends(get_db),
    _=_admin,
):
    grp = (await db.execute(
        select(PermissionGroup).where(PermissionGroup.sysname == group_sysname)
    )).scalar_one_or_none()
    if grp is None:
        raise HTTPException(status_code=404, detail="Group not found")

    await db.execute(
        delete(UserPermissionGroup).where(
            UserPermissionGroup.user_id == user_id,
            UserPermissionGroup.group_id == grp.id,
        )
    )
    await db.commit()


# ─── Permission Groups ────────────────────────────────────────────────────

@router.get("/permission-groups", response_model=List[PermissionGroupOut])
async def get_permission_groups(db: AsyncSession = Depends(get_db), _=_admin):
    result = await db.execute(select(PermissionGroup))
    return result.scalars().all()


@router.post("/permission-groups", response_model=PermissionGroupOut,
             status_code=status.HTTP_201_CREATED)
async def create_permission_group(
    body: ConfigItemCreate,
    db: AsyncSession = Depends(get_db),
    _=_admin,
):
    existing = (await db.execute(
        select(PermissionGroup).where(PermissionGroup.sysname == body.sysname)
    )).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=409, detail="sysname already exists")

    grp = PermissionGroup(
        sysname=body.sysname,
        display_name=body.display_name,
        default_redirect=body.default_redirect or "/dashboard",
    )
    db.add(grp)
    await db.commit()
    await db.refresh(grp)
    return grp


@router.put("/permission-groups/{sysname}", response_model=PermissionGroupOut)
async def update_permission_group(
    sysname: str,
    body: ConfigItemUpdate,
    db: AsyncSession = Depends(get_db),
    _=_admin,
):
    grp = (await db.execute(
        select(PermissionGroup).where(PermissionGroup.sysname == sysname)
    )).scalar_one_or_none()
    if grp is None:
        raise HTTPException(status_code=404, detail="Group not found")

    if body.display_name is not None:
        grp.display_name = body.display_name
    if body.default_redirect is not None:
        grp.default_redirect = body.default_redirect

    await db.commit()
    await db.refresh(grp)
    return grp


@router.delete("/permission-groups/{sysname}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_permission_group(
    sysname: str,
    db: AsyncSession = Depends(get_db),
    _=_admin,
):
    grp = (await db.execute(
        select(PermissionGroup).where(PermissionGroup.sysname == sysname)
    )).scalar_one_or_none()
    if grp is None:
        raise HTTPException(status_code=404, detail="Group not found")
    await db.delete(grp)
    await db.commit()


# ─── Permission Group ↔ Permission assignments ────────────────────────────

@router.get("/permissions", response_model=List[PermissionOut])
async def get_permissions(db: AsyncSession = Depends(get_db), _=_admin):
    result = await db.execute(select(Permission).order_by(Permission.resource, Permission.action))
    return result.scalars().all()


@router.post("/permission-groups/{group_sysname}/permissions/{perm_sysname}",
             status_code=status.HTTP_201_CREATED)
async def add_permission_to_group(
    group_sysname: str,
    perm_sysname: str,
    db: AsyncSession = Depends(get_db),
    _=_admin,
):
    grp = (await db.execute(
        select(PermissionGroup).where(PermissionGroup.sysname == group_sysname)
    )).scalar_one_or_none()
    if grp is None:
        raise HTTPException(status_code=404, detail="Group not found")

    perm = (await db.execute(
        select(Permission).where(Permission.sysname == perm_sysname)
    )).scalar_one_or_none()
    if perm is None:
        raise HTTPException(status_code=404, detail="Permission not found")

    existing = (await db.execute(
        select(PermissionGroupPermission).where(
            PermissionGroupPermission.group_id == grp.id,
            PermissionGroupPermission.permission_id == perm.id,
        )
    )).scalar_one_or_none()
    if not existing:
        db.add(PermissionGroupPermission(group_id=grp.id, permission_id=perm.id))
        await db.commit()

    return {"message": "Permission added to group"}


@router.delete("/permission-groups/{group_sysname}/permissions/{perm_sysname}",
               status_code=status.HTTP_204_NO_CONTENT)
async def remove_permission_from_group(
    group_sysname: str,
    perm_sysname: str,
    db: AsyncSession = Depends(get_db),
    _=_admin,
):
    grp = (await db.execute(
        select(PermissionGroup).where(PermissionGroup.sysname == group_sysname)
    )).scalar_one_or_none()
    if grp is None:
        raise HTTPException(status_code=404, detail="Group not found")

    perm = (await db.execute(
        select(Permission).where(Permission.sysname == perm_sysname)
    )).scalar_one_or_none()
    if perm is None:
        raise HTTPException(status_code=404, detail="Permission not found")

    await db.execute(
        delete(PermissionGroupPermission).where(
            PermissionGroupPermission.group_id == grp.id,
            PermissionGroupPermission.permission_id == perm.id,
        )
    )
    await db.commit()
