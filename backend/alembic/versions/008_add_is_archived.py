"""Add is_archived to clients, sites, visits

Revision ID: 008
Revises: 007
Create Date: 2026-03-02
"""

from alembic import op
import sqlalchemy as sa

revision = '008'
down_revision = '007'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('clients', sa.Column('is_archived', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('sites',   sa.Column('is_archived', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('visits',  sa.Column('is_archived', sa.Boolean(), nullable=False, server_default='false'))

    op.create_index('ix_clients_is_archived', 'clients', ['is_archived'])
    op.create_index('ix_sites_is_archived',   'sites',   ['is_archived'])
    op.create_index('ix_visits_is_archived',  'visits',  ['is_archived'])


def downgrade():
    op.drop_index('ix_visits_is_archived',  table_name='visits')
    op.drop_index('ix_sites_is_archived',   table_name='sites')
    op.drop_index('ix_clients_is_archived', table_name='clients')

    op.drop_column('visits',  'is_archived')
    op.drop_column('sites',   'is_archived')
    op.drop_column('clients', 'is_archived')
