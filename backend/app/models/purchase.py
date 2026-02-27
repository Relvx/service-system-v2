"""Модель закупки запасных частей или материалов."""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, Date, Numeric, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base


class Purchase(Base):
    """Закупка материала или запчасти для устранения дефекта.

    Привязана к дефекту (Defect) и объекту (Site).
    Проходит статусы: черновик → согласовано → заказано → получено → установлено → закрыто.
    """
    __tablename__ = "purchases"
    __table_args__ = {"info": {"display_name": "Закупка", "display_name_plural": "Закупки", "entity_type": "purchase"}}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    defect_id = Column(UUID(as_uuid=True), ForeignKey("defects.id", ondelete="CASCADE"), nullable=True)
    site_id = Column(UUID(as_uuid=True), ForeignKey("sites.id", ondelete="SET NULL"), nullable=True)
    item = Column(Text, nullable=False)
    qty = Column(Numeric, default=1, nullable=False)
    status = Column(String(20), nullable=False, default="draft")
    due_date = Column(Date, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)
