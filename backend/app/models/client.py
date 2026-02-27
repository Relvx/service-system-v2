"""Модель клиента — юридического или физического лица, заказывающего обслуживание."""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base


class Client(Base):
    """Клиент системы.

    Содержит реквизиты организации (ИНН, КПП) и контактные данные.
    К клиенту привязаны объекты обслуживания (Site).
    """
    __tablename__ = "clients"
    __table_args__ = {"info": {"display_name": "Клиент", "display_name_plural": "Клиенты", "entity_type": "client"}}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(Text, nullable=False)
    inn = Column(String(50), nullable=True)
    kpp = Column(String(50), nullable=True)
    contacts = Column(Text, nullable=True)
    contact_person = Column(String(255), nullable=True)
    notes = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
