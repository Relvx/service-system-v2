"""Реестр типов документов — русские названия сущностей системы."""

from sqlalchemy import Column, String
from app.database import Base


class EntityType(Base):
    """Тип документа (сущности) с русским названием.

    Используется для отображения читаемых имён в журнале и фильтрах.
    Sysname соответствует значению entity_type в таблице logs.
    """
    __tablename__ = "entity_types"

    sysname              = Column(String(50), primary_key=True)
    display_name         = Column(String(100), nullable=False)
    display_name_plural  = Column(String(100), nullable=False)
