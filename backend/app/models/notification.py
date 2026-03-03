"""Модель внутреннего уведомления пользователя."""

from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Text, ForeignKey, BigInteger
from app.database import Base


class Notification(Base):
    """Уведомление для конкретного пользователя.

    Создаётся автоматически при назначении или изменении выезда.
    Хранит статус прочтения (is_read) и ссылку на связанный выезд.
    """
    __tablename__ = "notifications"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    type = Column(String(50), nullable=False)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    related_visit_id = Column(BigInteger, ForeignKey("visits.id", ondelete="SET NULL"), nullable=True)
    is_read = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
