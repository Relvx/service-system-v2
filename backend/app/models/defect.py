"""Модель дефекта, выявленного во время выезда."""

from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, ForeignKey, BigInteger
from app.database import Base


class Defect(Base):
    """Дефект, обнаруженный мастером на объекте.

    Привязан к выезду (Visit) и объекту (Site).
    Имеет тип действия (ремонт/замена/наблюдение) и статус жизненного цикла.
    Может порождать закупки (Purchase).
    """
    __tablename__ = "defects"
    __table_args__ = {"info": {"display_name": "Дефект", "display_name_plural": "Дефекты", "entity_type": "defect"}}

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    visit_id = Column(BigInteger, ForeignKey("visits.id", ondelete="CASCADE"), nullable=True)
    site_id = Column(BigInteger, ForeignKey("sites.id", ondelete="CASCADE"), nullable=True)
    title = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    priority = Column(String(20), nullable=False, default="medium")
    action_type = Column(String(20), nullable=False, default="repair")
    suggested_parts = Column(Text, nullable=True)
    status = Column(String(20), nullable=False, default="open")
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)
