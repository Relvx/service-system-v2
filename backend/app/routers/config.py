from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.dependencies import get_db, get_current_user
from app.models.config_tables import (
    Role, VisitStatus, VisitType, Priority,
    DefectStatus, DefectActionType, AttachmentKind,
    PurchaseStatus, ServiceFrequency, NotificationType,
)
from app.schemas.config import (
    RoleOut, VisitStatusOut, VisitTypeOut, PriorityOut,
    DefectStatusOut, DefectActionTypeOut, AttachmentKindOut,
    PurchaseStatusOut, ServiceFrequencyOut, NotificationTypeOut,
)

router = APIRouter(prefix="/config", tags=["config"])


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
