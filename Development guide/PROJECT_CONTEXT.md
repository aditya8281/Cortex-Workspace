# Cortex Workspace - Project Context

Last verified: 2026-06-02

## Overview

Cortex Workspace is a FastAPI-based backend for an AI-assisted engineering workspace. The current codebase focuses on:

- user authentication and profile APIs
- an AI gateway that routes requests into an execution pipeline
- a lightweight RAG/indexing layer for repository search
- local memory storage for prior conversations
- repo and system inspection agents

The repository is still backend-first. There is no frontend application yet, and the top-level `docker-compose.yml` is currently empty.

## Current Stack

- Python 3.14
- FastAPI
- SQLAlchemy 2.0
- Alembic
- Pydantic v2 / `pydantic-settings`
- JWT auth with `python-jose`
- Password hashing with `passlib` and Argon2/Bcrypt
- FAISS for vector search
- `sentence-transformers` for embeddings
- `httpx` for LLM provider calls
- `pytest` for tests

## Runtime Entry Point

The application starts in [backend/app/main.py](/home/krishna/Desktop/AI Engineering Workspace/backend/app/main.py).

Key behavior:

- calls `setup_logging()`
- creates a FastAPI app with `settings.APP_NAME`, `settings.DEBUG`, and version `0.1.0`
- registers `RequestLoggingMiddleware`
- mounts the API router under `settings.API_V1_PREFIX`
- exposes a simple `GET /` health-style root response

The app imports both the `User` and `Memory` ORM models so SQLAlchemy metadata is registered at startup.

## Configuration

Settings live in [backend/app/core/config.py](/home/krishna/Desktop/AI Engineering Workspace/backend/app/core/config.py).

Important values:

- `APP_NAME=Cortex Workspace`
- `API_V1_PREFIX=/api/v1`
- `DEBUG` is now normalized defensively so values like `true`, `false`, `release`, `prod`, and `production` do not crash app import
- `DATABASE_URL` and `SECRET_KEY` are required from the environment or `.env`
- AI settings are read from `AI_MODE`, `AI_MODEL`, `AI_API_KEY`, `AI_API_URL`, and `LOCAL_MODEL`

The repo includes [.env.example](/home/krishna/Desktop/AI Engineering Workspace/.env.example). The local `.env` currently uses SQLite and a development secret placeholder.

## API Surface

API routing is assembled in [backend/app/api/router.py](/home/krishna/Desktop/AI Engineering Workspace/backend/app/api/router.py).

Current endpoints:

- `GET /`
- `GET /api/v1/health/live`
- `GET /api/v1/health/ready`
- `GET /api/v1/health/deep`
- `POST /api/v1/users`
- `GET /api/v1/users`
- `GET /api/v1/users/{user_id}`
- `POST /api/v1/login`
- `GET /api/v1/me`
- `POST /api/v1/ai/ask`
- `POST /api/v1/ai/chat`

Important note:

- the login route is `POST /api/v1/login`, not `POST /api/v1/users/login`

## Data Model

### Users

The user ORM model is in [backend/app/models/user.py](/home/krishna/Desktop/AI Engineering Workspace/backend/app/models/user.py).

Fields:

- `id`
- `email`
- `full_name`
- `hashed_password`
- `role` with default `"user"`

The matching Alembic chain is:

- `af83dc13972a_create_users_table.py`
- `e4834d8614aa_add_hashed_password_to_users.py`
- `3a5b9f32d36d_add_role_field_to_users.py`

### Memories

The memory ORM model is in [backend/app/ai/memory/models.py](/home/krishna/Desktop/AI Engineering Workspace/backend/app/ai/memory/models.py).

Fields:

- `id`
- `user_id`
- `query`
- `response`
- `created_at`

The memory migration is [migrations/versions/32a5943404d9_create_memories_table.py](/home/krishna/Desktop/AI Engineering Workspace/migrations/versions/32a5943404d9_create_memories_table.py).

## Authentication

Authentication helpers live in [backend/app/core/security.py](/home/krishna/Desktop/AI Engineering Workspace/backend/app/core/security.py).

Behavior:

- passwords are hashed before storage
- tokens are JWTs with an `exp` claim
- `get_current_user()` reads the bearer token, decodes the `sub` claim, and loads the user from the database
- `/api/v1/me` is protected by `HTTPBearer`

## AI Layer

### Gateway and Executor

The request flow is:

`API -> AIGateway -> AIExecutor -> planner/tools/memory/LLM -> ResponseBuilder`

Relevant files:

- [backend/app/ai/gateway.py](/home/krishna/Desktop/AI Engineering Workspace/backend/app/ai/gateway.py)
- [backend/app/executor/executor.py](/home/krishna/Desktop/AI Engineering Workspace/backend/app/executor/executor.py)
- [backend/app/executor/intent_classifier.py](/home/krishna/Desktop/AI Engineering Workspace/backend/app/executor/intent_classifier.py)
- [backend/app/executor/planner.py](/home/krishna/Desktop/AI Engineering Workspace/backend/app/executor/planner.py)
- [backend/app/executor/response_builder.py](/home/krishna/Desktop/AI Engineering Workspace/backend/app/executor/response_builder.py)

Current executor behavior:

- classifies the query into `chat`, `tool`, `system`, or `rag`
- optionally looks up conversation memory for authenticated requests
- can call the file search agent, system scanner, or repository RAG
- sends the final prompt to the selected LLM provider
- stores the new memory for authenticated requests

Small but important implementation detail:

- `user_id` is checked with `is not None`, so `0` is not treated as missing

### Providers

Provider selection lives in [backend/app/ai/providers/registry.py](/home/krishna/Desktop/AI Engineering Workspace/backend/app/ai/providers/registry.py).

Supported modes:

- `local` -> [backend/app/ai/local_llm.py](/home/krishna/Desktop/AI Engineering Workspace/backend/app/ai/local_llm.py) via Ollama at `http://localhost:11434/api/generate`
- `api` -> [backend/app/ai/api_llm.py](/home/krishna/Desktop/AI Engineering Workspace/backend/app/ai/api_llm.py) using an OpenAI-compatible chat-completions payload

The router is a simple mode switch, not a complex multi-provider balancer yet.

## RAG and Repository Search

There are two chunkers in the repo:

- [backend/app/rag/text_chunker.py](/home/krishna/Desktop/AI Engineering Workspace/backend/app/rag/text_chunker.py) is a simple chunk utility covered by tests
- [backend/app/ai/ingestion/chunker.py](/home/krishna/Desktop/AI Engineering Workspace/backend/app/ai/ingestion/chunker.py) is the chunker used by the repository retriever pipeline

The active RAG pipeline is:

- [backend/app/ai/ingestion/scanner.py](/home/krishna/Desktop/AI Engineering Workspace/backend/app/ai/ingestion/scanner.py) scans `.py`, `.md`, and `.txt` files
- [backend/app/ai/ingestion/extractor.py](/home/krishna/Desktop/AI Engineering Workspace/backend/app/ai/ingestion/extractor.py) reads file contents
- [backend/app/ai/ingestion/chunker.py](/home/krishna/Desktop/AI Engineering Workspace/backend/app/ai/ingestion/chunker.py) chunks text for embedding
- [backend/app/rag/embeddings.py](/home/krishna/Desktop/AI Engineering Workspace/backend/app/rag/embeddings.py) encodes chunks using `SentenceTransformer("all-MiniLM-L6-v2")`
- [backend/app/rag/vector_store.py](/home/krishna/Desktop/AI Engineering Workspace/backend/app/rag/vector_store.py) stores vectors in FAISS
- [backend/app/rag/storage.py](/home/krishna/Desktop/AI Engineering Workspace/backend/app/rag/storage.py) persists `index.faiss` and `metadata.pkl`
- [backend/app/rag/index_manager.py](/home/krishna/Desktop/AI Engineering Workspace/backend/app/rag/index_manager.py) loads `.cortex` if present, otherwise returns an empty `VectorStore(dim=384)`
- [backend/app/rag/service.py](/home/krishna/Desktop/AI Engineering Workspace/backend/app/rag/service.py) exposes `search(query, top_k)`

Operational note:

- repository indexing is not rebuilt automatically on startup
- use [scripts/rebuild_index.py](/home/krishna/Desktop/AI Engineering Workspace/scripts/rebuild_index.py) to regenerate `.cortex`
- the rebuild script now skips saving if no indexable content is found

## Agent Utilities

### File Search Agent

[backend/app/agent/file_search.py](/home/krishna/Desktop/AI Engineering Workspace/backend/app/agent/file_search.py)

- keyword search across the workspace
- scans file names and text content
- skips hidden and dependency directories

### System Scanner

[backend/app/agent/system_scanner.py](/home/krishna/Desktop/AI Engineering Workspace/backend/app/agent/system_scanner.py)

- reports OS, Python runtime, free disk space, database presence, and migration count
- performs lightweight readiness checks only

## Database and Migrations

Database wiring:

- [backend/app/db/base.py](/home/krishna/Desktop/AI Engineering Workspace/backend/app/db/base.py)
- [backend/app/db/session.py](/home/krishna/Desktop/AI Engineering Workspace/backend/app/db/session.py)
- [migrations/env.py](/home/krishna/Desktop/AI Engineering Workspace/migrations/env.py)

Important migration detail:

- Alembic now imports both `User` and `Memory` so future autogeneration sees the full ORM metadata

## Tests

Test coverage currently includes:

- auth flows
- user CRUD and login
- AI gateway routing
- memory recall behavior
- RAG utilities

Test support files:

- [tests/conftest.py](/home/krishna/Desktop/AI Engineering Workspace/tests/conftest.py) creates isolated SQLite databases for tests and mocks `sentence_transformers`
- [tests/test_auth.py](/home/krishna/Desktop/AI Engineering Workspace/tests/test_auth.py)
- [tests/test_ai_gateway.py](/home/krishna/Desktop/AI Engineering Workspace/tests/test_ai_gateway.py)
- [tests/test_rag.py](/home/krishna/Desktop/AI Engineering Workspace/tests/test_rag.py)

## Current Limitations

- `docker-compose.yml` exists but is empty
- there is no frontend app yet
- automatic RAG rebuild at startup is intentionally disabled
- `README.md` is still sparse compared to the codebase
- system diagnostics are intentionally lightweight rather than production-grade observability

## Recent Fixes / Mismatches Resolved

- normalized `DEBUG` parsing so nonstandard environment values do not crash app import
- changed executor memory checks to use `user_id is not None`
- guarded the index rebuild script against empty content
- imported `Memory` in Alembic env so migrations stay aligned with the ORM
- updated this context file to match the actual route paths and current module structure
