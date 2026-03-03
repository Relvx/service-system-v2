"""User model — role column removed in migration 003, groups managed via permission_groups."""

from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, BigInteger
from sqlalchemy.orm import relationship
from app.database import Base


class User(Base):
    """Application user. Permissions are managed via PermissionGroup memberships."""
    __tablename__ = "users"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    phone = Column(String(50), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)

    groups = relationship(
        "PermissionGroup",
        secondary="user_permission_groups",
        back_populates="users",
        lazy="selectin",
    )
