"""
Импорт расписания обслуживания из XLS в таблицу contract_schedule.

Логика:
  - Читает лист "договора" из XLS-файла
  - Берёт столбцы-даты за 2026–2028 год
  - Для каждой непустой ячейки ищет договор по contract_number
  - Если запись уже есть (upsert по contract_id+year+month) — обновляет note
  - Если нет — создаёт новую

Запуск:
  cd backend
  venv/bin/python scripts/import_schedule_xls.py /path/to/1.xls

  Или с указанием диапазона лет:
  venv/bin/python scripts/import_schedule_xls.py /path/to/1.xls --year-from 2026 --year-to 2028
"""

import asyncio
import sys
import os
import argparse
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.database import AsyncSessionLocal
from app.models import Contract, ContractSchedule


async def main(xls_path: str, year_from: int, year_to: int) -> None:
    print(f"Читаю файл: {xls_path}")
    df = pd.read_excel(xls_path, sheet_name="договора", header=0)

    # Столбцы-даты в нужном диапазоне лет
    date_cols = [
        c for c in df.columns
        if isinstance(c, datetime) and year_from <= c.year <= year_to
    ]
    print(f"Месяцев {year_from}–{year_to}: {len(date_cols)}")

    # Строки с хоть одной непустой ячейкой расписания
    has_schedule = df[date_cols].notna().any(axis=1)
    scheduled_df = df[has_schedule].copy()
    print(f"Строк с расписанием: {len(scheduled_df)}")

    async with AsyncSessionLocal() as db:
        # Загружаем все договора: номер → id
        result = await db.execute(select(Contract.id, Contract.contract_number))
        contract_map: dict[str, int] = {
            row.contract_number.strip(): row.id
            for row in result.all()
            if row.contract_number
        }

        inserted = 0
        updated = 0
        skipped_no_contract = 0

        for _, row in scheduled_df.iterrows():
            cn = str(row.get("Договор", "")).strip()
            contract_id = contract_map.get(cn)

            if not contract_id:
                skipped_no_contract += 1
                continue

            for col in date_cols:
                cell = row[col]
                if pd.isna(cell) or str(cell).strip() == "":
                    continue

                note = str(cell).strip()
                year = col.year
                month = col.month

                # Upsert: если запись есть — обновляем note, если нет — вставляем
                stmt = (
                    pg_insert(ContractSchedule)
                    .values(
                        contract_id=contract_id,
                        year=year,
                        month=month,
                        note=note,
                        created_at=datetime.now(),
                        updated_at=datetime.now(),
                    )
                    .on_conflict_do_update(
                        constraint="uq_contract_schedule",
                        set_={"note": note, "updated_at": datetime.now()},
                    )
                )
                result2 = await db.execute(stmt)
                if result2.rowcount == 1:
                    inserted += 1
                else:
                    updated += 1

        await db.commit()

    print()
    print("=" * 60)
    print(f"Записей вставлено:          {inserted}")
    print(f"Записей обновлено:          {updated}")
    print(f"Пропущено (нет в БД):       {skipped_no_contract}")
    print("=" * 60)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Импорт расписания из XLS")
    parser.add_argument("xls_path", help="Путь к XLS-файлу")
    parser.add_argument("--year-from", type=int, default=2026)
    parser.add_argument("--year-to", type=int, default=2028)
    args = parser.parse_args()

    asyncio.run(main(args.xls_path, args.year_from, args.year_to))
