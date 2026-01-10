from sqlalchemy import Column, String, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum

from app.db.models.base import BaseModel


class UserType(str, enum.Enum):
    ORGANIZATION = "organization"
    CANDIDATE = "candidate"
    ADMIN = "admin"


class User(BaseModel):
    __tablename__ = "users"
    
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=True)  # Nullable for OAuth users
    full_name = Column(String(255), nullable=True)
    avatar_url = Column(String(500), nullable=True)
    user_type = Column(Enum(UserType), nullable=False)
    
    # OAuth fields
    provider = Column(String(50), nullable=True)  # google, email, etc.
    provider_id = Column(String(255), nullable=True)
    
    # Email verification
    email_verified = Column(String(1), default="N")
    
    # Relationships
    organization = relationship("Organization", back_populates="user", uselist=False)
    candidate = relationship("Candidate", back_populates="user", uselist=False)
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email}, type={self.user_type})>"
