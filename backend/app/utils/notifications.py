from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.notification import Notification


async def create_notification(
    db: AsyncSession,
    user_id: int,
    type_: str,
    title: str,
    message: str,
    related_visit_id: int | None = None,
    related_defect_id: int | None = None,
    related_purchase_id: int | None = None,
) -> None:
    notif = Notification(
        user_id=user_id,
        type=type_,
        title=title,
        message=message,
        related_visit_id=related_visit_id,
        related_defect_id=related_defect_id,
        related_purchase_id=related_purchase_id,
    )
    db.add(notif)
    # caller commits the transaction


async def notify_users_by_group(
    db: AsyncSession,
    group_sysnames: list[str],
    exclude_user_id: int,
    type_: str,
    title: str,
    message: str,
    related_visit_id: int | None = None,
    related_defect_id: int | None = None,
    related_purchase_id: int | None = None,
) -> None:
    """Create notifications for all active users in given groups, excluding one user."""
    from app.models.user import User
    from app.models.config_tables import PermissionGroup, UserPermissionGroup

    result = await db.execute(
        select(User)
        .join(UserPermissionGroup, User.id == UserPermissionGroup.user_id)
        .join(PermissionGroup, UserPermissionGroup.group_id == PermissionGroup.id)
        .where(PermissionGroup.sysname.in_(group_sysnames))
        .where(User.id != exclude_user_id)
        .where(User.is_active == True)
        .distinct()
    )
    for user in result.scalars().all():
        await create_notification(
            db, user.id, type_, title, message,
            related_visit_id=related_visit_id,
            related_defect_id=related_defect_id,
            related_purchase_id=related_purchase_id,
        )
