from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Column, String, Text, Integer, Boolean, Float, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship, Mapped, mapped_column
from datetime import datetime
import enum

from app.db.models.base import BaseModel

if TYPE_CHECKING:
    from app.db.models.candidate import Candidate
    from app.db.models.job_role import JobRole


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
    
    candidate_id: Mapped[str] = mapped_column(String(36), ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False)
    job_role_id: Mapped[str] = mapped_column(String(36), ForeignKey("job_roles.id", ondelete="CASCADE"), nullable=False)
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_minutes: Mapped[int] = mapped_column(Integer, default=30)
    status: Mapped[str] = mapped_column(String(20), default=InterviewStatus.PENDING.value)
    
    # Scoring (ATS 30%, Interview 70%)
    ats_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    interview_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    final_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    is_shortlisted: Mapped[bool] = mapped_column(Boolean, default=False)
    feedback: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Video proctoring scores (populated when proctoring session ends)
    video_confidence_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    video_attention_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    video_integrity_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    
    # Relationships
    candidate: Mapped["Candidate"] = relationship("Candidate", back_populates="interviews")
    job_role: Mapped["JobRole"] = relationship("JobRole", back_populates="interviews")
    responses: Mapped[list["InterviewResponse"]] = relationship("InterviewResponse", back_populates="interview")
    
    def __repr__(self) -> str:
        return f"<Interview(id={self.id}, status={self.status})>"


class InterviewQuestion(BaseModel):
    __tablename__ = "interview_questions"
    
    job_role_id: Mapped[str] = mapped_column(String(36), ForeignKey("job_roles.id", ondelete="CASCADE"), nullable=False)
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    question_type: Mapped[str] = mapped_column(String(20), default=QuestionType.TECHNICAL.value)
    expected_answer_keywords: Mapped[list[str]] = mapped_column(JSON, default=[])
    expected_answer: Mapped[str | None] = mapped_column(Text, nullable=True)
    max_score: Mapped[float] = mapped_column(Float, default=10.0)
    order_index: Mapped[int] = mapped_column(Integer, default=0)
    
    # Relationships
    job_role: Mapped["JobRole"] = relationship("JobRole", back_populates="questions")
    responses: Mapped[list["InterviewResponse"]] = relationship("InterviewResponse", back_populates="question")
    
    def __repr__(self) -> str:
        return f"<InterviewQuestion(id={self.id}, type={self.question_type})>"


class InterviewResponse(BaseModel):
    __tablename__ = "interview_responses"
    
    interview_id: Mapped[str] = mapped_column(String(36), ForeignKey("interviews.id", ondelete="CASCADE"), nullable=False)
    question_id: Mapped[str] = mapped_column(String(36), ForeignKey("interview_questions.id", ondelete="CASCADE"), nullable=False)
    response_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    response_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    confidence_level: Mapped[float | None] = mapped_column(Float, nullable=True)
    relevance_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    cheating_detected: Mapped[bool] = mapped_column(Boolean, default=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Relationships
    interview: Mapped["Interview"] = relationship("Interview", back_populates="responses")
    question: Mapped["InterviewQuestion"] = relationship("InterviewQuestion", back_populates="responses")
    
    def __repr__(self) -> str:
        return f"<InterviewResponse(id={self.id}, score={self.response_score})>"


class ProctorSession(BaseModel):
    __tablename__ = "proctor_sessions"
    
    interview_id: Mapped[str] = mapped_column(String(36), ForeignKey("interviews.id", ondelete="CASCADE"), unique=True, nullable=False)
    total_frames: Mapped[int] = mapped_column(Integer, default=0)
    
    # Aggregated scores (0–100)
    confidence_score: Mapped[float] = mapped_column(Float, default=0.0)
    attention_score: Mapped[float] = mapped_column(Float, default=0.0)
    integrity_score: Mapped[float] = mapped_column(Float, default=0.0)
    posture_score: Mapped[float] = mapped_column(Float, default=0.0)
    
    # Detailed signal counters
    face_not_visible_count: Mapped[int] = mapped_column(Integer, default=0)
    gaze_away_count: Mapped[int] = mapped_column(Integer, default=0)
    head_turn_count: Mapped[int] = mapped_column(Integer, default=0)
    multi_person_count: Mapped[int] = mapped_column(Integer, default=0)
    excessive_movement_count: Mapped[int] = mapped_column(Integer, default=0)
    
    # Emotion breakdown (JSON: {"neutral": 45, "happy": 20, ...})
    emotion_distribution: Mapped[dict] = mapped_column(JSON, default=dict)
    
    # Detailed event log (JSON array of timestamped events)
    event_log: Mapped[list] = mapped_column(JSON, default=list)
    
    # Relationship
    interview: Mapped["Interview"] = relationship("Interview", backref="proctor_session", uselist=False)
    
    def __repr__(self) -> str:
        return f"<ProctorSession(interview_id={self.interview_id}, frames={self.total_frames})>"

