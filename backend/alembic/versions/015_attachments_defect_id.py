"""Add defect_id to attachments

Revision ID: 015
Revises: 014
Create Date: 2026-03-11
"""
from alembic import op
import sqlalchemy as sa

revision = "015"
down_revision = "014"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("attachments", sa.Column("defect_id", sa.BigInteger(), nullable=True))
    op.create_foreign_key(
        "fk_attachments_defect_id", "attachments", "defects", ["defect_id"], ["id"],
        ondelete="CASCADE",
    )


def downgrade():
    op.drop_constraint("fk_attachments_defect_id", "attachments", type_="foreignkey")
    op.drop_column("attachments", "defect_id")
