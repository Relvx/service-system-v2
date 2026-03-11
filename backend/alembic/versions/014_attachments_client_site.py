"""Add client_id and site_id to attachments; add DELETE support

Revision ID: 014
Revises: 013
Create Date: 2026-03-11
"""
from alembic import op
import sqlalchemy as sa

revision = "014"
down_revision = "013"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("attachments", sa.Column("client_id", sa.BigInteger(), nullable=True))
    op.add_column("attachments", sa.Column("site_id", sa.BigInteger(), nullable=True))
    op.add_column("attachments", sa.Column("file_name", sa.String(255), nullable=True))

    op.create_foreign_key(
        "fk_attachments_client_id", "attachments", "clients", ["client_id"], ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_attachments_site_id", "attachments", "sites", ["site_id"], ["id"],
        ondelete="CASCADE",
    )


def downgrade():
    op.drop_constraint("fk_attachments_client_id", "attachments", type_="foreignkey")
    op.drop_constraint("fk_attachments_site_id", "attachments", type_="foreignkey")
    op.drop_column("attachments", "client_id")
    op.drop_column("attachments", "site_id")
    op.drop_column("attachments", "file_name")
