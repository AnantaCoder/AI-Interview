from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy import select
from typing import List
from app.db.session import get_session_maker
from app.deps import get_current_candidate
from app.schemas.candidate import CandidateResponse, CandidateUpdate, CandidateApplicationResponse
from app.db.models.candidate import Candidate
from app.db.models.interview import Interview
from app.db.models.job_role import JobRole
from app.config.logging import get_logger
import shutil
import os
import tempfile

UPLOAD_DIR = os.path.join(tempfile.gettempdir(), "candidate_resumes")
os.makedirs(UPLOAD_DIR, exist_ok=True)

logger = get_logger("routers.candidate")

router = APIRouter(
    prefix="/candidate",
    tags=["candidate"],
    
)

@router.get("/profile",response_model=CandidateResponse)
async def get_candidate_profile(
    candidate:Candidate=Depends(get_current_candidate)
):
    """fetch candidate profile data"""
    return candidate
    
@router.put("/profile",response_model=CandidateResponse)
async def update_candidate_profile(
    update_data:CandidateUpdate,
    candidate:Candidate=Depends(get_current_candidate)
):
    """
    update candidate profile data for authendated ones 
    """
    session_maker = get_session_maker()
    async with session_maker() as session:
        # reattach candidate to the session
        result = await session.execute(
            select(Candidate).where(Candidate.id==candidate.id)


        )
        db_candidate = result.scalar_one_or_none()
        if not db_candidate:
            raise HTTPException(status_code=404,detail="candidate not found")
        
        # apply only the updated fields 
        changes=update_data.model_dump(exclude_unset=True)
        for key,value in changes.items():
            setattr(db_candidate,key,value)
            
        await session.commit()
        await session.refresh(db_candidate)
        session.expunge(db_candidate)
        return db_candidate




@router.post("/resume/upload", response_model=CandidateResponse)
async def upload_resume(
    resume_file: UploadFile = File(...),
    candidate: Candidate = Depends(get_current_candidate),
):
    """
    Upload a resume file. The backend will:
    1. Extract text from the PDF/DOCX
    2. Classify the resume into a category (using the ML model)
    3. Auto-update the candidate's profile with extracted data
    """
    # --- 1. Save the file ---
    file_path = os.path.join(UPLOAD_DIR, f"{candidate.id}_{resume_file.filename}")
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(resume_file.file, buffer)

    try:
        # --- 2. Extract text (reuse your existing ATS service) ---
        from app.db.services.ats_service import extract_text
        extracted_text = extract_text(file_path)
        if not extracted_text:
            raise HTTPException(status_code=400, detail="Could not extract text from resume")

        # --- 3. Classify the resume (reuse your existing resume ML model) ---
        from app.routers.resume import cleanResume, vectorizer, gb_classifier, CATEGORIES
        category = None
        if vectorizer and gb_classifier:
            clean_text = cleanResume(extracted_text)
            tfidf_features = vectorizer.transform([clean_text])
            prediction = gb_classifier.predict(tfidf_features)[0]
            category = CATEGORIES[int(prediction)] if 0 <= int(prediction) < len(CATEGORIES) else None

        # --- 4. Update the candidate record ---
        session_maker = get_session_maker()
        async with session_maker() as session:
            result = await session.execute(
                select(Candidate).where(Candidate.id == candidate.id)
            )
            db_candidate = result.scalar_one_or_none()
            if not db_candidate:
                raise HTTPException(status_code=404, detail="Candidate not found")

            db_candidate.resume_url = file_path  # or a cloud URL if you add S3 later
            if category:
                db_candidate.resume_category = category

            await session.commit()
            await session.refresh(db_candidate)
            session.expunge(db_candidate)
            return db_candidate

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Resume upload failed: {e}")
        raise HTTPException(status_code=500, detail=f"Resume processing failed: {str(e)}")
    finally:
        # Clean up temp file (optional — remove if you want to keep it)
        try:
            os.remove(file_path)
        except Exception:
            pass


@router.get("/applications", response_model=List[CandidateApplicationResponse])
async def get_candidate_applications(
    candidate: Candidate = Depends(get_current_candidate),
):
    """Fetch all campaigns the candidate has applied to and their interview status."""
    from app.db.models.organization import Organization

    session_maker = get_session_maker()
    async with session_maker() as session:
        # Join Interview → JobRole → Organization to get all the data we need
        result = await session.execute(
            select(Interview, JobRole, Organization)
            .join(JobRole, Interview.job_role_id == JobRole.id)
            .join(Organization, JobRole.organization_id == Organization.id)
            .where(Interview.candidate_id == candidate.id)
            .order_by(Interview.created_at.desc())
        )
        rows = result.all()

        applications = []
        for interview, job_role, org in rows:
            applications.append(
                CandidateApplicationResponse(
                    interview_id=interview.id,
                    campaign_title=job_role.title,
                    organization_name=org.name,
                    status=interview.status,
                    applied_at=interview.created_at,
                    ats_score=interview.ats_score,
                    interview_score=interview.interview_score,
                    final_score=interview.final_score,
                    is_shortlisted=interview.is_shortlisted,
                )
            )

        return applications