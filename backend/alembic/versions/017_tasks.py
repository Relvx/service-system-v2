"""Add tasks table and task_id to attachments

Revision ID: 017
Revises: 016
Create Date: 2026-03-12
"""
from alembic import op
import sqlalchemy as sa

revision = "017"
down_revision = "016"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "tasks",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("deadline", sa.Date(), nullable=True),
        sa.Column("is_done", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_by_user_id", sa.BigInteger(),
                  sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.add_column("attachments", sa.Column("task_id", sa.BigInteger(), nullable=True))
    op.create_foreign_key(
        "fk_attachments_task_id", "attachments", "tasks", ["task_id"], ["id"],
        ondelete="CASCADE",
    )


def downgrade():
    op.drop_constraint("fk_attachments_task_id", "attachments", type_="foreignkey")
    op.drop_column("attachments", "task_id")
    op.drop_table("tasks")
