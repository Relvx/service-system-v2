"""Add price fields to sites and cost to visits.

Revision ID: 010
Revises: 009
Create Date: 2026-03-03
"""

revision = '010'
down_revision = '009'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('sites', sa.Column('price_maintenance', sa.Float(), nullable=True))
    op.add_column('sites', sa.Column('price_repair', sa.Float(), nullable=True))
    op.add_column('sites', sa.Column('price_emergency', sa.Float(), nullable=True))
    op.add_column('visits', sa.Column('cost', sa.Float(), nullable=True))
    # history tables
    op.add_column('sites_history', sa.Column('v_price_maintenance', sa.Float(), nullable=True))
    op.add_column('sites_history', sa.Column('v_price_repair', sa.Float(), nullable=True))
    op.add_column('sites_history', sa.Column('v_price_emergency', sa.Float(), nullable=True))
    op.add_column('visits_history', sa.Column('v_cost', sa.Float(), nullable=True))


def downgrade():
    op.drop_column('sites', 'price_maintenance')
    op.drop_column('sites', 'price_repair')
    op.drop_column('sites', 'price_emergency')
    op.drop_column('visits', 'cost')
    op.drop_column('sites_history', 'v_price_maintenance')
    op.drop_column('sites_history', 'v_price_repair')
    op.drop_column('sites_history', 'v_price_emergency')
    op.drop_column('visits_history', 'v_cost')
