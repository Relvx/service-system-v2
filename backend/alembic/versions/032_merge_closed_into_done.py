"""merge visit status closed into done

Revision ID: 031
Revises: 030
Create Date: 2026-04-16

"""
from alembic import op

revision = '032'
down_revision = '2ed21365bbd9'
branch_labels = None
depends_on = None


def upgrade():
    # Переводим все закрытые выезды в статус «завершён»
    op.execute("UPDATE visits SET status='done' WHERE status='closed'")
    # Убираем статус closed из справочника
    op.execute("DELETE FROM visit_statuses WHERE sysname='closed'")


def downgrade():
    op.execute("INSERT INTO visit_statuses (sysname, display_name) VALUES ('closed', 'Закрыт') ON CONFLICT DO NOTHING")
