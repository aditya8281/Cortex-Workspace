.PHONY: help install dev dev-no-reload migrate migration shell test test-cov test-watch lint format check clean db-reset db-shell db-backup docker-build docker-up docker-down docker-logs docker-shell docs lock ci prod-check logs-app logs-error

# ============================================================================
# HELP
# ============================================================================

help:
	@echo "Cortex Workspace - Development Commands"
	@echo ""
	@echo "Setup:"
	@echo "  make install        Install dependencies"
	@echo ""
	@echo "Development:"
	@echo "  make dev            Run dev server (hot reload)"
	@echo "  make shell          Open Python shell"
	@echo ""
	@echo "Database:"
	@echo "  make migrate        Apply migrations"
	@echo "  make migration m=   Create new migration"
	@echo "  make db-reset       Reset database"
	@echo "  make db-shell       Open SQLite shell"
	@echo ""
	@echo "Quality:"
	@echo "  make lint           Run ruff + mypy"
	@echo "  make format         Format code"
	@echo "  make test           Run tests"
	@echo "  make check          Run lint + test"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-build   Build image"
	@echo "  make docker-up      Start containers"
	@echo "  make docker-down    Stop containers"

# ============================================================================
# SETUP
# ============================================================================

install:
	uv sync

# ============================================================================
# DEVELOPMENT
# ============================================================================

dev:
	uv run uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000

dev-no-reload:
	uv run uvicorn backend.app.main:app --host 0.0.0.0 --port 8000

shell:
	uv run python -i -c "from backend.app.main import app; from backend.app.db.session import SessionLocal; db = SessionLocal()"

# ============================================================================
# DATABASE
# ============================================================================

migrate:
	uv run alembic upgrade head

migration:
	uv run alembic revision -m "$(m)"

db-reset:
	@echo "⚠️ Resetting database..."
	rm -f app.db
	uv run alembic upgrade head
	@echo "✓ Database reset complete"

db-shell:
	sqlite3 app.db

db-backup:
	cp app.db app.db.backup.$(shell date +%Y%m%d_%H%M%S)

# ============================================================================
# QUALITY
# ============================================================================

lint:
	uv run ruff check backend/ tests/
	uv run mypy backend/ --ignore-missing-imports

format:
	uv run black backend/ tests/ --line-length 100
	uv run ruff check backend/ tests/ --fix

check: lint test
	@echo "✓ All checks passed"

# ============================================================================
# TESTING
# ============================================================================

test:
	uv run pytest -v --tb=short

test-cov:
	uv run pytest --cov=backend --cov-report=term-missing --cov-report=html -v

test-watch:
	uv run pytest -v --looponfail

# ============================================================================
# CLEANUP
# ============================================================================

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name ".coverage" -delete 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true

# ============================================================================
# DOCKER
# ============================================================================

docker-build:
	docker compose build

docker-up:
	docker compose up -d

docker-dev:
	docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build

docker-down:
	docker compose down

docker-logs:
	docker compose logs -f

docker-shell:
	docker compose exec backend /bin/bash

docker-gpu:
	@echo "To enable GPU acceleration, uncomment the 'deploy' block in docker-compose.yml under the 'ollama' service, then run: docker compose up -d"

# ============================================================================
# DOCS
# ============================================================================

docs:
	@echo "Swagger: http://localhost:8000/docs"
	@echo "ReDoc:   http://localhost:8000/redoc"

# ============================================================================
# CI/CD
# ============================================================================

ci: lint test
	@echo "✓ CI passed"

prod-check: clean lint test
	@echo "✓ Production checks passed"

# ============================================================================
# UTILITIES
# ============================================================================

lock:
	uv sync --upgrade

logs-app:
	tail -f logs/app.log

logs-error:
	tail -f logs/error.log

# ============================================================================
# DEFAULT
# ============================================================================

.DEFAULT_GOAL := help