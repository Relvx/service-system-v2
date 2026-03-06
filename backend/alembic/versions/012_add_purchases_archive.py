"""Add is_archived to purchases, add purchase_archive log action

Revision ID: 012
Revises: 011
Create Date: 2026-03-06
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.sql import table, column
from sqlalchemy import String

revision = "012"
down_revision = "011"
branch_labels = None
depends_on = None

log_actions = table(
    "log_actions",
    column("sysname", String),
    column("display_name", String),
)


def upgrade():
    op.add_column(
        "purchases",
        sa.Column("is_archived", sa.Boolean(), nullable=False, server_default="false"),
    )
    op.create_index("ix_purchases_is_archived", "purchases", ["is_archived"])
    op.bulk_insert(log_actions, [{"sysname": "purchase_archive", "display_name": "Архивирование закупки"}])


def downgrade():
    op.execute("DELETE FROM log_actions WHERE sysname = 'purchase_archive'")
    op.drop_index("ix_purchases_is_archived", table_name="purchases")
    op.drop_column("purchases", "is_archived")
