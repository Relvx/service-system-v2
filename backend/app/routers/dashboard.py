from datetime import date, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text

from app.dependencies import get_db, require_groups
from app.models.visit import Visit
from app.models.defect import Defect
from app.models.purchase import Purchase
from app.schemas.dashboard import DashboardStats, DefectPriorityCount

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/stats", response_model=DashboardStats)
async def get_stats(
    db: AsyncSession = Depends(get_db),
    _=Depends(require_groups("admin_group", "office_group")),
):
    today = date.today()
    week_end = today + timedelta(days=7)

    # visits today
    r1 = await db.execute(
        select(func.count()).where(Visit.planned_date == today, Visit.status != "cancelled")
    )
    visits_today = r1.scalar() or 0

    # visits this week
    r2 = await db.execute(
        select(func.count()).where(
            Visit.planned_date >= today,
            Visit.planned_date < week_end,
            Visit.status != "cancelled",
        )
    )
    visits_week = r2.scalar() or 0

    # open defects by priority
    r3 = await db.execute(
        select(Defect.priority, func.count().label("count"))
        .where(Defect.status.not_in(["fixed", "cancelled"]))
        .group_by(Defect.priority)
    )
    open_defects = [DefectPriorityCount(priority=row[0], count=row[1]) for row in r3.all()]

    # active purchases
    r4 = await db.execute(
        select(func.count()).where(Purchase.status.not_in(["closed", "cancelled"]))
    )
    active_purchases = r4.scalar() or 0

    return DashboardStats(
        visits_today=visits_today,
        visits_this_week=visits_week,
        open_defects=open_defects,
        active_purchases=active_purchases,
    )
