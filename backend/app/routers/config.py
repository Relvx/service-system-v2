"""Config router — GET all resources (public to authenticated users) + admin CRUD."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.dependencies import get_db, get_current_user, require_groups
from app.models.config_tables import (
    Role, VisitStatus, VisitType, Priority,
    DefectStatus, DefectActionType, AttachmentKind,
    PurchaseStatus, ServiceFrequency, NotificationType,
)
from app.schemas.config import (
    RoleOut, VisitStatusOut, VisitTypeOut, PriorityOut,
    DefectStatusOut, DefectActionTypeOut, AttachmentKindOut,
    PurchaseStatusOut, ServiceFrequencyOut, NotificationTypeOut,
    ConfigItemCreate, ConfigItemUpdate,
)

router = APIRouter(prefix="/config", tags=["config"])

# ─── Resource map for generic CRUD ─────────────────────────────────────────

_MODELS = {
    "visit-statuses": (VisitStatus, VisitStatusOut),
    "visit-types": (VisitType, VisitTypeOut),
    "priorities": (Priority, PriorityOut),
    "defect-statuses": (DefectStatus, DefectStatusOut),
    "defect-action-types": (DefectActionType, DefectActionTypeOut),
    "attachment-kinds": (AttachmentKind, AttachmentKindOut),
    "purchase-statuses": (PurchaseStatus, PurchaseStatusOut),
    "service-frequencies": (ServiceFrequency, ServiceFrequencyOut),
    "notification-types": (NotificationType, NotificationTypeOut),
}


# ─── Read endpoints (any authenticated user) ───────────────────────────────

@router.get("/roles", response_model=List[RoleOut])
async def get_roles(db: AsyncSession = Depends(get_db), _=Depends(get_current_user)):
    result = await db.execute(select(Role))
    return result.scalars().all()


@router.get("/visit-statuses", response_model=List[VisitStatusOut])
async def get_visit_statuses(db: AsyncSession = Depends(get_db), _=Depends(get_current_user)):
    result = await db.execute(select(VisitStatus))
    return result.scalars().all()


@router.get("/visit-types", response_model=List[VisitTypeOut])
async def get_visit_types(db: AsyncSession = Depends(get_db), _=Depends(get_current_user)):
    result = await db.execute(select(VisitType))
    return result.scalars().all()


@router.get("/priorities", response_model=List[PriorityOut])
async def get_priorities(db: AsyncSession = Depends(get_db), _=Depends(get_current_user)):
    result = await db.execute(select(Priority).order_by(Priority.sort_order))
    return result.scalars().all()


@router.get("/defect-statuses", response_model=List[DefectStatusOut])
async def get_defect_statuses(db: AsyncSession = Depends(get_db), _=Depends(get_current_user)):
    result = await db.execute(select(DefectStatus))
    return result.scalars().all()


@router.get("/defect-action-types", response_model=List[DefectActionTypeOut])
async def get_defect_action_types(db: AsyncSession = Depends(get_db), _=Depends(get_current_user)):
    result = await db.execute(select(DefectActionType))
    return result.scalars().all()


@router.get("/attachment-kinds", response_model=List[AttachmentKindOut])
async def get_attachment_kinds(db: AsyncSession = Depends(get_db), _=Depends(get_current_user)):
    result = await db.execute(select(AttachmentKind))
    return result.scalars().all()


@router.get("/purchase-statuses", response_model=List[PurchaseStatusOut])
async def get_purchase_statuses(db: AsyncSession = Depends(get_db), _=Depends(get_current_user)):
    result = await db.execute(select(PurchaseStatus))
    return result.scalars().all()


@router.get("/service-frequencies", response_model=List[ServiceFrequencyOut])
async def get_service_frequencies(db: AsyncSession = Depends(get_db), _=Depends(get_current_user)):
    result = await db.execute(select(ServiceFrequency))
    return result.scalars().all()


@router.get("/notification-types", response_model=List[NotificationTypeOut])
async def get_notification_types(db: AsyncSession = Depends(get_db), _=Depends(get_current_user)):
    result = await db.execute(select(NotificationType))
    return result.scalars().all()


# ─── Generic admin CRUD ─────────────────────────────────────────────────────

def _admin_dep():
    return Depends(require_groups("admin_group"))


@router.post("/{resource}", status_code=status.HTTP_201_CREATED)
async def create_config_item(
    resource: str,
    body: ConfigItemCreate,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_groups("admin_group")),
):
    if resource not in _MODELS:
        raise HTTPException(status_code=404, detail=f"Unknown config resource: {resource}")
    model_cls, schema_cls = _MODELS[resource]

    existing = await db.execute(
        select(model_cls).where(model_cls.sysname == body.sysname)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="sysname already exists")

    kwargs = {"sysname": body.sysname, "display_name": body.display_name}
    if body.sort_order is not None and hasattr(model_cls, "sort_order"):
        kwargs["sort_order"] = body.sort_order
    if body.default_redirect is not None and hasattr(model_cls, "default_redirect"):
        kwargs["default_redirect"] = body.default_redirect

    item = model_cls(**kwargs)
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return schema_cls.model_validate(item)


@router.put("/{resource}/{sysname}")
async def update_config_item(
    resource: str,
    sysname: str,
    body: ConfigItemUpdate,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_groups("admin_group")),
):
    if resource not in _MODELS:
        raise HTTPException(status_code=404, detail=f"Unknown config resource: {resource}")
    model_cls, schema_cls = _MODELS[resource]

    result = await db.execute(select(model_cls).where(model_cls.sysname == sysname))
    item = result.scalar_one_or_none()
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")

    if body.display_name is not None:
        item.display_name = body.display_name
    if body.sort_order is not None and hasattr(item, "sort_order"):
        item.sort_order = body.sort_order
    if body.default_redirect is not None and hasattr(item, "default_redirect"):
        item.default_redirect = body.default_redirect

    await db.commit()
    await db.refresh(item)
    return schema_cls.model_validate(item)


@router.delete("/{resource}/{sysname}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_config_item(
    resource: str,
    sysname: str,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_groups("admin_group")),
):
    if resource not in _MODELS:
        raise HTTPException(status_code=404, detail=f"Unknown config resource: {resource}")
    model_cls, _ = _MODELS[resource]

    result = await db.execute(select(model_cls).where(model_cls.sysname == sysname))
    item = result.scalar_one_or_none()
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")

    await db.delete(item)
    await db.commit()
