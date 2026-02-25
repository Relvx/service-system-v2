import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Date, Time, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.database import Base


class Visit(Base):
    __tablename__ = "visits"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    site_id = Column(UUID(as_uuid=True), ForeignKey("sites.id", ondelete="CASCADE"), nullable=True)
    assigned_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    planned_date = Column(Date, nullable=False)
    planned_time_from = Column(Time, nullable=True)
    planned_time_to = Column(Time, nullable=True)
    visit_type = Column(String(30), nullable=False, default="maintenance")
    priority = Column(String(20), nullable=False, default="medium")
    status = Column(String(20), nullable=False, default="planned")
    work_summary = Column(Text, nullable=True)
    checklist = Column(JSONB, nullable=True)
    defects_present = Column(Boolean, default=False, nullable=False)
    defects_summary = Column(Text, nullable=True)
    recommendations = Column(Text, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    office_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)
