# ── Stage 1: Build Frontend ────────────────────────────────────
FROM node:20-slim AS frontend-build
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm ci
COPY frontend/ .
RUN npm run build

# ── Stage 2: Python Backend ───────────────────────────────────
FROM python:3.12-slim AS production
WORKDIR /app

# System deps for tree-sitter compilation + git
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# Python deps
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Backend source
COPY backend/ .

# Frontend dist (served as static files)
COPY --from=frontend-build /app/frontend/dist /app/static

# Create temp directories
RUN mkdir -p /app/tmp/repos /app/tmp/indexes

ENV TEMP_REPOSITORY_PATH=/app/tmp/repos
ENV VECTOR_INDEX_PATH=/app/tmp/indexes
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
