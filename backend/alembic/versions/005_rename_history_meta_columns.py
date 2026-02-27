"""Rename history meta columns: v_date→changed_at, v_user_id→changed_by_user_id, v_method→method

Revision ID: 005
Revises: 004
Create Date: 2026-02-27
"""
from alembic import op

revision = "005"
down_revision = "004"
branch_labels = None
depends_on = None

HISTORY_TABLES = [
    "clients_history",
    "sites_history",
    "users_history",
    "visits_history",
    "purchases_history",
]


def upgrade():
    for tbl in HISTORY_TABLES:
        op.alter_column(tbl, "v_date",    new_column_name="changed_at")
        op.alter_column(tbl, "v_user_id", new_column_name="changed_by_user_id")
        op.alter_column(tbl, "v_method",  new_column_name="method")


def downgrade():
    for tbl in HISTORY_TABLES:
        op.alter_column(tbl, "changed_at",         new_column_name="v_date")
        op.alter_column(tbl, "changed_by_user_id", new_column_name="v_user_id")
        op.alter_column(tbl, "method",             new_column_name="v_method")
