FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PORT=8000 \
    NLTK_DATA=/usr/share/nltk_data

WORKDIR /app

# ── System dependencies for OpenCV, MediaPipe, ffmpeg ─────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgl1 \
    libglib2.0-0 \
    libgomp1 \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

# ── Install PyTorch CPU-only first ───────────────────────────────────
RUN pip install --upgrade pip setuptools wheel && \
    pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu

# ── Install backend requirements ─────────────────────────────────────
COPY backend/requirements.txt ./requirements.txt
RUN pip install -r requirements.txt

# ── Pre-download NLTK corpora (safe with fallback) ───────────────────
RUN mkdir -p /usr/share/nltk_data && \
    python -c "import nltk; [nltk.download(p, download_dir='/usr/share/nltk_data', quiet=True) for p in ['punkt', 'punkt_tab', 'stopwords']]" || true

# ── Copy backend source code and model files ────────────────────────
COPY backend/ ./

EXPOSE 8000
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]

