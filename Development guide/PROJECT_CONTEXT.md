# Cortex Workspace - Project Context

Last verified: 2026-06-03

## What This Project Is

Cortex Workspace is not just a chatbot.

It is being built as a local-first AI operating system and engineering platform for a personal computer, with a path to a later online product.

The core goal is to make the machine feel assistant-driven:

- a polished chat UI
- local server-based execution
- whole-laptop awareness
- repository awareness
- file and document search across the machine
- bug finding and codebase explanation
- model switching across local and hosted providers
- execution replay and debugging
- tool orchestration and observability
- a foundation that can later become cloud-capable

If another AI model reads this file, it should immediately understand the product direction and the expected architecture.

## Final Goal

The final product should behave like an AI layer on top of the computer:

- the user runs a local server
- the UI provides a good chat-first workspace
- the backend can inspect files, repos, memories, and execution traces
- the assistant can answer questions like:
  - where a PDF or document lives on the laptop
  - what a repository does
  - what bugs or mismatches exist in the codebase
  - how to generate project context from the current repo state
  - how to plan and build the next feature
- the system can route requests to:
  - local models such as Ollama or other local providers
  - hosted providers through API keys
- the platform stays expandable so local-only features can later become online features
- the project eventually gets proper testing, CI/CD, and deployable architecture

## Product Principles

- Local first, cloud optional
- Privacy aware by default
- Tool-driven, not prompt-only
- Modular and extensible
- Provider agnostic
- Repository aware
- OS aware
- Frontend is first-class
- Built for single-user desktop use first, then platform expansion

## Current Codebase State

The repository is currently a backend-first FastAPI application with:

- user authentication and profile APIs
- a graph-driven AI execution engine
- structured tool results
- tool fusion and tool intelligence scoring
- an adaptive tool feedback loop
- repository search and lightweight RAG
- persistent conversation memory
- file-system and system inspection agents
- execution state persistence for replay and debugging
- a React/Vite/TypeScript frontend workspace

## Runtime Entry Point

The application starts in [backend/app/main.py](../backend/app/main.py).

Behavior:

- calls `setup_logging()`
- creates the FastAPI app
- registers `RequestLoggingMiddleware`
- mounts the API router under `/api/v1`
- exposes `GET /` as a basic status endpoint

The app imports the ORM models that need metadata registration at startup.

## Configuration

Settings live in [backend/app/core/config.py](../backend/app/core/config.py).

Important values:

- `APP_NAME=Cortex Workspace`
- `API_V1_PREFIX=/api/v1`
- `DEBUG` is normalized defensively
- `DATABASE_URL` and `SECRET_KEY` come from the environment or `.env`
- AI settings are read from `AI_MODE`, `AI_MODEL`, `AI_API_KEY`, `AI_API_URL`, and `LOCAL_MODEL`

## API Surface

Routing is assembled in [backend/app/api/router.py](../backend/app/api/router.py).

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
- `GET /api/v1/execution`
- `GET /api/v1/execution/{execution_id}`
- `GET /api/v1/execution/{execution_id}/replay`
- `GET /api/v1/execution/{execution_id}/tools`

Important note:

- the execution router is mounted at `/api/v1/execution`, so the handler paths are relative and must not repeat `/execution`

## Data Model

### Users

The user ORM model is in [backend/app/models/user.py](../backend/app/models/user.py).

Fields:

- `id`
- `email`
- `full_name`
- `hashed_password`
- `role`

### Memories

The memory ORM model is in [backend/app/ai/memory/models.py](../backend/app/ai/memory/models.py).

Fields:

- `id`
- `user_id`
- `query`
- `response`
- `created_at`

## Authentication

Authentication helpers live in [backend/app/core/security.py](../backend/app/core/security.py).

Behavior:

- passwords are hashed before storage
- tokens are JWTs with an `exp` claim
- `get_current_user()` decodes the bearer token and loads the user
- `/api/v1/me` is protected by `HTTPBearer`

## AI Layer

### Execution Flow

The current execution flow is:

`API -> AIGateway -> AIExecutor -> IntentClassifier -> Planner -> GraphRunner -> ToolRegistry / Memory / LLM -> ResponseBuilder`

Relevant files:

- [backend/app/ai/gateway.py](../backend/app/ai/gateway.py)
- [backend/app/executor/executor.py](../backend/app/executor/executor.py)
- [backend/app/executor/intent_classifier.py](../backend/app/executor/intent_classifier.py)
- [backend/app/executor/planner.py](../backend/app/executor/planner.py)
- [backend/app/executor/graph.py](../backend/app/executor/graph.py)
- [backend/app/executor/graph_runner.py](../backend/app/executor/graph_runner.py)
- [backend/app/executor/tool_registry.py](../backend/app/executor/tool_registry.py)
- [backend/app/executor/tool_intelligence.py](../backend/app/executor/tool_intelligence.py)
- [backend/app/executor/tool_fusion.py](../backend/app/executor/tool_fusion.py)
- [backend/app/executor/context_compiler.py](../backend/app/executor/context_compiler.py)
- [backend/app/executor/tool_feedback.py](../backend/app/executor/tool_feedback.py)
- [backend/app/executor/tracer.py](../backend/app/executor/tracer.py)
- [backend/app/executor/response_builder.py](../backend/app/executor/response_builder.py)

Current behavior:

- the query is classified into an `IntentDecision`
- the planner builds a graph rather than a flat plan
- the graph always starts with memory recall
- tools are selected from intent plus tool bias
- the graph runner executes memory, tool, and LLM steps
- tool execution is routed through the tool registry
- tool results are structured with `ToolResult`
- tool fusion removes duplication and noisy outputs
- tool intelligence ranks results before synthesis
- the final LLM step compiles context from memory plus tools
- the response builder turns the assembled context into the final answer

Important implementation details:

- `user_id` is checked with `is not None`
- `GraphRunner` is the main emitter for execution events
- `StateManager` plus `StateStore` is the persisted source of truth for replayable executions
- `ExecutionTracer` is for timing and step tracing, not the replay source of truth
- built-in tools are registered automatically
- tool execution now flows through the shared tool abstraction

## Providers

Provider selection lives in [backend/app/ai/providers/registry.py](../backend/app/ai/providers/registry.py).

Supported modes:

- `local` -> [backend/app/ai/local_llm.py](../backend/app/ai/local_llm.py) via Ollama-style local generation
- `api` -> [backend/app/ai/api_llm.py](../backend/app/ai/api_llm.py) via an OpenAI-compatible request shape

The router is a simple mode switch right now.

## RAG and Repository Search

There are two chunkers in the repo:

- [backend/app/rag/text_chunker.py](../backend/app/rag/text_chunker.py)
- [backend/app/ai/ingestion/chunker.py](../backend/app/ai/ingestion/chunker.py)

The active RAG pipeline is:

- [backend/app/ai/ingestion/scanner.py](../backend/app/ai/ingestion/scanner.py) scans source files
- [backend/app/ai/ingestion/extractor.py](../backend/app/ai/ingestion/extractor.py) reads file contents
- [backend/app/ai/ingestion/chunker.py](../backend/app/ai/ingestion/chunker.py) chunks text
- [backend/app/rag/embeddings.py](../backend/app/rag/embeddings.py) generates embeddings
- [backend/app/rag/vector_store.py](../backend/app/rag/vector_store.py) stores vectors in FAISS
- [backend/app/rag/storage.py](../backend/app/rag/storage.py) persists the index files
- [backend/app/rag/index_manager.py](../backend/app/rag/index_manager.py) loads the local index
- [backend/app/rag/service.py](../backend/app/rag/service.py) exposes search

Operational note:

- repository indexing is not rebuilt automatically on startup
- use [scripts/rebuild_index.py](../scripts/rebuild_index.py) to regenerate the local index

## State and Replay

Current state modules:

- [backend/app/state/manager.py](../backend/app/state/manager.py)
- [backend/app/state/models.py](../backend/app/state/models.py)
- [backend/app/state/registry.py](../backend/app/state/registry.py)
- [backend/app/state/events.py](../backend/app/state/events.py)
- [backend/app/state/store.py](../backend/app/state/store.py)

Purpose:

- persist execution events
- keep an in-memory state registry
- support execution listing
- support replay and debugging

Replay behavior:

- `ExecutionReplayEngine` reads persisted events from SQLite
- `/api/v1/execution/{execution_id}/replay` returns:
  - `execution_id`
  - `status`
  - `summary`
  - `replay`
- `/api/v1/execution` returns execution list items for the frontend sidebar

## Frontend

Frontend stack:

- React
- Vite
- TypeScript

Current tree:

- [frontend/src/App.tsx](../frontend/src/App.tsx)
- [frontend/src/App.css](../frontend/src/App.css)
- [frontend/src/index.css](../frontend/src/index.css)
- [frontend/src/api](../frontend/src/api)

Current UI:

- 3-column workspace
- left: execution list
- center: execution timeline
- right: inspector

Current frontend state:

- the execution list is now backed by the backend execution list endpoint
- the replay panel reads from the replay API
- the inspector reads summary data from the same replay response

## Current Phase

Phase 1 completion work.

Primary objectives:

1. Stable execution IDs
2. Execution event persistence
3. Replay engine reliability
4. Replay API stabilization
5. Timeline UI stabilization
6. Inspector UI stabilization
7. Tool usage analytics
8. Execution debugging foundation

## Future Direction

After the local assistant is stable, the next major expansions are:

- richer model routing
- better OS-wide file intelligence
- stronger repo indexing and context generation
- online/cloud mode
- collaboration features
- CI/CD hardening
- production deployment readiness

## What Future AI Should Do With This File

When another AI model reads this file, it should:

1. Treat the local-first AI OS assistant vision as the top priority.
2. Keep the execution replay pipeline consistent with the backend event store.
3. Preserve the 3-panel frontend workspace pattern.
4. Prefer production-grade fixes over quick hacks.
5. Avoid reintroducing duplicate observability paths.
6. Keep the codebase expandable toward online and multi-provider support.
