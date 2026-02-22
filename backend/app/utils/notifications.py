from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification


async def create_notification(
    db: AsyncSession,
    user_id: UUID,
    type_: str,
    title: str,
    message: str,
    related_visit_id: UUID | None = None,
) -> None:
    notif = Notification(
        user_id=user_id,
        type=type_,
        title=title,
        message=message,
        related_visit_id=related_visit_id,
    )
    db.add(notif)
    # caller commits the transaction
