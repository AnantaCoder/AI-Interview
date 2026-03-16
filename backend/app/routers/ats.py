from fastapi import APIRouter, UploadFile, File, Form, HTTPException
import shutil
import os
from typing import Optional

from app.db.services.ats_service import extract_text, get_ats_score

router = APIRouter(
    prefix="/ats",
    tags=["ATS Scanner"]
)

import tempfile

UPLOAD_DIR = os.path.join(tempfile.gettempdir(), "ats_uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/evaluate")
async def evaluate_resume(
    resume_file: UploadFile = File(...),
    job_desc_file: Optional[UploadFile] = File(None),
    job_desc_text: Optional[str] = Form(None)
):
    """
    Evaluates a resume against a job description using Gemini AI.
    Provide either a `job_desc_file` or raw `job_desc_text`.
    """
    if not job_desc_file and not job_desc_text:
        raise HTTPException(
            status_code=400, 
            detail="You must provide either a job description file or job description text."
        )

    # 1. Save and extract Resume
    resume_path = os.path.join(UPLOAD_DIR, resume_file.filename)
    with open(resume_path, "wb") as buffer:
        shutil.copyfileobj(resume_file.file, buffer)
    
    extracted_resume_text = extract_text(resume_path)
    if not extracted_resume_text:
        raise HTTPException(status_code=400, detail="Failed to extract text from resume.")

    # 2. Save and extract JD
    extracted_jd_text = ""
    if job_desc_file:
        jd_path = os.path.join(UPLOAD_DIR, job_desc_file.filename)
        with open(jd_path, "wb") as buffer:
            shutil.copyfileobj(job_desc_file.file, buffer)
        extracted_jd_text = extract_text(jd_path)
    else:
        extracted_jd_text = job_desc_text
        
    if not extracted_jd_text:
         raise HTTPException(status_code=400, detail="Failed to collect job description text.")

    # 3. Call Service
    result = get_ats_score(extracted_resume_text, extracted_jd_text)

    # Cleanup temp files
    try:
        os.remove(resume_path)
        if job_desc_file:
            os.remove(jd_path)
    except Exception:
        pass

    if isinstance(result, dict) and "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])

    return result
