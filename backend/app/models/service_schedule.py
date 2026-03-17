"""Модель расписания выездов (из Excel)."""

from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Date, BigInteger, ForeignKey
from app.database import Base


class ServiceSchedule(Base):
    __tablename__ = "service_schedule"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    contract_id = Column(BigInteger, ForeignKey("contracts.id", ondelete="CASCADE"), nullable=True)
    site_id = Column(BigInteger, ForeignKey("sites.id", ondelete="CASCADE"), nullable=True)
    scheduled_month = Column(Date, nullable=False)
    work_type = Column(String(50), nullable=True)
    work_type_raw = Column(String(200), nullable=True)
    visit_id = Column(BigInteger, ForeignKey("visits.id", ondelete="SET NULL"), nullable=True)
    status = Column(String(50), nullable=False, default="scheduled")
    is_historical = Column(Boolean, nullable=False, default=False)
    is_archived = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
