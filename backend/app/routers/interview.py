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
            
        if interview.status not in (InterviewStatus.PENDING.value, InterviewStatus.IN_PROGRESS.value):
            raise HTTPException(status_code=400, detail="Interview is already completed or cancelled")
            
        # Update status and timestamp if it is still pending
        if interview.status == InterviewStatus.PENDING.value:
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
async def get_interview_questions(id: str, current_user: UserProfile = Depends(get_current_user)):
    """Fetch the list of questions for the interview."""
    session_maker = get_session_maker()
    async with session_maker() as session:
        result = await session.execute(
            select(Interview).where(Interview.id == id)
        )
        interview = result.scalar_one_or_none()
        
        if not interview:
            raise HTTPException(status_code=404, detail="Interview not found")
            
        # Verify access
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
                
        # Fetch questions for the job role
        questions_result = await session.execute(
            select(InterviewQuestion)
            .where(InterviewQuestion.job_role_id == interview.job_role_id)
            .order_by(InterviewQuestion.order_index.asc())
        )
        questions = questions_result.scalars().all()
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
        
        # --- FINAL SCORE CALCULATION (with proctoring integration) ---
        # Aggregate answer scores from all responses
        from app.db.models.interview import InterviewResponse as DBResp
        resp_result = await session.execute(
            select(DBResp).where(DBResp.interview_id == id)
        )
        responses = resp_result.scalars().all()
        
        if responses:
            avg_answer = sum(r.response_score or 0 for r in responses) / len(responses)
            # Normalize to 0-100 (max_score per question is 10)
            answer_quality = min(100.0, (avg_answer / 10.0) * 100)
        else:
            answer_quality = 0.0
        
        interview.interview_score = round(answer_quality, 1)
        
        # Load proctoring scores if available
        from app.db.models.interview import ProctorSession
        proctor_result = await session.execute(
            select(ProctorSession).where(ProctorSession.interview_id == id)
        )
        proctor = proctor_result.scalar_one_or_none()
        
        if proctor and proctor.total_frames > 0:
            # Full formula: 40% Answer + 20% Confidence + 20% Attention + 20% Integrity
            interview.final_score = round(
                0.40 * answer_quality +
                0.20 * proctor.confidence_score +
                0.20 * proctor.attention_score +
                0.20 * proctor.integrity_score,
                1
            )
            
            # Generate feedback based on proctoring
            feedback_parts = [f"Answer quality: {answer_quality:.0f}/100."]
            if proctor.attention_score < 60:
                feedback_parts.append(f"Attention was low ({proctor.attention_score:.0f}/100) — candidate frequently looked away.")
            if proctor.integrity_score < 80:
                feedback_parts.append(f"Integrity concerns ({proctor.integrity_score:.0f}/100) — possible external assistance detected.")
            if proctor.multi_person_count > 0:
                feedback_parts.append(f"Multiple persons detected in {proctor.multi_person_count} frames.")
            if proctor.confidence_score >= 70:
                feedback_parts.append(f"Confidence level was good ({proctor.confidence_score:.0f}/100).")
            interview.feedback = " ".join(feedback_parts)
        else:
            # No proctoring data — use answer quality only
            interview.final_score = round(
                (interview.ats_score or 0) * 0.3 + answer_quality * 0.7, 1
            )
            interview.feedback = f"Answer quality: {answer_quality:.0f}/100. No proctoring data available."
        # ---------------------------------------------------------------
        
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


@router.get("/{id}/proctor-results")
async def get_proctor_results(id: str, current_user: UserProfile = Depends(get_current_user)):
    """
    Fetch proctoring session results for an interview.
    Returns detailed CV metrics, signal counts, emotion distribution, and event log.
    Accessible by both candidate and organization.
    """
    from app.db.models.interview import ProctorSession
    
    session_maker = get_session_maker()
    async with session_maker() as session:
        # Verify interview exists
        int_result = await session.execute(select(Interview).where(Interview.id == id))
        interview = int_result.scalar_one_or_none()
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
        
        # Fetch proctor session
        result = await session.execute(
            select(ProctorSession).where(ProctorSession.interview_id == id)
        )
        proctor = result.scalar_one_or_none()
        
        if not proctor:
            raise HTTPException(status_code=404, detail="No proctoring data available for this interview")
        
        return {
            "interview_id": id,
            "total_frames": proctor.total_frames,
            "scores": {
                "confidence": proctor.confidence_score,
                "attention": proctor.attention_score,
                "integrity": proctor.integrity_score,
                "posture": proctor.posture_score,
            },
            "signal_counts": {
                "face_not_visible": proctor.face_not_visible_count,
                "gaze_away": proctor.gaze_away_count,
                "head_turn": proctor.head_turn_count,
                "multi_person": proctor.multi_person_count,
                "excessive_movement": proctor.excessive_movement_count,
            },
            "emotion_distribution": proctor.emotion_distribution,
            "event_log": proctor.event_log,
        }


@router.get("/{id}/responses", response_model=List[InterviewResponseDetail])
async def get_interview_responses(id: str, current_user: UserProfile = Depends(get_current_user)):
    """Fetch all submitted responses/answers for a specific interview."""
    session_maker = get_session_maker()
    async with session_maker() as session:
        # Verify interview exists
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
                
        # Fetch responses
        from app.db.models.interview import InterviewResponse as DBInterviewResponse
        responses_result = await session.execute(
            select(DBInterviewResponse).where(DBInterviewResponse.interview_id == id)
        )
        return responses_result.scalars().all()

