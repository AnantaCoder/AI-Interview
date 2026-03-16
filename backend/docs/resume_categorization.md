# Resume Categorization Feature

## Overview
The Resume Categorization feature is an intelligent endpoint that automatically predicts the professional field or industry of a candidate based on the text contents of their resume. 

This helps recruiters and organizations instantly assign candidates to the correct talent pools (e.g., Engineering, HR, Finance) without manual sorting.

---

## 🚀 How It Works

1. **Text Cleaning**: When resume text is submitted, the system strips out unnecessary noise such as URLs, hashtags, mentions, special characters, and extra spaces.
2. **Feature Extraction**: The cleaned text is transformed into numerical data using a pre-trained **TF-IDF Vectorizer**.
3. **Classification**: This numerical data is fed into a **Gradient Boosting Classifier**, which predicts the most likely category from 24 different predefined industries.

---

## 🔌 API Endpoint

### `POST /api/v1/resume/predict-category`

**Request Body (JSON):**
```json
{
  "text": "Experienced web developer with 5 years working in Next.js, FastAPI, and Postgres. Strong problem-solving skills..."
}
```

**Response (JSON):**
```json
{
  "category": "INFORMATION-TECHNOLOGY"
}
```

---

## 🤖 Supported Categories
The model is trained to recognize the following 24 professional categories:

- ACCOUNTANT
- ADVOCATE
- AGRICULTURE
- APPAREL
- ARTS
- AUTOMOBILE
- AVIATION
- BANKING
- BPO
- BUSINESS-DEVELOPMENT
- CHEF
- CONSTRUCTION
- CONSULTANT
- DESIGNER
- DIGITAL-MEDIA
- ENGINEERING
- FINANCE
- FITNESS
- HEALTHCARE
- HR
- INFORMATION-TECHNOLOGY
- PUBLIC-RELATIONS
- SALES
- TEACHER

---

## 📁 Technical Locations

- **Router Endpoint**: `app/routers/resume.py`
- **Jupyter Notebook (Training logic)**: `machine_learning/resume_categorizer.ipynb`
- **Saved Models**: 
  - `machine_learning/saved_models/tfidf_vectorizer_categorization.pkl`
  - `machine_learning/saved_models/gb_classifier_categorization.pkl`
