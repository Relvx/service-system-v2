from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.dependencies import get_db, get_current_user
from app.models.defect import Defect
from app.models.site import Site
from app.models.client import Client
from app.models.visit import Visit
from app.schemas.defect import DefectOut, DefectCreate, DefectUpdate
from app.utils.audit import save_log
from app.enums import enums

router = APIRouter(prefix="/defects", tags=["defects"])


def _build_defect_query():
    return (
        select(
            Defect,
            Site.title.label("site_title"),
            Site.address,
            Client.name.label("client_name"),
            Visit.planned_date.label("visit_date"),
            Visit.visit_type,
        )
        .outerjoin(Site, Defect.site_id == Site.id)
        .outerjoin(Client, Site.client_id == Client.id)
        .outerjoin(Visit, Defect.visit_id == Visit.id)
    )


def _row_to_out(row) -> DefectOut:
    defect = row[0]
    obj = DefectOut.model_validate(defect)
    obj.site_title = row[1]
    obj.address = row[2]
    obj.client_name = row[3]
    obj.visit_date = row[4]
    obj.visit_type = row[5]
    return obj


@router.get("", response_model=List[DefectOut])
async def get_defects(
    site_id: Optional[int] = None,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    stmt = _build_defect_query()
    if site_id:
        stmt = stmt.where(Defect.site_id == site_id)
    if status:
        stmt = stmt.where(Defect.status == status)
    if priority:
        stmt = stmt.where(Defect.priority == priority)
    stmt = stmt.order_by(Defect.created_at.desc())
    result = await db.execute(stmt)
    return [_row_to_out(r) for r in result.all()]


@router.post("", response_model=DefectOut, status_code=status.HTTP_201_CREATED)
async def create_defect(
    body: DefectCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    defect = Defect(**body.model_dump())
    db.add(defect)
    await db.flush()
    await save_log(db, current_user.id, enums.log_actions.defect_create, "defect", defect.id)
    await db.commit()
    await db.refresh(defect)

    stmt = _build_defect_query().where(Defect.id == defect.id)
    result = await db.execute(stmt)
    return _row_to_out(result.first())


@router.put("/{defect_id}", response_model=DefectOut)
async def update_defect(
    defect_id: int,
    body: DefectUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = await db.execute(select(Defect).where(Defect.id == defect_id))
    defect = result.scalar_one_or_none()
    if defect is None:
        raise HTTPException(status_code=404, detail="Defect not found")

    changed = body.model_dump(exclude_unset=True)
    for field, value in changed.items():
        setattr(defect, field, value)

    # Выбираем наиболее специфичное действие
    new_status = changed.get("status")
    if new_status == "approved":
        action = enums.log_actions.defect_approve
    elif "status" in changed:
        action = enums.log_actions.defect_change_status
    else:
        action = enums.log_actions.defect_update

    await save_log(db, current_user.id, action, "defect", defect_id,
                   details={"changed": list(changed.keys())})
    await db.commit()

    stmt = _build_defect_query().where(Defect.id == defect_id)
    result = await db.execute(stmt)
    return _row_to_out(result.first())
