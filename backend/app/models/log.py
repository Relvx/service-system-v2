"""Audit log tables."""

import uuid
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.database import Base


class LogAction(Base):
    """Lookup table for log action types (create, update, delete, …)."""
    __tablename__ = "log_actions"

    id = Column(Integer, primary_key=True)
    sysname = Column(String(50), unique=True, nullable=False)
    display_name = Column(String(100), nullable=False)


class Log(Base):
    """Audit log entry recording who did what to which entity."""
    __tablename__ = "logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True),
                     ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    action_sysname = Column(String(50),
                            ForeignKey("log_actions.sysname", ondelete="SET NULL"), nullable=True)
    entity_type = Column(String(50), nullable=False)
    entity_id = Column(UUID(as_uuid=True), nullable=False)
    details = Column(JSONB, nullable=True)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
