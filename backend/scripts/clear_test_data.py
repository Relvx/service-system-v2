"""
Удаление ТОЛЬКО тестовых данных из базы.

Тестовые записи определяются по именам — все они содержат
характерные маркеры: __ (двойное подчёркивание), TEST_, ZZZTEST_, BLK17-, TEST-B14-.

Что будет удалено (только строки с тестовыми именами):
  - выезды, привязанные к тестовым объектам
  - дефекты, привязанные к тестовым объектам (и их закупки)
  - закупки с тестовыми названиями
  - договоры тестовых клиентов + тестовые договора по номеру
  - тестовые объекты (sites)
  - тестовые клиенты (clients)
  - задачи с тестовыми названиями
  - напоминания с тестовыми названиями
  - заметки календаря с тестовыми текстами
  - уведомления, связанные с удалёнными выездами/дефектами

Что НЕ будет тронуто:
  - пользователи
  - реальные клиенты / объекты / выезды / дефекты / закупки
  - справочники (statuses, types, priorities)
  - группы прав

Запуск из папки backend/:
    venv/bin/python scripts/clear_test_data.py
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.database import AsyncSessionLocal

# Паттерны имён тестовых данных
# ВАЖНО: _ в SQL LIKE — wildcard (любой символ), поэтому используем ESCAPE '!'
# и экранируем реальные подчёркивания как !_
CLIENT_PATTERNS  = ['%!_!_%', 'TEST!_%', 'ZZZTEST!_%']
SITE_PATTERNS    = ['%!_!_%', 'TEST!_%', 'ZZZTEST!_%']
CONTRACT_PATTERNS = ['%!_!_%', 'BLK17-%', 'TEST-B14-%', 'TEST!_B%', 'ZZZTEST!_%']
DEFECT_PATTERNS  = ['%!_!_%', 'TEST!_%']
PURCHASE_PATTERNS = ['%!_!_%', 'TEST!_%']
TASK_PATTERNS    = ['%!_!_%', 'TEST!_%']
REMINDER_PATTERNS = ['%!_!_%', 'TEST!_%']
NOTE_PATTERNS    = ['%!_!_%', 'TEST!_%']


def like_clause(field: str, patterns: list[str]) -> str:
    parts = " OR ".join(f"{field} LIKE '{p}' ESCAPE '!'" for p in patterns)
    return f"({parts})"


async def clear():
    print("=" * 60)
    print("  УДАЛЕНИЕ ТЕСТОВЫХ ДАННЫХ")
    print("=" * 60)
    print()
    print("Паттерны тестовых имён: __ / TEST_ / ZZZTEST_ / BLK17- / TEST-B14-")
    print()

    async with AsyncSessionLocal() as session:

        # ── Предпросмотр ──────────────────────────────────────────────
        print("Будет удалено:")
        preview = [
            ("клиенты",    f"SELECT id, name FROM clients WHERE {like_clause('name', CLIENT_PATTERNS)}"),
            ("объекты",    f"SELECT id, title FROM sites WHERE {like_clause('title', SITE_PATTERNS)}"),
            ("договоры",   f"SELECT id, contract_number FROM contracts WHERE {like_clause('contract_number', CONTRACT_PATTERNS)}"),
            ("дефекты",    f"SELECT id, title FROM defects WHERE {like_clause('title', DEFECT_PATTERNS)}"),
            ("закупки",    f"SELECT id, item FROM purchases WHERE {like_clause('item', PURCHASE_PATTERNS)}"),
            ("задачи",     f"SELECT id, title FROM tasks WHERE {like_clause('title', TASK_PATTERNS)}"),
            ("напоминания",f"SELECT id, text FROM reminders WHERE {like_clause('text', REMINDER_PATTERNS)}"),
        ]

        found_anything = False
        for label, q in preview:
            r = await session.execute(text(q))
            rows = r.fetchall()
            if rows:
                found_anything = True
                print(f"\n  {label} ({len(rows)} шт.):")
                for row in rows:
                    print(f"    [{row[0]}] {row[1]}")

        # Выезды через тестовые объекты
        q_visits = f"""
            SELECT v.id, v.planned_date FROM visits v
            JOIN sites s ON s.id = v.site_id
            WHERE {like_clause('s.title', SITE_PATTERNS)}
        """
        r = await session.execute(text(q_visits))
        visit_rows = r.fetchall()
        if visit_rows:
            found_anything = True
            print(f"\n  выезды через тестовые объекты ({len(visit_rows)} шт.):")
            for row in visit_rows:
                print(f"    [{row[0]}] {row[1]}")

        if not found_anything:
            print("  — тестовых данных не найдено.")
            return

        print()
        confirm = input("Введите 'yes' для удаления: ").strip().lower()
        if confirm != "yes":
            print("Отменено.")
            return

        # ── Удаление ──────────────────────────────────────────────────
        print()
        async with session.begin():

            # 1. Собираем id тестовых объектов и клиентов
            r = await session.execute(text(
                f"SELECT id FROM sites WHERE {like_clause('title', SITE_PATTERNS)}"
            ))
            test_site_ids = [row[0] for row in r.fetchall()]

            r = await session.execute(text(
                f"SELECT id FROM clients WHERE {like_clause('name', CLIENT_PATTERNS)}"
            ))
            test_client_ids = [row[0] for row in r.fetchall()]

            # 2. Собираем id тестовых дефектов (по названию + по тестовым объектам)
            defect_cond = like_clause('title', DEFECT_PATTERNS)
            if test_site_ids:
                site_in = ",".join(str(i) for i in test_site_ids)
                defect_cond += f" OR site_id IN ({site_in})"
            r = await session.execute(text(f"SELECT id FROM defects WHERE {defect_cond}"))
            test_defect_ids = [row[0] for row in r.fetchall()]

            # 3. Собираем id тестовых выездов
            if test_site_ids:
                site_in = ",".join(str(i) for i in test_site_ids)
                r = await session.execute(text(f"SELECT id FROM visits WHERE site_id IN ({site_in})"))
                test_visit_ids = [row[0] for row in r.fetchall()]
            else:
                test_visit_ids = []

            # 4. Уведомления по выездам и дефектам
            notif_conditions = []
            if test_visit_ids:
                vids = ",".join(str(i) for i in test_visit_ids)
                notif_conditions.append(f"related_visit_id IN ({vids})")
            if test_defect_ids:
                dids = ",".join(str(i) for i in test_defect_ids)
                notif_conditions.append(f"related_defect_id IN ({dids})")
            if notif_conditions:
                r = await session.execute(text(
                    f"DELETE FROM notifications WHERE {' OR '.join(notif_conditions)}"
                ))
                if r.rowcount: print(f"  ✓ уведомления: {r.rowcount}")

            # 5. Закупки тестовых дефектов + по названию
            purchase_cond = like_clause('item', PURCHASE_PATTERNS)
            if test_defect_ids:
                dids = ",".join(str(i) for i in test_defect_ids)
                purchase_cond += f" OR defect_id IN ({dids})"
            r = await session.execute(text(f"DELETE FROM purchases WHERE {purchase_cond}"))
            if r.rowcount: print(f"  ✓ закупки: {r.rowcount}")

            # 6. Дефекты
            if test_defect_ids:
                dids = ",".join(str(i) for i in test_defect_ids)
                r = await session.execute(text(f"DELETE FROM defects WHERE id IN ({dids})"))
                if r.rowcount: print(f"  ✓ дефекты: {r.rowcount}")

            # 7. Выезды
            if test_visit_ids:
                vids = ",".join(str(i) for i in test_visit_ids)
                r = await session.execute(text(f"DELETE FROM visits WHERE id IN ({vids})"))
                if r.rowcount: print(f"  ✓ выезды: {r.rowcount}")

            # 8. Договоры по номеру + по тестовым клиентам
            contract_cond = like_clause('contract_number', CONTRACT_PATTERNS)
            if test_client_ids:
                cids = ",".join(str(i) for i in test_client_ids)
                contract_cond += f" OR client_id IN ({cids})"
            r = await session.execute(text(
                f"SELECT id FROM contracts WHERE {contract_cond}"
            ))
            test_contract_ids = [row[0] for row in r.fetchall()]
            if test_contract_ids:
                ctids = ",".join(str(i) for i in test_contract_ids)
                await session.execute(text(f"DELETE FROM contract_sites WHERE contract_id IN ({ctids})"))
                r = await session.execute(text(f"DELETE FROM contracts WHERE id IN ({ctids})"))
                if r.rowcount: print(f"  ✓ договоры: {r.rowcount}")

            # 9. Объекты
            if test_site_ids:
                sids = ",".join(str(i) for i in test_site_ids)
                r = await session.execute(text(f"DELETE FROM sites WHERE id IN ({sids})"))
                if r.rowcount: print(f"  ✓ объекты: {r.rowcount}")

            # 10. Клиенты
            if test_client_ids:
                cids = ",".join(str(i) for i in test_client_ids)
                await session.execute(text(f"DELETE FROM client_contacts WHERE client_id IN ({cids})"))
                await session.execute(text(f"DELETE FROM client_legal WHERE client_id IN ({cids})"))
                r = await session.execute(text(f"DELETE FROM clients WHERE id IN ({cids})"))
                if r.rowcount: print(f"  ✓ клиенты: {r.rowcount}")

            # 11. Задачи
            r = await session.execute(text(
                f"DELETE FROM tasks WHERE {like_clause('title', TASK_PATTERNS)}"
            ))
            if r.rowcount: print(f"  ✓ задачи: {r.rowcount}")

            # 12. Напоминания
            r = await session.execute(text(
                f"DELETE FROM reminders WHERE {like_clause('text', REMINDER_PATTERNS)}"
            ))
            if r.rowcount: print(f"  ✓ напоминания: {r.rowcount}")

            # 13. Заметки календаря
            r = await session.execute(text(
                f"DELETE FROM calendar_notes WHERE {like_clause('text', NOTE_PATTERNS)}"
            ))
            if r.rowcount: print(f"  ✓ заметки календаря: {r.rowcount}")

        print()
        print("Готово. Реальные данные не затронуты.")


if __name__ == "__main__":
    asyncio.run(clear())
