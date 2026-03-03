"""Глобальные enum-контейнеры, загружаемые из БД при старте приложения.

Использование в роутерах:
    from app.enums import enums

    # Получить ID по sysname (для FK-запросов и бизнес-логики)
    enums.visit_statuses.id("planned")            # → 1

    # Обращение к sysname как атрибуту — избавляет от хардкода строк
    enums.visit_statuses.planned                  # → "planned"
    enums.defect_statuses.fixed                   # → "fixed"
    Visit.status != enums.visit_statuses.cancelled

    # Получить display_name для отображения
    enums.visit_statuses.display_name("planned")  # → "Запланирован"

    # Список {id, display_name} — для отдачи на фронт
    enums.visit_statuses.all()

    # Типы документов и действия лога — без изменений
    enums.entity_types.display_name("visit")      # → "Выезд"
    enums.log_actions.visit_create                # → "visit_create"
"""

from sqlalchemy.ext.asyncio import AsyncSession


class _SysnameTable:
    """Универсальный in-memory кеш для одной системной таблицы.

    Загружается один раз при старте приложения. Предоставляет:
      - .id("sysname")           → int   (для запросов и бизнес-логики вместо хардкода)
      - .sysname_for(id)         → str   (обратный поиск)
      - .display_name("sysname") → str
      - .all()                   → [{id, display_name}, ...]
      - .planned / .cancelled    → "planned" / "cancelled"  (прямой доступ к sysname)
    """

    def __init__(self, table_name: str):
        object.__setattr__(self, "_table_name", table_name)
        object.__setattr__(self, "_by_sysname", {})  # sysname → {id, sysname, display_name}
        object.__setattr__(self, "_by_id", {})        # id → sysname

    def _register(self, row_id: int, sysname: str, display_name: str) -> None:
        by_sysname = object.__getattribute__(self, "_by_sysname")
        by_id = object.__getattribute__(self, "_by_id")
        by_sysname[sysname] = {"id": row_id, "sysname": sysname, "display_name": display_name}
        by_id[row_id] = sysname

    def id(self, sysname: str) -> int:
        """Вернуть целочисленный ID записи по sysname.

        Использовать в бизнес-логике вместо хардкода числовых ID:
            enums.visit_statuses.id("planned")
        """
        by_sysname = object.__getattribute__(self, "_by_sysname")
        if sysname not in by_sysname:
            table = object.__getattribute__(self, "_table_name")
            raise KeyError(f"'{sysname}' не найден в таблице '{table}'")
        return by_sysname[sysname]["id"]

    def sysname_for(self, row_id: int) -> str:
        """Вернуть sysname по целочисленному ID."""
        by_id = object.__getattribute__(self, "_by_id")
        if row_id not in by_id:
            table = object.__getattribute__(self, "_table_name")
            raise KeyError(f"ID {row_id} не найден в таблице '{table}'")
        return by_id[row_id]

    def display_name(self, sysname: str) -> str:
        """Вернуть отображаемое название по sysname."""
        by_sysname = object.__getattribute__(self, "_by_sysname")
        entry = by_sysname.get(sysname)
        if entry is None:
            table = object.__getattribute__(self, "_table_name")
            raise KeyError(f"'{sysname}' не найден в таблице '{table}'")
        return entry["display_name"]

    def all(self) -> list:
        """Список {id, display_name} — для отдачи на фронт в селектах."""
        by_sysname = object.__getattribute__(self, "_by_sysname")
        return [{"id": v["id"], "display_name": v["display_name"]} for v in by_sysname.values()]

    def __getattr__(self, name: str) -> str:
        """Прямой доступ к sysname как атрибуту: enums.visit_statuses.planned → 'planned'.

        Позволяет писать без хардкода строк:
            Visit.status != enums.visit_statuses.cancelled
        вместо:
            Visit.status != "cancelled"
        """
        if name.startswith("_"):
            raise AttributeError(name)
        by_sysname = object.__getattribute__(self, "_by_sysname")
        if name in by_sysname:
            return name
        table = object.__getattribute__(self, "_table_name")
        raise AttributeError(
            f"Sysname '{name}' не найден в таблице '{table}'. "
            "Убедитесь, что enums.load() вызван при старте и значение есть в БД."
        )


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
            f"LogAction '{name}' не найден. "
            "Проверьте, что enums.load() вызван при старте и sysname присутствует в log_actions."
        )


class _EntityTypes:
    """Контейнер типов документов. Заполняется из таблицы entity_types при старте."""

    def __init__(self):
        object.__setattr__(self, "_store", {})  # sysname → dict

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
    """Глобальный реестр enum-значений, загруженных из БД.

    Все системные таблицы доступны как атрибуты:
        enums.visit_statuses.id("planned")      → 1
        enums.visit_statuses.planned            → "planned"
        enums.visit_types.maintenance           → "maintenance"
        enums.defect_statuses.fixed             → "fixed"
        enums.purchase_statuses.installed       → "installed"
        enums.priorities.high                   → "high"
    """

    def __init__(self):
        self.log_actions         = _LogActions()
        self.entity_types        = _EntityTypes()
        self.visit_statuses      = _SysnameTable("visit_statuses")
        self.visit_types         = _SysnameTable("visit_types")
        self.priorities          = _SysnameTable("priorities")
        self.defect_statuses     = _SysnameTable("defect_statuses")
        self.defect_action_types = _SysnameTable("defect_action_types")
        self.attachment_kinds    = _SysnameTable("attachment_kinds")
        self.purchase_statuses   = _SysnameTable("purchase_statuses")
        self.service_frequencies = _SysnameTable("service_frequencies")
        self.notification_types  = _SysnameTable("notification_types")


enums = AppEnums()


async def load_enums(db: AsyncSession) -> None:
    """Загрузить все enum-таблицы из БД в память при старте приложения."""
    from sqlalchemy import select
    from app.models.log import LogAction
    from app.models.entity_type import EntityType
    from app.models.config_tables import (
        VisitStatus, VisitType, Priority,
        DefectStatus, DefectActionType, AttachmentKind,
        PurchaseStatus, ServiceFrequency, NotificationType,
    )

    result = await db.execute(select(LogAction))
    for action in result.scalars():
        enums.log_actions._register(action.sysname)

    result = await db.execute(select(EntityType))
    for et in result.scalars():
        enums.entity_types._register(et.sysname, et.display_name, et.display_name_plural)

    for model, container in [
        (VisitStatus,        enums.visit_statuses),
        (VisitType,          enums.visit_types),
        (Priority,           enums.priorities),
        (DefectStatus,       enums.defect_statuses),
        (DefectActionType,   enums.defect_action_types),
        (AttachmentKind,     enums.attachment_kinds),
        (PurchaseStatus,     enums.purchase_statuses),
        (ServiceFrequency,   enums.service_frequencies),
        (NotificationType,   enums.notification_types),
    ]:
        rows = await db.execute(select(model))
        for row in rows.scalars():
            container._register(row.id, row.sysname, row.display_name)
