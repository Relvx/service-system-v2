import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Text, Float, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base


class Site(Base):
    __tablename__ = "sites"

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
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
