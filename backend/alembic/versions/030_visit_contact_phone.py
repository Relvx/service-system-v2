"""add visit_contact_phone to visits and visits_history

Revision ID: 030
Revises: 029
Create Date: 2026-04-13

"""
from alembic import op
import sqlalchemy as sa

revision = '030'
down_revision = '029'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("visits", sa.Column("visit_contact_phone", sa.String(50), nullable=True))
    op.add_column("visits_history", sa.Column("v_visit_contact_phone", sa.String(50), nullable=True))


def downgrade():
    op.drop_column("visits_history", "v_visit_contact_phone")
    op.drop_column("visits", "visit_contact_phone")
