# Cortex Workspace - Project Context

Last verified: 2026-06-03

## What This Project Is

Cortex Workspace is an AI operating system for a personal computer and, later, an online platform.

The goal is not just a chatbot. The goal is a local-first assistant that can:

- talk in a polished chat UI
- understand and search the whole laptop
- read and analyze local repositories
- find files, documents, and knowledge across the machine
- explain bugs, architecture, and codebase state
- help build projects like a senior engineering copilot
- switch between local models and popular hosted LLMs through API keys
- later expand into an online, multi-user, cloud-capable product
- eventually feel like the OS itself is intelligent and assistant-driven

If another AI model reads this file, it should understand the product vision immediately and know what kind of system to build next.

## Final Goal

The final product should become a full assistant layer for the computer:

- a local server starts the system
- a frontend chat interface gives the user a clean conversational experience
- the backend can search the laptop, repository, and memory
- the assistant can inspect and explain the repo, project state, and code bugs
- the assistant can answer questions like:
  - "Where is the PDF about transformers on my laptop?"
  - "What does this repository do?"
  - "What bugs or mismatches exist here?"
  - "Generate project context from the current codebase."
  - "Help me plan and build the next feature."
- the assistant can route to:
  - local models like Ollama or other local providers
  - hosted providers like OpenAI-compatible APIs, Anthropic-style APIs, or future providers
- the system stays expandable so local features can later become online features
- the final product has a strong CI/CD pipeline, testing, and deployable architecture

## Product Principles

- Local first, cloud optional
- Privacy aware by default
- Tool-driven, not prompt-only
- Modular and extensible
- Provider agnostic
- Repository aware
- OS aware
- Frontend first-class, not an afterthought
- Easy to grow from single-user desktop assistant to online platform

## Current Codebase State

The repo is currently a backend-first FastAPI application with:

- user authentication and profile APIs
- a graph-driven AI execution engine
- a reusable tool abstraction layer
- repository search and lightweight RAG
- persistent conversation memory
- file-system and system inspection agents

The repository does not yet have the final frontend experience. The top-level `docker-compose.yml` is currently empty.

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
- exposes a simple `GET /` root response

The app imports both the `User` and `Memory` ORM models so SQLAlchemy metadata is registered at startup.

## Configuration

Settings live in [backend/app/core/config.py](/home/krishna/Desktop/AI Engineering Workspace/backend/app/core/config.py).

Important values:

- `APP_NAME=Cortex Workspace`
- `API_V1_PREFIX=/api/v1`
- `DEBUG` is normalized defensively so values like `true`, `false`, `release`, `prod`, and `production` do not crash app import
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

The request flow is graph-based:

`API -> AIGateway -> AIExecutor -> IntentClassifier -> Planner.build_graph() -> GraphRunner -> ToolRegistry / Memory / LLM -> ResponseBuilder`

Relevant files:

- [backend/app/ai/gateway.py](/home/krishna/Desktop/AI Engineering Workspace/backend/app/ai/gateway.py)
- [backend/app/executor/executor.py](/home/krishna/Desktop/AI Engineering Workspace/backend/app/executor/executor.py)
- [backend/app/executor/intent_classifier.py](/home/krishna/Desktop/AI Engineering Workspace/backend/app/executor/intent_classifier.py)
- [backend/app/executor/planner.py](/home/krishna/Desktop/AI Engineering Workspace/backend/app/executor/planner.py)
- [backend/app/executor/graph.py](/home/krishna/Desktop/AI Engineering Workspace/backend/app/executor/graph.py)
- [backend/app/executor/graph_runner.py](/home/krishna/Desktop/AI Engineering Workspace/backend/app/executor/graph_runner.py)
- [backend/app/executor/tool_registry.py](/home/krishna/Desktop/AI Engineering Workspace/backend/app/executor/tool_registry.py)
- [backend/app/executor/tracer.py](/home/krishna/Desktop/AI Engineering Workspace/backend/app/executor/tracer.py)
- [backend/app/executor/response_builder.py](/home/krishna/Desktop/AI Engineering Workspace/backend/app/executor/response_builder.py)

Current executor behavior:

- classifies the query into an `IntentDecision` with `intent`, `confidence`, `confidence_level`, `subtype`, and `keywords`
- builds an execution graph rather than a flat plan
- runs a dedicated memory step first
- executes tool steps via the `ToolRegistry`
- runs the final LLM step after memory and tool dependencies are satisfied
- stores authenticated conversation memory after the response is generated
- passes the final assembled context to `ResponseBuilder`

Important implementation detail:

- `user_id` is checked with `is not None`, so `0` is not treated as missing
- `GraphRunner` records memory, tool, and LLM outputs back into state so the executor can rebuild the final response correctly
- built-in tool adapters are registered automatically for `file_search`, `system_scanner`, and `rag`

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

## Tool Framework

The reusable tool layer lives in [backend/app/tools/](/home/krishna/Desktop/AI Engineering Workspace/backend/app/tools/).

Key files:

- [backend/app/tools/base.py](/home/krishna/Desktop/AI Engineering Workspace/backend/app/tools/base.py)
- [backend/app/tools/metadata.py](/home/krishna/Desktop/AI Engineering Workspace/backend/app/tools/metadata.py)
- [backend/app/tools/builtins.py](/home/krishna/Desktop/AI Engineering Workspace/backend/app/tools/builtins.py)
- [backend/app/tools/discovery.py](/home/krishna/Desktop/AI Engineering Workspace/backend/app/tools/discovery.py)

Current state:

- `BaseTool` defines `decide()` and `run()` for autonomous execution
- `RegisteredTool` binds tools to metadata
- `ToolMetadata` holds capability hints, priority, and tags
- `ToolRegistry` auto-registers the built-in executor tools when an executor instance is passed in
- `discover_tools()` exists for future package-based tool discovery, but the current repo ships only the built-in adapters

## Database and Migrations

Database wiring:

- [backend/app/db/base.py](/home/krishna/Desktop/AI Engineering Workspace/backend/app/db/base.py)
- [backend/app/db/session.py](/home/krishna/Desktop/AI Engineering Workspace/backend/app/db/session.py)
- [migrations/env.py](/home/krishna/Desktop/AI Engineering Workspace/migrations/env.py)

Important migration detail:

- Alembic imports both `User` and `Memory` so future autogeneration sees the full ORM metadata

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
- the final laptop-wide OS assistant, frontend, and online platform are still vision goals, not finished product features

## Roadmap To The Final Goal

### Phase 1: Stable Local Assistant

- keep the local FastAPI backend reliable
- keep the graph executor, memory, and tools working together
- make the chat experience smooth and useful
- keep local model support stable via Ollama or other local providers

### Phase 2: Strong Desktop Intelligence

- add OS-wide file discovery and indexing
- expand repo understanding and bug analysis
- improve memory and contextual recall
- allow the assistant to answer questions about local files, docs, and codebases
- support project-building assistance, not just Q&A

### Phase 3: Provider Flexibility

- support switching between local and hosted providers
- keep provider configuration explicit and pluggable
- support multiple API-key-backed model vendors
- unify responses and tool usage across providers

### Phase 4: Frontend Experience

- build a polished chat UI
- show tool activity, memory, repo context, and file search results
- support conversational workflows and project management
- make the interface feel like an assistant operating system layer

### Phase 5: Platform Expansion

- make the backend ready for online use
- separate local-only and cloud-ready components
- add tenancy, auth, and infrastructure concerns where needed
- build a CI/CD pipeline for testing, deployment, and release automation

## What Future AI Should Do With This File

If a model reads this file, it should:

1. Understand the product vision first.
2. Treat the current repo as a local-first backend foundation.
3. Prefer changes that keep the system modular, provider-agnostic, and expandable.
4. Preserve support for local models and hosted models.
5. Improve the assistant’s real-world ability to inspect the laptop, repository, and project state.
6. Build toward a strong frontend, offline-first UX, and later online expansion.
7. Keep CI/CD, tests, and observability in the roadmap from the start.

## Recent Fixes / Mismatches Resolved

- normalized `DEBUG` parsing so nonstandard environment values do not crash app import
- changed executor memory checks to use `user_id is not None`
- fixed `AIExecutor` initialization order so `tool_registry` and `tracer` exist before `GraphRunner` is created
- wired graph execution state so memory, tool, and LLM outputs are preserved for final response building
- ensured the LLM step waits for memory and tool steps before running
- fixed `ExecutionTracer.report()` to read from sessions instead of a missing attribute
- fixed `ExecutionSession.created_at` to use a per-session timestamp
- added built-in tool adapters and auto-registration so graph tool steps can actually execute
- normalized graph runner tool outputs so responses use readable tool content instead of raw envelopes
- guarded the index rebuild script against empty content
- imported `Memory` in Alembic env so migrations stay aligned with the ORM
