"""Модель дефекта, выявленного во время выезда."""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base


class Defect(Base):
    """Дефект, обнаруженный мастером на объекте.

    Привязан к выезду (Visit) и объекту (Site).
    Имеет тип действия (ремонт/замена/наблюдение) и статус жизненного цикла.
    Может порождать закупки (Purchase).
    """
    __tablename__ = "defects"
    __table_args__ = {"info": {"display_name": "Дефект", "display_name_plural": "Дефекты", "entity_type": "defect"}}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    visit_id = Column(UUID(as_uuid=True), ForeignKey("visits.id", ondelete="CASCADE"), nullable=True)
    site_id = Column(UUID(as_uuid=True), ForeignKey("sites.id", ondelete="CASCADE"), nullable=True)
    title = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    priority = Column(String(20), nullable=False, default="medium")
    action_type = Column(String(20), nullable=False, default="repair")
    suggested_parts = Column(Text, nullable=True)
    status = Column(String(20), nullable=False, default="open")
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)
