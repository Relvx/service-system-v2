"""
Скрипт добавляет 19 договоров которые есть в XLS-расписании но отсутствуют в БД.
Логика:
  - Если клиент уже есть (поиск по имени без учёта регистра) — используем его
  - Если клиента нет — создаём нового
  - Если договор уже есть (поиск по contract_number) — пропускаем
  - Если договора нет — создаём

Запуск:
  cd backend
  venv/bin/python scripts/add_missing_contracts.py
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import AsyncSessionLocal
from app.models import Contract, Client
from sqlalchemy import select, func

# Данные из XLS: (имя клиента, номер договора)
MISSING_CONTRACTS = [
    (
        'МКУ Управление по обеспечению деятельности органов местного самоуправления'
        ' (Администрация Дмитровского городского округа Московской области)',
        'Контракт № 44-26 от 27.03.2026',
    ),
    ('ГКОУ МО ЦЕНТР АРИАДНА', 'Контракт № 012773-26 от 13.03.2026'),
    ('ФБУ "Авиалесоохрана"', 'Договор поставки № 0319/1 от 19.03.2026'),
    ('АО "Мособлгаз" ("Запад")', 'Договор № 03/18249-25 от 26.12.2025'),
    ('МБУК ГОЩ ЦКД "ГРЕБНЕВО"', 'Контракт № 3628817 от 24.03.2026'),
    (
        'ГБУЗ МО "МОКПТД" (Клинический противотуберкулезный диспансер)',
        'Контракт № 260089 от 07.04.2026',
    ),
    ('Ступинский филиал ГАУ МО "Мособллес"', 'Договор № 12/ЭМ-2026 от 01.04.2026'),
    ('МОНОЛИТ ООО', 'Договор № 0401/2 от 01.04.2026'),
    ('ООО "Мэйджор Трак Центр"', 'Договор № 0316/1 от 16.03.2026'),
    ('ООО "Мэйджор Трак Центр"', 'Договор № 0407/1 от 07.04.2026'),
    ('ФГБНУ ВНИИ "Радуга"', 'Договор № 200910378126100016/2026 от 01.04.2026'),
    (
        'ГБУ города Москвы "Реабилитационный центр для инвалидов по зрению"',
        'Контракт № 0373200124026000006-1 ОТ 13.04.2026',
    ),
    (
        'МБУК " Одинцовский городской дом культуры "Солнечный" (МБУК ОГДК "Солнечный")',
        'Контракт № 30/26 от 12.03.2026',
    ),
    ('ГАУЗ Стоматологическая поликлиника № 11 ДЗМ', 'Договор № 32615831428 от 13.04.2026'),
    (
        'ФКУ СИЗО-1 УФСИН России по Московской области',
        'Контракт № 0348100020126000002 от 13.03.2026',
    ),
    (
        'ФКУ СИЗО-1 УФСИН России по Московской области',
        'Контракт № 0348100020126000006 от 07.04.2026',
    ),
    ('ООО СЗ Группа компаний СУ 22', 'Договор № 0227/1 от 27.02.2026 г.'),
    ('ГБУ МОСКОВСКОЙ ОБЛАСТИ "ЦГАМО"', 'Контракт № 08-26 от 10.04.2026 г.'),
    (
        'АО МАЗ "МОСКВИЧ" (РЕНО РОССИЯ)',
        '1209/1/4600027029 от 09.12.2020; ДС1 от 03.06.2022;'
        ' Заявка № 4 от 09.02.2024; Заявка № 5 от 07.08.2024;'
        ' ДС 3 от 15.01.2026; ДС 4 от 30.01.2026',
    ),
]


async def main():
    async with AsyncSessionLocal() as db:
        # Загружаем все существующие клиенты (имя → id, без учёта регистра)
        result = await db.execute(select(Client.id, Client.name))
        client_map: dict[str, int] = {
            row.name.strip().lower(): row.id for row in result.all()
        }

        # Загружаем все существующие договора (номер → id)
        result2 = await db.execute(select(Contract.id, Contract.contract_number))
        contract_set: set[str] = {
            row.contract_number.strip()
            for row in result2.all()
            if row.contract_number
        }

        clients_created = 0
        contracts_created = 0
        skipped = 0

        for client_name, contract_number in MISSING_CONTRACTS:
            # --- Договор уже есть? ---
            if contract_number.strip() in contract_set:
                print(f'  [ПРОПУСК]  договор уже есть: {contract_number[:60]}')
                skipped += 1
                continue

            # --- Клиент: найти или создать ---
            key = client_name.strip().lower()
            if key in client_map:
                client_id = client_map[key]
                client_status = 'существующий'
            else:
                new_client = Client(name=client_name.strip())
                db.add(new_client)
                await db.flush()  # получаем id
                client_id = new_client.id
                client_map[key] = client_id
                clients_created += 1
                client_status = 'СОЗДАН'

            # --- Создать договор ---
            new_contract = Contract(
                client_id=client_id,
                contract_number=contract_number.strip(),
                status='active',
            )
            db.add(new_contract)
            contract_set.add(contract_number.strip())
            contracts_created += 1

            print(
                f'  [ДОБАВЛЕН] договор: {contract_number[:55]}'
                f'  |  клиент ({client_status}): {client_name[:40]}'
            )

        await db.commit()

        print()
        print('=' * 60)
        print(f'Клиентов создано:   {clients_created}')
        print(f'Договоров создано:  {contracts_created}')
        print(f'Пропущено (дубли):  {skipped}')
        print('=' * 60)


if __name__ == '__main__':
    asyncio.run(main())
