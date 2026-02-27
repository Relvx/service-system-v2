"""Глобальные enum-контейнеры, загружаемые из БД при старте приложения.

Использование в роутерах:
    from app.enums import enums
    await save_log(db, user_id, enums.log_actions.visit_create, "visit", visit.id)
"""

from sqlalchemy.ext.asyncio import AsyncSession


class _LogActions:
    """Контейнер sysname действий лога. Заполняется из таблицы log_actions при старте."""

    def __init__(self):
        object.__setattr__(self, "_store", {})

    def _register(self, sysname: str) -> None:
        object.__getattribute__(self, "_store")[sysname] = sysname

    def __getattr__(self, name: str) -> str:
        store = object.__getattribute__(self, "_store")
        if name in store:
            return store[name]
        raise AttributeError(
            f"LogAction '{name}' not found. "
            "Проверьте, что enums.load() вызван при старте и sysname присутствует в таблице log_actions."
        )


class AppEnums:
    """Глобальный реестр enum-значений, загруженных из БД."""

    def __init__(self):
        self.log_actions = _LogActions()


enums = AppEnums()


async def load_enums(db: AsyncSession) -> None:
    """Загрузить все enum-таблицы из БД в память при старте приложения."""
    from sqlalchemy import select
    from app.models.log import LogAction

    result = await db.execute(select(LogAction))
    for action in result.scalars():
        enums.log_actions._register(action.sysname)
