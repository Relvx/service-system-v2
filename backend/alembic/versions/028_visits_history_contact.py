"""add visit_contact fields to visits_history

Revision ID: 028
Revises: 027
Create Date: 2026-04-07
"""
from alembic import op
import sqlalchemy as sa

revision = "028"
down_revision = "027"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("visits_history", sa.Column("v_visit_contact", sa.String(200), nullable=True))
    op.add_column("visits_history", sa.Column("v_visit_contact_position", sa.String(100), nullable=True))
    op.add_column("sites_history", sa.Column("v_service_frequency_custom", sa.Text, nullable=True))


def downgrade():
    op.drop_column("sites_history", "v_service_frequency_custom")
    op.drop_column("visits_history", "v_visit_contact_position")
    op.drop_column("visits_history", "v_visit_contact")
