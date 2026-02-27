"""Extend log_actions: add entity-specific action sysnames

Revision ID: 006
Revises: 005
Create Date: 2026-02-27
"""
from alembic import op
from sqlalchemy.sql import table, column
from sqlalchemy import String

revision = "006"
down_revision = "005"
branch_labels = None
depends_on = None

log_actions = table(
    "log_actions",
    column("sysname", String),
    column("display_name", String),
)

NEW_ACTIONS = [
    # clients
    ("client_create",        "Создание клиента"),
    ("client_update",        "Изменение клиента"),
    ("client_delete",        "Удаление клиента"),
    ("client_change_status", "Изменение статуса клиента"),
    # sites
    ("site_create",          "Создание объекта"),
    ("site_update",          "Изменение объекта"),
    ("site_delete",          "Удаление объекта"),
    # visits
    ("visit_create",         "Создание выезда"),
    ("visit_update",         "Изменение выезда"),
    ("visit_delete",         "Удаление выезда"),
    ("visit_complete",       "Завершение выезда"),
    ("visit_assign",         "Назначение мастера на выезд"),
    ("visit_change_status",  "Изменение статуса выезда"),
    # defects
    ("defect_create",        "Создание дефекта"),
    ("defect_update",        "Изменение дефекта"),
    ("defect_change_status", "Изменение статуса дефекта"),
    ("defect_approve",       "Согласование дефекта"),
    # purchases
    ("purchase_create",        "Создание закупки"),
    ("purchase_update",        "Изменение закупки"),
    ("purchase_change_status", "Изменение статуса закупки"),
]


def upgrade():
    op.bulk_insert(
        log_actions,
        [{"sysname": s, "display_name": d} for s, d in NEW_ACTIONS],
    )


def downgrade():
    sysnames = [s for s, _ in NEW_ACTIONS]
    op.execute(
        f"DELETE FROM log_actions WHERE sysname IN ({', '.join(repr(s) for s in sysnames)})"
    )
