"""Модель задачи (внутренний список дел для офиса/администратора)."""

from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, Date, ForeignKey, BigInteger, Boolean
from app.database import Base


class Task(Base):
    __tablename__ = "tasks"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    title = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    deadline = Column(Date, nullable=True)
    is_done = Column(Boolean, default=False, nullable=False)
    created_by_user_id = Column(BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)
