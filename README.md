# AI-Powered Interview & ATS Platform

A full-stack monorepo project combining **Next.js** (frontend) and **FastAPI** (backend) to deliver AI-driven interview analysis and ATS (Applicant Tracking System) resume scoring.

## 🚀 Features

* **Real-time Interview Analysis**: Uses webcam video + AI emotion detection to assess candidate confidence and detect possible cheating.
* **ATS Resume Checker**: Parses resumes (PDF/DOCX) and compares them against job descriptions using NLP.
* **JWT Authentication**: Secure login and role-based admin panel for recruiters.
* **Admin Dashboard**: View candidate interview scores, flagged incidents, and ATS reports.
* **Scalable Architecture**: Follows a clean 3-tier / hexagonal architecture for maintainability.

## 🛠 Tech Stack

**Frontend**

* Next.js + React
* Tailwind CSS or Chakra UI
* `react-webcam` for video capture

**Backend**

* FastAPI (Python)
* OpenCV / MediaPipe (face detection)
* TensorFlow/Keras (Emo0.1 emotion model)
* spaCy, Transformers (NLP & keyword extraction)
* pdfplumber, python-docx (resume parsing)
* Scikit-learn (TF-IDF similarity)

**Auth & Storage**

* OAuth2 + JWT (FastAPI)
* Secure password hashing
* Database integration (PostgreSQL/MySQL)

## 📂 Project Structure

```
/frontend   # Next.js app (UI, webcam capture, admin panel)
/backend    # FastAPI API (video analysis, ATS scoring)
/shared     # Shared types/utilities (if using monorepo workspaces)
```

## ⚙️ Setup

1. **Clone the repo**

```bash
git clone <repo-url>
cd <project-folder>
```

2. **Install dependencies**

```bash
# Frontend
cd frontend
npm install

# Backend
cd ../backend
pip install -r requirements.txt
```

3. **Run the development servers**

```bash
# Frontend
npm run dev

# Backend
uvicorn main:app --reload
```

4. **Access**

* Frontend: `http://localhost:3000`
* Backend API: `http://localhost:8000`

## 📊 Core Endpoints

| Method | Endpoint                 | Description                    |
| ------ | ------------------------ | ------------------------------ |
| POST   | `/api/interview/analyze` | Analyze interview video frames |
| POST   | `/api/resume/analyze`    | Parse and score resumes        |
| POST   | `/token`                 | Obtain JWT for authentication  |

## 🧠 AI Models

* **Emo0.1** (FER2013-trained) for facial emotion recognition
* **BERT/DistilBERT** for semantic similarity in resumes
* TF-IDF & cosine similarity for keyword matching

## 🗺 Development Roadmap

1. Project setup (monorepo, basic dependencies)
2. Authentication module
3. Webcam UI & video endpoint
4. Resume parsing endpoint
5. AI integration (emotion + NLP)
6. Admin dashboard
7. Model fine-tuning & scaling


Copyright [2025] [Anirban Sarkar , Trina Das , Samanjan Sarkar , Ankan Palai]