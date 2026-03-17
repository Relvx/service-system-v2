"""contracts and contract_sites

Revision ID: 020
Revises: 019
Create Date: 2026-03-17
"""
from alembic import op
import sqlalchemy as sa

revision = "020"
down_revision = "019"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "contracts",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("client_id", sa.BigInteger(), sa.ForeignKey("clients.id", ondelete="SET NULL"), nullable=True),
        sa.Column("contract_number", sa.String(255), nullable=True),
        sa.Column("contract_date", sa.Date(), nullable=True),
        sa.Column("subject", sa.Text(), nullable=True),
        sa.Column("amount", sa.Numeric(10, 2), nullable=True),
        sa.Column("act_amount", sa.Numeric(10, 2), nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="active"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("is_archived", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )

    op.create_table(
        "contract_sites",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("contract_id", sa.BigInteger(), sa.ForeignKey("contracts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("site_id", sa.BigInteger(), sa.ForeignKey("sites.id", ondelete="CASCADE"), nullable=False),
        sa.UniqueConstraint("contract_id", "site_id", name="uq_contract_sites"),
    )


def downgrade():
    op.drop_table("contract_sites")
    op.drop_table("contracts")
