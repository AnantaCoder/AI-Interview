# ML Integration Guide — AI Interview Analysis

This document is a comprehensive blueprint for integrating Machine Learning models and AI features into the interview workflow. It covers the full data flow from frontend to backend and explains exactly where each model plugs in.

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Interview Data Flow (Step-by-Step)](#2-interview-data-flow-step-by-step)
3. [Frontend Integration](#3-frontend-integration)
4. [Backend Integration Points](#4-backend-integration-points)
5. [ML Models to Implement](#5-ml-models-to-implement)
6. [WebSocket Architecture (Real-time Cheating Detection)](#6-websocket-architecture-real-time-cheating-detection)
7. [File Reference Map](#7-file-reference-map)

---

## 1. Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                          FRONTEND (React)                          │
│                                                                     │
│  ┌──────────┐   ┌──────────────┐   ┌──────────────┐               │
│  │  Camera   │──►│ Head/Eye     │──►│ WebSocket    │──── ws:// ────┐│
│  │  Feed     │   │ Tracking     │   │ Client       │              ││
│  └──────────┘   └──────────────┘   └──────────────┘              ││
│                                                                     ││
│  ┌──────────┐   ┌──────────────┐   ┌──────────────┐              ││
│  │  AI Voice │◄──│ TTS Engine   │◄──│ Questions    │◄── REST ──┐ ││
│  │  Speaker  │   │ (Browser API)│   │ from Backend │           │ ││
│  └──────────┘   └──────────────┘   └──────────────┘           │ ││
│                                                                  │ ││
│  ┌──────────────────────────────────┐                           │ ││
│  │  Speech-to-Text (Browser API)    │── answer text ──► REST ──┘ ││
│  └──────────────────────────────────┘                            ││
└──────────────────────────────────────────────────────────────────┘│
                                                                     │
┌────────────────────────────────────────────────────────────────────┘
│
▼
┌─────────────────────────────────────────────────────────────────────┐
│                       BACKEND (FastAPI)                             │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  routers/interview.py                                        │  │
│  │                                                              │  │
│  │  POST /{id}/start       → Start interview, init monitoring   │  │
│  │  GET  /{id}/questions   → Return questions (+ TTS audio?)    │  │
│  │  POST /{id}/responses   → Score answer, check cheating       │  │
│  │  POST /{id}/complete    → Calculate final score              │  │
│  │  GET  /{id}/results     → Return full report                 │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                          │                                          │
│                          ▼                                          │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  ML Services Layer                                           │  │
│  │                                                              │  │
│  │  services/answer_scorer.py     → LLM/NLP answer evaluation   │  │
│  │  services/cheating_detector.py → OpenCV head/eye tracking     │  │
│  │  services/tts_service.py       → Text-to-Speech generation    │  │
│  │  services/question_generator.py→ AI question generation       │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                          │                                          │
│                          ▼                                          │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  Database (SQLite / PostgreSQL)                              │  │
│  │                                                              │  │
│  │  interviews, interview_questions, interview_responses        │  │
│  └──────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 2. Interview Data Flow (Step-by-Step)

This is the exact sequence of events from the moment a candidate clicks **"Start Interview"** to **"Finish"**.

### Step 1: Candidate Clicks "Start Interview"
```
Frontend → POST /api/v1/interviews/{id}/start
```
- Backend updates `interview.status = "in_progress"` and sets `started_at`.
- **[FUTURE]** Backend initializes a WebSocket room for real-time cheating detection.
- Frontend activates the camera and begins local head/eye tracking.

### Step 2: Load Questions
```
Frontend → GET /api/v1/interviews/{id}/questions
```
- Backend returns the list of `InterviewQuestion` objects for the job role.
- Frontend uses the **Web Speech API** (`SpeechSynthesis`) to read each question aloud to the candidate via an AI voice.
- Questions are displayed one at a time on the screen.

### Step 3: Candidate Answers Each Question
```
Frontend → POST /api/v1/interviews/{id}/responses
         Body: { interview_id, question_id, response_text }
```
- The frontend uses the **Web Speech API** (`SpeechRecognition`) to convert the candidate's spoken answer to text.
- Backend receives the text and:
  1. **[FUTURE]** Passes it to the `answer_scorer.py` service for NLP/LLM scoring.
  2. **[FUTURE]** Checks the cheating flags accumulated during the question.
  3. Saves the `InterviewResponse` record with all scores.
- This repeats for every question.

### Step 4: Candidate Finishes
```
Frontend → POST /api/v1/interviews/{id}/complete
```
- Backend sets `interview.status = "completed"` and `completed_at`.
- **[FUTURE]** Backend aggregates all response scores into a final `interview_score`.
- Calculates `final_score = (ats_score * 0.3) + (interview_score * 0.7)`.
- Generates a text `feedback` summary.

### Step 5: View Results
```
Frontend → GET /api/v1/interviews/{id}/results
```
- Returns the interview object with `final_score`, `feedback`, `is_shortlisted`, etc.
- **[FUTURE]** A separate endpoint could return per-question breakdowns from `interview_responses`.

---

## 3. Frontend Integration

### 3.1 Camera Access & Head Tracking

Use the browser `getUserMedia` API to access the webcam:

```javascript
// Start camera
const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
videoElement.srcObject = stream;
```

For head/eye tracking, you have two options:

**Option A: Client-side with TensorFlow.js (Recommended for lower latency)**
```javascript
import * as faceLandmarksDetection from '@tensorflow-models/face-landmarks-detection';

const model = await faceLandmarksDetection.load(
  faceLandmarksDetection.SupportedPackages.mediapipeFacemesh
);

// In your animation loop:
const predictions = await model.estimateFaces({ input: videoElement });
// Extract eye positions, head tilt, gaze direction from `predictions`
// If gaze deviates beyond threshold → flag as potential cheating
```

**Option B: Server-side with OpenCV (Better accuracy, higher latency)**
- Capture video frames periodically (every 2-3 seconds).
- Send frames to the backend via WebSocket or as base64 in a REST call.
- Backend runs OpenCV / dlib face detection and returns cheating flags.

### 3.2 AI Voice (Text-to-Speech)

Use the built-in browser Speech Synthesis API:

```javascript
function speakQuestion(questionText) {
  const utterance = new SpeechSynthesisUtterance(questionText);
  utterance.rate = 0.9;   // Slightly slower for clarity
  utterance.pitch = 1.0;
  utterance.lang = 'en-US';
  speechSynthesis.speak(utterance);
  
  return new Promise(resolve => {
    utterance.onend = resolve;
  });
}
```

### 3.3 Speech-to-Text (Candidate's Answer)

```javascript
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
const recognition = new SpeechRecognition();
recognition.continuous = true;
recognition.interimResults = true;
recognition.lang = 'en-US';

let finalTranscript = '';
recognition.onresult = (event) => {
  for (let i = event.resultIndex; i < event.results.length; i++) {
    if (event.results[i].isFinal) {
      finalTranscript += event.results[i][0].transcript;
    }
  }
};

recognition.start();
// When candidate finishes answering:
// recognition.stop();
// Submit `finalTranscript` to POST /api/v1/interviews/{id}/responses
```

---

## 4. Backend Integration Points

The interview router (`app/routers/interview.py`) has clearly marked stubs where ML services should be plugged in. Here's where each service connects:

### 4.1 `POST /{id}/start` — Initialize Monitoring
**File:** `app/routers/interview.py` → `start_interview()`
```python
# --- ML INTEGRATION STUB: INITIALIZE CHEATING DETECTION ---
# Replace with:
from app.db.services.cheating_detector import CheatingDetector
detector = CheatingDetector(interview_id=id)
await detector.start_monitoring()
# ----------------------------------------------------------
```

### 4.2 `GET /{id}/questions` — AI Question Generation
**File:** `app/routers/interview.py` → `get_interview_questions()`
```python
# --- ML INTEGRATION STUB: AI VOICE GENERATION ---
# Replace with:
from app.db.services.question_generator import generate_questions
from app.db.services.tts_service import generate_audio

# If no questions exist yet, auto-generate them from the job role description:
if not questions:
    questions = await generate_questions(job_role=interview.job_role)
    # Save generated questions to DB

# Optionally pre-generate audio URLs:
for q in questions:
    q.audio_url = await generate_audio(q.question_text)
# ------------------------------------------------
```

### 4.3 `POST /{id}/responses` — Score Answer & Flag Cheating
**File:** `app/routers/interview.py` → `submit_interview_response()`
```python
# --- ML INTEGRATION STUB: ANSWER SCORING & CHEATING FLAGS ---
# Replace the hardcoded stubs with:
from app.db.services.answer_scorer import score_answer
from app.db.services.cheating_detector import get_cheating_events

scoring_result = await score_answer(
    question_text=question.question_text,
    answer_text=response_data.response_text,
    expected_keywords=question.expected_answer_keywords
)
calculated_score = scoring_result.score
ai_notes = scoring_result.feedback

cheating_events = await get_cheating_events(interview_id=id, question_id=response_data.question_id)
cheating_flag = len(cheating_events) > 0
# -----------------------------------------------------------
```

### 4.4 `POST /{id}/complete` — Final Score Aggregation
**File:** `app/routers/interview.py` → `complete_interview()`
```python
# --- ML INTEGRATION STUB: FINAL SCORE CALCULATION ---
# Replace the stub with:
responses = await session.execute(
    select(DBInterviewResponse).where(DBInterviewResponse.interview_id == id)
)
all_responses = responses.scalars().all()

total_score = sum(r.response_score or 0 for r in all_responses)
max_possible = len(all_responses) * 10.0  # max_score per question
interview.interview_score = (total_score / max_possible) * 100 if max_possible > 0 else 0

interview.final_score = (interview.ats_score or 0) * 0.3 + (interview.interview_score * 0.7)

# Generate feedback summary via LLM
from app.db.services.answer_scorer import generate_feedback_summary
interview.feedback = await generate_feedback_summary(all_responses)
# ----------------------------------------------------
```

---

## 5. ML Models to Implement

### 5.1 Answer Scorer (`app/db/services/answer_scorer.py`)

**Purpose:** Evaluate the quality, relevance, and depth of a candidate's answer.

**Approach Options:**
| Method | Pros | Cons |
|--------|------|------|
| **Keyword Matching** | Simple, fast, no API cost | Rigid, misses paraphrased answers |
| **Sentence Embeddings** (e.g., `sentence-transformers`) | Good semantic understanding | Requires model download (~400MB) |
| **LLM API** (e.g., Gemini, GPT) | Best quality, contextual | API cost, latency |

**Recommended starter implementation:**
```python
# app/db/services/answer_scorer.py
from dataclasses import dataclass

@dataclass
class ScoringResult:
    score: float          # 0-10
    confidence: float     # 0-100
    relevance: float      # 0-100
    feedback: str

async def score_answer(question_text: str, answer_text: str, expected_keywords: list[str]) -> ScoringResult:
    """Score a candidate's answer against expected criteria."""
    
    # --- PHASE 1: Simple keyword matching ---
    if not answer_text:
        return ScoringResult(score=0, confidence=0, relevance=0, feedback="No answer provided.")
    
    answer_lower = answer_text.lower()
    matched = [kw for kw in expected_keywords if kw.lower() in answer_lower]
    keyword_ratio = len(matched) / max(len(expected_keywords), 1)
    
    score = round(keyword_ratio * 10, 1)
    relevance = round(keyword_ratio * 100, 1)
    
    return ScoringResult(
        score=score,
        confidence=70.0,
        relevance=relevance,
        feedback=f"Matched {len(matched)}/{len(expected_keywords)} expected keywords."
    )
    
    # --- PHASE 2 (FUTURE): Replace with LLM-based scoring ---
    # import google.generativeai as genai
    # prompt = f"Score this interview answer 0-10...\nQuestion: {question_text}\nAnswer: {answer_text}"
    # response = genai.GenerativeModel('gemini-pro').generate_content(prompt)
    # Parse the LLM response into ScoringResult
```

### 5.2 Cheating Detector (`app/db/services/cheating_detector.py`)

**Purpose:** Detect suspicious behavior during the interview via webcam analysis.

**What to detect:**
- Frequent gaze aversion (looking away from screen)
- Head turning (looking at another screen or person)
- Multiple faces in frame
- Tab switching (can be detected via browser `visibilitychange` event on frontend)

**Approach:**
```python
# app/db/services/cheating_detector.py
import cv2
import numpy as np
from dataclasses import dataclass

@dataclass
class CheatingEvent:
    timestamp: float
    event_type: str   # "gaze_aversion", "head_turn", "multiple_faces", "tab_switch"
    confidence: float
    details: str

async def analyze_frame(frame_bytes: bytes) -> list[CheatingEvent]:
    """Analyze a single video frame for suspicious behavior."""
    
    # Decode the image
    nparr = np.frombuffer(frame_bytes, np.uint8)
    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    events = []
    
    # Face detection
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.3, 5)
    
    if len(faces) == 0:
        events.append(CheatingEvent(
            timestamp=0, event_type="no_face", confidence=90.0,
            details="No face detected in frame"
        ))
    elif len(faces) > 1:
        events.append(CheatingEvent(
            timestamp=0, event_type="multiple_faces", confidence=85.0,
            details=f"{len(faces)} faces detected"
        ))
    
    # For advanced gaze/head tracking, use dlib or mediapipe
    # import dlib
    # predictor = dlib.shape_predictor("shape_predictor_68_face_landmarks.dat")
    # ... extract eye landmarks, compute gaze direction ...
    
    return events
```

### 5.3 TTS Service (`app/db/services/tts_service.py`)

**Purpose:** Convert question text to audio that is played to the candidate.

**Recommended:** Use the browser's built-in `SpeechSynthesis` API (see Section 3.2). This avoids backend complexity and latency. Only build a backend TTS service if you need:
- A specific voice (e.g., ElevenLabs, Google Cloud TTS)
- Pre-generated audio files for consistency

### 5.4 Question Generator (`app/db/services/question_generator.py`)

**Purpose:** Auto-generate interview questions from a job role description.

```python
# app/db/services/question_generator.py

async def generate_questions(job_title: str, required_skills: list[str], count: int = 5) -> list[dict]:
    """Generate interview questions using an LLM."""
    
    # --- PHASE 1: Template-based ---
    templates = [
        f"Explain your experience with {{skill}} and how you've applied it in a project.",
        f"What challenges have you faced while working with {{skill}}?",
        f"How would you approach debugging a complex issue involving {{skill}}?",
    ]
    
    questions = []
    for i, skill in enumerate(required_skills[:count]):
        template = templates[i % len(templates)]
        questions.append({
            "question_text": template.format(skill=skill),
            "question_type": "technical",
            "expected_answer_keywords": [skill.lower()],
            "order_index": i
        })
    
    return questions
    
    # --- PHASE 2 (FUTURE): LLM-based ---
    # prompt = f"Generate {count} interview questions for a {job_title} role requiring: {', '.join(required_skills)}"
    # response = await llm.generate(prompt)
    # Parse and return structured questions
```

---

## 6. WebSocket Architecture (Real-time Cheating Detection)

For real-time cheating detection, REST APIs are too slow. Here's how to add WebSocket support:

### Backend Setup
```python
# app/routers/ws_interview.py
from fastapi import WebSocket, WebSocketDisconnect
from app.db.services.cheating_detector import analyze_frame

@router.websocket("/ws/interview/{interview_id}")
async def interview_ws(websocket: WebSocket, interview_id: str):
    await websocket.accept()
    
    cheating_events = []
    
    try:
        while True:
            # Receive video frame from frontend
            data = await websocket.receive_bytes()
            
            # Analyze frame
            events = await analyze_frame(data)
            cheating_events.extend(events)
            
            # Send back real-time feedback
            if events:
                await websocket.send_json({
                    "type": "cheating_alert",
                    "events": [{"type": e.event_type, "confidence": e.confidence} for e in events]
                })
                
    except WebSocketDisconnect:
        # Save accumulated events to database
        pass
```

### Frontend Connection
```javascript
// Connect to WebSocket when interview starts
const ws = new WebSocket(`ws://localhost:8000/api/v1/ws/interview/${interviewId}`);

// Send video frames periodically
const canvas = document.createElement('canvas');
const ctx = canvas.getContext('2d');

setInterval(() => {
  ctx.drawImage(videoElement, 0, 0, 320, 240);
  canvas.toBlob(blob => {
    if (ws.readyState === WebSocket.OPEN) {
      ws.send(blob);
    }
  }, 'image/jpeg', 0.5);
}, 3000); // Every 3 seconds

// Listen for cheating alerts
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  if (data.type === 'cheating_alert') {
    console.warn('Cheating detected:', data.events);
    // Log this event for the final report
  }
};
```

---

## 7. File Reference Map

| File | Status | Purpose |
|------|--------|---------|
| `app/routers/interview.py` | ✅ DONE | Interview workflow REST endpoints |
| `app/routers/ws_interview.py` | 🔲 TODO | WebSocket for real-time cheating detection |
| `app/db/services/answer_scorer.py` | 🔲 TODO | NLP/LLM-based answer evaluation |
| `app/db/services/cheating_detector.py` | 🔲 TODO | OpenCV/MediaPipe cheating detection |
| `app/db/services/tts_service.py` | 🔲 OPTIONAL | Server-side TTS (browser API preferred) |
| `app/db/services/question_generator.py` | 🔲 TODO | AI question generation from job description |
| `app/db/models/interview.py` | ✅ DONE | Interview, InterviewQuestion, InterviewResponse models |
| `app/schemas/interview.py` | ✅ DONE | Pydantic schemas for all interview entities |
| `app/deps.py` | ✅ DONE | Authentication dependencies |
| `app/main.py` | ✅ DONE | Router registration |

---

## Quick Start Checklist

To implement the full AI interview experience, follow these steps in order:

1. **[Backend]** Create `app/db/services/answer_scorer.py` — Start with keyword matching (Phase 1)
2. **[Backend]** Create `app/db/services/question_generator.py` — Start with templates
3. **[Backend]** Replace the stubs in `app/routers/interview.py` with real service calls
4. **[Frontend]** Build the Interview Screen component:
   - Camera feed with `getUserMedia`
   - TTS with `SpeechSynthesis` API
   - Speech-to-Text with `SpeechRecognition` API
   - Sequential question display + answer submission
5. **[Backend]** Add WebSocket endpoint for real-time frame analysis
6. **[Frontend]** Connect WebSocket to send video frames during interview
7. **[Backend]** Create `app/db/services/cheating_detector.py` with OpenCV
8. **[Backend]** Upgrade answer scorer to LLM-based (Phase 2)

---

*Last updated: April 28, 2026*
