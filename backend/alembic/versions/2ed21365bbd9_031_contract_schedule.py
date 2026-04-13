"""031_contract_schedule

Revision ID: 2ed21365bbd9
Revises: 030
Create Date: 2026-04-13 16:43:50.691483

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '2ed21365bbd9'
down_revision: Union[str, None] = '030'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'contract_schedule',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('contract_id', sa.BigInteger(), nullable=False),
        sa.Column('year', sa.Integer(), nullable=False),
        sa.Column('month', sa.Integer(), nullable=False),
        sa.Column('note', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['contract_id'], ['contracts.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('contract_id', 'year', 'month', name='uq_contract_schedule'),
    )


def downgrade() -> None:
    op.drop_table('contract_schedule')
