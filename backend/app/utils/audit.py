"""Вспомогательные функции для версионирования записей и аудит-лога."""

from datetime import datetime
from typing import Any, Optional, Dict
from sqlalchemy.ext.asyncio import AsyncSession


def _has_changes(record: Any, new_values: Dict[str, Any]) -> bool:
    """Возвращает True, если хотя бы одно поле из new_values отличается от текущего."""
    for key, new_val in new_values.items():
        if not hasattr(record, key):
            continue
        current = getattr(record, key)
        # Сравниваем строковое представление для дат/времени/Decimal
        if str(current) != str(new_val):
            return True
    return False


_EXCLUDE_FROM_SNAPSHOT = {"is_archived", "created_at", "updated_at"}


def _build_v_kwargs(record: Any) -> Dict[str, Any]:
    """Возвращает словарь {v_<col>: value} по всем колонкам записи.

    Системные поля (is_archived, created_at, updated_at) исключаются —
    они не несут бизнес-смысла в исторических снапшотах.
    """
    kwargs: Dict[str, Any] = {}
    for col in record.__table__.columns:
        if col.name in _EXCLUDE_FROM_SNAPSHOT:
            continue
        kwargs[f"v_{col.name}"] = getattr(record, col.name)
    return kwargs


async def save_history(
    db: AsyncSession,
    history_model,
    record: Any,
    user_id: Optional[int],
    method: str,
    new_values: Optional[Dict[str, Any]] = None,
) -> bool:
    """Записать версию в таблицу *_history.

    Для method='update' запись создаётся только если new_values содержит
    хотя бы одно изменённое поле.  Для 'create'/'delete' всегда.

    Возвращает True, если запись была добавлена.
    """
    if method == "update" and new_values is not None:
        if not _has_changes(record, new_values):
            return False

    kwargs = _build_v_kwargs(record)
    kwargs["changed_at"] = datetime.now()
    kwargs["changed_by_user_id"] = user_id
    kwargs["method"] = method

    db.add(history_model(**kwargs))
    return True


async def save_log(
    db: AsyncSession,
    user_id: Optional[int],
    action_sysname: str,
    entity_type: str,
    entity_id: int,
    details: Optional[dict] = None,
) -> None:
    """Добавить запись в audit-лог."""
    from app.models.log import Log
    db.add(Log(
        user_id=user_id,
        action_sysname=action_sysname,
        entity_type=entity_type,
        entity_id=entity_id,
        details=details,
    ))
