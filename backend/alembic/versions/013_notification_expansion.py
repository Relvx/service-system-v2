"""Add related_defect_id/related_purchase_id to notifications, seed new notification types

Revision ID: 013
Revises: 012
Create Date: 2026-03-10
"""
from alembic import op
import sqlalchemy as sa

revision = "013"
down_revision = "012"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "notifications",
        sa.Column(
            "related_defect_id",
            sa.BigInteger(),
            sa.ForeignKey("defects.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.add_column(
        "notifications",
        sa.Column(
            "related_purchase_id",
            sa.BigInteger(),
            sa.ForeignKey("purchases.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )

    op.execute("""
        INSERT INTO notification_types (sysname, display_name) VALUES
        ('defect_status_changed', 'Изменён статус дефекта'),
        ('purchase_status_changed', 'Изменён статус закупки')
        ON CONFLICT (sysname) DO NOTHING
    """)


def downgrade():
    op.drop_column("notifications", "related_purchase_id")
    op.drop_column("notifications", "related_defect_id")

    op.execute("""
        DELETE FROM notification_types
        WHERE sysname IN ('defect_status_changed', 'purchase_status_changed')
    """)
