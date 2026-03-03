"""Add client_contacts and client_legal tables.

Revision ID: 009
Revises: 008
Create Date: 2026-03-03
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = '009'
down_revision = '008'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'client_contacts',
        sa.Column('id', UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('gen_random_uuid()')),
        sa.Column('client_id', UUID(as_uuid=True),
                  sa.ForeignKey('clients.id', ondelete='CASCADE'), nullable=False),
        sa.Column('full_name', sa.Text(), nullable=False),
        sa.Column('position', sa.String(100), nullable=True),
        sa.Column('phone', sa.String(50), nullable=True),
        sa.Column('email', sa.String(100), nullable=True),
        sa.Column('is_primary', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(),
                  server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('ix_client_contacts_client_id', 'client_contacts', ['client_id'])

    op.create_table(
        'client_legal',
        sa.Column('id', UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('gen_random_uuid()')),
        sa.Column('client_id', UUID(as_uuid=True),
                  sa.ForeignKey('clients.id', ondelete='CASCADE'),
                  nullable=False, unique=True),
        sa.Column('legal_address', sa.Text(), nullable=True),
        sa.Column('bank', sa.String(200), nullable=True),
        sa.Column('bik', sa.String(20), nullable=True),
        sa.Column('account', sa.String(30), nullable=True),
        sa.Column('created_at', sa.DateTime(),
                  server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(),
                  server_default=sa.text('now()'), nullable=False),
    )


def downgrade():
    op.drop_table('client_legal')
    op.drop_index('ix_client_contacts_client_id', table_name='client_contacts')
    op.drop_table('client_contacts')
