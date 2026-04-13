"""Расписание обслуживания по договорам (матрица договор × месяц)."""

from datetime import datetime
from sqlalchemy import Column, BigInteger, Integer, Text, DateTime, ForeignKey, UniqueConstraint
from app.database import Base


class ContractSchedule(Base):
    """Одна ячейка расписания: договор + год + месяц + заметка."""

    __tablename__ = "contract_schedule"
    __table_args__ = (
        UniqueConstraint("contract_id", "year", "month", name="uq_contract_schedule"),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    contract_id = Column(BigInteger, ForeignKey("contracts.id", ondelete="CASCADE"), nullable=False)
    year = Column(Integer, nullable=False)
    month = Column(Integer, nullable=False)  # 1–12
    note = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)
