"""Модель объекта обслуживания — физического адреса, где проводятся выезды."""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Text, Float, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base


class Site(Base):
    """Объект обслуживания (котельная, здание и т.п.).

    Привязан к клиенту (Client). Хранит адрес, координаты для карты,
    инструкции по доступу и периодичность обслуживания.
    """
    __tablename__ = "sites"
    __table_args__ = {"info": {"display_name": "Объект", "display_name_plural": "Объекты", "entity_type": "site"}}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id = Column(UUID(as_uuid=True), ForeignKey("clients.id", ondelete="SET NULL"), nullable=True)
    title = Column(Text, nullable=False)
    address = Column(Text, nullable=False)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    access_notes = Column(Text, nullable=True)
    onsite_contact = Column(Text, nullable=True)
    service_frequency = Column(String(30), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    is_archived = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)
