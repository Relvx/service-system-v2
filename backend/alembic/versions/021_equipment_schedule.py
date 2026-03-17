"""equipment, service_schedule, visits contract_id/master_name_raw

Revision ID: 021
Revises: 020
Create Date: 2026-03-17
"""
from alembic import op
import sqlalchemy as sa

revision = "021"
down_revision = "020"
branch_labels = None
depends_on = None


def upgrade():
    # ── equipment ─────────────────────────────────────────────────────────
    op.create_table(
        "equipment",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("site_id", sa.BigInteger(),
                  sa.ForeignKey("sites.id", ondelete="CASCADE"), nullable=True),
        sa.Column("contract_id", sa.BigInteger(),
                  sa.ForeignKey("contracts.id", ondelete="SET NULL"), nullable=True),
        sa.Column("brand", sa.String(200), nullable=True),       # марка: СТГ1-2Д10(В)-3шт.
        sa.Column("quantity", sa.Integer(), nullable=True),       # количество приборов
        sa.Column("serial_numbers", sa.Text(), nullable=True),    # серийники текстом
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("idx_equipment_site_id", "equipment", ["site_id"])

    # ── service_schedule ──────────────────────────────────────────────────
    op.create_table(
        "service_schedule",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("contract_id", sa.BigInteger(),
                  sa.ForeignKey("contracts.id", ondelete="CASCADE"), nullable=True),
        sa.Column("site_id", sa.BigInteger(),
                  sa.ForeignKey("sites.id", ondelete="CASCADE"), nullable=True),
        sa.Column("scheduled_month", sa.Date(), nullable=False),  # первый день месяца
        sa.Column("work_type", sa.String(50), nullable=True),     # нормализованный: maintenance/inspection/repair/emergency
        sa.Column("work_type_raw", sa.String(200), nullable=True),# исходный текст из Excel
        sa.Column("visit_id", sa.BigInteger(),
                  sa.ForeignKey("visits.id", ondelete="SET NULL"), nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="scheduled"),
        sa.Column("is_historical", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("is_archived", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("idx_schedule_contract_id", "service_schedule", ["contract_id"])
    op.create_index("idx_schedule_site_id", "service_schedule", ["site_id"])
    op.create_index("idx_schedule_month", "service_schedule", ["scheduled_month"])

    # ── contracts: поле для хранения текстовой истории из Excel ──────────
    op.add_column("contracts", sa.Column("raw_visit_history", sa.Text(), nullable=True))

    # ── visits: два новых поля ────────────────────────────────────────────
    op.add_column("visits", sa.Column(
        "contract_id", sa.BigInteger(),
        sa.ForeignKey("contracts.id", ondelete="SET NULL"), nullable=True
    ))
    op.add_column("visits", sa.Column(
        "master_name_raw", sa.String(100), nullable=True
    ))


def downgrade():
    op.drop_column("visits", "master_name_raw")
    op.drop_column("visits", "contract_id")
    op.drop_column("contracts", "raw_visit_history")
    op.drop_index("idx_schedule_month", "service_schedule")
    op.drop_index("idx_schedule_site_id", "service_schedule")
    op.drop_index("idx_schedule_contract_id", "service_schedule")
    op.drop_table("service_schedule")
    op.drop_index("idx_equipment_site_id", "equipment")
    op.drop_table("equipment")
