from sqlalchemy import Column, DateTime, Boolean, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from datetime import datetime
import uuid

from app.db.session import Base


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class SoftDeleteMixin:
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class BaseModel(Base, TimestampMixin, SoftDeleteMixin):
    __abstract__ = True
    
    # Use String(36) for UUID — works on both SQLite and PostgreSQL
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    def to_dict(self) -> dict:
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
