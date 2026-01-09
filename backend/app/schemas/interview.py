from pydantic import Field
from typing import Optional, Literal
from uuid import UUID
from datetime import datetime

from app.schemas.base import AppBaseModel, TimestampMixin, IdMixin


class InterviewBase(AppBaseModel):
    scheduled_at: Optional[datetime] = Field(default=None, description="Scheduled interview time")
    duration_minutes: int = Field(default=30, ge=5, le=180, description="Interview duration")
    status: Literal["pending", "in_progress", "completed", "cancelled"] = Field(default="pending")


class InterviewCreate(InterviewBase):
    candidate_id: UUID = Field(..., description="Candidate ID")
    job_role_id: UUID = Field(..., description="Job role ID")


class InterviewUpdate(AppBaseModel):
    scheduled_at: Optional[datetime] = None
    duration_minutes: Optional[int] = Field(default=None, ge=5, le=180)
    status: Optional[Literal["pending", "in_progress", "completed", "cancelled"]] = None
    ats_score: Optional[float] = Field(default=None, ge=0, le=100)
    interview_score: Optional[float] = Field(default=None, ge=0, le=100)
    final_score: Optional[float] = Field(default=None, ge=0, le=100)
    is_shortlisted: Optional[bool] = None
    feedback: Optional[str] = None


class InterviewResponse(InterviewBase, IdMixin, TimestampMixin):
    candidate_id: UUID
    job_role_id: UUID
    ats_score: Optional[float] = Field(default=None, description="ATS score (30% weight)")
    interview_score: Optional[float] = Field(default=None, description="Interview score (70% weight)")
    final_score: Optional[float] = Field(default=None, description="Final combined score")
    is_shortlisted: bool = Field(default=False, description="Whether candidate is shortlisted")
    feedback: Optional[str] = Field(default=None, description="Interview feedback")
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class InterviewQuestionBase(AppBaseModel):
    question_text: str = Field(..., description="Interview question")
    question_type: Literal["technical", "behavioral", "situational"] = Field(default="technical")
    expected_answer_keywords: Optional[list[str]] = Field(default_factory=list)
    max_score: float = Field(default=10.0, ge=0)
    order_index: int = Field(default=0, ge=0)


class InterviewQuestionCreate(InterviewQuestionBase):
    job_role_id: UUID = Field(..., description="Associated job role")


class InterviewQuestionResponse(InterviewQuestionBase, IdMixin, TimestampMixin):
    job_role_id: UUID


class InterviewResponseBase(AppBaseModel):
    response_text: Optional[str] = Field(default=None, description="Candidate's response")
    response_score: Optional[float] = Field(default=None, ge=0, description="Score for this response")
    confidence_level: Optional[float] = Field(default=None, ge=0, le=100, description="Confidence level")
    relevance_score: Optional[float] = Field(default=None, ge=0, le=100, description="Answer relevance")
    cheating_detected: bool = Field(default=False, description="Whether cheating was detected")
    notes: Optional[str] = Field(default=None, description="AI analysis notes")


class InterviewResponseCreate(InterviewResponseBase):
    interview_id: UUID = Field(..., description="Interview ID")
    question_id: UUID = Field(..., description="Question ID")


class InterviewResponseDetail(InterviewResponseBase, IdMixin, TimestampMixin):
    interview_id: UUID
    question_id: UUID
