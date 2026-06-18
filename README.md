# Cortex

A local-first workspace with authentication, a central memory system, and a clean foundation for AI-powered features.

## What Cortex Does

- Secure user authentication (register, login, JWT tokens, refresh tokens)
- Multi-step registration wizard (Account → Profile → GitHub → Vault)
- Real-time username availability checking
- Central memory system for storing and retrieving knowledge entries
- User profile management (with profile photo upload, avatar thumbnails)
- GitHub account integration (encrypted token storage)
- Admin user management (promote/demote/delete)
- Health monitoring endpoints

## Architecture

```
Client (Next.js :3000) ──► FastAPI Backend (:8000) ──► SQLite + Redis
```

- **Frontend**: Next.js 15 App Router, React 19, Tailwind CSS
- **Backend**: FastAPI (Python 3.10+), SQLAlchemy ORM, Alembic migrations
- **Storage**: SQLite database, Redis cache (optional)

## Repository Layout

- `backend/` — FastAPI backend (auth, memory, core infrastructure)
- `frontend/` — Next.js + React UI
- `scripts/` — Helper scripts
- `migrations/` — Alembic database migrations
- `tests/` — Pytest test suite

## Setup

### Docker Setup (Primary)

```bash
cp .env.docker .env
./scripts/docker-run.sh
```

- Frontend: `http://localhost`
- Backend API: `http://localhost:8000`

### Manual Setup (Development)

**Prerequisites**: Python 3.10+, Node.js 18+, `uv`, npm

#### Backend

```bash
cp .env.example .env
uv sync
uv run alembic upgrade head
uv run uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
```

#### Frontend

```bash
cd frontend
npm install
npm run dev
```

## Configuration

Set these in your `.env` file:

| Variable | Default | Purpose |
|----------|---------|---------|
| `SECRET_KEY` | (empty) | JWT signing key |
| `DATABASE_URL` | (computed) | SQLite path |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis for refresh tokens |
| `NEXT_PUBLIC_API_BASE_URL` | `http://localhost:8000` | Backend URL for frontend |

## API Endpoints

See [API_ENDPOINTS.md](API_ENDPOINTS.md) for the full endpoint reference.

### Quick Reference

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/auth/register` | Create account (multi-step wizard) |
| POST | `/api/auth/login` | Login |
| POST | `/api/auth/refresh` | Refresh tokens |
| POST | `/api/auth/logout` | Logout |
| GET | `/api/auth/me` | Current user |
| PUT | `/api/auth/me` | Update account |
| POST | `/api/auth/check-username` | Check username availability |
| GET | `/api/memory` | List memories |
| POST | `/api/memory` | Store memory |
| GET | `/api/v1/health/live` | Liveness check |
| GET | `/api/v1/health/ready` | Readiness check |
| GET | `/api/v1/health/deep` | Deep health check |
| GET | `/api/v1/me/profile` | Get profile |
| PUT | `/api/v1/me/profile` | Update profile |
| POST | `/api/v1/me/profile/photo` | Upload photo |
| GET | `/api/v1/me/profile/photo/{id}` | Get user photo (public) |
| GET | `/api/v1/users` | List users (admin) |
| DELETE | `/api/v1/users/{id}` | Delete user (admin) |
| GET | `/api/v1/me/github` | GitHub status |
| POST | `/api/v1/me/github` | Connect GitHub |
| DELETE | `/api/v1/me/github` | Disconnect GitHub |

## Testing

```bash
uv run pytest
```

## License

MIT
