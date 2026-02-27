# Схема базы данных — service-system-v2

## Основные сущности

### users
Пользователи системы. Права управляются через группы (RBAC), колонка `role` удалена в миграции 003.

| Колонка       | Тип          | Описание                        |
|---------------|--------------|---------------------------------|
| id            | UUID PK      | Первичный ключ                  |
| email         | VARCHAR(255) | Уникальный e-mail, индекс       |
| password_hash | VARCHAR(255) | Bcrypt-хэш пароля               |
| full_name     | VARCHAR(255) | Полное имя                      |
| phone         | VARCHAR(50)  | Телефон (опционально)           |
| is_active     | BOOLEAN      | Флаг активности                 |
| created_at    | TIMESTAMP    | Дата создания                   |
| updated_at    | TIMESTAMP    | Дата последнего обновления      |

**Связи:**
- `users` ←→ `permission_groups` через `user_permission_groups` (M2M)
- `users.id` ← `visits.assigned_user_id`
- `users.id` ← `logs.user_id`
- `users.id` ← `*_history.v_user_id`

---

### clients
Клиенты (юр. или физ. лица), заказывающие обслуживание.

| Колонка        | Тип          | Описание                       |
|----------------|--------------|--------------------------------|
| id             | UUID PK      |                                |
| name           | TEXT         | Наименование                   |
| inn            | VARCHAR(50)  | ИНН (опционально)              |
| kpp            | VARCHAR(50)  | КПП (опционально)              |
| contacts       | TEXT         | Контактная информация          |
| contact_person | VARCHAR(255) | Контактное лицо                |
| notes          | TEXT         | Примечания                     |
| is_active      | BOOLEAN      | Активен                        |
| created_at     | TIMESTAMP    |                                |
| updated_at     | TIMESTAMP    |                                |

**Связи:**
- `clients.id` ← `sites.client_id`

---

### sites
Объекты обслуживания (здания, котельные и т.п.).

| Колонка           | Тип         | Описание                          |
|-------------------|-------------|-----------------------------------|
| id                | UUID PK     |                                   |
| client_id         | UUID FK     | → clients.id (SET NULL)           |
| title             | TEXT        | Название объекта                  |
| address           | TEXT        | Адрес                             |
| latitude          | FLOAT       | Широта (для карты)                |
| longitude         | FLOAT       | Долгота (для карты)               |
| access_notes      | TEXT        | Инструкции по доступу             |
| onsite_contact    | TEXT        | Контакт на объекте                |
| service_frequency | VARCHAR(30) | Периодичность (FK → service_frequencies.sysname) |
| is_active         | BOOLEAN     |                                   |
| created_at        | TIMESTAMP   |                                   |
| updated_at        | TIMESTAMP   |                                   |

**Связи:**
- `sites.client_id` → `clients.id`
- `sites.id` ← `visits.site_id`
- `sites.id` ← `defects.site_id`
- `sites.id` ← `purchases.site_id`

---

### visits
Выезды мастеров на объекты — основная рабочая единица.

| Колонка            | Тип         | Описание                                    |
|--------------------|-------------|---------------------------------------------|
| id                 | UUID PK     |                                             |
| site_id            | UUID FK     | → sites.id (CASCADE)                        |
| assigned_user_id   | UUID FK     | → users.id (SET NULL) — назначенный мастер  |
| planned_date       | DATE        | Дата выезда                                 |
| planned_time_from  | TIME        | Начало временного окна                      |
| planned_time_to    | TIME        | Конец временного окна                       |
| visit_type         | VARCHAR(30) | Тип (FK → visit_types.sysname)              |
| priority           | VARCHAR(20) | Приоритет (FK → priorities.sysname)         |
| status             | VARCHAR(20) | Статус (FK → visit_statuses.sysname)        |
| work_summary       | TEXT        | Итоги работ                                 |
| checklist          | JSONB       | Чек-лист выполненных работ                  |
| defects_present    | BOOLEAN     | Флаг наличия дефектов                       |
| defects_summary    | TEXT        | Краткое описание дефектов                   |
| recommendations    | TEXT        | Рекомендации мастера                        |
| completed_at       | TIMESTAMP   | Время завершения                            |
| office_notes       | TEXT        | Заметки офиса                               |
| created_at         | TIMESTAMP   |                                             |
| updated_at         | TIMESTAMP   |                                             |

**Связи:**
- `visits.site_id` → `sites.id`
- `visits.assigned_user_id` → `users.id`
- `visits.id` ← `defects.visit_id`
- `visits.id` ← `attachments.visit_id`

---

### defects
Дефекты, выявленные мастером на объекте.

| Колонка         | Тип         | Описание                                     |
|-----------------|-------------|----------------------------------------------|
| id              | UUID PK     |                                              |
| visit_id        | UUID FK     | → visits.id (CASCADE)                        |
| site_id         | UUID FK     | → sites.id (CASCADE)                         |
| title           | TEXT        | Наименование дефекта                         |
| description     | TEXT        | Подробное описание                           |
| priority        | VARCHAR(20) | Приоритет (FK → priorities.sysname)          |
| action_type     | VARCHAR(20) | Тип действия (FK → defect_action_types.sysname) |
| suggested_parts | TEXT        | Предполагаемые запчасти                      |
| status          | VARCHAR(20) | Статус (FK → defect_statuses.sysname)        |
| created_at      | TIMESTAMP   |                                              |
| updated_at      | TIMESTAMP   |                                              |

**Связи:**
- `defects.visit_id` → `visits.id`
- `defects.site_id` → `sites.id`
- `defects.id` ← `purchases.defect_id`

---

### purchases
Закупки запасных частей и материалов для устранения дефектов.

| Колонка    | Тип         | Описание                                     |
|------------|-------------|----------------------------------------------|
| id         | UUID PK     |                                              |
| defect_id  | UUID FK     | → defects.id (CASCADE)                       |
| site_id    | UUID FK     | → sites.id (SET NULL)                        |
| item       | TEXT        | Наименование позиции                         |
| qty        | NUMERIC     | Количество                                   |
| status     | VARCHAR(20) | Статус (FK → purchase_statuses.sysname)      |
| due_date   | DATE        | Плановая дата получения                      |
| notes      | TEXT        | Примечания                                   |
| created_at | TIMESTAMP   |                                              |
| updated_at | TIMESTAMP   |                                              |

---

### attachments
Файловые вложения к выездам (фото, акты, отчёты).

| Колонка    | Тип          | Описание                                  |
|------------|--------------|-------------------------------------------|
| id         | UUID PK      |                                           |
| visit_id   | UUID FK      | → visits.id (CASCADE)                     |
| kind       | VARCHAR(30)  | Вид файла (FK → attachment_kinds.sysname) |
| url        | TEXT         | Ссылка на файл                            |
| filename   | VARCHAR(255) | Имя файла                                 |
| created_at | TIMESTAMP    |                                           |

---

### notifications
Уведомления для пользователей.

| Колонка    | Тип          | Описание                                        |
|------------|--------------|-------------------------------------------------|
| id         | UUID PK      |                                                 |
| user_id    | UUID FK      | → users.id (CASCADE) — получатель               |
| type       | VARCHAR(50)  | Тип (FK → notification_types.sysname)           |
| title      | VARCHAR(255) | Заголовок                                       |
| body       | TEXT         | Текст уведомления                               |
| entity_type| VARCHAR(50)  | Тип связанной сущности (visit, defect, …)       |
| entity_id  | UUID         | ID связанной сущности                           |
| is_read    | BOOLEAN      | Прочитано                                       |
| created_at | TIMESTAMP    |                                                 |

---

## RBAC (контроль доступа на основе групп прав)

### permission_groups
Именованные группы пользователей с набором прав. Заменяют колонку `role`.

| Колонка          | Тип          | Описание                                |
|------------------|--------------|-----------------------------------------|
| id               | SERIAL PK    |                                         |
| sysname          | VARCHAR(50)  | Системное имя (уникальное)              |
| display_name     | VARCHAR(100) | Название для отображения                |
| default_redirect | VARCHAR(100) | URL редиректа после входа               |

Стандартные группы: `admin_group`, `office_group`, `master_group`.

### permissions
Отдельные права формата `resource:action` (напр. `visits:view`).

| Колонка      | Тип          | Описание                       |
|--------------|--------------|--------------------------------|
| id           | SERIAL PK    |                                |
| sysname      | VARCHAR(100) | Уникальное имя (resource:action)|
| display_name | VARCHAR(100) | Название для UI                |
| resource     | VARCHAR(50)  | Ресурс (visits, clients, …)    |
| action       | VARCHAR(20)  | Действие (view, create, …)     |

### permission_group_permissions
M2M: какие права есть у группы.

| Колонка       | Тип    | FK                          |
|---------------|--------|-----------------------------|
| group_id      | INT FK | → permission_groups.id      |
| permission_id | INT FK | → permissions.id            |

### user_permission_groups
M2M: в каких группах состоит пользователь.

| Колонка  | Тип     | FK                         |
|----------|---------|----------------------------|
| user_id  | UUID FK | → users.id                 |
| group_id | INT FK  | → permission_groups.id     |

---

## Аудит

### logs
Журнал всех значимых действий пользователей.

| Колонка        | Тип         | Описание                                |
|----------------|-------------|-----------------------------------------|
| id             | UUID PK     |                                         |
| user_id        | UUID FK     | → users.id (SET NULL)                   |
| action_sysname | VARCHAR(50) | Действие (FK → log_actions.sysname)     |
| entity_type    | VARCHAR(50) | Тип сущности (visit, client, …)         |
| entity_id      | UUID        | ID изменённой записи                    |
| details        | JSONB       | Дополнительный контекст (изменения)     |
| created_at     | TIMESTAMP   |                                         |

### log_actions
Справочник типов действий в логе.

| Колонка      | Тип          | Значения                                  |
|--------------|--------------|-------------------------------------------|
| id           | SERIAL PK    |                                           |
| sysname      | VARCHAR(50)  | create, update, delete, complete, approve, assign |
| display_name | VARCHAR(100) | Название для UI                           |

---

## Версионирование

Для сущностей `clients`, `sites`, `users`, `visits`, `purchases` существуют history-таблицы (`*_history`).
Каждая строка — снапшот записи **в момент изменения**, если хотя бы одно поле изменилось.

**Структура каждой history-таблицы:**
- `id` — UUID PK (собственный идентификатор записи версии)
- `v_<поле>` — все поля оригинальной таблицы с префиксом `v_` (значения **до** изменения)
- `v_date` — момент записи версии (TIMESTAMP)
- `v_user_id` — кто инициировал изменение (FK → users.id, SET NULL)
- `v_method` — тип операции: `create` / `update` / `delete`

Таблицы: `clients_history`, `sites_history`, `users_history`, `visits_history`, `purchases_history`.

Логика записи реализована в `backend/app/utils/audit.py` (функция `save_history`):
- При `create` — запись создаётся всегда
- При `update` — запись создаётся только если изменилось хотя бы одно поле
- При `delete` — запись создаётся всегда

---

## Справочные таблицы (config tables)

Все справочники имеют единообразную структуру `id / sysname / display_name`.

| Таблица              | Назначение                                 |
|----------------------|--------------------------------------------|
| visit_statuses       | Статусы выездов (planned, in_progress, …)  |
| visit_types          | Типы выездов (maintenance, repair, …)      |
| priorities           | Приоритеты (low, medium, high, critical)   |
| defect_statuses      | Статусы дефектов (open, in_progress, …)    |
| defect_action_types  | Типы действий по дефектам                  |
| attachment_kinds     | Виды вложений (photo, act, report, …)      |
| purchase_statuses    | Статусы закупок (draft, approved, …)       |
| service_frequencies  | Частота обслуживания (monthly, quarterly, …)|
| notification_types   | Типы уведомлений                           |

CRUD для справочников: `POST/PUT/DELETE /api/config/{resource}/{sysname}` (только `admin_group`).

---

## Схема связей (ERD в тексте)

```
clients ──< sites ──< visits ──< defects ──< purchases
                 \              \
                  \              └──< attachments
                   \
                    └── (site_id в defects, purchases)

users ──< visits (assigned_user_id)
users ──< notifications
users ──< logs
users ><─ permission_groups (через user_permission_groups)
permission_groups ><─ permissions (через permission_group_permissions)
```
