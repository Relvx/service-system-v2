"""Website enquiries stay separate from confirmed clients and planned visits."""
from datetime import datetime, timezone
from sqlalchemy import BigInteger, Boolean, Column, DateTime, ForeignKey, Index, Integer, String, Text, CheckConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from app.database import Base


def utcnow():
    return datetime.now(timezone.utc)


class WebsiteRequest(Base):
    __tablename__ = 'website_requests'
    __table_args__ = (
        CheckConstraint("status IN ('new', 'in_progress', 'closed', 'spam')", name='ck_website_request_status'),
        Index('ix_website_requests_status_date', 'status', 'received_at', 'id'),
        Index('ix_website_requests_assignee_date', 'assigned_user_id', 'received_at'),
    )
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    external_id = Column(UUID(as_uuid=True), nullable=False, unique=True)
    website_reference = Column(String(40), nullable=False)
    submitted_at = Column(DateTime(timezone=True), nullable=False)
    received_at = Column(DateTime(timezone=True), nullable=False, default=utcnow, index=True)
    payload = Column(JSONB, nullable=False)
    payload_hash = Column(String(64), nullable=False)
    phone = Column(String(20), nullable=False, index=True)
    contact_name = Column(String(100))
    company_name = Column(String(180))
    service_category = Column(String(20))
    work_type = Column(String(30))
    status = Column(String(20), nullable=False, default='new')
    assigned_user_id = Column(BigInteger, ForeignKey('users.id', ondelete='SET NULL'))
    working_data = Column(JSONB, nullable=False, default=dict)
    outcome = Column(Text)
    version = Column(Integer, nullable=False, default=1)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=utcnow)
    client_id = Column(BigInteger, ForeignKey('clients.id', ondelete='SET NULL'))
    contact_id = Column(BigInteger, ForeignKey('client_contacts.id', ondelete='SET NULL'))
    site_id = Column(BigInteger, ForeignKey('sites.id', ondelete='SET NULL'))

    def __repr__(self):
        return f'<WebsiteRequest id={self.id}>'


class WebsiteRequestEvent(Base):
    __tablename__ = 'website_request_events'
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    request_id = Column(BigInteger, ForeignKey('website_requests.id', ondelete='CASCADE'), nullable=False, index=True)
    user_id = Column(BigInteger, ForeignKey('users.id', ondelete='SET NULL'))
    author_name = Column(String(255))
    kind = Column(String(30), nullable=False)
    data = Column(JSONB, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utcnow)


class WebsiteIntegrationConnection(Base):
    __tablename__ = 'website_integration_connections'
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    token_hash = Column(String(64), nullable=False, unique=True)
    label = Column(String(100), nullable=False)
    created_by = Column(BigInteger, ForeignKey('users.id', ondelete='SET NULL'))
    revoked = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utcnow)
    expires_at = Column(DateTime(timezone=True), nullable=False)

    def __repr__(self):
        return f'<WebsiteIntegrationConnection id={self.id}>'


class WebsiteRequestCommand(Base):
    __tablename__ = 'website_request_commands'
    id = Column(UUID(as_uuid=True), primary_key=True)
    request_id = Column(BigInteger, ForeignKey('website_requests.id', ondelete='CASCADE'), nullable=False, index=True)
    payload_hash = Column(String(64), nullable=False)
    result = Column(JSONB, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utcnow)
