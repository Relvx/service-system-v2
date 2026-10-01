from datetime import datetime, timezone
from sqlalchemy import Column, BigInteger, Text, String, DateTime, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import JSONB
from app.database import Base


def utcnow():
    return datetime.now(timezone.utc)


class VisitReview(Base):
    __tablename__ = 'visit_reviews'
    visit_id = Column(BigInteger, ForeignKey('visits.id', ondelete='CASCADE'), primary_key=True)
    report_hash = Column(String(64), nullable=False)
    snapshot = Column(JSONB, nullable=False)
    notes = Column(Text, nullable=False, default='')
    reviewed_by = Column(BigInteger, ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=False, default=utcnow)


class ReportProposal(Base):
    __tablename__ = 'report_proposals'
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    visit_id = Column(BigInteger, ForeignKey('visits.id', ondelete='CASCADE'), nullable=False, index=True)
    report_hash = Column(String(64), nullable=False)
    proposal_key = Column(String(64), nullable=False, unique=True)
    data = Column(JSONB, nullable=False)
    status = Column(String(20), nullable=False, default='pending')
    source = Column(String(20), nullable=False)
    created_by = Column(BigInteger, ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    defect_id = Column(BigInteger, ForeignKey('defects.id', ondelete='SET NULL'), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utcnow)


class ReportConnection(Base):
    __tablename__ = 'report_connections'
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    token_hash = Column(String(64), nullable=False, unique=True)
    revoked = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utcnow)
    expires_at = Column(DateTime(timezone=True), nullable=False)
