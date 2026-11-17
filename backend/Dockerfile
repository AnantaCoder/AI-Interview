FROM python:3.12-slim

# ── env ──────────────────────────────────────────────────────────────
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=8000

WORKDIR /app

# ── system deps (OpenCV, MediaPipe, ffmpeg) ──────────────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgl1 \
    libglib2.0-0 \
    libgomp1 \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

# ── pip install in two stages for better caching ─────────────────────
# Stage 1 – install torch CPU-only FIRST (much smaller than GPU torch)
# ultralytics pulls torch; pre-installing the CPU wheel prevents the
# huge CUDA bundle from being downloaded.
RUN pip install --upgrade pip setuptools wheel && \
    pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu

# Stage 2 – install everything else
COPY requirements.txt .
RUN pip install -r requirements.txt

# ── download NLTK data needed at runtime ─────────────────────────────
RUN python -c "import nltk; nltk.download('punkt_tab', download_dir='/usr/share/nltk_data'); nltk.download('punkt', download_dir='/usr/share/nltk_data'); nltk.download('stopwords', download_dir='/usr/share/nltk_data')"
ENV NLTK_DATA=/usr/share/nltk_data

# ── copy application code ───────────────────────────────────────────
COPY . .

# ── expose & run ─────────────────────────────────────────────────────
EXPOSE 8000
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
