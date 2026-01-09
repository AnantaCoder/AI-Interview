from sqlalchemy import Column, String, Text, Integer, ForeignKey, Float
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship

from app.db.models.base import BaseModel


class Candidate(BaseModel):
    __tablename__ = "candidates"
    
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    email = Column(String(255), nullable=False, index=True)
    full_name = Column(String(255), nullable=False)
    phone = Column(String(20), nullable=True)
    education = Column(Text, nullable=True)
    experience_years = Column(Integer, default=0)
    skills = Column(ARRAY(String), default=[])
    resume_url = Column(String(500), nullable=True)
    linkedin_url = Column(String(500), nullable=True)
    portfolio_url = Column(String(500), nullable=True)
    
    # ATS scoring
    ats_score = Column(Float, nullable=True)
    resume_category = Column(String(100), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="candidate")
    interviews = relationship("Interview", back_populates="candidate", lazy="dynamic")
    
    def __repr__(self) -> str:
        return f"<Candidate(id={self.id}, name={self.full_name})>"
