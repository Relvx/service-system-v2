"""SQLAlchemy models for all configuration / lookup tables."""

from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, BigInteger
from sqlalchemy.orm import relationship
from app.database import Base


class Role(Base):
    """Legacy role lookup — kept for seed data reference only."""
    __tablename__ = "roles"
    id = Column(Integer, primary_key=True)
    sysname = Column(String(50), unique=True)
    display_name = Column(String(100))
    default_redirect = Column(String(100), default="/dashboard")


class VisitStatus(Base):
    """Possible statuses for a visit (planned, in_progress, closed, cancelled)."""
    __tablename__ = "visit_statuses"
    id = Column(Integer, primary_key=True)
    sysname = Column(String(50), unique=True)
    display_name = Column(String(100))


class VisitType(Base):
    """Types of visit (maintenance, repair, inspection, emergency)."""
    __tablename__ = "visit_types"
    id = Column(Integer, primary_key=True)
    sysname = Column(String(50), unique=True)
    display_name = Column(String(100))


class Priority(Base):
    """Priority levels for visits and defects."""
    __tablename__ = "priorities"
    id = Column(Integer, primary_key=True)
    sysname = Column(String(50), unique=True)
    display_name = Column(String(100))
    sort_order = Column(Integer, default=0)


class DefectStatus(Base):
    """Possible statuses for a defect."""
    __tablename__ = "defect_statuses"
    id = Column(Integer, primary_key=True)
    sysname = Column(String(50), unique=True)
    display_name = Column(String(100))


class DefectActionType(Base):
    """Action types for resolving defects."""
    __tablename__ = "defect_action_types"
    id = Column(Integer, primary_key=True)
    sysname = Column(String(50), unique=True)
    display_name = Column(String(100))


class AttachmentKind(Base):
    """Categories for file attachments."""
    __tablename__ = "attachment_kinds"
    id = Column(Integer, primary_key=True)
    sysname = Column(String(50), unique=True)
    display_name = Column(String(100))


class PurchaseStatus(Base):
    """Workflow statuses for purchases."""
    __tablename__ = "purchase_statuses"
    id = Column(Integer, primary_key=True)
    sysname = Column(String(50), unique=True)
    display_name = Column(String(100))


class ServiceFrequency(Base):
    """Scheduled service frequency options for sites."""
    __tablename__ = "service_frequencies"
    id = Column(Integer, primary_key=True)
    sysname = Column(String(50), unique=True)
    display_name = Column(String(100))


class NotificationType(Base):
    """Notification type registry."""
    __tablename__ = "notification_types"
    id = Column(Integer, primary_key=True)
    sysname = Column(String(50), unique=True)
    display_name = Column(String(100))


# ─── Permission / RBAC tables ──────────────────────────────────────────────

class PermissionGroup(Base):
    """A named group of users that share a set of permissions (replaces roles)."""
    __tablename__ = "permission_groups"
    id = Column(Integer, primary_key=True)
    sysname = Column(String(50), unique=True, nullable=False)
    display_name = Column(String(100), nullable=False)
    default_redirect = Column(String(100), nullable=False, default="/dashboard")

    permissions = relationship(
        "Permission",
        secondary="permission_group_permissions",
        back_populates="groups",
        lazy="selectin",
    )
    users = relationship(
        "User",
        secondary="user_permission_groups",
        back_populates="groups",
        lazy="selectin",
    )


class Permission(Base):
    """A single permission e.g. 'visits:view', 'clients:create'."""
    __tablename__ = "permissions"
    id = Column(Integer, primary_key=True)
    sysname = Column(String(100), unique=True, nullable=False)
    display_name = Column(String(100), nullable=False)
    resource = Column(String(50), nullable=False)
    action = Column(String(20), nullable=False)

    groups = relationship(
        "PermissionGroup",
        secondary="permission_group_permissions",
        back_populates="permissions",
        lazy="selectin",
    )


class PermissionGroupPermission(Base):
    """Many-to-many link between PermissionGroup and Permission."""
    __tablename__ = "permission_group_permissions"
    group_id = Column(Integer, ForeignKey("permission_groups.id", ondelete="CASCADE"),
                      primary_key=True)
    permission_id = Column(Integer, ForeignKey("permissions.id", ondelete="CASCADE"),
                           primary_key=True)


class UserPermissionGroup(Base):
    """Many-to-many link between User and PermissionGroup."""
    __tablename__ = "user_permission_groups"
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    group_id = Column(Integer, ForeignKey("permission_groups.id", ondelete="CASCADE"),
                      primary_key=True)
