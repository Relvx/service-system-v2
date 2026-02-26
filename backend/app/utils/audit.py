"""Helpers for writing history snapshots and audit log entries."""

import uuid
from datetime import datetime
from typing import Any, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession


def _to_json(obj: Any) -> Any:
    """Convert a SQLAlchemy model instance to a JSON-serialisable dict."""
    if obj is None:
        return None
    result = {}
    for col in obj.__table__.columns:
        val = getattr(obj, col.name)
        if isinstance(val, UUID):
            val = str(val)
        elif isinstance(val, datetime):
            val = val.isoformat()
        result[col.name] = val
    return result


async def save_history(
    db: AsyncSession,
    history_model,
    record: Any,
    changed_by_user_id: Optional[UUID],
) -> None:
    """Append a snapshot row to a *_history table."""
    entry = history_model(
        record_id=record.id,
        changed_by_user_id=changed_by_user_id,
        snapshot=_to_json(record),
    )
    db.add(entry)


async def save_log(
    db: AsyncSession,
    user_id: Optional[UUID],
    action_sysname: str,
    entity_type: str,
    entity_id: UUID,
    details: Optional[dict] = None,
) -> None:
    """Append an audit log row."""
    from app.models.log import Log
    entry = Log(
        user_id=user_id,
        action_sysname=action_sysname,
        entity_type=entity_type,
        entity_id=entity_id,
        details=details,
    )
    db.add(entry)
