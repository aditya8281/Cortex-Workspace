.PHONY: help install dev dev-no-reload migrate migration shell test test-cov test-watch lint format check clean db-reset db-shell db-backup docker-build docker-up docker-down docker-restart docker-reset docker-logs docker-shell docs lock ci prod-check logs-app logs-error auto auto-pre auto-dev auto-health auto-bugs auto-complete auto-report hooks hooks-pre hooks-push hooks-merge hooks-onchange

# ============================================================================
# HELP
# ============================================================================

help:
	@echo "CORTEX - Development Commands"
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
	@echo "  make db-shell       Open PostgreSQL shell"
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
	@echo ""
	@echo "Automation:"
	@echo "  make auto           Run all automation checks"
	@echo "  make auto-pre       Pre-work validation only"
	@echo "  make auto-dev       Development validation only"
	@echo "  make auto-health    Health checks only"
	@echo "  make auto-bugs      Bug discovery only"
	@echo "  make auto-complete  Completion validation only"
	@echo "  make auto-report    Generate health report"
	@echo ""
	@echo "Hooks:"
	@echo "  make hooks          Run all hooks"
	@echo "  make hooks-pre      Run pre-commit hooks (ui-review, code-quality)"
	@echo "  make hooks-push     Run pre-push hooks (quality, architecture, contract, docs)"
	@echo "  make hooks-merge    Run all hooks before merge"
	@echo "  make hooks-onchange Run hooks on code change (quality, contract)"

# ============================================================================
# SETUP
# ============================================================================

install:
	uv sync
	cd frontend && npm install

# ============================================================================
# DEVELOPMENT
# ============================================================================

dev:
	uv run uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000

dev-no-reload:
	uv run uvicorn backend.app.main:app --host 0.0.0.0 --port 8000

dev-frontend:
	cd frontend && npm run dev

dev-full:
	@echo "Starting backend + frontend..."
	uv run uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000 &
	cd frontend && npm run dev

build-frontend:
	cd frontend && npm run build

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
	@echo "⚠️  Resetting database..."
	@uv run python -c " \
from sqlalchemy import create_engine, text; \
from backend.app.core.config import settings; \
e = create_engine(settings.DATABASE_URL); \
conn = e.connect(); \
conn.execute(text('DROP SCHEMA public CASCADE; CREATE SCHEMA public')); \
conn.commit(); conn.close(); e.dispose() \
" 2>/dev/null || true
	uv run alembic upgrade head
	@echo "✓ Database reset complete"

db-shell:
	psql $${DATABASE_URL:-postgresql://cortex:cortex@localhost:5432/cortex}

db-backup:
	pg_dump $${DATABASE_URL:-postgresql://cortex:cortex@localhost:5432/cortex} > cortex_backup_$(shell date +%Y%m%d_%H%M%S).sql

# ============================================================================
# QUALITY
# ============================================================================

lint:
	uv run ruff check backend/ tests/
	uv run mypy backend/ --ignore-missing-imports --explicit-package-bases --implicit-optional

format:
	uv run ruff format backend/ tests/
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
# WORKER (arq task queue)
# ============================================================================

worker:
	uv run python -m backend.app.tasks.worker

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
	./scripts/docker-build.sh

docker-up:
	./scripts/docker-run.sh

docker-restart:
	./scripts/docker-restart.sh

docker-reset:
	./scripts/docker-clean-reset.sh

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
# AUTOMATION FRAMEWORK
# ============================================================================

auto:
	python scripts/automation/run_all.py

auto-pre:
	python scripts/automation/run_all.py pre-work

auto-dev:
	python scripts/automation/run_all.py development

auto-health:
	python scripts/automation/run_all.py health

auto-bugs:
	python scripts/automation/run_all.py bug-discovery

auto-complete:
	python scripts/automation/run_all.py completion

auto-report:
	python scripts/automation/run_all.py report

# ============================================================================
# HOOK SYSTEM
# ============================================================================

hooks:
	python .claude/hooks/run_hooks.py

hooks-pre:
	python .claude/hooks/run_hooks.py --phase pre-commit

hooks-push:
	python .claude/hooks/run_hooks.py --phase pre-push

hooks-merge:
	python .claude/hooks/run_hooks.py --phase pre-merge

hooks-onchange:
	python .claude/hooks/run_hooks.py --phase on-change

# ============================================================================
# DEFAULT
# ============================================================================

.DEFAULT_GOAL := help
