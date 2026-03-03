"""Модель юридических реквизитов клиента."""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base


class ClientLegal(Base):
    """Юридические реквизиты клиента.

    Один клиент — одна запись (UNIQUE на client_id).
    ИНН и КПП хранятся в основной таблице clients.
    """
    __tablename__ = "client_legal"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id = Column(UUID(as_uuid=True), ForeignKey("clients.id", ondelete="CASCADE"),
                       nullable=False, unique=True)
    legal_address = Column(Text, nullable=True)
    bank = Column(String(200), nullable=True)
    bik = Column(String(20), nullable=True)
    account = Column(String(30), nullable=True)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)
