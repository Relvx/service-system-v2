"""Separate website intake, office processing and scoped credentials."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision = '035'
down_revision = '034'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('website_requests',
        sa.Column('id', sa.BigInteger(), primary_key=True),
        sa.Column('external_id', UUID(as_uuid=True), nullable=False, unique=True),
        sa.Column('website_reference', sa.String(40), nullable=False),
        sa.Column('submitted_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('received_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('payload', JSONB(), nullable=False),
        sa.Column('payload_hash', sa.String(64), nullable=False),
        sa.Column('phone', sa.String(20), nullable=False),
        sa.Column('contact_name', sa.String(100)),
        sa.Column('company_name', sa.String(180)),
        sa.Column('service_category', sa.String(20)),
        sa.Column('work_type', sa.String(30)),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('assigned_user_id', sa.BigInteger(), sa.ForeignKey('users.id', ondelete='SET NULL')),
        sa.Column('working_data', JSONB(), nullable=False),
        sa.Column('outcome', sa.Text()),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('client_id', sa.BigInteger(), sa.ForeignKey('clients.id', ondelete='SET NULL')),
        sa.Column('contact_id', sa.BigInteger(), sa.ForeignKey('client_contacts.id', ondelete='SET NULL')),
        sa.Column('site_id', sa.BigInteger(), sa.ForeignKey('sites.id', ondelete='SET NULL')),
        sa.CheckConstraint("status IN ('new', 'in_progress', 'closed', 'spam')", name='ck_website_request_status'))
    for name, columns in [
        ('ix_website_requests_status_date', ['status', 'received_at', 'id']),
        ('ix_website_requests_assignee_date', ['assigned_user_id', 'received_at']),
        ('ix_website_requests_phone', ['phone']), ('ix_website_requests_received_at', ['received_at'])]:
        op.create_index(name, 'website_requests', columns)
    op.create_table('website_request_events',
        sa.Column('id', sa.BigInteger(), primary_key=True),
        sa.Column('request_id', sa.BigInteger(), sa.ForeignKey('website_requests.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', sa.BigInteger(), sa.ForeignKey('users.id', ondelete='SET NULL')),
        sa.Column('author_name', sa.String(255)),
        sa.Column('kind', sa.String(30), nullable=False),
        sa.Column('data', JSONB(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False))
    op.create_index('ix_website_request_events_request_id', 'website_request_events', ['request_id'])
    op.create_table('website_integration_connections',
        sa.Column('id', sa.BigInteger(), primary_key=True),
        sa.Column('token_hash', sa.String(64), nullable=False, unique=True),
        sa.Column('label', sa.String(100), nullable=False),
        sa.Column('created_by', sa.BigInteger(), sa.ForeignKey('users.id', ondelete='SET NULL')),
        sa.Column('revoked', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False))
    op.create_table('website_request_commands',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('request_id', sa.BigInteger(), sa.ForeignKey('website_requests.id', ondelete='CASCADE'), nullable=False),
        sa.Column('payload_hash', sa.String(64), nullable=False),
        sa.Column('result', JSONB(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False))
    op.create_index('ix_website_request_commands_request_id', 'website_request_commands', ['request_id'])
    op.add_column('notifications', sa.Column('related_website_request_id', sa.BigInteger(), nullable=True))
    op.create_foreign_key('fk_notifications_website_request', 'notifications', 'website_requests',
                          ['related_website_request_id'], ['id'], ondelete='SET NULL')
    op.alter_column('client_contacts', 'email', existing_type=sa.String(100), type_=sa.String(254))
    op.execute("INSERT INTO log_actions (sysname, display_name) VALUES ('website_request_event', 'Обработка заявки сайта') ON CONFLICT (sysname) DO NOTHING")
    op.execute("INSERT INTO notification_types (sysname, display_name) VALUES ('website_request_new', 'Новая заявка с сайта') ON CONFLICT (sysname) DO NOTHING")


def downgrade():
    # Fail rather than silently truncate contacts if a longer email was saved.
    op.alter_column('client_contacts', 'email', existing_type=sa.String(254), type_=sa.String(100))
    op.drop_constraint('fk_notifications_website_request', 'notifications', type_='foreignkey')
    op.drop_column('notifications', 'related_website_request_id')
    op.drop_table('website_request_commands')
    op.drop_table('website_integration_connections')
    op.drop_table('website_request_events')
    op.drop_table('website_requests')
    op.execute("DELETE FROM log_actions WHERE sysname='website_request_event'")
    op.execute("DELETE FROM notification_types WHERE sysname='website_request_new'")
