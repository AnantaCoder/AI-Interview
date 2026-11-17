FROM python:3.12-slim

# Avoid buffering stdout/stderr and prevent Python from writing .pyc files
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000

WORKDIR /app

# Install system dependencies needed by OpenCV, MediaPipe, Ultralytics, and networking
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgl1 \
    libglib2.0-0 \
    libgomp1 \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Pre-download NLTK data required by resume analysis
RUN python -m nltk.downloader punkt_tab stopwords

# Copy backend files (app, classifier_model, yolov8n.pt, etc.)
COPY . .

# Expose default port
EXPOSE 8000

# Start FastAPI using uvicorn binding to 0.0.0.0 and Railway's dynamic $PORT
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]

