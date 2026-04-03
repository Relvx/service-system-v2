"""
Скрипт полной очистки тестовых данных.

Удаляет ВСЕ бизнес-данные (выезды, клиенты, объекты, договоры,
дефекты, закупки, уведомления, задачи, напоминания и т.д.).

Оставляет нетронутыми:
  - Системные справочники (config_tables: статусы, типы, приоритеты)
  - Группы прав (permission_groups)
  - Типы сущностей (entity_types)
  - Пользователя admin (все остальные пользователи удаляются)

Запуск из папки backend/:
    venv/bin/python scripts/clear_data.py

Для подтверждения ввести "yes" когда скрипт спросит.
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.database import AsyncSessionLocal


TABLES_IN_ORDER = [
    # Зависимые таблицы — сначала
    "notifications",
    "attachments",
    "logs",
    "service_schedules",
    "equipment",
    "calendar_notes",
    "reminders",
    "tasks",
    "purchases",
    "defects",
    "visits",
    "contract_sites",       # связь договор↔объект
    "contracts",
    "client_contacts",
    "client_legals",
    "sites",
    "clients",
    "history",
]

KEEP_ADMIN_USERNAME = "admin"


async def clear():
    print("=" * 55)
    print("  ОЧИСТКА ТЕСТОВЫХ ДАННЫХ")
    print("=" * 55)
    print()
    print("Будет удалено ВСЁ содержимое таблиц:")
    for t in TABLES_IN_ORDER:
        print(f"  - {t}")
    print()
    print("Пользователи: будут удалены все, кроме 'admin'")
    print()
    confirm = input("Введите 'yes' для подтверждения: ").strip().lower()
    if confirm != "yes":
        print("Отменено.")
        return

    async with AsyncSessionLocal() as session:
        async with session.begin():
            # Считаем записи до удаления
            print()
            print("Количество записей до очистки:")
            for table in TABLES_IN_ORDER:
                try:
                    r = await session.execute(text(f"SELECT COUNT(*) FROM {table}"))
                    count = r.scalar()
                    if count:
                        print(f"  {table}: {count}")
                except Exception:
                    pass

            r = await session.execute(
                text("SELECT COUNT(*) FROM users WHERE username != :u"),
                {"u": KEEP_ADMIN_USERNAME}
            )
            non_admin_count = r.scalar()
            if non_admin_count:
                print(f"  users (не admin): {non_admin_count}")

            print()
            print("Удаляю...")

            # Удаляем таблицы в правильном порядке
            for table in TABLES_IN_ORDER:
                try:
                    result = await session.execute(text(f"DELETE FROM {table}"))
                    if result.rowcount:
                        print(f"  ✓ {table}: удалено {result.rowcount}")
                except Exception as e:
                    print(f"  ✗ {table}: ошибка — {e}")

            # Удаляем пользователей кроме admin
            try:
                result = await session.execute(
                    text("DELETE FROM users WHERE username != :u"),
                    {"u": KEEP_ADMIN_USERNAME}
                )
                if result.rowcount:
                    print(f"  ✓ users (не admin): удалено {result.rowcount}")
            except Exception as e:
                print(f"  ✗ users: ошибка — {e}")

        print()
        print("Готово. База данных очищена.")
        print(f"Пользователь '{KEEP_ADMIN_USERNAME}' сохранён.")


if __name__ == "__main__":
    asyncio.run(clear())
