"""Версионные таблицы — каждая строка хранит слепок записи на момент изменения.

Структура: поля оригинальной таблицы с префиксом v_ + служебные поля:
  v_date    — момент записи версии
  v_user_id — кто инициировал изменение
  v_method  — тип операции: create / update / delete
"""

from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Date, Time, Text, Float, Numeric, ForeignKey, BigInteger
from sqlalchemy.dialects.postgresql import JSONB
from app.database import Base


class ClientHistory(Base):
    """Версионная таблица клиентов.

    Фиксирует состояние записи clients до/после каждого изменения.
    """
    __tablename__ = "clients_history"

    id                = Column(BigInteger, primary_key=True, autoincrement=True)
    v_id              = Column(BigInteger,    nullable=True, index=True)
    v_name            = Column(Text,         nullable=True)
    v_inn             = Column(String(50),   nullable=True)
    v_kpp             = Column(String(50),   nullable=True)
    v_contacts        = Column(Text,         nullable=True)
    v_contact_person  = Column(String(255),  nullable=True)
    v_notes           = Column(Text,         nullable=True)
    v_is_active       = Column(Boolean,      nullable=True)
    v_created_at      = Column(DateTime,     nullable=True)
    v_updated_at      = Column(DateTime,     nullable=True)
    changed_at         = Column(DateTime, default=datetime.now, nullable=False)
    changed_by_user_id = Column(BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    method             = Column(String(20), nullable=False)


class SiteHistory(Base):
    """Версионная таблица объектов обслуживания (sites)."""
    __tablename__ = "sites_history"

    id                   = Column(BigInteger, primary_key=True, autoincrement=True)
    v_id                 = Column(BigInteger,    nullable=True, index=True)
    v_client_id          = Column(BigInteger,    nullable=True)
    v_title              = Column(Text,        nullable=True)
    v_address            = Column(Text,        nullable=True)
    v_latitude           = Column(Float,       nullable=True)
    v_longitude          = Column(Float,       nullable=True)
    v_access_notes       = Column(Text,        nullable=True)
    v_onsite_contact      = Column(Text,        nullable=True)
    v_service_frequency   = Column(String(30),  nullable=True)
    v_price_maintenance   = Column(Float,       nullable=True)
    v_price_repair        = Column(Float,       nullable=True)
    v_price_emergency     = Column(Float,       nullable=True)
    v_is_active           = Column(Boolean,     nullable=True)
    v_created_at         = Column(DateTime,    nullable=True)
    v_updated_at         = Column(DateTime,    nullable=True)
    changed_at         = Column(DateTime, default=datetime.now, nullable=False)
    changed_by_user_id = Column(BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    method             = Column(String(20), nullable=False)


class UserHistory(Base):
    """Версионная таблица пользователей.

    Пароль (v_password_hash) сохраняется для аудита; не выдаётся через API.
    """
    __tablename__ = "users_history"

    id             = Column(BigInteger, primary_key=True, autoincrement=True)
    v_id           = Column(BigInteger,    nullable=True, index=True)
    v_email        = Column(String(255), nullable=True)
    v_password_hash = Column(String(255), nullable=True)
    v_full_name    = Column(String(255), nullable=True)
    v_phone        = Column(String(50),  nullable=True)
    v_is_active    = Column(Boolean,     nullable=True)
    v_created_at   = Column(DateTime,    nullable=True)
    v_updated_at   = Column(DateTime,    nullable=True)
    changed_at         = Column(DateTime, default=datetime.now, nullable=False)
    changed_by_user_id = Column(BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    method             = Column(String(20), nullable=False)


class VisitHistory(Base):
    """Версионная таблица выездов (visits)."""
    __tablename__ = "visits_history"

    id                  = Column(BigInteger, primary_key=True, autoincrement=True)
    v_id                = Column(BigInteger,    nullable=True, index=True)
    v_site_id           = Column(BigInteger,    nullable=True)
    v_assigned_user_id  = Column(BigInteger,    nullable=True)
    v_planned_date      = Column(Date,      nullable=True)
    v_planned_time_from = Column(Time,      nullable=True)
    v_planned_time_to   = Column(Time,      nullable=True)
    v_visit_type        = Column(String(30), nullable=True)
    v_priority          = Column(String(20), nullable=True)
    v_status            = Column(String(20), nullable=True)
    v_work_summary      = Column(Text,       nullable=True)
    v_checklist         = Column(JSONB,      nullable=True)
    v_defects_present   = Column(Boolean,    nullable=True)
    v_defects_summary   = Column(Text,       nullable=True)
    v_recommendations   = Column(Text,       nullable=True)
    v_completed_at      = Column(DateTime,   nullable=True)
    v_office_notes      = Column(Text,       nullable=True)
    v_cost              = Column(Float,      nullable=True)
    v_created_at        = Column(DateTime,   nullable=True)
    v_updated_at        = Column(DateTime,   nullable=True)
    changed_at         = Column(DateTime, default=datetime.now, nullable=False)
    changed_by_user_id = Column(BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    method             = Column(String(20), nullable=False)


class PurchaseHistory(Base):
    """Версионная таблица закупок (purchases)."""
    __tablename__ = "purchases_history"

    id           = Column(BigInteger, primary_key=True, autoincrement=True)
    v_id         = Column(BigInteger,    nullable=True, index=True)
    v_defect_id  = Column(BigInteger,    nullable=True)
    v_site_id    = Column(BigInteger,    nullable=True)
    v_item       = Column(Text,        nullable=True)
    v_qty        = Column(Numeric,     nullable=True)
    v_status     = Column(String(20),  nullable=True)
    v_due_date   = Column(Date,        nullable=True)
    v_notes      = Column(Text,        nullable=True)
    v_created_at = Column(DateTime,    nullable=True)
    v_updated_at = Column(DateTime,    nullable=True)
    changed_at         = Column(DateTime, default=datetime.now, nullable=False)
    changed_by_user_id = Column(BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    method             = Column(String(20), nullable=False)
