# =============================================================================
# Cortex Workspace — Multi-stage Dockerfile
# =============================================================================
# Build:  docker build -t cortex .
# Run:    docker run -p 8000:8000 --env-file .env cortex
# =============================================================================

# ── Stage 1: Frontend build ──────────────────────────────────────────
FROM node:20-alpine AS frontend-build

WORKDIR /app/frontend

COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --prefer-offline

COPY frontend/ ./
RUN npm run build

# ── Stage 2: Backend runtime ─────────────────────────────────────────
FROM python:3.12-slim AS backend

# System deps for psycopg2, cryptography, onnxruntime
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install uv for fast dependency resolution
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy dependency files first for layer caching
COPY pyproject.toml uv.lock ./

# Install Python dependencies
RUN uv sync --frozen --no-dev --no-install-project

# Copy backend source
COPY backend/ ./backend/
COPY alembic.ini ./
COPY migrations/ ./migrations/

# Copy frontend build output
COPY --from=frontend-build /app/frontend/.next/ ./frontend/.next/
COPY --from=frontend-build /app/frontend/public/ ./frontend/public/
COPY frontend/package.json frontend/next.config.ts frontend/tailwind.config.ts frontend/tsconfig.json frontend/postcss.config.mjs ./

# Create non-root user
RUN groupadd -r cortex && useradd -r -g cortex -d /app -s /sbin/nologin cortex \
    && mkdir -p /app/CortexMemory && chown -R cortex:cortex /app

USER cortex

EXPOSE 8000

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health/live || exit 1

CMD ["uv", "run", "uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
