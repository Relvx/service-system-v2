from sqlalchemy import Column, Integer, String, Boolean
from app.database import Base


class Role(Base):
    __tablename__ = "roles"
    id = Column(Integer, primary_key=True)
    code = Column(String(50), unique=True)
    display_name = Column(String(100))
    default_redirect = Column(String(100), default="/dashboard")


class VisitStatus(Base):
    __tablename__ = "visit_statuses"
    id = Column(Integer, primary_key=True)
    code = Column(String(50), unique=True)
    display_name = Column(String(100))
    color = Column(String(50), default="gray")


class VisitType(Base):
    __tablename__ = "visit_types"
    id = Column(Integer, primary_key=True)
    code = Column(String(50), unique=True)
    display_name = Column(String(100))


class Priority(Base):
    __tablename__ = "priorities"
    id = Column(Integer, primary_key=True)
    code = Column(String(50), unique=True)
    display_name = Column(String(100))
    color = Column(String(50), default="gray")
    sort_order = Column(Integer, default=0)


class DefectStatus(Base):
    __tablename__ = "defect_statuses"
    id = Column(Integer, primary_key=True)
    code = Column(String(50), unique=True)
    display_name = Column(String(100))
    color = Column(String(50), default="gray")


class DefectActionType(Base):
    __tablename__ = "defect_action_types"
    id = Column(Integer, primary_key=True)
    code = Column(String(50), unique=True)
    display_name = Column(String(100))


class AttachmentKind(Base):
    __tablename__ = "attachment_kinds"
    id = Column(Integer, primary_key=True)
    code = Column(String(50), unique=True)
    display_name = Column(String(100))


class PurchaseStatus(Base):
    __tablename__ = "purchase_statuses"
    id = Column(Integer, primary_key=True)
    code = Column(String(50), unique=True)
    display_name = Column(String(100))
    color = Column(String(50), default="gray")


class ServiceFrequency(Base):
    __tablename__ = "service_frequencies"
    id = Column(Integer, primary_key=True)
    code = Column(String(50), unique=True)
    display_name = Column(String(100))


class NotificationType(Base):
    __tablename__ = "notification_types"
    id = Column(Integer, primary_key=True)
    code = Column(String(50), unique=True)
    display_name = Column(String(100))
