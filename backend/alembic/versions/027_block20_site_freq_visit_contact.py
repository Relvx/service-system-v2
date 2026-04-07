"""block20: once in service_frequencies, service_frequency_custom on sites, visit_contact fields

Revision ID: 027
Revises: 026
Create Date: 2026-04-07
"""
from alembic import op
import sqlalchemy as sa

revision = "027"
down_revision = "026"
branch_labels = None
depends_on = None


def upgrade():
    # 1. Добавляем 'once' (Разово) в справочник частот обслуживания
    op.execute("""
        INSERT INTO service_frequencies (sysname, display_name)
        VALUES ('once', 'Разово')
        ON CONFLICT (sysname) DO NOTHING
    """)

    # 2. Поле свободного текста частоты на объекте
    op.add_column("sites", sa.Column("service_frequency_custom", sa.Text, nullable=True))

    # 3. Контакт при выезде
    op.add_column("visits", sa.Column("visit_contact", sa.String(200), nullable=True))
    op.add_column("visits", sa.Column("visit_contact_position", sa.String(100), nullable=True))

    # 4. Контакт при выезде — история
    op.add_column("visits_history", sa.Column("v_visit_contact", sa.String(200), nullable=True))
    op.add_column("visits_history", sa.Column("v_visit_contact_position", sa.String(100), nullable=True))


def downgrade():
    op.drop_column("visits_history", "v_visit_contact_position")
    op.drop_column("visits_history", "v_visit_contact")
    op.drop_column("visits", "visit_contact_position")
    op.drop_column("visits", "visit_contact")
    op.drop_column("sites", "service_frequency_custom")
    op.execute("DELETE FROM service_frequencies WHERE sysname = 'once'")
