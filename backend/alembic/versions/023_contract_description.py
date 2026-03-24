"""contract description field

Revision ID: 023
Revises: 022
Create Date: 2026-03-24
"""
from alembic import op
import sqlalchemy as sa

revision = '023'
down_revision = '022'
branch_labels = None
depends_on = None

def upgrade():
    op.add_column('contracts', sa.Column('description', sa.Text(), nullable=True))

def downgrade():
    op.drop_column('contracts', 'description')
