from sqlalchemy import Column, String, Text, Integer, Boolean, Float, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship

from app.db.models.base import BaseModel


class JobRole(BaseModel):
    __tablename__ = "job_roles"
    
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    required_skills = Column(ARRAY(String), default=[])
    preferred_skills = Column(ARRAY(String), default=[])
    min_experience_years = Column(Integer, default=0)
    max_experience_years = Column(Integer, nullable=True)
    education_requirement = Column(String(255), nullable=True)
    salary_range_min = Column(Integer, nullable=True)
    salary_range_max = Column(Integer, nullable=True)
    location = Column(String(255), nullable=True)
    is_remote = Column(Boolean, default=False)
    cutoff_score = Column(Float, default=60.0)  # Score threshold for shortlisting
    
    # Relationships
    organization = relationship("Organization", back_populates="job_roles")
    interviews = relationship("Interview", back_populates="job_role", lazy="dynamic")
    questions = relationship("InterviewQuestion", back_populates="job_role", lazy="dynamic")
    
    def __repr__(self) -> str:
        return f"<JobRole(id={self.id}, title={self.title})>"
