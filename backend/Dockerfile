FROM python:3.12-slim AS builder

# ── env ──────────────────────────────────────────────────────────────
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PORT=8000

WORKDIR /app

# ── system deps (OpenCV, MediaPipe, ffmpeg) ──────────────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgl1 \
    libglib2.0-0 \
    libgomp1 \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# ── Stage 1: install torch CPU-only BEFORE requirements ──────────────
# ultralytics declares torch as a dependency; pre-installing the CPU
# wheel prevents pip from pulling the 2 GB CUDA bundle.
RUN pip install --upgrade pip setuptools wheel && \
    pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu

# ── Stage 2: install everything else ─────────────────────────────────
COPY requirements.txt .
RUN pip install -r requirements.txt

# ── Stage 3: pre-download NLTK data ─────────────────────────────────
RUN python -c "\
import nltk, os; \
d = '/usr/share/nltk_data'; \
os.makedirs(d, exist_ok=True); \
nltk.download('punkt_tab', download_dir=d); \
nltk.download('punkt', download_dir=d); \
nltk.download('stopwords', download_dir=d); \
print('NLTK data ready')"
ENV NLTK_DATA=/usr/share/nltk_data

# ── copy application code ───────────────────────────────────────────
COPY . .

# ── expose & run ─────────────────────────────────────────────────────
EXPOSE 8000
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
