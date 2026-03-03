"""Модель контактного лица клиента."""

from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Text, ForeignKey, BigInteger
from app.database import Base


class ClientContact(Base):
    """Контактное лицо клиента.

    У одного клиента может быть несколько контактов.
    Один из них помечается is_primary=True.
    """
    __tablename__ = "client_contacts"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    client_id = Column(BigInteger, ForeignKey("clients.id", ondelete="CASCADE"), nullable=False)
    full_name = Column(Text, nullable=False)
    position = Column(String(100), nullable=True)
    phone = Column(String(50), nullable=True)
    email = Column(String(100), nullable=True)
    is_primary = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
