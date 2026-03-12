"""Модель напоминания (общего или личного)."""

from datetime import datetime
from sqlalchemy import Column, DateTime, Text, ForeignKey, BigInteger, Boolean
from app.database import Base


class Reminder(Base):
    __tablename__ = "reminders"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    text = Column(Text, nullable=False)
    is_personal = Column(Boolean, default=False, nullable=False)
    created_by_user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
