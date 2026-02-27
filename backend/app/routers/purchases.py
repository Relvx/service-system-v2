from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.dependencies import get_db, get_current_user
from app.models.purchase import Purchase
from app.models.defect import Defect
from app.models.site import Site
from app.models.history import PurchaseHistory
from app.schemas.purchase import PurchaseOut, PurchaseCreate, PurchaseUpdate
from app.utils.audit import save_history, save_log

router = APIRouter(prefix="/purchases", tags=["purchases"])


def _build_query():
    return (
        select(
            Purchase,
            Defect.title.label("defect_title"),
            Site.title.label("site_title"),
        )
        .outerjoin(Defect, Purchase.defect_id == Defect.id)
        .outerjoin(Site, Purchase.site_id == Site.id)
    )


def _row_to_out(row) -> PurchaseOut:
    p = row[0]
    obj = PurchaseOut.model_validate(p)
    obj.defect_title = row[1]
    obj.site_title = row[2]
    return obj


@router.get("", response_model=List[PurchaseOut])
async def get_purchases(
    status: Optional[str] = None,
    defect_id: Optional[UUID] = None,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    stmt = _build_query()
    if status:
        stmt = stmt.where(Purchase.status == status)
    if defect_id:
        stmt = stmt.where(Purchase.defect_id == defect_id)
    stmt = stmt.order_by(Purchase.created_at.desc())
    result = await db.execute(stmt)
    return [_row_to_out(r) for r in result.all()]


@router.post("", response_model=PurchaseOut, status_code=status.HTTP_201_CREATED)
async def create_purchase(
    body: PurchaseCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    p = Purchase(**body.model_dump())
    db.add(p)
    await db.flush()
    await save_log(db, current_user.id, "create", "purchase", p.id)
    await db.commit()
    await db.refresh(p)

    stmt = _build_query().where(Purchase.id == p.id)
    result = await db.execute(stmt)
    return _row_to_out(result.first())


@router.put("/{purchase_id}", response_model=PurchaseOut)
async def update_purchase(
    purchase_id: UUID,
    body: PurchaseUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = await db.execute(select(Purchase).where(Purchase.id == purchase_id))
    p = result.scalar_one_or_none()
    if p is None:
        raise HTTPException(status_code=404, detail="Purchase not found")

    changed = body.model_dump(exclude_unset=True)
    await save_history(db, PurchaseHistory, p, current_user.id,
                       method="update", new_values=changed)

    for field, value in changed.items():
        setattr(p, field, value)

    await save_log(db, current_user.id, "update", "purchase", purchase_id)
    await db.commit()

    stmt = _build_query().where(Purchase.id == purchase_id)
    result = await db.execute(stmt)
    return _row_to_out(result.first())
