from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from typing import List
from datetime import datetime, timezone

from app.db.session import get_session_maker
from app.deps import get_current_user, get_current_candidate, get_current_organization
from app.schemas.auth import UserProfile
from app.schemas.interview import (
    InterviewResponse, 
    InterviewQuestionResponse, 
    InterviewResponseCreate, 
    InterviewResponseDetail
)
from app.db.models.interview import Interview, InterviewQuestion, InterviewResponse as DBInterviewResponse, InterviewStatus
from app.db.models.candidate import Candidate
from app.db.models.organization import Organization
from app.config.logging import get_logger

logger = get_logger("routers.interview")

router = APIRouter(prefix="/interviews", tags=["Interview"])

@router.get("/", response_model=List[InterviewResponse])
async def list_interviews(current_user: UserProfile = Depends(get_current_user)):
    """Fetch all interviews relevant to the user (Candidate or Organization)."""
    session_maker = get_session_maker()
    async with session_maker() as session:
        if current_user.user_type == "candidate":
            # Fetch interviews for this candidate
            result = await session.execute(
                select(Candidate).where(Candidate.user_id == current_user.id)
            )
            candidate = result.scalar_one_or_none()
            if not candidate:
                return []
            
            interviews_result = await session.execute(
                select(Interview).where(Interview.candidate_id == candidate.id).order_by(Interview.created_at.desc())
            )
            return interviews_result.scalars().all()
            
        elif current_user.user_type == "organization":
            # Fetch interviews for campaigns owned by this organization
            from app.db.models.job_role import JobRole
            result = await session.execute(
                select(Organization).where(Organization.user_id == current_user.id)
            )
            org = result.scalar_one_or_none()
            if not org:
                return []
            
            interviews_result = await session.execute(
                select(Interview)
                .join(JobRole, Interview.job_role_id == JobRole.id)
                .where(JobRole.organization_id == org.id)
                .order_by(Interview.created_at.desc())
            )
            return interviews_result.scalars().all()
            
        else:
            raise HTTPException(status_code=403, detail="Not authorized to view interviews")

@router.post("/{id}/start", response_model=InterviewResponse)
async def start_interview(id: str, candidate: Candidate = Depends(get_current_candidate)):
    """Candidate initiates the interview."""
    session_maker = get_session_maker()
    async with session_maker() as session:
        result = await session.execute(
            select(Interview).where(Interview.id == id, Interview.candidate_id == candidate.id)
        )
        interview = result.scalar_one_or_none()
        
        if not interview:
            raise HTTPException(status_code=404, detail="Interview not found")
            
        if interview.status != InterviewStatus.PENDING.value:
            raise HTTPException(status_code=400, detail="Interview is already started or completed")
            
        # Update status and timestamp
        interview.status = InterviewStatus.IN_PROGRESS.value
        interview.started_at = datetime.now(timezone.utc)
        
        # --- ML INTEGRATION STUB: INITIALIZE CHEATING DETECTION ---
        # Here you could trigger a websocket or background task to start monitoring the
        # candidate's video feed for head movements, eye tracking, etc.
        # logger.info(f"Started cheating detection monitor for interview {id}")
        # ----------------------------------------------------------
        
        await session.commit()
        await session.refresh(interview)
        return interview

@router.get("/{id}/questions", response_model=List[InterviewQuestionResponse])
async def get_interview_questions(id: str, candidate: Candidate = Depends(get_current_candidate)):
    """Fetch the list of questions for the interview."""
    session_maker = get_session_maker()
    async with session_maker() as session:
        # Verify interview ownership
        result = await session.execute(
            select(Interview).where(Interview.id == id, Interview.candidate_id == candidate.id)
        )
        interview = result.scalar_one_or_none()
        
        if not interview:
            raise HTTPException(status_code=404, detail="Interview not found")
            
        # Fetch questions for the job role
        questions_result = await session.execute(
            select(InterviewQuestion)
            .where(InterviewQuestion.job_role_id == interview.job_role_id)
            .order_by(InterviewQuestion.order_index.asc())
        )
        questions = questions_result.scalars().all()
        
        # --- ML INTEGRATION STUB: AI VOICE GENERATION ----------------------------------
        # When questions are fetched, the frontend might request the AI Voice.
        # Alternatively, you could pre-generate the Text-to-Speech audio URLs here
        # and attach them to the response schema.
        # -------------------------------------------------------------------------------        
        return questions

@router.post("/{id}/responses", response_model=InterviewResponseDetail)
async def submit_interview_response(
    id: str, 
    response_data: InterviewResponseCreate, 
    candidate: Candidate = Depends(get_current_candidate)
):
    """Candidate submits text/audio/video response for a specific question."""
    session_maker = get_session_maker()
    async with session_maker() as session:
        # Verify interview
        result = await session.execute(
            select(Interview).where(Interview.id == id, Interview.candidate_id == candidate.id)
        )
        interview = result.scalar_one_or_none()
        if not interview or interview.status != InterviewStatus.IN_PROGRESS.value:
            raise HTTPException(status_code=400, detail="Interview is not in progress")
            
        # Validate question belongs to this interview's role
        q_result = await session.execute(
            select(InterviewQuestion).where(
                InterviewQuestion.id == str(response_data.question_id), 
                InterviewQuestion.job_role_id == interview.job_role_id
            )
        )
        if not q_result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Question not found for this role")
        
        # Check if response already exists
        existing_res = await session.execute(
            select(DBInterviewResponse).where(
                DBInterviewResponse.interview_id == id,
                DBInterviewResponse.question_id == str(response_data.question_id)
            )
        )
        if existing_res.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Response already submitted for this question")
            
        # --- ML INTEGRATION STUB: ANSWER SCORING & CHEATING FLAGS ---
        # 1. Answer Scoring: Pass `response_data.response_text` to your LLM or NLP model 
        #    to generate `relevance_score`, `confidence_level`, and `response_score`.
        # 2. Cheating Detection: Analyze the video chunk / metrics sent from the frontend 
        #    to set `cheating_detected = True` if the candidate looked away frequently.
        #
        # For now, we stub these values:
        calculated_score = 8.5 # Example generated by AI
        cheating_flag = False  # Example generated by Computer Vision model
        ai_notes = "Candidate answered clearly with good structure."
        # -----------------------------------------------------------
        
        db_response = DBInterviewResponse(
            interview_id=id,
            question_id=str(response_data.question_id),
            response_text=response_data.response_text,
            response_score=calculated_score,
            confidence_level=90.0,
            relevance_score=85.0,
            cheating_detected=cheating_flag,
            notes=ai_notes
        )
        
        session.add(db_response)
        await session.commit()
        await session.refresh(db_response)
        return db_response

@router.post("/{id}/complete", response_model=InterviewResponse)
async def complete_interview(id: str, candidate: Candidate = Depends(get_current_candidate)):
    """Candidate finishes the interview."""
    session_maker = get_session_maker()
    async with session_maker() as session:
        result = await session.execute(
            select(Interview).where(Interview.id == id, Interview.candidate_id == candidate.id)
        )
        interview = result.scalar_one_or_none()
        
        if not interview or interview.status != InterviewStatus.IN_PROGRESS.value:
            raise HTTPException(status_code=400, detail="Interview is not in progress")
            
        interview.status = InterviewStatus.COMPLETED.value
        interview.completed_at = datetime.now(timezone.utc)
        
        # --- ML INTEGRATION STUB: FINAL SCORE CALCULATION ---
        # Aggregate the scores from all DBInterviewResponse records for this interview
        # Apply weighting (e.g., ATS 30%, Interview 70%) to calculate `final_score`.
        # Provide overall summary in `feedback`.
        # For now, stubbing:
        interview.interview_score = 85.0
        interview.final_score = (interview.ats_score or 0) * 0.3 + (interview.interview_score * 0.7)
        interview.feedback = "Overall performance was solid. No suspicious activities detected."
        # ----------------------------------------------------
        
        await session.commit()
        await session.refresh(interview)
        return interview

@router.get("/{id}/results", response_model=InterviewResponse)
async def get_interview_results(id: str, current_user: UserProfile = Depends(get_current_user)):
    """Fetch detailed AI feedback and results (Accessible by Candidate or Org)."""
    session_maker = get_session_maker()
    async with session_maker() as session:
        result = await session.execute(select(Interview).where(Interview.id == id))
        interview = result.scalar_one_or_none()
        
        if not interview:
            raise HTTPException(status_code=404, detail="Interview not found")
            
        # Verify access rights
        if current_user.user_type == "candidate":
            cand_res = await session.execute(select(Candidate).where(Candidate.user_id == current_user.id))
            cand = cand_res.scalar_one_or_none()
            if not cand or interview.candidate_id != cand.id:
                raise HTTPException(status_code=403, detail="Not authorized")
        elif current_user.user_type == "organization":
            from app.db.models.job_role import JobRole
            org_res = await session.execute(select(Organization).where(Organization.user_id == current_user.id))
            org = org_res.scalar_one_or_none()
            
            job_res = await session.execute(select(JobRole).where(JobRole.id == interview.job_role_id))
            job = job_res.scalar_one_or_none()
            
            if not org or not job or job.organization_id != org.id:
                raise HTTPException(status_code=403, detail="Not authorized")
                
        return interview
