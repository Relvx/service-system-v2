"""Add visit_completed notification type

Revision ID: 016
Revises: 015
Create Date: 2026-03-12
"""
from alembic import op

revision = "016"
down_revision = "015"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        INSERT INTO notification_types (sysname, display_name)
        VALUES ('visit_completed', 'Выезд завершён мастером')
        ON CONFLICT (sysname) DO NOTHING
    """)


def downgrade():
    op.execute("DELETE FROM notification_types WHERE sysname = 'visit_completed'")
