"""Comments in defect cards."""
from alembic import op
import sqlalchemy as sa

revision = "034"
down_revision = "033"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("defect_comments",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("defect_id", sa.BigInteger(), sa.ForeignKey("defects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False))
    op.create_index("ix_defect_comments_defect_id", "defect_comments", ["defect_id"])
    op.execute("INSERT INTO log_actions (sysname, display_name) VALUES ('defect_comment_create', 'Комментарий к дефекту') ON CONFLICT (sysname) DO NOTHING")


def downgrade():
    op.drop_table("defect_comments")
    op.execute("DELETE FROM log_actions WHERE sysname='defect_comment_create'")
