"""
Заполняет contract_id на выездах у которых он пустой,
используя цепочку: visit.site_id → contract_sites → contract_id.

Если объект привязан к нескольким договорам — берём самый последний (max id).

Запуск:
  cd backend
  venv/bin/python scripts/backfill_visit_contract.py
"""
import asyncio, sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import AsyncSessionLocal
from app.models import Visit
from app.models.contract import ContractSite
from sqlalchemy import select, func

async def main():
    async with AsyncSessionLocal() as db:
        # Все выезды без contract_id у которых есть site_id
        result = await db.execute(
            select(Visit).where(
                Visit.contract_id.is_(None),
                Visit.site_id.isnot(None),
            )
        )
        visits = result.scalars().all()
        print(f"Выездов без contract_id: {len(visits)}")

        updated = 0
        skipped = 0

        for visit in visits:
            # Берём договор с максимальным id для данного объекта
            cs_result = await db.execute(
                select(func.max(ContractSite.contract_id))
                .where(ContractSite.site_id == visit.site_id)
            )
            contract_id = cs_result.scalar()

            if contract_id:
                visit.contract_id = contract_id
                updated += 1
            else:
                skipped += 1

        await db.commit()

        print(f"Обновлено:  {updated}")
        print(f"Пропущено (нет договора для объекта): {skipped}")

if __name__ == "__main__":
    asyncio.run(main())
