from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import joblib
import re
import os

router = APIRouter(
    prefix="/resume",
    tags=["Resume Analysis"]
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
models_dir = os.path.join(BASE_DIR, "machine_learning", "saved_models")

try:
    vectorizer = joblib.load(os.path.join(models_dir, "tfidf_vectorizer_categorization.pkl"))
    gb_classifier = joblib.load(os.path.join(models_dir, "gb_classifier_categorization.pkl"))
except Exception as e:
    vectorizer = None
    gb_classifier = None
    print(f"Failed to load resume categorization models: {e}")

CATEGORIES = [
    'ACCOUNTANT', 'ADVOCATE', 'AGRICULTURE', 'APPAREL', 'ARTS', 'AUTOMOBILE', 
    'AVIATION', 'BANKING', 'BPO', 'BUSINESS-DEVELOPMENT', 'CHEF', 'CONSTRUCTION', 
    'CONSULTANT', 'DESIGNER', 'DIGITAL-MEDIA', 'ENGINEERING', 'FINANCE', 'FITNESS', 
    'HEALTHCARE', 'HR', 'INFORMATION-TECHNOLOGY', 'PUBLIC-RELATIONS', 'SALES', 'TEACHER'
]

# Regex patterns for cleaning
url_pattern = re.compile(r'http\S*')
rt_cc_pattern = re.compile(r'\b(RT|cc)\b')
hashtag_pattern = re.compile(r'#\S*')
mention_pattern = re.compile(r'@\S+')
special_chars_pattern = re.compile(r'[%s]' % re.escape(r"""!"#$%&'()*+,-./:;<=>?@[\]^_`{|}~"""))
non_ascii_pattern = re.compile(r'[^\x00-\x7f]')
extra_spaces_pattern = re.compile(r'\s+')

def cleanResume(txt: str) -> str:
    txt = txt.lower()
    txt = url_pattern.sub(' ', txt)
    txt = rt_cc_pattern.sub(' ', txt)
    txt = hashtag_pattern.sub(' ', txt)
    txt = mention_pattern.sub(' ', txt)
    txt = special_chars_pattern.sub(' ', txt)
    txt = non_ascii_pattern.sub(' ', txt)
    txt = extra_spaces_pattern.sub(' ', txt).strip()
    return txt

class ResumeTextRequest(BaseModel):
    text: str

class ResumePredictionResponse(BaseModel):
    category: str

@router.post("/predict-category", response_model=ResumePredictionResponse)
async def predict_resume_category(request: ResumeTextRequest):
    if vectorizer is None or gb_classifier is None:
        raise HTTPException(status_code=500, detail="Models not loaded")
    
    clean_text = cleanResume(request.text)
    if not clean_text:
        raise HTTPException(status_code=400, detail="Resume text is empty after cleaning")
        
    try:
        tfidf_features = vectorizer.transform([clean_text])
        prediction = gb_classifier.predict(tfidf_features)[0]
        
        category = CATEGORIES[int(prediction)] if 0 <= int(prediction) < len(CATEGORIES) else "UNKNOWN"
        return {"category": category}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction error: {str(e)}")
