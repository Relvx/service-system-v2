"""Work report review, proposals and scoped MCP connections; repair done lookup."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
revision = '033'
down_revision = '6800ce707a70'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("INSERT INTO log_actions (sysname, display_name) VALUES ('report_proposal_create', 'Предложение дефекта из отчёта'), ('report_proposal_dismiss', 'Отклонение предложения дефекта'), ('report_review', 'Проверка итога выезда'), ('report_connection_create', 'Подключение к отчётам'), ('report_connection_revoke', 'Отзыв подключения к отчётам') ON CONFLICT (sysname) DO NOTHING")
    op.execute("INSERT INTO visit_statuses (sysname, display_name) VALUES ('done', 'Завершён') ON CONFLICT (sysname) DO UPDATE SET display_name = EXCLUDED.display_name")
    op.execute("UPDATE visits SET status='done' WHERE status='closed'")
    op.execute("DELETE FROM visit_statuses WHERE sysname='closed'")
    op.create_table('visit_reviews',
        sa.Column('visit_id', sa.BigInteger(), sa.ForeignKey('visits.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('report_hash', sa.String(64), nullable=False), sa.Column('snapshot', postgresql.JSONB(), nullable=False), sa.Column('notes', sa.Text(), nullable=False),
        sa.Column('reviewed_by', sa.BigInteger(), sa.ForeignKey('users.id', ondelete='SET NULL')),
        sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=False))
    op.create_table('report_proposals',
        sa.Column('id', sa.BigInteger(), primary_key=True),
        sa.Column('visit_id', sa.BigInteger(), sa.ForeignKey('visits.id', ondelete='CASCADE'), nullable=False),
        sa.Column('report_hash', sa.String(64), nullable=False),
        sa.Column('proposal_key', sa.String(64), nullable=False, unique=True),
        sa.Column('data', postgresql.JSONB(), nullable=False),
        sa.Column('status', sa.String(20), nullable=False), sa.Column('source', sa.String(20), nullable=False),
        sa.Column('created_by', sa.BigInteger(), sa.ForeignKey('users.id', ondelete='SET NULL')),
        sa.Column('defect_id', sa.BigInteger(), sa.ForeignKey('defects.id', ondelete='SET NULL')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False))
    op.create_index('ix_report_proposals_visit_id', 'report_proposals', ['visit_id'])
    op.create_table('report_connections',
        sa.Column('id', sa.BigInteger(), primary_key=True),
        sa.Column('user_id', sa.BigInteger(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('token_hash', sa.String(64), nullable=False, unique=True),
        sa.Column('revoked', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False))


def downgrade():
    op.drop_table('report_connections')
    op.drop_table('report_proposals')
    op.drop_table('visit_reviews')
    # done is still required by the existing visit completion code.
