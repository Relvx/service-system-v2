"""migrate contact_person/contacts fields to client_contacts table

Revision ID: 029
Revises: 028
Create Date: 2026-04-13
"""
from alembic import op
import sqlalchemy as sa

revision = "029"
down_revision = "028"
branch_labels = None
depends_on = None


def upgrade():
    # Переносим данные из contact_person/contacts → client_contacts
    # Только для клиентов у которых:
    #   - есть хоть одно непустое поле (contact_person или contacts)
    #   - ещё нет записей в client_contacts
    op.execute("""
        INSERT INTO client_contacts (client_id, full_name, phone, is_primary, created_at)
        SELECT
            c.id,
            CASE
                WHEN c.contact_person IS NOT NULL AND TRIM(c.contact_person) != ''
                THEN TRIM(c.contact_person)
                ELSE 'Контакт'
            END,
            CASE
                WHEN c.contacts IS NOT NULL AND TRIM(c.contacts) != ''
                THEN TRIM(c.contacts)
                ELSE NULL
            END,
            TRUE,
            NOW()
        FROM clients c
        WHERE (
            (c.contact_person IS NOT NULL AND TRIM(c.contact_person) != '')
            OR (c.contacts IS NOT NULL AND TRIM(c.contacts) != '')
        )
        AND NOT EXISTS (
            SELECT 1 FROM client_contacts cc WHERE cc.client_id = c.id
        )
    """)

    # Удаляем устаревшие колонки
    op.drop_column("clients", "contact_person")
    op.drop_column("clients", "contacts")


def downgrade():
    op.add_column("clients", sa.Column("contact_person", sa.String(255), nullable=True))
    op.add_column("clients", sa.Column("contacts", sa.Text, nullable=True))
