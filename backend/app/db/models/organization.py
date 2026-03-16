from sqlalchemy import Column, String, Text, ForeignKey
from sqlalchemy.orm import relationship

from app.db.models.base import BaseModel


class Organization(BaseModel):
    __tablename__ = "organizations"
    
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    website = Column(String(500), nullable=True)
    industry = Column(String(100), nullable=True)
    logo_url = Column(String(500), nullable=True)
    contact_email = Column(String(255), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="organization")
    job_roles = relationship("JobRole", back_populates="organization")
    
    def __repr__(self) -> str:
        return f"<Organization(id={self.id}, name={self.name})>"
