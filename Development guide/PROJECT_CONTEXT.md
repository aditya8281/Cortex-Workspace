# Cortex Workspace - Project Context

Last verified: 2026-06-03

## What This Project Is

Cortex Workspace is a local-first AI workspace and repository intelligence system.
It is not just a chatbot.

The product is being shaped as a second brain for the computer:

- chat-first assistant workspace
- repository understanding and codebase reasoning
- workspace intelligence and activity feeds
- execution replay and debugging
- model routing across local and hosted providers
- memory, summaries, and knowledge graphs
- read-first filesystem discovery with approval gates for mutations

The current direction is:

- keep the UI minimal and productive
- make Cortex feel alive without turning it into a dashboard
- let Cortex read broadly across meaningful user files
- keep modification actions explicit and approval-driven

## Product Principles

- Local first, cloud optional
- Read broadly, modify carefully
- Chat-first, not trace-first
- Repository aware
- Memory aware
- Graph aware
- Provider agnostic
- Minimal but useful UI
- Safe autonomy with explicit approval for mutations

## Current High-Level Shape

The repository is currently a full-stack FastAPI + React application with:

- authenticated and guest chat flows
- execution routing and replay support
- persistent memory storage
- repository search and RAG foundations
- workspace intelligence reporting
- an activity feed for repository discoveries
- a system access and autonomy policy surface
- a responsive React/Vite/TypeScript frontend

## Runtime Entry Point

The application starts in [backend/app/main.py](../backend/app/main.py).

Behavior:

- sets up logging
- creates the FastAPI app
- mounts the API router under `/api/v1`
- exposes a simple health/status root endpoint
- initializes the backend services used by AI, execution, and state layers

## Configuration

Settings live in [backend/app/core/config.py](../backend/app/core/config.py).

Important values:

- `APP_NAME=Cortex Workspace`
- `API_V1_PREFIX=/api/v1`
- `WORKSPACE_ROOT` controls the main workspace root for scanning and indexing
- `DATABASE_URL` and `SECRET_KEY` come from the environment or `.env`
- AI configuration is controlled by:
  - `AI_MODE`
  - `AI_MODEL`
  - `AI_API_KEY`
  - `AI_API_URL`
  - `LOCAL_MODEL`
  - `OLLAMA_URL`

## API Surface

Routing is assembled in [backend/app/api/router.py](../backend/app/api/router.py).

Current top-level API groups:

- health
- users
- authentication
- AI chat and ask
- execution and replay
- model management
- user settings
- workspace intelligence

Important endpoints:

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
- `GET /api/v1/workspace/intelligence`
- `GET /api/v1/models/installed`
- `POST /api/v1/models/pull`
- `DELETE /api/v1/models/{model_name}`
- `GET /api/v1/users/me/settings`
- `PUT /api/v1/users/me/settings`

## Authentication

Authentication helpers live in [backend/app/core/security.py](../backend/app/core/security.py).

Behavior:

- passwords are hashed before storage
- tokens are JWTs
- protected endpoints resolve the current user from bearer auth
- the frontend supports sign-in, registration, and sign-out flows
- API credentials can be stored in user settings for authenticated usage

## AI and Execution Layer

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

- **Intent-Driven Routing**: Every incoming user query is classified before execution (into CHAT, TOOL, RAG, or SYSTEM intent) to avoid unnecessary tool overhead.
- **Weighted Graph Execution Planning**: Unlike flat linear agent execution, Cortex structures reasoning using a directed acyclic execution graph (`ExecutionGraph`). The planner orders tasks, starting from `memory_step` and feeding outputs downstream to `tool_step_i` before final synthesis in `llm_step`.
- **Feedback & Tool Bias**: Execution includes real-time feedback logging. Successful tool runs build up positive score bias for future selections, optimizing overall planning accuracy.
- **DFS-Based Context Expansion**: When building prompt context, directories and file structures are crawled recursively using Depth-First-Search (DFS) to build context lists, respecting exclusions and boundaries.
- **Incremental & Persistent Memory**: Previous queries and responses are stored in a local SQLite database for fast local retrieval. Relevant context is injected back into the execution flow through the `memory_recall` step.

## Providers

Provider selection lives in [backend/app/ai/providers/registry.py](../backend/app/ai/providers/registry.py).

Supported modes:

- `local` -> [backend/app/ai/local_llm.py](../backend/app/ai/local_llm.py) (uses Ollama to execute offline local queries; supports model customization, e.g., llama3, qwen3:8b)
- `api` -> [backend/app/ai/api_llm.py](../backend/app/ai/api_llm.py) (routes to external hosted REST endpoints like OpenAI/Anthropic/compatible APIs)

The router acts as a dynamic hybrid mode switch. This architecture allows Cortex to remain local-first while allowing heavy cloud fallback processing when local models hit context limitations.

## RAG and Repository Search

Current retrieval and indexing pieces:

- [backend/app/ai/ingestion/scanner.py](../backend/app/ai/ingestion/scanner.py)
- [backend/app/ai/ingestion/extractor.py](../backend/app/ai/ingestion/extractor.py)
- [backend/app/ai/ingestion/chunker.py](../backend/app/ai/ingestion/chunker.py)
- [backend/app/rag/embeddings.py](../backend/app/rag/embeddings.py)
- [backend/app/rag/vector_store.py](../backend/app/rag/vector_store.py)
- [backend/app/rag/storage.py](../backend/app/rag/storage.py)
- [backend/app/rag/index_manager.py](../backend/app/rag/index_manager.py)
- [backend/app/rag/service.py](../backend/app/rag/service.py)
- [backend/app/rag/retriever.py](../backend/app/rag/retriever.py)

Important behavior:

- **AST-Aware Structural Chunking**: The text chunker (`TextChunker`) supports language-aware parsing. For Python files, it uses the AST module to segment classes and functions into discrete context units. Other code bases fall back on regular expression pattern matching.
- **Semantic Codebase Retrieval**: Extracts text and code files, creates vector representations using local embedding models (`BAAI/bge-small-en-v1.5`), and indexes them into FAISS.
- **Hybrid Retrieval Reranking**: When a query is made, FAISS returns semantic candidates. The retriever (`RepoRetriever`) performs a hybrid scoring pass, adding keyword match boosts (based on exact word boundaries and substring matching) to the semantic scores to rank chunks before injecting them into prompt templates.
- **Incremental Indexing**: Uses filesystem modification timestamps (`mtime`) stored in `.cortex/filesystem_index_state.json` to process changes dynamically, bypassing unmodified files to keep indexing fast.
- **Multi-File Patch Generation**: Context compiler builds detailed, file-linked codebases for the LLM to construct multi-file code modifications, which are staged in a pending state awaiting user verification and approval.

Operational note:

- Repository indexing is run automatically during the new setup pipeline or triggered via the `/api/v1/workspace/sync` endpoint.
- Rebuilding the vector store updates the local `.cortex` folder.


## Workspace Intelligence

The current workspace intelligence endpoint lives in [backend/app/api/v1/workspace.py](../backend/app/api/v1/workspace.py).

The backing service is [backend/app/services/workspace_intelligence_service.py](../backend/app/services/workspace_intelligence_service.py).

It now produces a structured report containing:

- project purpose
- architecture summary
- repository list
- concept list
- repository model
- dependency graph
- module graph
- knowledge graph
- query classification guidance
- memory summary
- activity feed
- system access and autonomy policy
- entrypoints
- APIs
- build process
- key files
- warnings
- evidence snippets

### Activity Feed

The activity feed is meant to make Cortex feel alive without intrusive notifications.

Examples:

- Cortex indexed 3 new repositories
- Cortex learned 12 new concepts
- Cortex found 4 TODOs
- Cortex detected architecture changes

### System Access and Autonomy

The workspace report now exposes a clear permission model:

- Observation Mode: read-only
- Approval Mode: default
- Automated Mode: allowed for selected safe categories

Read actions are treated as normal system behavior.
Modify actions remain approval-driven.

Ignored OS paths include:

- `/proc`
- `/sys`
- `/dev`
- `/run`
- `/tmp`

The intent is:

- read broadly across meaningful user data
- avoid indexing OS noise
- keep the user in control of any state changes

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
- `/api/v1/execution/{execution_id}/replay` returns replay metadata and timeline data
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

Current UI direction:

- chat-first assistant workspace
- minimal top bar with auth access
- left history rail
- centered conversation area
- utility drawer for traces, config, workspace intelligence, and admin tools
- compact, premium, techy visual treatment

Frontend behavior:

- messages are rendered in a centered conversation column
- auth actions are accessible at the top
- config and workspace intelligence are available on demand
- traces are hidden until needed instead of dominating the layout
- the workspace drawer now includes activity feed, repository model, graphs, and system access policy

## Current State of the Repository

The repo currently includes:

- backend APIs for AI, execution, models, users, settings, health, and workspace intelligence
- a React interface that is more product-like and chat-oriented
- a broad read-only scanner for meaningful user files
- structured workspace intelligence that models the repository as a graph
- explicit permission and autonomy guidance

## Near-Term Direction

The next useful expansions are:

- a real background observer/indexer for new files and repositories
- semantic search across the broader read scope
- explicit user-configurable autonomy levels in settings
- richer memory persistence for repo decisions and architecture notes
- more detailed import, symbol, and dependency graph traversal
- proactive, low-noise discovery notifications
- permission-aware modification workflows

## What Future AI Should Do With This File

When another AI model reads this file, it should:

1. Treat the current chat-first workspace as the default product shape.
2. Preserve the read-first, approval-driven system access model.
3. Keep workspace intelligence structured and graph-based.
4. Prefer production-grade fixes over quick hacks.
5. Avoid reintroducing a dashboard-first layout.
6. Keep the repo extensible toward richer indexing and autonomous observation.

