"""
Скрипт импорта данных из Excel в систему.

Запуск (только вручную!):
    cd backend
    venv/bin/python scripts/import_xls.py --file "/path/to/График выездов последний.xls" --dry-run
    venv/bin/python scripts/import_xls.py --file "/path/to/График выездов последний.xls"

Флаги:
    --dry-run   Только считать и показать статистику, ничего не записывать
    --limit N   Обработать только первые N строк (для тестирования)
"""

import asyncio
import argparse
import re
import sys
from datetime import datetime, date
from collections import defaultdict

import xlrd

sys.path.insert(0, "/Users/relvx223/Projects/service-system-v2/backend")

from app.database import AsyncSessionLocal
from app.models.client import Client
from app.models.client_contact import ClientContact
from app.models.site import Site
from app.models.contract import Contract, ContractSite
from app.models.equipment import Equipment
from app.models.service_schedule import ServiceSchedule

# ── Константы ──────────────────────────────────────────────────────────────

ARCHIVE_BEFORE_YEAR = 2025   # всё до 2025 → архив
SCHEDULE_START_COL = 15      # первая колонка с датами
TODAY = date.today()

# ── Нормализация типов работ ────────────────────────────────────────────────

SKIP_PATTERNS = [
    r"^пролонг",
    r"^доки",
    r"^бух",
    r"^закрытие",
    r"^договор",
    r"^заключ",
    r"^роспись",
    r"^обход",
    r"^еженедельн",
    r"^работы$",
    r"^поставка",
    r"^doc",
]

TYPE_MAP = [
    (r"поверк",        "inspection"),
    (r"госповерк",     "inspection"),
    (r"^монтаж",       "repair"),
    (r"^ремонт",       "repair"),
    (r"замена",        "repair"),
    (r"калибровк",     "repair"),
    (r"авар",          "emergency"),
    (r"то",            "maintenance"),   # широкий — идёт последним
]


def normalize_work_type(raw: str):
    """Вернуть (work_type, is_prolongation) или (None, False) если пропустить."""
    if not raw:
        return None, False
    text = raw.strip().lower()
    # первая часть до +/,
    root = re.split(r"[+,]", text)[0].strip()

    # пролонгация — особый случай
    if re.match(r"^пролонг", root):
        return None, True

    # пропускаемые
    for pat in SKIP_PATTERNS:
        if re.search(pat, root):
            return None, False

    for pat, wtype in TYPE_MAP:
        if re.search(pat, root):
            return wtype, False

    return None, False


# ── Парсинг оборудования ────────────────────────────────────────────────────

def parse_equipment(brand_raw: str, serial_raw: str):
    """Вернуть (brand, quantity) из строки вида 'СТГ1-2Д10(В)-3шт.'"""
    if not brand_raw:
        return None, None
    brand_raw = brand_raw.strip()
    qty = None
    m = re.search(r"[- ](\d+)\s*шт", brand_raw, re.IGNORECASE)
    if m:
        qty = int(m.group(1))
        brand = brand_raw[:m.start()].strip(" -")
    else:
        brand = brand_raw
    return brand, qty


# ── Дата из числа Excel ─────────────────────────────────────────────────────

def xl_to_date(xl_val, datemode) -> date | None:
    if not xl_val:
        return None
    try:
        return xlrd.xldate_as_datetime(xl_val, datemode).date()
    except Exception:
        return None


# ── Основной импорт ─────────────────────────────────────────────────────────

async def run_import(xls_path: str, dry_run: bool, limit: int | None):
    wb = xlrd.open_workbook(xls_path)
    sh = wb.sheet_by_index(0)
    datemode = wb.datemode

    # Читаем заголовки дат
    date_cols = []
    for col in range(SCHEDULE_START_COL, sh.ncols):
        val = sh.cell_value(0, col)
        if val:
            d = xl_to_date(val, datemode)
            if d:
                date_cols.append((col, date(d.year, d.month, 1)))

    total_rows = sh.nrows - 1  # без строки заголовка
    if limit:
        total_rows = min(total_rows, limit)

    print(f"Строк для обработки: {total_rows}")
    print(f"Колонок с датами: {len(date_cols)} ({date_cols[0][1]} → {date_cols[-1][1]})")
    print(f"Режим: {'DRY RUN' if dry_run else 'ЗАПИСЬ В БД'}")
    print()

    # Счётчики
    stats = defaultdict(int)
    errors = []

    async with AsyncSessionLocal() as db:
        # ── Pass 1: клиенты ────────────────────────────────────────────────
        print("Pass 1 — Клиенты...")
        client_map = {}  # name → client_id

        for row in range(1, total_rows + 1):
            name = str(sh.cell_value(row, 1)).strip()
            if not name or name in client_map:
                continue

            if not dry_run:
                from sqlalchemy import select
                res = await db.execute(select(Client).where(Client.name == name))
                existing = res.scalar_one_or_none()
                if existing:
                    client_map[name] = existing.id
                    stats["clients_existing"] += 1
                else:
                    phone = str(sh.cell_value(row, 3)).strip() or None
                    contact_person = str(sh.cell_value(row, 4)).strip() or None
                    client = Client(
                        name=name,
                        contacts=phone,
                        contact_person=contact_person,
                        is_active=True,
                        is_archived=False,
                        created_at=datetime.now(),
                        updated_at=datetime.now(),
                    )
                    db.add(client)
                    await db.flush()
                    client_map[name] = client.id
                    stats["clients_created"] += 1
            else:
                client_map[name] = -1
                stats["clients_created"] += 1

        if not dry_run:
            await db.commit()
        print(f"  Новых клиентов: {stats['clients_created']}, уже существовало: {stats['clients_existing']}")

        # ── Pass 2: объекты и договоры ─────────────────────────────────────
        print("Pass 2 — Объекты и договоры...")
        site_map = {}      # (client_id, address) → site_id
        contract_ids = []  # список всех созданных contract_id

        for row in range(1, total_rows + 1):
            client_name = str(sh.cell_value(row, 1)).strip()
            if not client_name:
                continue

            client_id = client_map.get(client_name)
            address = str(sh.cell_value(row, 10)).strip() or "Адрес не указан"
            contract_number = str(sh.cell_value(row, 6)).strip() or None
            subject_raw = str(sh.cell_value(row, 11)).strip() or None
            act_amount_raw = sh.cell_value(row, 8)
            act_amount = float(act_amount_raw) if act_amount_raw else None
            history_text = str(sh.cell_value(row, 7)).strip() or None
            note = str(sh.cell_value(row, 0)).strip() or None

            # Признак пролонгации
            is_prolongation = contract_number and re.search(r"пролонг", str(sh.cell_value(row, 7)), re.IGNORECASE)
            subject = subject_raw
            if is_prolongation and subject:
                subject = subject + " (пролонг.)"

            if not dry_run:
                from sqlalchemy import select

                # Объект
                site_key = (client_id, address)
                if site_key not in site_map:
                    res = await db.execute(
                        select(Site).where(Site.client_id == client_id, Site.address == address)
                    )
                    existing_site = res.scalar_one_or_none()
                    if existing_site:
                        site_map[site_key] = existing_site.id
                        stats["sites_existing"] += 1
                    else:
                        site = Site(
                            client_id=client_id,
                            title=address[:100],
                            address=address,
                            is_active=True,
                            is_archived=False,
                            created_at=datetime.now(),
                            updated_at=datetime.now(),
                        )
                        db.add(site)
                        await db.flush()
                        site_map[site_key] = site.id
                        stats["sites_created"] += 1

                site_id = site_map[site_key]

                # Договор
                contract = Contract(
                    client_id=client_id,
                    contract_number=contract_number,
                    subject=subject,
                    act_amount=act_amount,
                    raw_visit_history=history_text,
                    notes=note,
                    status="active",
                    is_archived=False,
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                )
                db.add(contract)
                await db.flush()
                contract_ids.append((contract.id, client_id, site_id))
                stats["contracts_created"] += 1

                # Связь договор → объект
                db.add(ContractSite(contract_id=contract.id, site_id=site_id))

            else:
                stats["sites_created"] += 1
                stats["contracts_created"] += 1

        if not dry_run:
            await db.commit()
        print(f"  Объектов новых: {stats['sites_created']}, существующих: {stats['sites_existing']}")
        print(f"  Договоров создано: {stats['contracts_created']}")

        # ── Pass 3: оборудование ───────────────────────────────────────────
        print("Pass 3 — Оборудование...")

        contract_idx = 0
        for row in range(1, total_rows + 1):
            client_name = str(sh.cell_value(row, 1)).strip()
            if not client_name:
                continue

            brand_raw = str(sh.cell_value(row, 12)).strip()
            serial_raw = str(sh.cell_value(row, 13)).strip() or None
            if not brand_raw:
                contract_idx += 1
                continue

            brand, qty = parse_equipment(brand_raw, serial_raw)

            if not dry_run and contract_idx < len(contract_ids):
                contract_id, client_id, site_id = contract_ids[contract_idx]
                db.add(Equipment(
                    site_id=site_id,
                    contract_id=contract_id,
                    brand=brand,
                    quantity=qty,
                    serial_numbers=serial_raw,
                    is_active=True,
                    created_at=datetime.now(),
                ))
                stats["equipment_created"] += 1

            contract_idx += 1

        if not dry_run:
            await db.commit()
        print(f"  Оборудования создано: {stats['equipment_created']}")

        # ── Pass 4: расписание ─────────────────────────────────────────────
        print("Pass 4 — Расписание...")

        contract_idx = 0
        for row in range(1, total_rows + 1):
            client_name = str(sh.cell_value(row, 1)).strip()
            if not client_name:
                continue

            if not dry_run and contract_idx < len(contract_ids):
                contract_id, client_id, site_id = contract_ids[contract_idx]
            else:
                contract_id, client_id, site_id = None, None, None

            for col, month_date in date_cols:
                raw = str(sh.cell_value(row, col)).strip()
                if not raw or raw == "0.0":
                    continue

                work_type, is_prolongation = normalize_work_type(raw)
                if work_type is None and not is_prolongation:
                    stats["schedule_skipped"] += 1
                    continue

                if is_prolongation:
                    stats["schedule_prolongation"] += 1
                    continue

                is_historical = month_date < TODAY.replace(day=1)
                is_archived = month_date.year < ARCHIVE_BEFORE_YEAR

                if not dry_run and contract_id:
                    db.add(ServiceSchedule(
                        contract_id=contract_id,
                        site_id=site_id,
                        scheduled_month=month_date,
                        work_type=work_type,
                        work_type_raw=raw[:200],
                        status="scheduled",
                        is_historical=is_historical,
                        is_archived=is_archived,
                        created_at=datetime.now(),
                    ))
                stats["schedule_created"] += 1

            contract_idx += 1

            # Коммитим батчами чтобы не переполнять память
            if not dry_run and row % 200 == 0:
                await db.commit()
                print(f"  ... обработано строк: {row}/{total_rows}")

        if not dry_run:
            await db.commit()
        print(f"  Записей расписания: {stats['schedule_created']}")
        print(f"  Пролонгаций (пропущено): {stats['schedule_prolongation']}")
        print(f"  Прочих (пропущено): {stats['schedule_skipped']}")

        # ── Pass 5: архивация ──────────────────────────────────────────────
        if not dry_run:
            print("Pass 5 — Архивация старых данных...")
            from sqlalchemy import select, update

            # Клиенты без расписания в 2025-2026 → архив
            archive_date = date(ARCHIVE_BEFORE_YEAR, 1, 1)

            # Находим site_id у которых есть расписание в 2025+
            active_sites_res = await db.execute(
                select(ServiceSchedule.site_id).where(
                    ServiceSchedule.scheduled_month >= archive_date,
                    ServiceSchedule.is_archived == False,
                ).distinct()
            )
            active_site_ids = set(r[0] for r in active_sites_res if r[0])

            # Клиенты чьи объекты все неактивны
            all_sites_res = await db.execute(select(Site.id, Site.client_id))
            client_has_active = set()
            for sid, cid in all_sites_res:
                if sid in active_site_ids:
                    client_has_active.add(cid)

            # Архивируем клиентов
            all_clients_res = await db.execute(select(Client.id))
            all_client_ids = [r[0] for r in all_clients_res]
            archive_client_ids = [cid for cid in all_client_ids if cid not in client_has_active]

            if archive_client_ids:
                await db.execute(
                    update(Client).where(Client.id.in_(archive_client_ids))
                    .values(is_archived=True)
                )
                # Их объекты
                await db.execute(
                    update(Site).where(Site.client_id.in_(archive_client_ids))
                    .values(is_archived=True)
                )
                # Их договоры
                await db.execute(
                    update(Contract).where(Contract.client_id.in_(archive_client_ids))
                    .values(is_archived=True)
                )
                stats["clients_archived"] = len(archive_client_ids)

            await db.commit()
            print(f"  Клиентов заархивировано: {stats['clients_archived']}")

    # ── Итог ───────────────────────────────────────────────────────────────
    print()
    print("=" * 50)
    print("ИТОГ ИМПОРТА")
    print("=" * 50)
    for key, val in sorted(stats.items()):
        print(f"  {key}: {val}")
    if errors:
        print(f"\nОШИБКИ ({len(errors)}):")
        for e in errors[:20]:
            print(f"  {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", required=True, help="Путь к XLS файлу")
    parser.add_argument("--dry-run", action="store_true", help="Только статистика, без записи")
    parser.add_argument("--limit", type=int, default=None, help="Обработать первые N строк")
    args = parser.parse_args()

    asyncio.run(run_import(args.file, args.dry_run, args.limit))
