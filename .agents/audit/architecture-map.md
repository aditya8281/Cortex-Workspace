# Cortex Architecture Map

**Generated:** 2026-06-22
**Scope:** Complete system architecture — data flows, service boundaries, ownership, and risks

---

## Table of Contents

1. [System Overview](#system-overview)
2. [High-Level Architecture Diagram](#high-level-architecture-diagram)
3. [Data Flow](#data-flow)
4. [API Flow](#api-flow)
5. [Agent Flow](#agent-flow)
6. [Memory Flow](#memory-flow)
7. [Retrieval Flow (RAG)](#retrieval-flow-rag)
8. [Model Flow](#model-flow)
9. [Sync Flow](#sync-flow)
10. [State Flow](#state-flow)
11. [Service Boundaries](#service-boundaries)
12. [Ownership Boundaries](#ownership-boundaries)
13. [Sources of Truth](#sources-of-truth)
14. [Dependencies](#dependencies)
15. [Risks & Single Points of Failure](#risks--single-points-of-failure)
16. [Areas Requiring Deeper Investigation](#areas-requiring-deeper-investigation)

---

## System Overview

Cortex is a "cognitive operating layer for personal computing" — a full-stack application that:

- Indexes code repositories and documents into a searchable knowledge graph
- Provides AI-powered agents that can plan, execute, and reason over code
- Manages local LLM inference via llama.cpp and Ollama providers
- Maintains persistent long-term memory with decay/confidence mechanics
- Offers encrypted per-user vault storage
- Syncs file changes via filesystem watchers

### Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 15 (App Router), React 19, TypeScript, Tailwind CSS |
| UI Components | Radix UI, framer-motion, cmdk, Three.js (Neural Network bg) |
| Backend | FastAPI (Python 3.12+) |
| ORM | SQLAlchemy 2.0 + Alembic |
| Database | PostgreSQL 16 |
| Vector DB | Qdrant (embedded, port 6333) |
| Cache/PubSub | Redis 7 (optional, graceful fallback) |
| Embeddings | ONNX Runtime (BGE-M3) or Ollama fallback |
| LLM Inference | llama.cpp, Ollama (provider abstraction) |
| Task Queue | arq (Redis-based) |
| Auth | JWT (httpOnly cookies) + Argon2 |
| Encryption | Fernet + PBKDF2 (vault), Fernet (GitHub token) |

---

## High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND (Next.js 15)                    │
│                        http://localhost:3000                     │
│                                                                 │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐           │
│  │ AuthPage │ │Dashboard │ │ Vault    │ │  Models  │           │
│  │ /auth    │ │ /app     │ │ /vault   │ │ /models  │           │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘           │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐           │
│  │  Agents  │ │  Chat    │ │  Search  │ │ Memory   │           │
│  │ /agents  │ │ /chat    │ │ /search  │ │ /memory  │           │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘           │
│                                                                 │
│  ┌─────────────────────────────────────────────────────┐       │
│  │  Shared Layer: AuthProvider, cortexApi, DashboardShell│       │
│  │  API clients: agent.ts, models.ts, search.ts, etc.   │       │
│  └─────────────────────┬───────────────────────────────┘       │
└────────────────────────┼────────────────────────────────────────┘
                         │ HTTP (CORS / Next.js proxy)
                         │ Credentials: httpOnly cookies
                         │ CSRF: double-submit token
┌────────────────────────▼────────────────────────────────────────┐
│                        BACKEND (FastAPI)                         │
│                        http://localhost:8000                     │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                     Middleware Stack                      │   │
│  │  CORS → RequestLogging → GZip → RequestSizeLimit →       │   │
│  │  RateLimit → CSRF → HTTPSRedirect                        │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    API Router Layer                       │   │
│  │  /api/v1/auth/*    /api/v1/users/*    /api/v1/me/*       │   │
│  │  /api/v1/repos    /api/v1/agents     /api/v1/models     │   │
│  │  /api/v1/search   /api/v1/conversations                  │   │
│  │  /api/v1/sync     /api/v1/indexing   /api/v1/knowledge  │   │
│  │  /api/v1/long-term-memory                                 │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────────────┐    │
│  │  Auth Layer  │ │ Agent Layer  │ │    Service Layer      │    │
│  │  deps.py     │ │ base.py      │ │  llm/manager.py       │    │
│  │  security.py │ │ planner.py   │ │  embedding_service.py │    │
│  │  db.py       │ │ executor.py  │ │  hybrid_retrieval.py  │    │
│  │              │ │ run_mgr.py   │ │  rag_pipeline.py      │    │
│  │              │ │ tools.py     │ │  conversation_svc.py  │    │
│  │              │ │              │ │  long_term_memory.py  │    │
│  └──────────────┘ └──────────────┘ │  sync_service.py      │    │
│                                     │  file_watcher_v2.py   │    │
│                                     │  model_downloader.py  │    │
│                                     │  vault_service.py     │    │
│                                     │  repo_scanner.py      │    │
│                                     │  graph_builder.py     │    │
│                                     └──────────────────────┘    │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    Model Layer (SQLAlchemy)               │   │
│  │  User, AuthEvent, Agent, AgentRun, AgentStep,            │   │
│  │  Conversation, ConversationMessage, LongTermMemory,      │   │
│  │  RepoIndex, CodeChunk, GraphNode, GraphEdge,             │   │
│  │  ModelCatalog, ModelVariant, ModelDownload, Provider,     │   │
│  │  Document, DocumentChunk, SyncState, etc.                │   │
│  └──────────────────────────────────────────────────────────┘   │
└──────┬────────────────┬────────────────────┬────────────────────┘
       │                │                    │
  ┌────▼────┐    ┌──────▼──────┐    ┌───────▼───────┐
  │PostgreSQL│    │   Qdrant    │    │     Redis     │
  │  (port   │    │  (port 6333)│    │  (port 6379)  │
  │  5432)   │    │  vectors    │    │  cache/queue   │
  └──────────┘    └─────────────┘    └───────────────┘
       │
  ┌────▼──────────────────────┐
  │     Filesystem Layer       │
  │  CortexMemory/ (shared)    │
  │  <storage_root>/ (per-user)│
  │  Watched repos (sync)      │
  └───────────────────────────┘
```

---

## Data Flow

### User Input → Processing → Storage → Retrieval

```
User Action
    │
    ├─→ [Frontend] React state + API client (cortexApi.ts / api/*.ts)
    │       │
    │       ▼
    ├─→ [HTTP] POST/GET/PUT/DELETE → /api/v1/* or /api/auth/*
    │       │
    │       ▼
    ├─→ [FastAPI Middleware] CORS → Logging → GZip → SizeLimit → RateLimit → CSRF
    │       │
    │       ▼
    ├─→ [Router] api/router.py dispatches to domain-specific router
    │       │
    │       ├─→ [Auth Check] get_current_user() extracts JWT from cookie/header
    │       │       │
    │       │       ▼
    │       │   verify_access_token() → JWT decode → Redis revocation check
    │       │       │
    │       │       ▼
    │       │   db.query(User).filter(User.id == user_id)
    │       │
    │       ▼
    ├─→ [Service Layer] Business logic (services/*.py)
    │       │
    │       ├─→ [DB Write] SQLAlchemy ORM → PostgreSQL
    │       ├─→ [Vector Write] Qdrant upsert (embeddings)
    │       ├─→ [File Write] Vault encryption / filesystem
    │       └─→ [Cache Write] Redis set
    │
    └─→ [Response] JSON → HTTP → Frontend state update → UI render
```

### Key Data Stores

| Store | Purpose | Data Types |
|-------|---------|------------|
| PostgreSQL | Primary relational data | Users, agents, conversations, repos, indexes, models, memories |
| Qdrant | Vector embeddings | Code chunks, document chunks, knowledge entries |
| Redis | Caching, rate limiting, token revocation | Session tokens, rate limit counters, cached queries |
| Filesystem | File storage, vault, index state | Vault files (encrypted), repo indexes, sync state |

---

## API Flow

### Request Lifecycle (Authenticated Endpoint)

```
1. Frontend: fetch("/api/v1/agents", { credentials: "include" })
   │  - Cookie: cortex_access=JWT, cortex_refresh=JWT, cortex_csrf=TOKEN
   │  - Header: x-csrf-token: TOKEN
   │
2. Next.js Proxy (optional): forwards /api/* to backend:8000
   │  - Passes cookies through
   │
3. FastAPI Middleware Stack:
   │  CORS → validates Origin header
   │  RequestLoggingMiddleware → adds request_id to contextvars
   │  GZip → decompresses if needed
   │  RequestSizeLimitMiddleware → rejects >10MB (2MB for uploads)
   │  RateLimit → checks Redis counters (100 req/60s default)
   │  CSRF → validates double-submit cookie (exempt for Bearer auth)
   │
4. Router: api/router.py → agents_router
   │
5. Dependency Injection:
   │  db = Depends(get_db)  → SessionLocal() → PostgreSQL connection
   │  user = Depends(get_current_user)  → JWT verify → User query
   │
6. Endpoint Handler:
   │  - Validates input (Pydantic schemas)
   │  - Calls service layer
   │  - Returns response_model=AgentResponse
   │
7. Response: JSON → HTTP 200 → Frontend
```

### Auth Flow (Cookie-Based JWT)

```
Register/Login:
  POST /api/v1/auth/register or /login
    → backend validates credentials
    → creates JWT access token (30min) + refresh token (7 days)
    → sets httpOnly cookies: cortex_access, cortex_refresh
    → sets csrf cookie: cortex_csrf
    → returns user object

Request:
  Any authenticated request
    → cookies sent automatically
    → backend extracts JWT from cortex_access cookie (or Authorization header)
    → verifies signature + checks revocation in Redis

Refresh:
  POST /api/v1/auth/refresh (with cortex_refresh cookie)
    → validates refresh token
    → rotates: issues new access + refresh, revokes old
    → updates cookies

Logout:
  POST /api/v1/auth/logout
    → revokes refresh token in Redis
    → locks vault
    → clears cookies
```

---

## Agent Flow

### Agent Creation → Dispatch → Execution → Results

```
┌─────────────────────────────────────────────────────────────┐
│                    AGENT SYSTEM                              │
│                                                             │
│  1. Agent Definition (DB: agents table)                     │
│     │  - name, description, system_prompt                   │
│     │  - model_id (which LLM to use)                       │
│     │  - tools_json (allowed tools list)                    │
│     │  - user_id (ownership)                                │
│     │                                                       │
│  2. Agent Run Creation                                      │
│     │  POST /api/v1/agents/{id}/run                         │
│     │  → AgentRunManager.create_run(agent_id, user_id, input)│
│     │  → Creates AgentRun record (status=pending)           │
│     │                                                       │
│  3. Planning Phase                                          │
│     │  AgentRunManager.run_agent()                          │
│     │  → PlannerAgent.plan(task)                            │
│     │    ├─ With LLM: sends system prompt + task to LLM     │
│     │    │  → Parses JSON plan from response                │
│     │    └─ Without LLM: returns single-step plan           │
│     │  → Plan = list of {goal, agent, dependencies,         │
│     │                    expected_output}                    │
│     │                                                       │
│  4. Execution Phase                                         │
│     │  For each step in plan:                               │
│     │  → Create AgentStep record (status=running)           │
│     │  → ExecutorAgent.run(goal, context)                   │
│     │    ├─ With LLM: tool-calling loop (max 10 iterations) │
│     │    │  → LLM decides which tools to call               │
│     │    │  → execute_tool(name, **kwargs)                  │
│     │    │  → Appends results to messages                   │
│     │    │  → Returns when LLM produces final answer        │
│     │    └─ Without LLM: keyword-based fallback routing     │
│     │       → "search" → _search_tool()                    │
│     │       → "read" → _read_file_tool()                   │
│     │       → "list" → _list_files_tool()                  │
│     │                                                       │
│  5. Available Tools                                         │
│     │  Built-in: search, read_file, write_file, list_files  │
│     │  Registry: tools.py TOOL_REGISTRY                     │
│     │  Approval: requires_approval() for dangerous ops      │
│     │                                                       │
│  6. Completion                                              │
│     → AgentRun.status = "completed"                         │
│     → AgentRun.output = last step result                    │
│     → SSE events emitted for real-time UI updates           │
│                                                             │
│  7. Feedback                                                │
│     POST /api/v1/agents/runs/{id}/feedback                  │
│     → AgentFeedback (rating 1-5, comment)                   │
└─────────────────────────────────────────────────────────────┘
```

### Agent Architecture

```
                    ┌─────────────────┐
                    │   AgentRunManager│
                    │  (orchestrator)  │
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
    ┌─────────▼──────┐ ┌────▼─────┐ ┌──────▼──────┐
    │ PlannerAgent   │ │ Executor │ │ LLM Manager │
    │ (task → plan)  │ │ Agent    │ │ (llm/       │
    │                │ │ (tool    │ │  manager.py)│
    │ - LLM planning │ │  use)    │ │             │
    │ - JSON parse   │ │          │ │ - llama.cpp │
    │ - Simple plan  │ │ - search │ │ - ollama    │
    │   fallback     │ │ - read   │ │ - auto      │
    └────────────────┘ │ - write  │ └─────────────┘
                       │ - list   │
                       └──────────┘
```

---

## Memory Flow

### Long-Term Memory Lifecycle

```
┌─────────────────────────────────────────────────────────────┐
│                  LONG-TERM MEMORY SYSTEM                     │
│                                                             │
│  Creation Sources:                                          │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐        │
│  │ Conversation │ │   Manual     │ │   Agent      │        │
│  │  Pipeline    │ │  Creation    │ │  Extraction  │        │
│  └──────┬───────┘ └──────┬───────┘ └──────┬───────┘        │
│         │                │                │                  │
│         └────────────────┼────────────────┘                  │
│                          │                                   │
│                          ▼                                   │
│              LongTermMemoryService.create()                  │
│              → category: preference|pattern|correction|      │
│                          fact|context                        │
│              → confidence: 0.5 (initial)                     │
│              → access_count: 0                               │
│              → tags: []                                      │
│                                                             │
│  Storage: PostgreSQL (long_term_memories table)              │
│  - No vector embeddings (text search only via ILIKE)         │
│  - Decay: confidence *= 0.95 after 30 days inactive         │
│  - Reinforce: confidence += 0.1 on access                   │
│                                                             │
│  Retrieval:                                                 │
│  - search(user_id, query, category, min_confidence)         │
│  - Ordered by confidence DESC                                │
│  - Filtered by is_active=True, confidence >= threshold      │
│                                                             │
│  Conversation-to-Memory Pipeline:                           │
│  ConversationService.extract_insights()                     │
│  → LLM analyzes conversation                                │
│  → Extracts insights (category, title, content)             │
│  → Stores via LongTermMemoryService.create()                │
│  → Source tracking: source="conversation", source_id=conv_id│
└─────────────────────────────────────────────────────────────┘
```

### Knowledge Entry Memory

```
Knowledge Entry (knowledge_entries table)
    │
    ├─→ Embedding Service → Qdrant (cortex_memory collection)
    │   - ONNX (BGE-M3) → Ollama fallback → Mock fallback
    │   - Vector stored with payload: {content, category, tags, user_id}
    │
    ├─→ Memory Manager (memory_manager.py)
    │   - CRUD operations
    │   - Vector search via Qdrant
    │   - Semantic search over knowledge
    │
    └─→ Unified Search (/api/v1/search)
        - Combines: vector + fulltext + graph
```

---

## Retrieval Flow (RAG)

### End-to-End RAG Pipeline

```
┌─────────────────────────────────────────────────────────────┐
│                    RAG PIPELINE                              │
│                                                             │
│  1. Query Input                                             │
│     User message → /api/v1/conversations/{id}/messages      │
│                                                             │
│  2. Context Retrieval (RAGPipeline.retrieve_context)         │
│     │                                                       │
│     ├─→ HybridRetrievalV2.retrieve(query, repo_id)          │
│     │   │                                                   │
│     │   ├─→ Vector Search (Qdrant)                          │
│     │   │   ├─ Collection: cortex_code (code chunks)        │
│     │   │   ├─ Collection: cortex_memory (knowledge)        │
│     │   │   ├─ Query: embed_single(query) → 768-dim vector │
│     │   │   ├─ Filter: repo_id (if specified)               │
│     │   │   └─ Returns: content, file_path, score, etc.     │
│     │   │                                                   │
│     │   ├─→ Fulltext Search (PostgreSQL ts_vector)          │
│     │   │   ├─ Search code_chunks (GIN index)               │
│     │   │   └─ Search document_chunks (GIN index)           │
│     │   │                                                   │
│     │   └─→ Graph Search (optional)                         │
│     │       ├─ Find nodes matching query terms              │
│     │       └─ Traverse edges to connected nodes            │
│     │                                                       │
│     ├─→ RRF Merge (Reciprocal Rank Fusion)                  │
│     │   - K=60 constant                                     │
│     │   - Combines rankings from all sources                │
│     │                                                       │
│     ├─→ Deduplication                                       │
│     │   - By file_path + line ranges                        │
│     │   - Overlap detection (>50% overlap = duplicate)      │
│     │                                                       │
│     └─→ MMR Rerank (Maximal Marginal Relevance)            │
│         - λ=0.3 (relevance vs diversity)                    │
│         - Text similarity via word overlap                   │
│                                                             │
│  3. Message Construction                                    │
│     │                                                       │
│     ├─→ System prompt + retrieved context (formatted)       │
│     │   - Citations: [1], [2], etc.                         │
│     │   - Max 4000 tokens, max 8 results                    │
│     │                                                       │
│     ├─→ Conversation history (token-budgeted)               │
│     │   - Max 28000 tokens                                  │
│     │   - Most recent messages kept first                   │
│     │                                                       │
│     └─→ User message                                       │
│                                                             │
│  4. LLM Call                                                │
│     llm_manager.chat(messages) → streaming response          │
│                                                             │
│  5. Response Storage                                        │
│     → ConversationMessage (role=assistant)                  │
│     → Token counting (prompt + completion)                  │
│                                                             │
│  6. Post-Processing                                         │
│     → ConversationService.extract_insights()                │
│     → Stores insights as LongTermMemory                     │
└─────────────────────────────────────────────────────────────┘
```

### Embedding Pipeline

```
Text Input
    │
    ▼
EmbeddingService.embed(text)
    │
    ├─→ ONNX Backend (if model_path set + onnxruntime installed)
    │   ├─ Tokenize via transformers.AutoTokenizer
    │   ├─ Run ONNX inference session
    │   └─ Return 768-dim vector
    │
    ├─→ Ollama Backend (if httpx installed)
    │   ├─ POST http://localhost:11434/api/embeddings
    │   ├─ model: nomic-embed-text (configurable)
    │   └─ Return embedding vector
    │
    └─→ Mock Fallback (last resort)
        ├─ MD5 hash → deterministic vector
        ├─ NOT semantically meaningful
        └─ Warning logged
```

---

## Model Flow

### LLM Model Management

```
┌─────────────────────────────────────────────────────────────┐
│                    MODEL SYSTEM                              │
│                                                             │
│  Model Catalog (model_catalog table)                        │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Sources:                                             │   │
│  │  1. Ollama Catalog (three-source pipeline)           │   │
│  │     ├─ OCI Registry (registry.ollama.ai)             │   │
│  │     ├─ Cloud API (ollama.com)                        │   │
│  │     └─ Local API (localhost:11434)                   │   │
│  │  2. Registered Providers (provider_registry)         │   │
│  │  3. Seed Data (seed_data.py)                         │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                             │
│  LLM Manager (llm/manager.py) - Singleton                   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Provider Selection:                                  │   │
│  │  1. Auto: tries Ollama → llama.cpp → fails           │   │
│  │  2. Explicit: uses configured provider               │   │
│  │                                                      │   │
│  │ Providers:                                           │   │
│  │  ├─ OllamaProvider (ollama.py)                       │   │
│  │  │  └─ httpx → http://localhost:11434                │   │
│  │  └─ LlamaCppProvider (llama_cpp.py)                  │   │
│  │     └─ llama-cpp-python → local GGUF file            │   │
│  │                                                      │   │
│  │ Capabilities:                                        │   │
│  │  ├─ chat(messages, model, max_tokens, temp)          │   │
│  │  ├─ chat_stream(messages, ...) → async generator     │   │
│  │  ├─ health_check() → provider availability           │   │
│  │  └─ fetch_ollama_catalog() → model list              │   │
│  │                                                      │   │
│  │ Reliability:                                         │   │
│  │  ├─ Semaphore(4) for concurrency control             │   │
│  │  ├─ 3 retries with exponential backoff               │   │
│  │  └─ Retryable: ConnectionError, TimeoutError         │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                             │
│  Model Downloads (model_downloader.py)                      │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  - Background download manager                       │   │
│  │  - Progress tracking via WebSocket (/ws/models)      │   │
│  │  - Downloads to <storage_root>/models/               │   │
│  │  - Hash verification                                 │   │
│  │  - Status: pending → downloading → completed/failed  │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                             │
│  Usage Tracking (usage_tracker.py)                          │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  - Records per-request: model, tokens, duration      │   │
│  │  - Stored in model_usage table                       │   │
│  │  - Aggregated for statistics                         │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## Sync Flow

### File System Sync

```
┌─────────────────────────────────────────────────────────────┐
│                    SYNC SYSTEM                               │
│                                                             │
│  File Watcher v2 (file_watcher_v2.py)                       │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  - Watches filesystem paths for changes              │   │
│  │  - Persists state in sync_states table               │   │
│  │  - Recovers active watches on startup                │   │
│  │                                                      │   │
│  │  Lifecycle:                                          │   │
│  │  1. User starts sync via POST /api/v1/sync/start     │   │
│  │  2. SyncService creates SyncState record             │   │
│  │  3. FileWatcher watches repo_path                    │   │
│  │  4. On change: triggers incremental indexing         │   │
│  │  5. Updates SyncState (files_watched, files_changed) │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                             │
│  Incremental Indexer (incremental_indexer.py)               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  - Hash-based change detection                       │   │
│  │  - Tracks in indexed_files table                     │   │
│  │  - Only re-indexes changed files                     │   │
│  │                                                      │   │
│  │  Pipeline:                                           │   │
│  │  1. Scan filesystem → list files                     │   │
│  │  2. Compare hashes with indexed_files                │   │
│  │  3. Chunk new/changed files                          │   │
│  │  4. Generate embeddings                              │   │
│  │  5. Upsert to Qdrant                                │   │
│  │  6. Update indexed_files status                      │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                             │
│  Model Catalog Sync (sync_service.py)                       │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  - Syncs models from providers to model_catalog      │   │
│  │  - Uses ollama_catalog three-source pipeline         │   │
│  │  - Upserts into ModelCatalog table                   │   │
│  │  - Tracks SyncJob with status/metrics                │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                             │
│  Redis Pub/Sub (not actively used for sync currently)       │
│  - Redis is optional (graceful fallback)                    │
│  - Used for: rate limiting, token revocation, caching       │
│  - NOT used for real-time file sync (uses filesystem)       │
└─────────────────────────────────────────────────────────────┘
```

---

## State Flow

### Application State Management

```
┌─────────────────────────────────────────────────────────────┐
│                    STATE FLOW                                │
│                                                             │
│  Frontend State (React)                                     │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  AuthProvider (React Context)                        │   │
│  │  ├─ user: User | null                                │   │
│  │  ├─ loading: boolean                                 │   │
│  │  ├─ login(user) / logout() / updateUser(user)        │   │
│  │  └─ Session cache: getSessionUser() / setSession()   │   │
│  │                                                      │   │
│  │  Page-level state:                                   │   │
│  │  ├─ useState for local UI state                      │   │
│  │  ├─ API calls → response → state update              │   │
│  │  └─ No global state manager (Redux/Zustand)          │   │
│  │                                                      │   │
│  │  Token state:                                        │   │
│  │  ├─ Access token: httpOnly cookie (invisible to JS)  │   │
│  │  ├─ Refresh token: httpOnly cookie                   │   │
│  │  ├─ CSRF token: readable cookie (JS-accessible)      │   │
│  │  └─ Auto-refresh: tryRefresh() on 401                │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                             │
│  Backend State (Python)                                     │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Singletons:                                        │   │
│  │  ├─ llm_manager: LLMManager (provider routing)      │   │
│  │  ├─ redis_cache: RedisCache (async client)          │   │
│  │  ├─ _embedding_service: EmbeddingService             │   │
│  │  ├─ _vector_db: VectorDB (Qdrant client)            │   │
│  │  └─ download_manager: DownloadManager                │   │
│  │                                                      │   │
│  │  Per-request state:                                  │   │
│  │  ├─ DB session: Depends(get_db) → scoped to request  │   │
│  │  ├─ User: Depends(get_current_user) → from JWT       │   │
│  │  └─ Request ID: contextvars (correlation)            │   │
│  │                                                      │   │
│  │  Background state:                                   │   │
│  │  ├─ FileWatcher: watches filesystem paths            │   │
│  │  ├─ DownloadManager: tracks model downloads          │   │
│  │  └─ AgentRunManager: tracks running agents           │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                             │
│  Database State (PostgreSQL)                                │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Session factory: SessionLocal (dynamic, per-request)│   │
│  │  Engine: connection pool (size=5, overflow=10)       │   │
│  │  Bootstrap: run_migrations() on startup              │   │
│  │  Migrations: Alembic (single baseline migration)     │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## Service Boundaries

### Backend Services

| Service | File | Boundaries | Dependencies |
|---------|------|-----------|--------------|
| **LLM Manager** | `services/llm/manager.py` | Provider abstraction, routing, retry logic | llama.cpp, Ollama |
| **Embedding Service** | `services/embedding_service.py` | Text → vector, ONNX/Ollama/mock backends | ONNX Runtime, Ollama |
| **Vector DB** | `core/vector_db.py` | Qdrant wrapper, upsert/search/delete | Qdrant server |
| **Memory Manager** | `services/memory_manager.py` | Knowledge entry CRUD + vector search | EmbeddingService, VectorDB |
| **Hybrid Retrieval** | `services/hybrid_retrieval.py` | Multi-source search + RRF + MMR | VectorDB, FullTextSearch |
| **RAG Pipeline** | `services/rag_pipeline.py` | Context retrieval + message construction | HybridRetrieval, ConversationService |
| **Conversation Service** | `services/conversation_service.py` | Chat history + context management | LLM Manager |
| **Long-Term Memory** | `services/long_term_memory.py` | Persistent memory with decay/confidence | PostgreSQL |
| **Agent System** | `agents/*.py` | Plan → execute → feedback loop | LLM Manager, Tools |
| **Repo Scanner** | `services/repo_scanner.py` | Walk + chunk + embed + store | Chunker, EmbeddingService, VectorDB |
| **Graph Builder** | `services/graph_builder.py` | Knowledge graph construction | CodeChunk, GraphNode/Edge |
| **File Watcher** | `services/file_watcher_v2.py` | Filesystem monitoring | SyncState, IncrementalIndexer |
| **Sync Service** | `services/sync_service.py` | Model catalog synchronization | OllamaCatalog, Providers |
| **Model Downloader** | `services/model_downloader.py` | Background model downloads | ModelVariant, DownloadManager |
| **Vault Service** | `services/vault_service.py` | Encrypted file storage | Fernet, PBKDF2 |
| **Full-Text Search** | `services/fulltext_search.py` | PostgreSQL ts_vector search | PostgreSQL GIN indexes |

### Frontend Modules

| Module | Path | Boundaries |
|--------|------|-----------|
| **Auth** | `shared/auth/` | AuthProvider, cortexApi, session management |
| **API Clients** | `shared/api/` | Domain-specific API wrappers (agent, models, search, etc.) |
| **Layout** | `shared/layout/` | DashboardShell, sidebar, navigation |
| **UI Components** | `shared/ui/` | Button, Card, Modal, NeuralNetwork, Toast, etc. |
| **Design System** | `shared/design/` | Design tokens, CSS variables |
| **Services** | `shared/services/` | Folder picker abstraction (browser + Tauri) |

---

## Ownership Boundaries

| Responsibility | Owner | Files |
|---------------|-------|-------|
| User authentication | `backend/app/auth/` | auth.py, security.py, deps.py |
| User management | `backend/app/api/v1/users.py` | + user model/service |
| Profile management | `backend/app/api/v1/profile.py` | + user model |
| Vault operations | `backend/app/services/vault_service.py` | + api/v1/vault.py |
| Agent system | `backend/app/agents/` | base.py, planner.py, executor.py, run_manager.py, tools.py |
| LLM integration | `backend/app/services/llm/` | manager.py, llama_cpp.py, ollama.py, provider.py |
| Model catalog | `backend/app/services/catalogue.py` | + model_catalog models |
| Embeddings | `backend/app/services/embedding_service.py` | + embedding_cache.py |
| Vector search | `backend/app/core/vector_db.py` | + hybrid_retrieval.py |
| Full-text search | `backend/app/services/fulltext_search.py` | PostgreSQL ts_vector |
| Knowledge graph | `backend/app/services/graph_builder.py` | + graph models |
| Conversation/chat | `backend/app/services/conversation_service.py` | + api/v1/conversations.py |
| Long-term memory | `services/long_term_memory.py` | + long_term_memory models |
| File sync | `services/file_watcher_v2.py` | + sync_service.py, sync_state model |
| Indexing pipeline | `services/indexing_orchestrator.py` | + repo_scanner, chunker, semantic_chunker |
| Document indexing | `services/document_indexer.py` | + document models |
| Frontend UI | `frontend/app/` + `frontend/src/shared/` | All React components |
| Database schema | `backend/app/models/` + `migrations/` | SQLAlchemy models + Alembic |
| Configuration | `backend/app/core/config.py` | Settings class |
| Middleware | `backend/app/core/` | csrf.py, rate_limit.py, middleware.py |

---

## Sources of Truth

| Data Type | Source of Truth | Secondary |
|-----------|----------------|-----------|
| User accounts | PostgreSQL `users` table | Session cache (frontend) |
| Authentication tokens | Redis (revocation) | JWT (stateless verification) |
| Agent definitions | PostgreSQL `agents` table | — |
| Agent runs/steps | PostgreSQL `agent_runs`/`agent_steps` | In-memory during execution |
| Conversations | PostgreSQL `conversations`/`conversation_messages` | — |
| Long-term memories | PostgreSQL `long_term_memories` | — |
| Code chunks | PostgreSQL `code_chunks` + Qdrant `cortex_code` | — |
| Document chunks | PostgreSQL `document_chunks` + Qdrant `cortex_memory` | — |
| Knowledge entries | PostgreSQL `knowledge_entries` + Qdrant `cortex_memory` | — |
| Knowledge graph | PostgreSQL `graph_nodes`/`graph_edges` | — |
| Model catalog | PostgreSQL `model_catalog` | Ollama catalog cache |
| Model downloads | PostgreSQL `model_downloads` + filesystem | DownloadManager state |
| Vault files | Filesystem (encrypted) | PostgreSQL `user_storage_registry` (path only) |
| Sync state | PostgreSQL `sync_states` | FileWatcher in-memory state |
| File index state | PostgreSQL `indexed_files` | — |
| Embedding cache | PostgreSQL `embedding_cache` | — |
| Hardware profiles | PostgreSQL `hardware_profiles` | — |
| User settings | PostgreSQL `user_model_settings` | — |

---

## Dependencies

### External Services

| Service | Required | Default | Fallback |
|---------|----------|---------|----------|
| PostgreSQL 16 | Yes | localhost:5432 | None (fatal) |
| Qdrant | Yes | localhost:6333 | None (fatal) |
| Redis 7 | No | localhost:6379 | Graceful degradation (caching/rate limiting disabled) |
| Ollama | No | localhost:11434 | llama.cpp or no LLM |
| llama.cpp | No | Local GGUF file | Ollama or no LLM |

### Python Packages (Key)

| Package | Purpose |
|---------|---------|
| fastapi, uvicorn | Web framework |
| sqlalchemy, alembic | ORM + migrations |
| jose, passlib | JWT + password hashing |
| cryptography (Fernet) | Vault encryption |
| qdrant-client | Vector database |
| onnxruntime | Local embeddings |
| httpx | Ollama API client |
| arq | Task queue |
| structlog | Structured logging |
| pydantic-settings | Configuration |

### Frontend Packages (Key)

| Package | Purpose |
|---------|---------|
| next (15) | React framework |
| react (19) | UI library |
| tailwindcss | Styling |
| @radix-ui/* | UI primitives |
| framer-motion | Animations |
| cmdk | Command palette |
| sonner | Toast notifications |
| three, @react-three/fiber | Neural Network background |

---

## Risks & Single Points of Failure

### Critical Risks

| Risk | Severity | Impact | Mitigation |
|------|----------|--------|------------|
| **PostgreSQL failure** | Critical | All data access fails | Regular backups (`make db-backup`), Docker health checks |
| **Qdrant failure** | Critical | Vector search fails, embeddings lost | Data persisted in Docker volume |
| **LLM provider unavailable** | High | Agent/chat features degrade | Auto-fallback: Ollama → llama.cpp → error |
| **Embedding service unavailable** | High | Cannot create new embeddings | Mock fallback (non-semantic), cached embeddings still work |
| **Redis unavailable** | Medium | Rate limiting disabled, no token revocation | Graceful fallback (app continues) |
| **No SECRET_KEY** | High | JWT signing uses empty key | Validator warns in dev, rejects in production |

### Architecture Risks

| Risk | Details |
|------|---------|
| **Singleton dependencies** | `llm_manager`, `redis_cache`, `_embedding_service`, `_vector_db` are module-level singletons. Testing requires careful patching. |
| **Mixed sync/async** | EmbeddingService uses `_run_async()` helper to bridge sync → async. Can cause issues in event loop contexts. |
| **Agent execution blocking** | Agent runs execute synchronously in the request handler. Long-running agents can block other requests. |
| **No horizontal scaling** | File watchers, download managers, and agent runs are process-local. Cannot scale horizontally without external coordination. |
| **Vault password caching** | Vault password hash is cached in memory after unlock. Lost on restart (user must re-unlock). |
| **CSRF complexity** | Double-submit cookie pattern adds complexity. 25 of 35 pre-existing test failures are CSRF-related. |
| **Consolidated migration** | Single baseline migration (b00000000000) replaces 27 prior migrations. Historical schema evolution is lost. |

### Single Points of Failure

```
┌─────────────────────────────────────────────────────────────┐
│  SPOF Analysis                                              │
│                                                             │
│  1. PostgreSQL                                              │
│     - All relational data stored here                       │
│     - No replication configured                             │
│     - Backup strategy: pg_dump (manual)                     │
│                                                             │
│  2. Qdrant                                                  │
│     - All vector embeddings stored here                     │
│     - Data in Docker volume (qdrant_data)                   │
│     - No replication                                        │
│                                                             │
│  3. LLM Manager (singleton)                                 │
│     - Routes all LLM requests                               │
│     - Single process, no clustering                         │
│                                                             │
│  4. File Watcher (single process)                           │
│     - Watches filesystem for changes                        │
│     - Cannot be distributed                                 │
│                                                             │
│  5. Download Manager (single process)                       │
│     - Manages model downloads                               │
│     - State lost on restart                                 │
└─────────────────────────────────────────────────────────────┘
```

---

## Areas Requiring Deeper Investigation

### Unclear / Incomplete

| Area | Issue | Notes |
|------|-------|-------|
| **Redis Pub/Sub** | Listed in architecture diagram but not actively used for sync | Redis is used for caching/rate limiting, not real-time sync |
| **arq Task Queue** | `tasks/worker.py` exists but usage is unclear | Worker is defined but not prominently used in main flows |
| **WebSocket Endpoints** | Three WS endpoints defined (`/ws`, `/ws/models`, `/ws/system`) | Usage pattern unclear — model download progress + system metrics |
| **Document Indexing** | `document_indexer.py` + `parsers/` directory | Parsers exist for various formats but integration depth unclear |
| **Search Clustering** | `search_clustering.py` + `recommendation.py` | Feature completeness unclear |
| **Entity Extraction** | `entity_extractor.py` | How it integrates with graph building needs investigation |
| **CLI** | `cli/` directory exists | Scaffolded but not implemented — purpose unclear |

### Contradictions

| Observation | Details |
|-------------|---------|
| **README says "Vector DB (Qdrant)" is required** | But embedding service has mock fallback. Qdrant is required for meaningful search but app starts without it. |
| **Redis described as "optional"** | But rate limiting and token revocation depend on it. App "works" without Redis but with reduced security. |
| **Two API clients** | `cortexApi.ts` (legacy) and `api/client.ts` (new) both exist. cortexApi.ts is used by AuthProvider and many pages. api/client.ts is used by newer API modules. Potential duplication. |

### Circular Dependencies

| Chain | Risk |
|-------|------|
| `llm/manager.py` → `usage_tracker.py` → `SessionLocal` (creates new DB session inside LLM call) | Potential session leak if not carefully managed |
| `conversation_service.py` → `llm/manager.py` → `usage_tracker.py` → `db` | Circular import avoided by lazy imports |
| `agent/run_manager.py` → `llm/manager.py` → back to agent system | Managed via dependency injection |

### Missing / Recommended

| Area | Recommendation |
|------|---------------|
| **Observability** | No APM/tracing integration (OpenTelemetry, etc.) |
| **Rate limiting** | Global only — no per-user or per-endpoint granularity beyond auth |
| **Circuit breaker** | LLM providers have retry but no circuit breaker pattern |
| **Event sourcing** | Agent runs could benefit from event sourcing for replay |
| **Horizontal scaling** | File watchers and download managers are process-local |
| **Backup automation** | pg_dump is manual — no scheduled backups |
| **Schema versioning** | Single baseline migration loses historical context |

---

*This document is a reference map. It should be updated as the architecture evolves.*
