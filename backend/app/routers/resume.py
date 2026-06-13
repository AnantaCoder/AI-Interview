from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import joblib
import re
import os
import tensorflow as tf
from tensorflow.keras.models import load_model
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import PorterStemmer

# Ensure NLTK data is downloaded
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')
try:
    nltk.data.find('tokenizers/punkt_tab')
except LookupError:
    nltk.download('punkt_tab')
try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

router = APIRouter(
    prefix="/resume",
    tags=["Resume Analysis"]
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
models_dir = os.path.join(BASE_DIR, "classifier_model")

try:
    vectorizer = joblib.load(os.path.join(models_dir, "tfidf_vectorizer.pkl"))
    encoder = joblib.load(os.path.join(models_dir, "label_encoder.pkl"))
    model = load_model(os.path.join(models_dir, "my_text_classifier.keras"))
except Exception as e:
    vectorizer = None
    encoder = None
    model = None
    print(f"Failed to load resume categorization models: {e}")

def resume_cleaning(text: str) -> str:
    # Remove HTML tags 
    cleaned_text = re.sub(r'<.*?>', ' ', text)
    # Remove non-english characters, punctuation, digits, extra whitespace
    cleaned_text = re.sub('[^a-zA-Z]', ' ', cleaned_text)
    cleaned_text = re.sub(r'[^\w\s]|_', ' ', cleaned_text)
    cleaned_text = re.sub(r'\d+', ' ', cleaned_text)
    cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()
    cleaned_text = re.sub(r'http\S+\s', " ", cleaned_text)
    
    # Convert to lowercase
    cleaned_text = cleaned_text.lower()
    
    # Tokenize and remove stopwords
    words = word_tokenize(cleaned_text)
    stop_words = set(stopwords.words('english'))
    filtered_words = [word for word in words if word not in stop_words]
    
    # Apply stemming
    stemmer = PorterStemmer()
    stemmed_words = [stemmer.stem(word) for word in filtered_words]
    
    return ' '.join(stemmed_words)

class ResumeTextRequest(BaseModel):
    text: str

class ResumePredictionResponse(BaseModel):
    category: str

@router.post("/predict-category", response_model=ResumePredictionResponse)
async def predict_resume_category(request: ResumeTextRequest):
    if vectorizer is None or model is None or encoder is None:
        raise HTTPException(status_code=500, detail="Models not loaded")
    
    clean_text = resume_cleaning(request.text)
    if not clean_text:
        raise HTTPException(status_code=400, detail="Resume text is empty after cleaning")
        
    try:
        tfidf_features = vectorizer.transform([clean_text])
        if hasattr(tfidf_features, "toarray"):
            tfidf_features = tfidf_features.toarray()
            
        prediction_probs = model.predict(tfidf_features, verbose=0)
        predicted_index = prediction_probs.argmax(axis=1)
        
        category = encoder.inverse_transform(predicted_index)[0]
        return {"category": category}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction error: {str(e)}")
