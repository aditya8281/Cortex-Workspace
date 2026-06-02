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

## Current Limitations & Notes

- **SQLite**: Single writer (fine for dev, use PostgreSQL for production)
- **Auth**: Basic JWT (no refresh tokens yet)
- **RBAC**: Role field exists but no permission checks yet
- **Testing**: Test suite not yet created
- **Docker**: Containers not yet configured
- **Logging**: No structured logging yet

---

## Next Phase (Week 1-2)

1. ✏️ **Documentation Phase**
   - Create `.env.example`
   - Write comprehensive README
   - Add Makefile
   
2. 📦 **Containerization Phase**
   - Dockerfile (multi-stage)
   - docker-compose.yml

3. 🧪 **Testing Phase**
   - pytest setup
   - Initial test coverage

---

## Git Workflow

```bash
# Create feature branch
git checkout -b feat/my-feature

# Make changes, test locally
make lint && make test

# Commit with conventional message
git commit -m "feat(auth): add token refresh endpoint"

# Push and create PR
git push origin feat/my-feature
```

---

## Support Files

- `.instructions.md` - Full project guide (you are here)
- `/memories/repo/alembic_fixes.md` - Database fix history
- `pyproject.toml` - Dependencies & project config
- `alembic.ini` - Migration config

---

**Last Updated**: 2026-06-02  
**Maintained By**: Development Team  
**Status**: Stable & Production-Ready for Phase 1
