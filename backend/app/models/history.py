"""Snapshot-based history tables — one row per change event."""

import uuid
from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.database import Base


class _HistoryBase(Base):
    """Abstract base for all history tables."""
    __abstract__ = True

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    record_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    changed_by_user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    changed_at = Column(DateTime, default=datetime.now, nullable=False)
    snapshot = Column(JSONB, nullable=False)


class ClientHistory(_HistoryBase):
    """History snapshots for the clients table."""
    __tablename__ = "clients_history"


class SiteHistory(_HistoryBase):
    """History snapshots for the sites table."""
    __tablename__ = "sites_history"


class UserHistory(_HistoryBase):
    """History snapshots for the users table."""
    __tablename__ = "users_history"


class VisitHistory(_HistoryBase):
    """History snapshots for the visits table."""
    __tablename__ = "visits_history"


class PurchaseHistory(_HistoryBase):
    """History snapshots for the purchases table."""
    __tablename__ = "purchases_history"
