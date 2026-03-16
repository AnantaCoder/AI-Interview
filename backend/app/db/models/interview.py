from sqlalchemy import Column, String, Text, Integer, Boolean, Float, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship
import enum

from app.db.models.base import BaseModel


class InterviewStatus(str, enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class QuestionType(str, enum.Enum):
    TECHNICAL = "technical"
    BEHAVIORAL = "behavioral"
    SITUATIONAL = "situational"


class Interview(BaseModel):
    __tablename__ = "interviews"
    
    candidate_id = Column(String(36), ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False)
    job_role_id = Column(String(36), ForeignKey("job_roles.id", ondelete="CASCADE"), nullable=False)
    scheduled_at = Column(DateTime(timezone=True), nullable=True)
    duration_minutes = Column(Integer, default=30)
    status = Column(String(20), default=InterviewStatus.PENDING.value)
    
    # Scoring (ATS 30%, Interview 70%)
    ats_score = Column(Float, nullable=True)
    interview_score = Column(Float, nullable=True)
    final_score = Column(Float, nullable=True)
    is_shortlisted = Column(Boolean, default=False)
    feedback = Column(Text, nullable=True)
    
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    candidate = relationship("Candidate", back_populates="interviews")
    job_role = relationship("JobRole", back_populates="interviews")
    responses = relationship("InterviewResponse", back_populates="interview")
    
    def __repr__(self) -> str:
        return f"<Interview(id={self.id}, status={self.status})>"


class InterviewQuestion(BaseModel):
    __tablename__ = "interview_questions"
    
    job_role_id = Column(String(36), ForeignKey("job_roles.id", ondelete="CASCADE"), nullable=False)
    question_text = Column(Text, nullable=False)
    question_type = Column(String(20), default=QuestionType.TECHNICAL.value)
    expected_answer_keywords = Column(JSON, default=[])
    max_score = Column(Float, default=10.0)
    order_index = Column(Integer, default=0)
    
    # Relationships
    job_role = relationship("JobRole", back_populates="questions")
    responses = relationship("InterviewResponse", back_populates="question")
    
    def __repr__(self) -> str:
        return f"<InterviewQuestion(id={self.id}, type={self.question_type})>"


class InterviewResponse(BaseModel):
    __tablename__ = "interview_responses"
    
    interview_id = Column(String(36), ForeignKey("interviews.id", ondelete="CASCADE"), nullable=False)
    question_id = Column(String(36), ForeignKey("interview_questions.id", ondelete="CASCADE"), nullable=False)
    response_text = Column(Text, nullable=True)
    response_score = Column(Float, nullable=True)
    confidence_level = Column(Float, nullable=True)
    relevance_score = Column(Float, nullable=True)
    cheating_detected = Column(Boolean, default=False)
    notes = Column(Text, nullable=True)
    
    # Relationships
    interview = relationship("Interview", back_populates="responses")
    question = relationship("InterviewQuestion", back_populates="responses")
    
    def __repr__(self) -> str:
        return f"<InterviewResponse(id={self.id}, score={self.response_score})>"
