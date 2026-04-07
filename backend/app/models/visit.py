"""Модель выезда — основная рабочая единица системы."""

from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Date, Time, Text, Float, ForeignKey, BigInteger, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, ARRAY
from app.database import Base


class VisitMaster(Base):
    """Связь выезда с мастером (many-to-many).

    Позволяет назначать несколько мастеров на один выезд.
    assigned_user_id на Visit хранит основного мастера для уведомлений.
    """
    __tablename__ = "visit_masters"
    __table_args__ = (
        UniqueConstraint("visit_id", "user_id", name="uq_visit_masters"),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    visit_id = Column(BigInteger, ForeignKey("visits.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)


class Visit(Base):
    """Выезд мастера на объект.

    Содержит плановую дату/время, тип работ, приоритет и статус.
    После завершения хранит итоги работ, чек-лист и рекомендации.
    Связан с объектом (Site) и назначенным мастером (User).
    """
    __tablename__ = "visits"
    __table_args__ = {"info": {"display_name": "Выезд", "display_name_plural": "Выезды", "entity_type": "visit"}}

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    site_id = Column(BigInteger, ForeignKey("sites.id", ondelete="CASCADE"), nullable=True)
    assigned_user_id = Column(BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    planned_date = Column(Date, nullable=False)
    planned_time_from = Column(Time, nullable=True)
    planned_time_to = Column(Time, nullable=True)
    visit_type = Column(String(30), nullable=False, default="maintenance")
    visit_types = Column(ARRAY(String(30)), nullable=True)  # множественные типы; если NULL — используется visit_type
    priority = Column(String(20), nullable=False, default="medium")
    status = Column(String(20), nullable=False, default="planned")
    work_summary = Column(Text, nullable=True)
    checklist = Column(JSONB, nullable=True)
    defects_present = Column(Boolean, default=False, nullable=False)
    defects_summary = Column(Text, nullable=True)
    recommendations = Column(Text, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    office_notes = Column(Text, nullable=True)
    cost = Column(Float, nullable=True)
    contract_id = Column(BigInteger, ForeignKey("contracts.id", ondelete="SET NULL"), nullable=True)
    master_name_raw = Column(String(100), nullable=True)
    is_archived = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)
