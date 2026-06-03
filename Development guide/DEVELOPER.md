# Cortex Workspace - Developer Quick Reference

## Project At-a-Glance

**Status**: Phase 1 - Stabilization & Documentation  
**Tech Stack**: FastAPI 0.136.3 | SQLAlchemy 2.0 | Python 3.14 | SQLite (dev)  
**Last Fixed**: 2026-06-02 (Alembic migrations + auth system)  
**Maintenance**: Stable - all tests passing

---

## Key Commands

```bash
# Setup
uv sync                  # Install/update dependencies
make install            # One-time setup

# Development  
make dev                # Run dev server (hot reload)
make migrate            # Apply database migrations
make test               # Run pytest suite
make lint               # Check code quality (ruff)
make format             # Auto-format code (black)

# Database
alembic upgrade head    # Apply all pending migrations
alembic downgrade -1    # Revert last migration
alembic revision -m "description"  # Create new migration

# Docker
docker-compose up       # Start app + services
docker-compose down     # Stop containers
```

---

## API Endpoints (Current)

### Health
- `GET /` - Root health check
- `GET /api/v1/health` - Service health

### Users (Public)
- `POST /api/v1/users` - Register (body: email, full_name, password)
- `POST /api/v1/login` - Login (body: email, password) → returns JWT

### Users (Protected)
- `GET /api/v1/users` - List all users (requires auth header)
- `GET /api/v1/users/{id}` - Get single user (requires auth header)
- `GET /api/v1/users/me` - Get current user (requires auth header)

### Auth Header Format
```
Authorization: Bearer <jwt_token>
```

---

## Code Structure

```
backend/app
├── api/              # HTTP routing & dependencies
├── core/             # Config, security, settings
├── db/               # Database configuration
├── models/           # SQLAlchemy ORM models
├── schemas/          # Pydantic validation schemas
├── services/         # Business logic layer
└── main.py           # FastAPI app entry point
```

**Rule**: Logic goes in `services/`, never in routers

---

## Adding Features (Checklist)

1. **Database Change**?
   - [ ] Update model in `models/`
   - [ ] Run: `alembic revision -m "description"`
   - [ ] Edit migration file with schema changes
   - [ ] Test: `alembic upgrade head`

2. **New Endpoint**?
   - [ ] Add schema to `schemas/`
   - [ ] Add service function to `services/`
   - [ ] Add route to `api/v1/`
   - [ ] Add dependency injection if needed

3. **New Service Function**?
   - [ ] Add to appropriate `services/` file
   - [ ] Use type hints
   - [ ] Add docstring
   - [ ] Use dependency injection for db: `db: Session`

4. **Before Commit**
   - [ ] `make lint` passes
   - [ ] `make test` passes
   - [ ] Database migrations work
   - [ ] Commit follows: `<type>(<scope>): <message>`

---

## Common Issues & Fixes

### "alembic upgrade head" fails
```bash
# Option 1: Check migration syntax
alembic revision --autogenerate -m "fix"

# Option 2: Reset dev database
rm app.db
alembic upgrade head
```

### Import errors
```bash
# Reinstall dependencies
uv sync

# Check PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### Auth failing
- Check JWT secret in `.env`: `SECRET_KEY=your-key`
- Verify token format: `Authorization: Bearer <token>`
- Check token expiration: Default 30 minutes

### Database locked (SQLite)
```bash
# Single writer issue - check if dev server is running
make dev  # Only one instance at a time
```

---

## File Checklist (What Goes Where)

| What | Where |
|------|-------|
| API routes | `backend/app/api/v1/` |
| Database models | `backend/app/models/` |
| Validation schemas | `backend/app/schemas/` |
| Business logic | `backend/app/services/` |
| Configuration | `backend/app/core/config.py` |
| Security functions | `backend/app/core/security.py` |
| Environment vars | `.env` |
| Dependencies | `pyproject.toml` |

---

## Environment Variables

Required (in `.env`):
```
DATABASE_URL=sqlite:///./app.db
SECRET_KEY=your-super-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
DEBUG=True
```

---

## Testing Endpoints (curl)

```bash
# Health check
curl http://localhost:8000/api/v1/health

# Register user
curl -X POST http://localhost:8000/api/v1/users \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","full_name":"John Doe","password":"securepass123"}'

# Login
curl -X POST http://localhost:8000/api/v1/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"securepass123"}'

# Get users (replace TOKEN with JWT from login)
curl -H "Authorization: Bearer TOKEN" \
  http://localhost:8000/api/v1/users
```

---

## Codebase Discovery & Optimization

To avoid system latency, the filesystem scanner in `FilesystemDiscovery` has been heavily optimized:
- **No recursive home walking**: The home directory (`~`) root is never walked recursively.
- **Targeted Code Scanning**: We only perform full crawls on directories explicitly named inside code-promoted keys (e.g. `~/projects`, `~/workspace`, `~/code`, `~/dev`).
- **One-level general directory discovery**: High-volume personal storage folders like `~/Downloads` or `~/Documents` are traversed only 1 level down. We only add subfolders containing project markers (like `.git`, `pyproject.toml`, or `package.json`), bypassing other folders and reducing file crawl latency by 99%.
- **CPU RAG Embeddings**: SentenceTransformer embeddings run on CPU (`CUDA_VISIBLE_DEVICES=""`), ensuring GPU resources remain available for running Ollama/local LLM inference engines.

---

## Current Status & Limitations

- **SQLite**: Single-writer database used for development state. Excellent for local-first operations.
- **Auth**: Fully functional JWT-based security with password hashing (argon2).
- **Testing**: Complete pytest test suite configured in `tests/` with 100% pass rate.
- **Docker**: Ready-to-go `docker-compose.yml` defining Ollama, FastAPI Backend, and React Frontend containers.
- **Logging**: Structured logger config implemented via `backend/app/core/logging.py`.
- **System Autonomy**: Permission gate settings supporting Observation, Approval, and Automated modes.

---

## Git Workflow & Contribution Standards

Always adhere to the following workflow when contributing features or bug fixes:

1. **Create Branch**: `git checkout -b <type>/<description>` (e.g., `feat/token-refresh` or `fix/index-leak`).
2. **Implement & Format**: Run `make format` to run black and ruff checks.
3. **Lint & Test**: Ensure `make check` (runs ruff, mypy, and pytest) passes with zero errors before pushing.
4. **Pull Requests**: Pull requests must target the `main` branch. Provide clear issue references, reproduction steps for fixes, and screenshot diffs for UI changes.

---

## Support Files

- `Development guide/PROJECT_CONTEXT.md` - In-depth architecture specification
- `Development guide/DEVELOPER.md` - Quick developer reference (you are here)
- `pyproject.toml` - Dependencies & project config
- `alembic.ini` - Database migration config

---

**Last Updated**: 2026-06-03  
**Maintained By**: Development Team  
**Status**: Stable, Optimized & Developer-Ready

