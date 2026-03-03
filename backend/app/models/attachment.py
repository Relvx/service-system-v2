"""Модель файлового вложения, прикреплённого к выезду."""

from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, ForeignKey, BigInteger
from app.database import Base


class Attachment(Base):
    """Файловое вложение (фото акта, фото дефекта и др.).

    Привязано к выезду (Visit). Хранит URL файла в облачном хранилище
    и тип вложения (kind).
    """
    __tablename__ = "attachments"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    visit_id = Column(BigInteger, ForeignKey("visits.id", ondelete="CASCADE"), nullable=True)
    kind = Column(String(30), nullable=False, default="act_photo")
    file_url = Column(Text, nullable=False)
    created_by_user_id = Column(BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
