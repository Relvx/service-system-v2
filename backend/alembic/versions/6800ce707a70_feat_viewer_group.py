"""feat: viewer_group

Revision ID: 6800ce707a70
Revises: 032
Create Date: 2026-04-24 12:43:25.706557

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6800ce707a70'
down_revision: Union[str, None] = '032'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        INSERT INTO permission_groups (sysname, display_name, default_redirect)
        VALUES ('viewer_group', 'Просмотр', '/dashboard')
        ON CONFLICT (sysname) DO NOTHING;
    """)
    op.execute("""
        INSERT INTO permission_group_permissions (group_id, permission_id)
        SELECT
            (SELECT id FROM permission_groups WHERE sysname = 'viewer_group'),
            id
        FROM permissions
        WHERE sysname IN (
            'visits:view','clients:view','sites:view',
            'defects:view','purchases:view',
            'users:view','dashboard:view','config:view'
        )
        ON CONFLICT DO NOTHING;
    """)


def downgrade() -> None:
    op.execute("""
        DELETE FROM permission_groups WHERE sysname = 'viewer_group';
    """)
