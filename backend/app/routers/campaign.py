from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from sqlalchemy import select
from app.db.session import get_session_maker
from app.deps import get_current_organization
from app.schemas.campaign import CampaignCreate, CampaignUpdate, CampaignResponse
from app.db.models.job_role import JobRole
from app.db.models.organization import Organization
from app.deps import get_current_candidate
from app.db.models.candidate import Candidate
from app.db.models.interview import Interview, InterviewStatus
from app.schemas.interview import InterviewResponse, GenerateQuestionsRequest, InterviewQuestionResponse
from app.schemas.campaign import CampaignApplicantResponse, ApplicantStatusUpdate
from app.db.models.interview import InterviewQuestion
from app.db.services.question_service import generate_questions_for_role
router = APIRouter(prefix="/campaigns", tags=["Campaigns"])

@router.get("/", response_model=List[CampaignResponse])
async def list_campaigns(org: Organization = Depends(get_current_organization)):
    session_maker = get_session_maker()
    async with session_maker() as session:
        result = await session.execute(
            select(JobRole).where(JobRole.organization_id == org.id)
        )
        campaigns = result.scalars().all()
        return campaigns

@router.post("/", response_model=CampaignResponse)
async def create_campaign(campaign: CampaignCreate, org: Organization = Depends(get_current_organization)):
    session_maker = get_session_maker()
    async with session_maker() as session:
        new_campaign = JobRole(
            organization_id=org.id,
            **campaign.model_dump()
        )
        session.add(new_campaign)
        await session.commit()
        await session.refresh(new_campaign)
        return new_campaign

@router.get("/{id}", response_model=CampaignResponse)
async def get_campaign(id: str, org: Organization = Depends(get_current_organization)):
    session_maker = get_session_maker()
    async with session_maker() as session:
        result = await session.execute(
            select(JobRole).where(JobRole.id == id, JobRole.organization_id == org.id)
        )
        campaign = result.scalar_one_or_none()
        if not campaign:
            raise HTTPException(status_code=404, detail="Campaign not found")
        return campaign

@router.patch("/{id}", response_model=CampaignResponse)
async def update_campaign(id: str, campaign_update: CampaignUpdate, org: Organization = Depends(get_current_organization)):
    session_maker = get_session_maker()
    async with session_maker() as session:
        result = await session.execute(
            select(JobRole).where(JobRole.id == id, JobRole.organization_id == org.id)
        )
        campaign = result.scalar_one_or_none()
        if not campaign:
            raise HTTPException(status_code=404, detail="Campaign not found")
            
        update_data = campaign_update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(campaign, key, value)
            
        await session.commit()
        await session.refresh(campaign)
        return campaign

@router.post("/{id}/apply", response_model=InterviewResponse)
async def apply_to_campaign(
    id: str, 
    candidate: Candidate = Depends(get_current_candidate)
):
    """Candidate applies to a campaign, creating an Interview record."""
    session_maker = get_session_maker()
    async with session_maker() as session:
        # Check if campaign exists
        result = await session.execute(select(JobRole).where(JobRole.id == id))
        campaign = result.scalar_one_or_none()
        if not campaign:
            raise HTTPException(status_code=404, detail="Campaign not found")
            
        # Check if already applied
        existing = await session.execute(
            select(Interview).where(
                Interview.candidate_id == candidate.id,
                Interview.job_role_id == id
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Already applied to this campaign")
            
        # Create Interview record
        interview = Interview(
            candidate_id=candidate.id,
            job_role_id=id,
            status=InterviewStatus.PENDING.value,
            ats_score=candidate.ats_score # Using candidate's base ATS score for now
        )
        session.add(interview)
        await session.commit()
        await session.refresh(interview)
        return interview

@router.get("/{id}/applicants", response_model=List[CampaignApplicantResponse])
async def get_campaign_applicants(
    id: str, 
    org: Organization = Depends(get_current_organization)
):
    """Organization fetches all candidates who applied to a specific campaign."""
    session_maker = get_session_maker()
    async with session_maker() as session:
        # Verify org owns this campaign
        result = await session.execute(
            select(JobRole).where(JobRole.id == id, JobRole.organization_id == org.id)
        )
        if not result.scalar_one_or_none():
            raise HTTPException(status_code=403, detail="Not authorized or campaign not found")
            
        # Fetch Interviews + Candidate data
        result = await session.execute(
            select(Interview, Candidate)
            .join(Candidate, Interview.candidate_id == Candidate.id)
            .where(Interview.job_role_id == id)
            .order_by(Interview.ats_score.desc().nullslast())
        )
        
        applicants = []
        for interview, candidate in result.all():
            applicants.append(
                CampaignApplicantResponse(
                    interview_id=str(interview.id),
                    status=interview.status,
                    ats_score=interview.ats_score,
                    interview_score=interview.interview_score,
                    final_score=interview.final_score,
                    is_shortlisted=interview.is_shortlisted,
                    applied_at=interview.created_at,
                    candidate=candidate
                )
            )
        return applicants

@router.patch("/{id}/applicants/{candidate_id}/status")
async def update_applicant_status(
    id: str,
    candidate_id: str,
    update_data: ApplicantStatusUpdate,
    org: Organization = Depends(get_current_organization)
):
    """Organization shortlists or updates status of a candidate."""
    session_maker = get_session_maker()
    async with session_maker() as session:
        # Verify org owns this campaign
        result = await session.execute(
            select(JobRole).where(JobRole.id == id, JobRole.organization_id == org.id)
        )
        if not result.scalar_one_or_none():
            raise HTTPException(status_code=403, detail="Not authorized or campaign not found")
            
        # Fetch the Interview record
        result = await session.execute(
            select(Interview).where(
                Interview.job_role_id == id,
                Interview.candidate_id == candidate_id
            )
        )
        interview = result.scalar_one_or_none()
        if not interview:
            raise HTTPException(status_code=404, detail="Applicant not found")
            
        if update_data.status is not None:
            interview.status = update_data.status
        if update_data.is_shortlisted is not None:
            interview.is_shortlisted = update_data.is_shortlisted
            
        await session.commit()
        await session.refresh(interview)
        return {"success": True, "message": "Applicant status updated"}


@router.post("/{id}/generate-questions", response_model=List[InterviewQuestionResponse])
async def generate_campaign_questions(
    id: str,
    request_data: GenerateQuestionsRequest,
    org: Organization = Depends(get_current_organization)
):
    """
    Generate questions with answers using Gemini AI and store them in the database.
    Only available to the campaign organizer (organization).
    """
    session_maker = get_session_maker()
    async with session_maker() as session:
        # Verify organization owns this campaign
        result = await session.execute(
            select(JobRole).where(JobRole.id == id, JobRole.organization_id == org.id)
        )
        campaign = result.scalar_one_or_none()
        if not campaign:
            raise HTTPException(status_code=404, detail="Campaign not found or unauthorized")

        # Generate questions via Gemini service
        try:
            generated_questions = await generate_questions_for_role(
                campaign,
                num_questions=request_data.num_questions,
                question_type=request_data.question_type,
                difficulty=request_data.difficulty
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to generate questions: {str(e)}")

        # Delete existing questions to avoid duplication
        from sqlalchemy import delete
        await session.execute(
            delete(InterviewQuestion).where(InterviewQuestion.job_role_id == id)
        )

        # Insert new questions into database
        for idx, q in enumerate(generated_questions):
            db_q = InterviewQuestion(
                job_role_id=id,
                question_text=q["question_text"],
                question_type=q["question_type"],
                expected_answer=q.get("expected_answer"),
                expected_answer_keywords=q.get("expected_answer_keywords", []),
                order_index=idx
            )
            session.add(db_q)

        await session.commit()

        # Query back the full list of saved questions
        result = await session.execute(
            select(InterviewQuestion)
            .where(InterviewQuestion.job_role_id == id)
            .order_by(InterviewQuestion.order_index.asc())
        )
        questions = result.scalars().all()
        return questions
