"""Глобальные enum-контейнеры, загружаемые из БД при старте приложения.

Использование в роутерах:
    from app.enums import enums
    await save_log(db, user_id, enums.log_actions.visit_create, "visit", visit.id)

Доступ к названиям документов:
    enums.entity_types.get("visit")           # {"sysname": "visit", "display_name": "Выезд", ...}
    enums.entity_types.display_name("client") # "Клиент"
    enums.entity_types.all()                  # список всех типов
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


class _EntityTypes:
    """Контейнер типов документов. Заполняется из таблицы entity_types при старте."""

    def __init__(self):
        object.__setattr__(self, "_store", {})   # sysname → dict

    def _register(self, sysname: str, display_name: str, display_name_plural: str) -> None:
        store = object.__getattribute__(self, "_store")
        store[sysname] = {
            "sysname": sysname,
            "display_name": display_name,
            "display_name_plural": display_name_plural,
        }

    def get(self, sysname: str) -> dict:
        store = object.__getattribute__(self, "_store")
        return store.get(sysname, {"sysname": sysname, "display_name": sysname, "display_name_plural": sysname})

    def display_name(self, sysname: str) -> str:
        return self.get(sysname)["display_name"]

    def display_name_plural(self, sysname: str) -> str:
        return self.get(sysname)["display_name_plural"]

    def all(self) -> list:
        return list(object.__getattribute__(self, "_store").values())


class AppEnums:
    """Глобальный реестр enum-значений, загруженных из БД."""

    def __init__(self):
        self.log_actions  = _LogActions()
        self.entity_types = _EntityTypes()


enums = AppEnums()


async def load_enums(db: AsyncSession) -> None:
    """Загрузить все enum-таблицы из БД в память при старте приложения."""
    from sqlalchemy import select
    from app.models.log import LogAction
    from app.models.entity_type import EntityType

    result = await db.execute(select(LogAction))
    for action in result.scalars():
        enums.log_actions._register(action.sysname)

    result = await db.execute(select(EntityType))
    for et in result.scalars():
        enums.entity_types._register(et.sysname, et.display_name, et.display_name_plural)
