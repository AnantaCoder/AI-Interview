from sqlalchemy import Column, DateTime, Boolean, String
from sqlalchemy.sql import func
from datetime import datetime
import uuid

from app.db.session import Base


class TimestampMixin:
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class SoftDeleteMixin:
    is_active = Column(Boolean, default=True, nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)


class BaseModel(Base, TimestampMixin, SoftDeleteMixin):
    __abstract__ = True
    
    # Use String(36) for UUID — works on both SQLite and PostgreSQL
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    def to_dict(self) -> dict:
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
