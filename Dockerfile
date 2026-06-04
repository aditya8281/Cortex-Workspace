# syntax=docker/dockerfile:1.7

FROM node:22-bookworm-slim AS frontend-build
WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ ./
ARG NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1
ENV NEXT_PUBLIC_API_BASE_URL=${NEXT_PUBLIC_API_BASE_URL}
RUN npm run build

FROM ghcr.io/astral-sh/uv:python3.14-bookworm-slim AS backend
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_NO_CACHE=1 \
    UV_LINK_MODE=copy

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl git \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY . .
RUN mkdir -p /cortex_memory \
    && useradd --create-home --shell /bin/bash cortex \
    && chown -R cortex:cortex /app /cortex_memory

USER cortex

EXPOSE 8000

CMD ["sh", "-lc", "uv run alembic upgrade head && exec uv run uvicorn backend.app.main:app --host 0.0.0.0 --port 8000"]

FROM node:22-bookworm-slim AS frontend
WORKDIR /app/frontend

COPY --from=frontend-build /app/frontend/package*.json ./
COPY --from=frontend-build /app/frontend/next.config.js ./next.config.js
COPY --from=frontend-build /app/frontend/.next ./.next
COPY --from=frontend-build /app/frontend/public ./public
COPY --from=frontend-build /app/frontend/node_modules ./node_modules

EXPOSE 3000
ENV PORT=3000
ENV HOSTNAME=0.0.0.0

CMD ["npm", "run", "start"]
