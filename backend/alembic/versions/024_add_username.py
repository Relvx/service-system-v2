"""add username to users

Revision ID: 024
Revises: 023
Create Date: 2026-03-31
"""
from alembic import op
import sqlalchemy as sa

revision = "024"
down_revision = "023"
branch_labels = None
depends_on = None


def upgrade():
    # Add nullable first
    op.add_column("users", sa.Column("username", sa.String(150), nullable=True))

    # Populate from email (part before '@')
    op.execute("UPDATE users SET username = split_part(email, '@', 1)")

    # Make NOT NULL + unique
    op.alter_column("users", "username", nullable=False)
    op.create_unique_constraint("uq_users_username", "users", ["username"])
    op.create_index("ix_users_username", "users", ["username"])


def downgrade():
    op.drop_index("ix_users_username", table_name="users")
    op.drop_constraint("uq_users_username", "users", type_="unique")
    op.drop_column("users", "username")
