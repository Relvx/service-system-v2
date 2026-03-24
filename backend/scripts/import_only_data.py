"""
Скрипт импорта данных из only_data (2).xlsx

Логика:
- Каждая строка = один договор
- Клиент дедуплицируется по имени (Заказчик)
- Адрес через ";" → несколько объектов, все привязаны к договору
- Телефон + контактное лицо → текстом в client.contacts
- Выезды → текстом в contract.raw_visit_history
- Оборудование + № прибора → текстом в equipment (brand + serial_numbers)
- Архив: если Архив=True и год активной даты < 2022 → is_archived=True

Запуск:
    python scripts/import_only_data.py --dry-run
    python scripts/import_only_data.py
"""

import asyncio
import sys
import re
import argparse
from datetime import datetime, date
from pathlib import Path

import openpyxl

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import AsyncSessionLocal
from app.models.client import Client
from app.models.client_contact import ClientContact
from app.models.site import Site
from app.models.contract import Contract, ContractSite
from sqlalchemy import select

FILE_PATH = Path(__file__).parent.parent.parent / "only_data (2).xlsx"
# Если файл лежит в Downloads
FALLBACK_PATH = Path.home() / "Downloads" / "only_data (2).xlsx"

ARCHIVE_BEFORE_YEAR = 2022


# ─── Парсинг комментария ──────────────────────────────────────────────────────

def extract_field(comment: str, key: str) -> str | None:
    """Извлекает значение по ключу из комментария вида 'Ключ: значение;'"""
    if not comment:
        return None
    pattern = re.compile(rf'{re.escape(key)}\s*:\s*([^;]+)', re.IGNORECASE)
    m = pattern.search(comment)
    if m:
        return m.group(1).strip()
    return None


def parse_comment(comment: str) -> dict:
    """Парсит поле Комментарий, возвращает словарь полей."""
    if not comment:
        return {}

    result = {}

    phone = extract_field(comment, 'Телефон')
    if not phone:
        phone = extract_field(comment, 'Телефоны')
    result['phone'] = phone

    result['contact_person'] = extract_field(comment, 'Контактное лицо')
    result['subject'] = extract_field(comment, 'Предмет договора')
    result['equipment'] = extract_field(comment, 'Оборудование')
    result['serial_numbers'] = extract_field(comment, '№ прибора')
    result['visits_raw'] = extract_field(comment, 'Выезды')

    # Стоимость
    MAX_AMOUNT = 9_999_999.99  # NUMERIC(10,2) max safe value

    amount_str = extract_field(comment, 'Стоимость работ по договору')
    if amount_str:
        try:
            val = float(re.sub(r'[^\d.]', '', amount_str))
            result['amount'] = val if val <= MAX_AMOUNT else None
        except Exception:
            result['amount'] = None
    else:
        result['amount'] = None

    act_amount_str = extract_field(comment, 'Сумма акта')
    if act_amount_str:
        try:
            val = float(re.sub(r'[^\d.]', '', act_amount_str))
            result['act_amount'] = val if val <= MAX_AMOUNT else None
        except Exception:
            result['act_amount'] = None
    else:
        result['act_amount'] = None

    return result


def parse_contract_date(contract_str: str) -> date | None:
    """Пытается извлечь дату из строки договора."""
    if not contract_str:
        return None

    # Паттерны дат: 08.09.04 / 08.09.2004 / 22 августа 2005
    months_ru = {
        'января': 1, 'февраля': 2, 'марта': 3, 'апреля': 4,
        'мая': 5, 'июня': 6, 'июля': 7, 'августа': 8,
        'сентября': 9, 'октября': 10, 'ноября': 11, 'декабря': 12,
    }

    # dd.mm.yy или dd.mm.yyyy
    m = re.search(r'(\d{1,2})\.(\d{2})\.(\d{2,4})', contract_str)
    if m:
        day, month, year = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if year < 100:
            year += 2000 if year < 30 else 1900
        try:
            return date(year, month, day)
        except Exception:
            pass

    # dd месяц yyyy
    m = re.search(r'(\d{1,2})\s+([а-яё]+)\s+(\d{4})', contract_str, re.IGNORECASE)
    if m:
        day = int(m.group(1))
        month = months_ru.get(m.group(2).lower())
        year = int(m.group(3))
        if month:
            try:
                return date(year, month, day)
            except Exception:
                pass

    return None


def should_archive(row_archive: bool, active_date) -> bool:
    """Определяет нужно ли архивировать запись."""
    if row_archive:
        return True
    if active_date and hasattr(active_date, 'year'):
        return active_date.year < ARCHIVE_BEFORE_YEAR
    return False


def split_addresses(address_str: str) -> list[str]:
    """Разбивает адрес по ';' на несколько адресов."""
    if not address_str:
        return []
    parts = [a.strip() for a in str(address_str).split(';')]
    return [p for p in parts if p]


# ─── Основная логика ──────────────────────────────────────────────────────────

async def run_import(dry_run: bool = True):
    # Найти файл
    file_path = FILE_PATH if FILE_PATH.exists() else FALLBACK_PATH
    if not file_path.exists():
        print(f"❌ Файл не найден: {file_path}")
        sys.exit(1)

    print(f"📂 Файл: {file_path}")
    print(f"🔧 Режим: {'DRY-RUN (без записи в БД)' if dry_run else 'РЕАЛЬНЫЙ ИМПОРТ'}")
    print()

    wb = openpyxl.load_workbook(str(file_path))
    ws = wb['Sheet1']

    # Читаем строки
    raw_rows = []
    for r in range(2, ws.max_row + 1):
        raw_rows.append({
            'ext_id':       ws.cell(r, 1).value,
            'client_name':  ws.cell(r, 2).value,
            'address':      ws.cell(r, 3).value,
            'contract_str': ws.cell(r, 4).value,
            'note':         ws.cell(r, 5).value,
            'description':  ws.cell(r, 6).value,
            'comment':      ws.cell(r, 7).value,
            'active_date':  ws.cell(r, 8).value,
            'archive':      ws.cell(r, 9).value,
        })

    print(f"📊 Строк в файле: {len(raw_rows)}")

    # Статистика
    stats = {
        'clients_created': 0,
        'clients_reused': 0,
        'sites_created': 0,
        'contracts_created': 0,
        'skipped_no_client': 0,
        'archived': 0,
    }

    async with AsyncSessionLocal() as db:
        # Кэш клиентов: имя → объект Client
        client_cache: dict[str, Client] = {}

        for idx, row in enumerate(raw_rows):
            client_name = str(row['client_name']).strip() if row['client_name'] else None
            if not client_name:
                stats['skipped_no_client'] += 1
                continue

            parsed = parse_comment(str(row['comment']) if row['comment'] else '')
            is_archived = should_archive(row['archive'] or False, row['active_date'])

            if is_archived:
                stats['archived'] += 1

            # ── Клиент ──
            if client_name not in client_cache:
                # Собираем contacts текстом
                contacts_parts = []
                if parsed.get('phone'):
                    contacts_parts.append(f"Тел: {parsed['phone']}")
                if parsed.get('contact_person'):
                    contacts_parts.append(f"Контакт: {parsed['contact_person']}")
                contacts_text = '; '.join(contacts_parts) if contacts_parts else None

                client = Client(
                    name=client_name,
                    contacts=contacts_text,
                    is_archived=is_archived,
                )
                if not dry_run:
                    db.add(client)
                    await db.flush()
                else:
                    client.id = -(idx + 1)  # фиктивный id для dry-run

                client_cache[client_name] = client
                stats['clients_created'] += 1
            else:
                client = client_cache[client_name]
                # Если хотя бы один договор активен — клиент не архивный
                if not is_archived and client.is_archived:
                    client.is_archived = False
                stats['clients_reused'] += 1

            # ── Объекты (адреса) ──
            addresses = split_addresses(str(row['address']) if row['address'] else '')
            if not addresses:
                addresses = ['Адрес не указан']

            created_sites = []
            for addr in addresses:
                # title = описание или первые 80 символов адреса
                title = str(row['description']).strip() if row['description'] else addr[:80]

                site = Site(
                    client_id=client.id,
                    title=title,
                    address=addr,
                    is_archived=is_archived,
                )
                if not dry_run:
                    db.add(site)
                    await db.flush()
                else:
                    site.id = -(idx * 100 + len(created_sites) + 1)

                created_sites.append(site)
                stats['sites_created'] += 1

            # ── Договор ──
            contract_number = str(row['contract_str']).strip() if row['contract_str'] else None
            contract_date = parse_contract_date(contract_number) if contract_number else None

            # notes = оборудование текстом
            equip_notes_parts = []
            if parsed.get('equipment'):
                equip_notes_parts.append(f"Оборудование: {parsed['equipment']}")
            if parsed.get('serial_numbers'):
                equip_notes_parts.append(f"№ прибора: {parsed['serial_numbers']}")
            equip_notes = '\n'.join(equip_notes_parts) if equip_notes_parts else None

            # description = примечание (col E) + описание (col F)
            description_parts = []
            if row['description']:
                description_parts.append(str(row['description']).strip())
            if row['note']:
                description_parts.append(str(row['note']).strip())
            description_text = '\n'.join(description_parts) if description_parts else None

            contract = Contract(
                client_id=client.id,
                contract_number=contract_number,
                contract_date=contract_date,
                subject=parsed.get('subject'),
                amount=parsed.get('amount'),
                act_amount=parsed.get('act_amount'),
                notes=equip_notes,
                description=description_text,
                raw_visit_history=parsed.get('visits_raw'),
                is_archived=is_archived,
                status='archived' if is_archived else 'active',
            )
            if not dry_run:
                db.add(contract)
                await db.flush()
            else:
                contract.id = -(idx + 1)

            stats['contracts_created'] += 1

            # ── ContractSite (договор ↔ объекты) ──
            for site in created_sites:
                cs = ContractSite(
                    contract_id=contract.id,
                    site_id=site.id,
                )
                if not dry_run:
                    db.add(cs)

            # Equipment не создаём — оборудование уже текстом в contract.notes

            # Прогресс каждые 500 строк
            if (idx + 1) % 500 == 0:
                print(f"  ... обработано {idx + 1}/{len(raw_rows)}")

        if not dry_run:
            await db.commit()
            print("✅ Данные сохранены в БД")
        else:
            print("✅ DRY-RUN завершён (в БД ничего не записано)")

    # ── Итог ──
    print()
    print("─" * 50)
    print("📈 ИТОГ:")
    print(f"  Клиентов создано:     {stats['clients_created']}")
    print(f"  Клиентов повторно:    {stats['clients_reused']}")
    print(f"  Объектов создано:     {stats['sites_created']}")
    print(f"  Договоров создано:    {stats['contracts_created']}")
    print(f"  Архивных записей:     {stats['archived']}")
    print(f"  Пропущено (нет имени):{stats['skipped_no_client']}")
    print("─" * 50)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Импорт данных из only_data (2).xlsx')
    parser.add_argument('--dry-run', action='store_true', help='Тестовый прогон без записи в БД')
    args = parser.parse_args()

    asyncio.run(run_import(dry_run=args.dry_run))
