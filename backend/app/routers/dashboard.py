from datetime import date, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.dependencies import get_db, require_groups
from app.models.visit import Visit
from app.models.site import Site
from app.models.client import Client
from app.models.user import User
from app.models.defect import Defect
from app.models.purchase import Purchase
from app.schemas.dashboard import DashboardStats, DefectPriorityCount, VisitShort
from app.enums import enums

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


def _visit_short_query():
    return (
        select(
            Visit.id,
            Visit.planned_date,
            Visit.status,
            Visit.visit_type,
            Site.title.label("site_title"),
            Client.name.label("client_name"),
            User.full_name.label("master_name"),
        )
        .outerjoin(Site, Visit.site_id == Site.id)
        .outerjoin(Client, Site.client_id == Client.id)
        .outerjoin(User, Visit.assigned_user_id == User.id)
    )


def _row_to_visit_short(row) -> VisitShort:
    return VisitShort(
        id=row.id,
        planned_date=row.planned_date,
        status=row.status,
        visit_type=row.visit_type,
        site_title=row.site_title,
        client_name=row.client_name,
        master_name=row.master_name,
    )


@router.get("/stats", response_model=DashboardStats)
async def get_stats(
    db: AsyncSession = Depends(get_db),
    _=Depends(require_groups("admin_group", "office_group")),
):
    today = date.today()
    week_end = today + timedelta(days=7)

    # visits today (count)
    r1 = await db.execute(
        select(func.count()).where(Visit.planned_date == today, Visit.status != enums.visit_statuses.cancelled)
    )
    visits_today = r1.scalar() or 0

    # visits this week (count)
    r2 = await db.execute(
        select(func.count()).where(
            Visit.planned_date >= today,
            Visit.planned_date < week_end,
            Visit.status != enums.visit_statuses.cancelled,
        )
    )
    visits_week = r2.scalar() or 0

    # open defects by priority
    r3 = await db.execute(
        select(Defect.priority, func.count().label("count"))
        .where(Defect.status != enums.defect_statuses.fixed)
        .group_by(Defect.priority)
    )
    open_defects = [DefectPriorityCount(priority=row[0], count=row[1]) for row in r3.all()]

    # active purchases (count)
    r4 = await db.execute(
        select(func.count()).where(Purchase.status != enums.purchase_statuses.closed)
    )
    active_purchases = r4.scalar() or 0

    # today's visits list
    r5 = await db.execute(
        _visit_short_query()
        .where(Visit.planned_date == today, Visit.status != enums.visit_statuses.cancelled)
        .order_by(Visit.planned_time_from)
    )
    today_visits = [_row_to_visit_short(row) for row in r5.all()]

    # last 5 completed visits
    r6 = await db.execute(
        _visit_short_query()
        .where(Visit.status == enums.visit_statuses.closed)
        .order_by(Visit.completed_at.desc())
        .limit(5)
    )
    recent_completed = [_row_to_visit_short(row) for row in r6.all()]

    return DashboardStats(
        visits_today=visits_today,
        visits_this_week=visits_week,
        open_defects=open_defects,
        active_purchases=active_purchases,
        today_visits=today_visits,
        recent_completed=recent_completed,
    )
