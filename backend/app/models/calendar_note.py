from datetime import datetime
from sqlalchemy import BigInteger, Column, Date, DateTime, ForeignKey, Text

from app.database import Base


class CalendarNote(Base):
    __tablename__ = "calendar_notes"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    date = Column(Date, nullable=False)
    text = Column(Text, nullable=False)
    created_by_user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)
