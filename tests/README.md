# Tests — CORTEX

All backend tests live here. Frontend tests are colocated with their components under `frontend/src/`.

## Structure

```
tests/
├── conftest.py              # Root fixtures — mocks external services (vector DB, embedding, cache, RAG)
├── test_infrastructure.py   # Meta-tests: verifies factories and mocks work
├── api/                     # API endpoint tests (routers, request/response, auth flows)
├── services/                # Service unit tests (business logic, pipelines, integrations)
├── models/                  # Model-specific tests (schema, columns, serialization)
├── agents/                  # Agent system tests (loop, tools, security, compaction)
│   └── integrity/           # Integrity engine tests (structural, semantic, evolution)
├── daemon/                  # Daemon lifecycle tests (health, PID, signals, sleep)
├── factories/               # Test factory functions (Faker-based model builders)
├── mocks/                   # Mock objects (LLM, Redis, Qdrant, HTTP, agent loop)
├── integration/             # Integration tests (DB-backed, multi-component)
└── performance/             # Performance baselines and benchmarks
```

## Conventions

- **`api/`** — Tests that hit FastAPI TestClient routes. Name: `test_<feature>_api.py`
- **`services/`** — Tests that exercise service layer logic. Name: `test_<service>.py`
- **`agents/`** — Tests for the agent loop, tools, and integrity engines. Name: `test_<component>.py`
- **`factories/`** — Not tests themselves. Functions that build test data. Imported by test files.
- **`mocks/`** — Not tests themselves. Mock objects for external services. Imported by test files.
- **`conftest.py`** — Root-level autouse fixtures that mock vector DB, embeddings, cache, RAG, file watcher.

## Running

```bash
make test                    # All backend tests
.venv/bin/pytest tests/api/  # Only API tests
.venv/bin/pytest tests/agents/  # Only agent tests
```

## Frontend Tests

Located alongside components: `frontend/app/<route>/page.test.tsx` and `frontend/src/<module>/<component>.test.tsx`.

```bash
cd frontend && npm test      # All frontend tests
```
