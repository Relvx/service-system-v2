"""Add entity_types table with display names for document entities

Revision ID: 007
Revises: 006
Create Date: 2026-02-27
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.sql import table, column
from sqlalchemy import String

revision = "007"
down_revision = "006"
branch_labels = None
depends_on = None

entity_types = table(
    "entity_types",
    column("sysname", String),
    column("display_name", String),
    column("display_name_plural", String),
)

SEED = [
    ("client",   "Клиент",   "Клиенты"),
    ("site",     "Объект",   "Объекты"),
    ("visit",    "Выезд",    "Выезды"),
    ("defect",   "Дефект",   "Дефекты"),
    ("purchase", "Закупка",  "Закупки"),
]


def upgrade():
    op.create_table(
        "entity_types",
        sa.Column("sysname", sa.String(50), primary_key=True),
        sa.Column("display_name", sa.String(100), nullable=False),
        sa.Column("display_name_plural", sa.String(100), nullable=False),
    )
    op.bulk_insert(
        entity_types,
        [{"sysname": s, "display_name": d, "display_name_plural": p} for s, d, p in SEED],
    )


def downgrade():
    op.drop_table("entity_types")
