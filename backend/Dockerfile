FROM python:3.11-slim

# Install system deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy only requirements first to leverage layer caching
COPY requirements.txt /app/requirements.txt

RUN python -m pip install --upgrade pip setuptools wheel
RUN pip install --no-cache-dir -r /app/requirements.txt

# Make model cache location predictable and include it in the image so the
# SentenceTransformers model can be downloaded at build time (faster cold
# start at runtime).
ENV HF_HOME=/app/.cache/huggingface
ENV TRANSFORMERS_CACHE=/app/.cache/huggingface

# Pre-download embedding model to avoid runtime downloads during container
# startup. This will make the image larger but reduces startup latency.
RUN python - <<'PY'
from sentence_transformers import SentenceTransformer
print('Pre-downloading embedding model: all-MiniLM-L6-v2')
SentenceTransformer('all-MiniLM-L6-v2')
print('Model pre-download complete')
PY

# Copy backend code
COPY backend /app/backend
COPY .env /app/.env

ENV PYTHONPATH=/app/backend

WORKDIR /app/backend

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
