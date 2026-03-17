"""Модель договора и связующей таблицы договор-объект."""

from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Date, Text, BigInteger, ForeignKey, Numeric, UniqueConstraint
from app.database import Base


class Contract(Base):
    """Договор с клиентом.

    Один договор может охватывать несколько объектов (через ContractSite).
    """
    __tablename__ = "contracts"
    __table_args__ = {
        "info": {"display_name": "Договор", "display_name_plural": "Договоры", "entity_type": "contract"}
    }

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    client_id = Column(BigInteger, ForeignKey("clients.id", ondelete="SET NULL"), nullable=True)
    contract_number = Column(String(255), nullable=True)
    contract_date = Column(Date, nullable=True)
    subject = Column(Text, nullable=True)
    amount = Column(Numeric(10, 2), nullable=True)
    act_amount = Column(Numeric(10, 2), nullable=True)
    status = Column(String(50), nullable=False, default="active")
    notes = Column(Text, nullable=True)
    is_archived = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)


class ContractSite(Base):
    """Связь договор — объект (многие ко многим)."""

    __tablename__ = "contract_sites"
    __table_args__ = (
        UniqueConstraint("contract_id", "site_id", name="uq_contract_sites"),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    contract_id = Column(BigInteger, ForeignKey("contracts.id", ondelete="CASCADE"), nullable=False)
    site_id = Column(BigInteger, ForeignKey("sites.id", ondelete="CASCADE"), nullable=False)
