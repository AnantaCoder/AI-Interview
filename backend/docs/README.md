# AI Interview Analysis Backend Documentation

Welcome to the documentation for the **AI Interview Analysis Backend**! This directory contains simple, easy-to-understand guides for understanding and working with the various features of this backend application.

## 🌟 Core Features

The backend is built with FastAPI and integrates several advanced capabilities to power our interview analysis system. Below are the dedicated guides for each core feature:

### 1. 🛡️ Authentication System
Learn how users (candidates, organizations, and admins) sign up, log in, and securely access the platform using our Supabase-powered authentication flow.
👉 **[Read the Authentication Guide](./authentication.md)**

### 2. 🗄️ Database Management
Understand how we store data, create new tables, and interact with our PostgreSQL database using SQLAlchemy.
👉 **[Read the Database Guide](./database.md)**

### 3. 📄 Resume Categorization (Machine Learning)
Discover how our intelligent pipeline uses Machine Learning (Gradient Boosting & TF-IDF) to automatically categorize uploaded resumes into industries (e.g., HR, Engineering, IT, etc.).
👉 **[Read the Resume Categorization Guide](./resume_categorization.md)**

### 4. 📹 Video Proctoring & Behavior Analysis (Computer Vision)
Explore how the backend analyzes webcam streams in real time via WebSockets to detect gaze direction, evaluate head pose, classify emotions, score sitting posture, and run YOLOv8n-based multi-person detection.
👉 **[Read the Video Analysis Guide](./video_analysis.md)**

---

## 🛠️ Quick Start for Developers

1. **Environment Setup**: Ensure your `.env` file is populated with Supabase credentials and database URLs.
2. **Run the Server**: 
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```
3. **API Documentation**: Once running, interactive API docs are automatically available at:
   - **Swagger UI**: `http://localhost:8000/docs`
   - **ReDoc**: `http://localhost:8000/redoc`

Explore the individual guides above to dive deeper into specific architectural details!
