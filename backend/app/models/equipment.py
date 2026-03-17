"""Модель оборудования на объекте."""

from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Text, BigInteger, Integer, ForeignKey
from app.database import Base


class Equipment(Base):
    __tablename__ = "equipment"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    site_id = Column(BigInteger, ForeignKey("sites.id", ondelete="CASCADE"), nullable=True)
    contract_id = Column(BigInteger, ForeignKey("contracts.id", ondelete="SET NULL"), nullable=True)
    brand = Column(String(200), nullable=True)
    quantity = Column(Integer, nullable=True)
    serial_numbers = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
