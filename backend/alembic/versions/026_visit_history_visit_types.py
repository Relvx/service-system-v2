"""add v_visit_types to visits_history

Revision ID: 026
Revises: 025
Create Date: 2026-04-07
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ARRAY

revision = "026"
down_revision = "025"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "visits_history",
        sa.Column("v_visit_types", ARRAY(sa.String(30)), nullable=True),
    )


def downgrade():
    op.drop_column("visits_history", "v_visit_types")
