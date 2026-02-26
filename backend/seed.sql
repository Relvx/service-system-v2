-- seed.sql — populate lookup tables, permission groups, and test users
-- Usage: psql service_system_v2 < seed.sql
-- Run AFTER: alembic upgrade head

-- ─── Config tables ──────────────────────────────────────────────────────────

INSERT INTO visit_statuses (sysname, display_name) VALUES
    ('planned',     'Запланирован'),
    ('in_progress', 'В работе'),
    ('closed',      'Завершён'),
    ('cancelled',   'Отменён')
ON CONFLICT (sysname) DO NOTHING;

INSERT INTO visit_types (sysname, display_name) VALUES
    ('maintenance', 'Техобслуживание'),
    ('repair',      'Ремонт'),
    ('inspection',  'Осмотр'),
    ('emergency',   'Аварийный')
ON CONFLICT (sysname) DO NOTHING;

INSERT INTO priorities (sysname, display_name, sort_order) VALUES
    ('low',    'Низкий',  1),
    ('medium', 'Средний', 2),
    ('high',   'Высокий', 3),
    ('urgent', 'Срочный', 4)
ON CONFLICT (sysname) DO NOTHING;

INSERT INTO defect_statuses (sysname, display_name) VALUES
    ('open',        'Открыт'),
    ('approved',    'Согласован'),
    ('in_progress', 'В работе'),
    ('fixed',       'Устранён')
ON CONFLICT (sysname) DO NOTHING;

INSERT INTO defect_action_types (sysname, display_name) VALUES
    ('repair',  'Ремонт'),
    ('replace', 'Замена'),
    ('monitor', 'Наблюдение'),
    ('other',   'Другое')
ON CONFLICT (sysname) DO NOTHING;

INSERT INTO attachment_kinds (sysname, display_name) VALUES
    ('act_photo',    'Фото акта'),
    ('defect_photo', 'Фото дефекта'),
    ('other',        'Другое')
ON CONFLICT (sysname) DO NOTHING;

INSERT INTO purchase_statuses (sysname, display_name) VALUES
    ('draft',     'Черновик'),
    ('approved',  'Согласовано'),
    ('ordered',   'Заказано'),
    ('received',  'Получено'),
    ('installed', 'Установлено'),
    ('closed',    'Закрыто')
ON CONFLICT (sysname) DO NOTHING;

INSERT INTO service_frequencies (sysname, display_name) VALUES
    ('monthly',    'Ежемесячно'),
    ('quarterly',  'Ежеквартально'),
    ('seasonal',   'Сезонно'),
    ('custom',     'Индивидуально')
ON CONFLICT (sysname) DO NOTHING;

INSERT INTO notification_types (sysname, display_name) VALUES
    ('visit_assigned', 'Назначен выезд'),
    ('visit_updated',  'Изменён выезд')
ON CONFLICT (sysname) DO NOTHING;

-- ─── Log actions ─────────────────────────────────────────────────────────────

INSERT INTO log_actions (sysname, display_name) VALUES
    ('create',   'Создание'),
    ('update',   'Изменение'),
    ('delete',   'Удаление'),
    ('complete', 'Завершение'),
    ('approve',  'Согласование'),
    ('assign',   'Назначение')
ON CONFLICT (sysname) DO NOTHING;

-- ─── Permission groups ────────────────────────────────────────────────────────

INSERT INTO permission_groups (sysname, display_name, default_redirect) VALUES
    ('admin_group',  'Администраторы', '/dashboard'),
    ('office_group', 'Офис',           '/dashboard'),
    ('master_group', 'Мастера',        '/my-visits')
ON CONFLICT (sysname) DO NOTHING;

-- ─── Permissions ──────────────────────────────────────────────────────────────

INSERT INTO permissions (sysname, display_name, resource, action) VALUES
    ('visits:view',      'Просмотр выездов',           'visits',     'view'),
    ('visits:create',    'Создание выездов',            'visits',     'create'),
    ('visits:update',    'Изменение выездов',           'visits',     'update'),
    ('visits:delete',    'Удаление выездов',            'visits',     'delete'),
    ('visits:complete',  'Завершение выездов',          'visits',     'complete'),
    ('clients:view',     'Просмотр клиентов',           'clients',    'view'),
    ('clients:create',   'Создание клиентов',           'clients',    'create'),
    ('clients:update',   'Изменение клиентов',          'clients',    'update'),
    ('clients:delete',   'Удаление клиентов',           'clients',    'delete'),
    ('sites:view',       'Просмотр объектов',           'sites',      'view'),
    ('sites:create',     'Создание объектов',           'sites',      'create'),
    ('sites:update',     'Изменение объектов',          'sites',      'update'),
    ('sites:delete',     'Удаление объектов',           'sites',      'delete'),
    ('defects:view',     'Просмотр дефектов',           'defects',    'view'),
    ('defects:create',   'Создание дефектов',           'defects',    'create'),
    ('defects:update',   'Изменение дефектов',          'defects',    'update'),
    ('defects:approve',  'Согласование дефектов',       'defects',    'approve'),
    ('purchases:view',   'Просмотр закупок',            'purchases',  'view'),
    ('purchases:create', 'Создание закупок',            'purchases',  'create'),
    ('purchases:update', 'Изменение закупок',           'purchases',  'update'),
    ('users:view',       'Просмотр пользователей',      'users',      'view'),
    ('users:create',     'Создание пользователей',      'users',      'create'),
    ('users:update',     'Изменение пользователей',     'users',      'update'),
    ('dashboard:view',   'Просмотр дашборда',           'dashboard',  'view'),
    ('config:view',      'Просмотр справочников',       'config',     'view'),
    ('config:manage',    'Управление справочниками',    'config',     'manage'),
    ('admin:access',     'Доступ к панели админа',      'admin',      'access'),
    ('my_visits:view',   'Мои выезды',                  'my_visits',  'view')
ON CONFLICT (sysname) DO NOTHING;

-- ─── Assign all permissions to admin_group ────────────────────────────────────

INSERT INTO permission_group_permissions (group_id, permission_id)
SELECT
    (SELECT id FROM permission_groups WHERE sysname = 'admin_group'),
    id
FROM permissions
ON CONFLICT DO NOTHING;

-- ─── Assign office_group permissions ─────────────────────────────────────────

INSERT INTO permission_group_permissions (group_id, permission_id)
SELECT
    (SELECT id FROM permission_groups WHERE sysname = 'office_group'),
    id
FROM permissions
WHERE sysname IN (
    'visits:view','visits:create','visits:update','visits:delete','visits:complete',
    'clients:view','clients:create','clients:update','clients:delete',
    'sites:view','sites:create','sites:update','sites:delete',
    'defects:view','defects:create','defects:update','defects:approve',
    'purchases:view','purchases:create','purchases:update',
    'users:view','dashboard:view','config:view'
)
ON CONFLICT DO NOTHING;

-- ─── Assign master_group permissions ─────────────────────────────────────────

INSERT INTO permission_group_permissions (group_id, permission_id)
SELECT
    (SELECT id FROM permission_groups WHERE sysname = 'master_group'),
    id
FROM permissions
WHERE sysname IN (
    'visits:view','visits:complete',
    'defects:view','defects:create',
    'my_visits:view','config:view'
)
ON CONFLICT DO NOTHING;

-- ─── Users (password: admin123) ──────────────────────────────────────────────

INSERT INTO users (email, password_hash, full_name, phone) VALUES
    ('admin@system.local',
     '$2b$12$IYRa/XTcXPnpTgZ3gjoFxu3NhRA5ig89y0fdmHHq9zIpDP.3UdCHW',
     'Администратор', NULL),
    ('master1@system.local',
     '$2b$12$IYRa/XTcXPnpTgZ3gjoFxu3NhRA5ig89y0fdmHHq9zIpDP.3UdCHW',
     'Мастер Иванов', '8-999-111-22-33'),
    ('master2@system.local',
     '$2b$12$IYRa/XTcXPnpTgZ3gjoFxu3NhRA5ig89y0fdmHHq9zIpDP.3UdCHW',
     'Мастер Петров', '8-999-444-55-66'),
    ('office1@system.local',
     '$2b$12$IYRa/XTcXPnpTgZ3gjoFxu3NhRA5ig89y0fdmHHq9zIpDP.3UdCHW',
     'Офис Сидоров', '8-495-777-88-99')
ON CONFLICT (email) DO NOTHING;

-- ─── Assign users to groups ───────────────────────────────────────────────────

INSERT INTO user_permission_groups (user_id, group_id)
SELECT u.id, (SELECT id FROM permission_groups WHERE sysname = 'admin_group')
FROM users u WHERE u.email = 'admin@system.local'
ON CONFLICT DO NOTHING;

INSERT INTO user_permission_groups (user_id, group_id)
SELECT u.id, (SELECT id FROM permission_groups WHERE sysname = 'master_group')
FROM users u WHERE u.email IN ('master1@system.local', 'master2@system.local')
ON CONFLICT DO NOTHING;

INSERT INTO user_permission_groups (user_id, group_id)
SELECT u.id, (SELECT id FROM permission_groups WHERE sysname = 'office_group')
FROM users u WHERE u.email = 'office1@system.local'
ON CONFLICT DO NOTHING;

-- ─── Test clients & sites ─────────────────────────────────────────────────────

INSERT INTO clients (name, contacts, contact_person, notes) VALUES
    ('Тестовый клиент 1', '8-495-123-45-67', 'Иван Иванов', 'Тестовый клиент для разработки'),
    ('Тестовый клиент 2', '8-495-765-43-21', 'Петр Петров', 'Ещё один тестовый клиент')
ON CONFLICT DO NOTHING;

INSERT INTO sites (client_id, title, address, latitude, longitude, access_notes)
SELECT
    (SELECT id FROM clients WHERE name = 'Тестовый клиент 1'),
    'Котельная №1', 'Москва, ул. Ленина, д. 10', 55.751244, 37.618423, 'Ключ у охранника'
WHERE NOT EXISTS (SELECT 1 FROM sites WHERE title = 'Котельная №1');

INSERT INTO sites (client_id, title, address, latitude, longitude, access_notes)
SELECT
    (SELECT id FROM clients WHERE name = 'Тестовый клиент 2'),
    'Котельная №2', 'Московская область, г. Химки, ул. Победы, д. 5',
    55.889339, 37.429857, 'Вход с торца здания'
WHERE NOT EXISTS (SELECT 1 FROM sites WHERE title = 'Котельная №2');

-- ─── Test visits ─────────────────────────────────────────────────────────────

INSERT INTO visits (site_id, assigned_user_id, planned_date, visit_type, priority, status)
SELECT
    (SELECT id FROM sites WHERE title = 'Котельная №1'),
    (SELECT id FROM users WHERE email = 'master1@system.local'),
    CURRENT_DATE, 'maintenance', 'medium', 'planned'
WHERE NOT EXISTS (
    SELECT 1 FROM visits v
    JOIN sites s ON s.id = v.site_id
    WHERE s.title = 'Котельная №1' AND v.planned_date = CURRENT_DATE
);

INSERT INTO visits (site_id, assigned_user_id, planned_date, visit_type, priority, status)
SELECT
    (SELECT id FROM sites WHERE title = 'Котельная №2'),
    (SELECT id FROM users WHERE email = 'master2@system.local'),
    CURRENT_DATE + INTERVAL '1 day', 'repair', 'high', 'planned'
WHERE NOT EXISTS (
    SELECT 1 FROM visits v
    JOIN sites s ON s.id = v.site_id
    WHERE s.title = 'Котельная №2' AND v.planned_date = CURRENT_DATE + INTERVAL '1 day'
);
