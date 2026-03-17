# Блок 11 — Импорт данных из XLS (полный план)

> Файл-источник: `График выездов последний.xls`
> 4 343 договора, 216 месяцев выездов (янв 2011 — дек 2028)

---

## Что нужно сделать — простыми словами

В Excel-файле хранится вся история работы компании: клиенты, их адреса, номера договоров, какое оборудование стоит на каждом объекте (газовые счётчики, клапаны), серийные номера приборов и по какому месяцу кто куда выезжал. Всё это нужно перенести в систему.

Сейчас в системе нет понятия "договор" и "оборудование" — это главное, что нужно добавить. После этого можно написать скрипт, который прочитает Excel и заполнит базу данных.

**Что получим в итоге:**
- В карточке объекта появится вкладка "Договоры" и "Оборудование"
- Можно будет найти объект по серийному номеру прибора
- На дашборде появится виджет "Приборы с истекающей поверкой"
- Вся история выездов из Excel загрузится как завершённые выезды
- Все плановые выезды из Excel (будущие месяцы) загрузятся как запланированные

---

## Шаг 1 — Добавить таблицу "Договоры" (contracts)

**Что это:** Каждая строка в Excel — это договор. Один клиент может иметь несколько договоров (на разные объекты или разные годы).

**Что добавить в БД:**
```sql
CREATE TABLE contracts (
    id SERIAL PRIMARY KEY,
    client_id INTEGER REFERENCES clients(id) ON DELETE SET NULL,
    site_id INTEGER REFERENCES sites(id) ON DELETE SET NULL,
    contract_number VARCHAR(255),      -- номер: "0817/2 от 17.08.2006"
    contract_date DATE,                -- дата договора
    subject TEXT,                      -- предмет: "ТО на год", "Поверка и ТО"
    amount NUMERIC(10, 2),             -- стоимость работ
    act_amount NUMERIC(10, 2),         -- сумма акта
    status VARCHAR(50) DEFAULT 'active',
    notes TEXT,                        -- заметки по договору
    raw_visit_history TEXT,            -- исходная история выездов из col 7 (для справки)
    is_archived BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

**Что добавить к таблице visits:**
```sql
ALTER TABLE visits ADD COLUMN contract_id INTEGER REFERENCES contracts(id) ON DELETE SET NULL;
ALTER TABLE visits ADD COLUMN master_name_raw VARCHAR(100); -- фамилия мастера из текста Excel
```

---

## Шаг 2 — Добавить таблицу "Оборудование" (equipment)

**Что это:** На каждом объекте стоят газовые приборы (счётчики, сигнализаторы, клапаны). У каждого есть серийный номер и дата последней поверки. Поверку нужно делать раз в год — система должна об этом напоминать.

**Что добавить в БД:**
```sql
CREATE TABLE equipment (
    id SERIAL PRIMARY KEY,
    site_id INTEGER REFERENCES sites(id) ON DELETE CASCADE,
    contract_id INTEGER REFERENCES contracts(id) ON DELETE SET NULL,
    brand VARCHAR(100),                -- марка: СТГ, СЗ, СГГ, КЗГЭМ
    model VARCHAR(100),
    serial_number VARCHAR(100),        -- серийный номер (для поиска!)
    equipment_type VARCHAR(50),        -- газоанализатор, клапан, датчик
    installation_date DATE,
    last_verification_date DATE,       -- последняя поверка
    next_verification_date DATE,       -- следующая плановая поверка
    notes TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_equipment_serial ON equipment(serial_number);
CREATE INDEX idx_equipment_next_verification ON equipment(next_verification_date);
```

---

## Шаг 3 — Добавить таблицу "Расписание выездов" (service_schedule)

**Что это:** В Excel каждая ячейка с датой — это запись в расписании. Строка "ТО" в колонке "Март 2025" значит: на этом объекте в марте 2025 должно быть ТО. Это расписание нужно хранить отдельно, чтобы потом из него создавать реальные выезды.

**Что добавить в БД:**
```sql
CREATE TABLE service_schedule (
    id SERIAL PRIMARY KEY,
    contract_id INTEGER REFERENCES contracts(id) ON DELETE CASCADE,
    site_id INTEGER REFERENCES sites(id) ON DELETE CASCADE,
    scheduled_month DATE,              -- первый день месяца (напр. 2025-03-01)
    work_type VARCHAR(50),             -- нормализованный: maintenance/inspection/repair
    work_type_raw VARCHAR(100),        -- исходный текст из Excel: "поверка+ТО"
    visit_id INTEGER REFERENCES visits(id) ON DELETE SET NULL, -- NULL пока выезд не создан
    status VARCHAR(50) DEFAULT 'scheduled', -- scheduled / completed / cancelled
    is_historical BOOLEAN DEFAULT FALSE,    -- TRUE если дата уже прошла
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

## Шаг 4 — Написать скрипт импорта

**Что делает скрипт (по шагам):**

```
PASS 1 — Клиенты
  - Читать Excel, сгруппировать строки по имени клиента (col 1)
  - Для каждого уникального клиента → создать запись в clients
  - Парсить ИНН/КПП из col 2 → создать client_legal
  - Парсить телефоны из col 3 → создать client_contacts

PASS 2 — Объекты и договоры
  - Для каждой строки Excel:
    1. Найти или создать site (по адресу + client_id)
    2. Создать contract (номер из col 6, стоимость из col 5, предмет из col 11)
    3. Сохранить историю выездов из col 7 в contract.raw_visit_history

PASS 3 — Оборудование
  - Разобрать col 12 (марки) и col 13 (серийники)
  - Создать записи в equipment для каждого прибора

PASS 4 — Расписание (из 216 дата-колонок)
  - Для каждой непустой ячейки в дата-колонках:
    1. Создать запись в service_schedule
    2. Нормализовать тип работы (ТО → maintenance, поверка → inspection и т.д.)
    3. Пометить is_historical=TRUE если дата < сегодня

PASS 5 — Выезды из истории
  - Для каждой исторической записи расписания → создать visit (status="closed")
  - Для каждой будущей записи → создать visit (status="planned")
  - Попытаться сопоставить фамилию мастера из текста → assigned_user_id

PASS 6 — Отчёт
  - Вывести: сколько создано clients / sites / contracts / equipment / visits
  - Вывести: сколько записей не распознано (тип работы, адрес и т.д.)
```

**Скрипт:** `backend/scripts/import_xls.py`

---

## Шаг 5 — Добавить API endpoints

```
GET    /api/contracts/                  — список договоров
GET    /api/contracts/{id}             — карточка договора
POST   /api/contracts/                  — создать вручную
PATCH  /api/contracts/{id}             — обновить

GET    /api/equipment/                  — поиск по серийнику, марке, объекту
GET    /api/equipment/{id}             — карточка прибора
GET    /api/equipment/verification-due — приборы с истекающей поверкой (30 дней)

GET    /api/schedule/                   — план выездов по месяцам
POST   /api/schedule/{id}/create-visit — создать выезд из записи расписания
```

---

## Шаг 6 — Добавить страницы на фронтенде

| Страница | Что показывает |
|----------|---------------|
| `/contracts` | Список всех договоров с фильтрами |
| `/contracts/:id` | Карточка: реквизиты, оборудование, расписание, история выездов |
| `/equipment` | Реестр оборудования с поиском по серийнику |
| `/equipment/:id` | Карточка прибора: история поверок, текущий объект |

**Изменения в существующих страницах:**
- `SiteDetail.vue` — новая вкладка "Договоры" и "Оборудование"
- `VisitDetail.vue` — показывать связанный договор и прибор
- `Dashboard.vue` — виджет "Приборы с истекающей поверкой"

---

## Оценка объёма

| Часть | Время |
|-------|-------|
| Миграции (3 новые таблицы + изменения в visits) | 0.5 дня |
| Скрипт импорта XLS | 1.5 дня |
| API endpoints (бэкенд) | 1.5 дня |
| Фронтенд (4 новые страницы + изменения) | 3 дня |
| Тесты | 1 день |
| **Итого** | **~7.5 дней** |

---

## Нормализация типов работ из Excel

При импорте текст из ячеек нужно конвертировать в типы системы:

| Текст в Excel | Тип в системе |
|--------------|---------------|
| ТО, то, т/о | `maintenance` |
| поверка, Поверка | `inspection` |
| поверка+ТО, ТО+поверка | `inspection` |
| монтаж, Монтаж | `repair` |
| пролонг., пролонгация | `maintenance` |
| ремонт | `repair` |
| аварийный, авар. | `emergency` |

---

*Документ создан: 2026-03-17*
