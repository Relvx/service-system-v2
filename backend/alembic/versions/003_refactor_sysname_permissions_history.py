"""Refactor: code→sysname, drop color, add history/log/permission tables

Revision ID: 003
Revises: 6efd48e9d59e
Create Date: 2026-02-26
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision: str = "003"
down_revision: Union[str, None] = "6efd48e9d59e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()

    # ─── 1. Rename code → sysname in all config tables ─────────────────────

    for table in [
        "roles", "visit_statuses", "visit_types", "priorities",
        "defect_statuses", "defect_action_types", "attachment_kinds",
        "purchase_statuses", "service_frequencies", "notification_types",
    ]:
        op.alter_column(table, "code", new_column_name="sysname")

    # ─── 2. Drop color columns ──────────────────────────────────────────────

    op.drop_column("visit_statuses", "color")
    op.drop_column("priorities", "color")
    op.drop_column("defect_statuses", "color")
    op.drop_column("purchase_statuses", "color")

    # ─── 3. History tables ──────────────────────────────────────────────────

    for entity in ["clients", "sites", "users", "visits", "purchases"]:
        op.create_table(
            f"{entity}_history",
            sa.Column("id", UUID(as_uuid=True), primary_key=True,
                      server_default=sa.text("gen_random_uuid()")),
            sa.Column("record_id", UUID(as_uuid=True), nullable=False),
            sa.Column("changed_by_user_id", UUID(as_uuid=True),
                      sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
            sa.Column("changed_at", sa.DateTime(), nullable=False,
                      server_default=sa.text("now()")),
            sa.Column("snapshot", JSONB(), nullable=False),
        )
        op.create_index(
            f"idx_{entity}_history_record",
            f"{entity}_history",
            ["record_id"],
        )

    # ─── 4. Log tables ───────────────────────────────────────────────────────

    op.create_table(
        "log_actions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("sysname", sa.String(50), unique=True, nullable=False),
        sa.Column("display_name", sa.String(100), nullable=False),
    )

    op.create_table(
        "logs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("action_sysname", sa.String(50),
                  sa.ForeignKey("log_actions.sysname", ondelete="SET NULL"), nullable=True),
        sa.Column("entity_type", sa.String(50), nullable=False),
        sa.Column("entity_id", UUID(as_uuid=True), nullable=False),
        sa.Column("details", JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False,
                  server_default=sa.text("now()")),
    )
    op.create_index("idx_logs_entity", "logs", ["entity_type", "entity_id"])
    op.create_index("idx_logs_user", "logs", ["user_id"])

    # Seed log_actions
    conn.execute(sa.text("""
        INSERT INTO log_actions (sysname, display_name) VALUES
        ('create',   'Создание'),
        ('update',   'Изменение'),
        ('delete',   'Удаление'),
        ('complete', 'Завершение'),
        ('approve',  'Согласование'),
        ('assign',   'Назначение')
    """))

    # ─── 5. Permission tables ────────────────────────────────────────────────

    op.create_table(
        "permission_groups",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("sysname", sa.String(50), unique=True, nullable=False),
        sa.Column("display_name", sa.String(100), nullable=False),
        sa.Column("default_redirect", sa.String(100), nullable=False,
                  server_default="/dashboard"),
    )

    op.create_table(
        "permissions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("sysname", sa.String(100), unique=True, nullable=False),
        sa.Column("display_name", sa.String(100), nullable=False),
        sa.Column("resource", sa.String(50), nullable=False),
        sa.Column("action", sa.String(20), nullable=False),
    )

    op.create_table(
        "permission_group_permissions",
        sa.Column("group_id", sa.Integer(),
                  sa.ForeignKey("permission_groups.id", ondelete="CASCADE"),
                  nullable=False),
        sa.Column("permission_id", sa.Integer(),
                  sa.ForeignKey("permissions.id", ondelete="CASCADE"),
                  nullable=False),
        sa.PrimaryKeyConstraint("group_id", "permission_id"),
    )

    op.create_table(
        "user_permission_groups",
        sa.Column("user_id", UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("group_id", sa.Integer(),
                  sa.ForeignKey("permission_groups.id", ondelete="CASCADE"),
                  nullable=False),
        sa.PrimaryKeyConstraint("user_id", "group_id"),
    )

    # Seed permission groups
    conn.execute(sa.text("""
        INSERT INTO permission_groups (sysname, display_name, default_redirect) VALUES
        ('admin_group',  'Администраторы', '/dashboard'),
        ('office_group', 'Офис',           '/dashboard'),
        ('master_group', 'Мастера',        '/my-visits')
    """))

    # Seed permissions
    conn.execute(sa.text("""
        INSERT INTO permissions (sysname, display_name, resource, action) VALUES
        ('visits:view',     'Просмотр выездов',      'visits',     'view'),
        ('visits:create',   'Создание выездов',      'visits',     'create'),
        ('visits:update',   'Изменение выездов',     'visits',     'update'),
        ('visits:delete',   'Удаление выездов',      'visits',     'delete'),
        ('visits:complete', 'Завершение выездов',    'visits',     'complete'),
        ('clients:view',    'Просмотр клиентов',     'clients',    'view'),
        ('clients:create',  'Создание клиентов',     'clients',    'create'),
        ('clients:update',  'Изменение клиентов',    'clients',    'update'),
        ('clients:delete',  'Удаление клиентов',     'clients',    'delete'),
        ('sites:view',      'Просмотр объектов',     'sites',      'view'),
        ('sites:create',    'Создание объектов',     'sites',      'create'),
        ('sites:update',    'Изменение объектов',    'sites',      'update'),
        ('sites:delete',    'Удаление объектов',     'sites',      'delete'),
        ('defects:view',    'Просмотр дефектов',     'defects',    'view'),
        ('defects:create',  'Создание дефектов',     'defects',    'create'),
        ('defects:update',  'Изменение дефектов',    'defects',    'update'),
        ('defects:approve', 'Согласование дефектов', 'defects',    'approve'),
        ('purchases:view',  'Просмотр закупок',      'purchases',  'view'),
        ('purchases:create','Создание закупок',      'purchases',  'create'),
        ('purchases:update','Изменение закупок',     'purchases',  'update'),
        ('users:view',      'Просмотр пользователей','users',      'view'),
        ('users:create',    'Создание пользователей','users',      'create'),
        ('users:update',    'Изменение пользователей','users',     'update'),
        ('dashboard:view',  'Просмотр дашборда',     'dashboard',  'view'),
        ('config:view',     'Просмотр справочников', 'config',     'view'),
        ('config:manage',   'Управление справочниками','config',   'manage'),
        ('admin:access',    'Доступ к панели админа','admin',      'access'),
        ('my_visits:view',  'Мои выезды',            'my_visits',  'view')
    """))

    # Assign all permissions to admin_group
    conn.execute(sa.text("""
        INSERT INTO permission_group_permissions (group_id, permission_id)
        SELECT
            (SELECT id FROM permission_groups WHERE sysname = 'admin_group'),
            id
        FROM permissions
    """))

    # Assign office_group permissions
    conn.execute(sa.text("""
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
    """))

    # Assign master_group permissions
    conn.execute(sa.text("""
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
    """))

    # Migrate existing users to permission groups based on role
    conn.execute(sa.text("""
        INSERT INTO user_permission_groups (user_id, group_id)
        SELECT u.id, pg.id
        FROM users u
        JOIN permission_groups pg ON pg.sysname = (u.role || '_group')
        WHERE u.role IN ('admin', 'office', 'master')
    """))

    # ─── 6. Drop role column from users ─────────────────────────────────────

    op.drop_column("users", "role")


def downgrade() -> None:
    conn = op.get_bind()

    # Re-add role column
    op.add_column("users", sa.Column("role", sa.String(20), nullable=True))

    # Restore role from permission groups
    conn.execute(sa.text("""
        UPDATE users u
        SET role = REPLACE(pg.sysname, '_group', '')
        FROM user_permission_groups upg
        JOIN permission_groups pg ON pg.id = upg.group_id
        WHERE upg.user_id = u.id
          AND pg.sysname IN ('admin_group','office_group','master_group')
    """))

    # Make role NOT NULL with a fallback
    conn.execute(sa.text("UPDATE users SET role = 'office' WHERE role IS NULL"))
    op.alter_column("users", "role", nullable=False)

    # Drop permission tables
    op.drop_table("user_permission_groups")
    op.drop_table("permission_group_permissions")
    op.drop_table("permissions")
    op.drop_table("permission_groups")

    # Drop log tables
    op.drop_index("idx_logs_user", "logs")
    op.drop_index("idx_logs_entity", "logs")
    op.drop_table("logs")
    op.drop_table("log_actions")

    # Drop history tables
    for entity in ["clients", "sites", "users", "visits", "purchases"]:
        op.drop_index(f"idx_{entity}_history_record", f"{entity}_history")
        op.drop_table(f"{entity}_history")

    # Restore color columns
    op.add_column("visit_statuses",
                  sa.Column("color", sa.String(50), nullable=False, server_default="gray"))
    op.add_column("priorities",
                  sa.Column("color", sa.String(50), nullable=False, server_default="gray"))
    op.add_column("defect_statuses",
                  sa.Column("color", sa.String(50), nullable=False, server_default="gray"))
    op.add_column("purchase_statuses",
                  sa.Column("color", sa.String(50), nullable=False, server_default="gray"))

    # Rename sysname → code in all config tables
    for table in [
        "roles", "visit_statuses", "visit_types", "priorities",
        "defect_statuses", "defect_action_types", "attachment_kinds",
        "purchase_statuses", "service_frequencies", "notification_types",
    ]:
        op.alter_column(table, "sysname", new_column_name="code")
