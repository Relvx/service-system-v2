"""block19: visit_masters many-to-many, visit_types array

Revision ID: 025
Revises: 024
Create Date: 2026-04-07
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ARRAY

revision = "025"
down_revision = "024"
branch_labels = None
depends_on = None


def upgrade():
    # 1. Таблица visit_masters (many-to-many)
    op.create_table(
        "visit_masters",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("visit_id", sa.BigInteger, sa.ForeignKey("visits.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.BigInteger, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
    )
    op.create_unique_constraint("uq_visit_masters", "visit_masters", ["visit_id", "user_id"])
    op.create_index("ix_visit_masters_visit_id", "visit_masters", ["visit_id"])
    op.create_index("ix_visit_masters_user_id", "visit_masters", ["user_id"])

    # 2. Заполняем visit_masters из assigned_user_id
    op.execute("""
        INSERT INTO visit_masters (visit_id, user_id)
        SELECT id, assigned_user_id
        FROM visits
        WHERE assigned_user_id IS NOT NULL
    """)

    # 3. Добавляем колонку visit_types (массив строк)
    op.add_column("visits", sa.Column("visit_types", ARRAY(sa.String(30)), nullable=True))

    # 4. Заполняем visit_types из visit_type
    op.execute("UPDATE visits SET visit_types = ARRAY[visit_type]")


def downgrade():
    op.drop_column("visits", "visit_types")
    op.drop_index("ix_visit_masters_user_id", table_name="visit_masters")
    op.drop_index("ix_visit_masters_visit_id", table_name="visit_masters")
    op.drop_constraint("uq_visit_masters", "visit_masters", type_="unique")
    op.drop_table("visit_masters")
