"""visits_history: add v_contract_id and v_master_name_raw

Revision ID: 022
Revises: 021
Create Date: 2026-03-18
"""
from alembic import op
import sqlalchemy as sa

revision = "022"
down_revision = "021"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("ALTER TABLE visits_history ADD COLUMN IF NOT EXISTS v_contract_id BIGINT")
    op.execute("ALTER TABLE visits_history ADD COLUMN IF NOT EXISTS v_master_name_raw VARCHAR(100)")


def downgrade():
    op.drop_column("visits_history", "v_master_name_raw")
    op.drop_column("visits_history", "v_contract_id")
