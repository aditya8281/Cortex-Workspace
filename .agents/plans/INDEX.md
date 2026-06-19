# Cortex 90-Day Master Plan

> **For agentic workers:** This is the master index. Read prerequisite.md first, then follow the execution order below.

**Goal:** Build Cortex — a local-first, autonomous AI workspace with reasoning, planning, and multi-agent intelligence — from Phase 2 to Desktop V1 in 90 days.

**Architecture:** FastAPI + PostgreSQL backend, Next.js 15 + React 19 frontend, Qdrant for vectors, Tauri v2 for desktop. All data local, zero telemetry.

**Status:** Prerequisites complete. Phase 2 (Memory & Indexing) is next.

---

## Prerequisite — COMPLETE

All items in prerequisite.md have been completed:
- Critical fixes (plan alignment, FK constraints, TypeScript strict)
- Required refactors (vault decomposition, token consolidation, async auth, JSONB)
- Missing foundations (task queue, vector DB, embeddings, WebSocket, rate limiting)
- Security improvements (JWT cookies, CSP, soft delete)
- Production readiness (TLS, logging, metrics, backups, frontend tests)

---

## Plan Files (Phase 2+)

| Weeks | File | Focus | Key Deliverables |
|-------|------|-------|------------------|
| 3-4 | [01-WEEK-3-4-MEMORY.md](./01-WEEK-3-4-MEMORY.md) | Memory | Vector DB, embeddings, repo scanner, memory UI |
| 5-6 | [02-WEEK-5-6-INDEXING.md](./02-WEEK-5-6-INDEXING.md) | Indexing | Code intelligence, knowledge graph, graph viz |
| 7-8 | [03-WEEK-7-8-AGENTS.md](./03-WEEK-7-8-AGENTS.md) | Agents | Unified search, agent runtime, Coder/Researcher |
| 9-10 | [04-WEEK-9-10-INTELLIGENCE.md](./04-WEEK-9-10-INTELLIGENCE.md) | Intelligence | Reasoning, planning, multi-agent orchestration |
| 11-12 | [05-WEEK-11-12-LAUNCH.md](./05-WEEK-11-12-LAUNCH.md) | Launch | System understanding, learning loop, Desktop V1 |

---

## Dependency Graph

```
Prerequisite: Repository Alignment (must complete first)
    ├── Critical fixes (plan alignment, FK constraints, TypeScript strict)
    ├── Required refactors (vault decomposition, token consolidation, async auth)
    ├── Missing foundations (task queue, vector DB, embeddings, WebSocket)
    ├── Security improvements (JWT cookies, CSP, rate limiting)
    └── Production readiness (TLS, logging, metrics, backups)

Week 3-4: Memory
    ├── Depends on: Prerequisites (VectorDB, EmbeddingService, TaskQueue)
    ├── Qdrant embedded vector DB
    ├── BGE-M3 ONNX embeddings
    ├── Repository scanner (git-aware)
    └── Memory & vault frontend UI

Week 5-6: Indexing
    ├── Depends on: Memory (VectorDB, RepoScanner, EmbeddingService)
    ├── tree-sitter code intelligence
    ├── Knowledge Graph (PostgreSQL adjacency)
    ├── ColBERT code embeddings
    └── Graph visualization (Cytoscape.js)

Week 7-8: Agents
    ├── Depends on: Memory (VectorDB), Indexing (CodeIntelligence), TaskQueue
    ├── Unified search with reciprocal rank fusion
    ├── Agent runtime (tool-use loop)
    ├── Local models (GGUF, llama.cpp)
    ├── Coder agent (file read/write/execute)
    └── Researcher agent (search/browse)

Week 9-10: Intelligence
    ├── Depends on: Agents (AgentRuntime, ToolRegistry), TaskQueue
    ├── Reasoning engine (chain-of-thought + reflection)
    ├── Planning engine (task DAGs)
    ├── Task store (persistent state)
    └── Multi-agent orchestrator

Week 11-12: Launch
    ├── Depends on: Intelligence, Agents
    ├── System understanding (codebase analysis)
    ├── Learning loop (feedback + metrics)
    ├── Desktop V1 (Tauri v2 bundle)
    ├── System tray & global shortcuts
    ├── Auto-update (GitHub releases)
    └── CI/CD for all platforms
```

---

## Tech Stack

| Layer | Technology | Version |
|-------|------------|---------|
| **Backend** | Python | 3.12+ |
| **API** | FastAPI | 0.110+ |
| **Database** | PostgreSQL | 15+ |
| **Vector DB** | Qdrant | embedded |
| **Frontend** | Next.js | 15 |
| **UI** | React | 19 |
| **Desktop** | Tauri | v2 |
| **Language** | TypeScript | 5.3+ |
| **Styling** | Tailwind CSS | 3.4+ |
| **Embeddings** | ONNX Runtime | BGE-M3 |
| **Task Queue** | arq | Redis-based |

---

## Global Constraints

- Python 3.12+, Node.js 20+, Rust 2024 edition
- TypeScript strict mode (enabled via prerequisite), ESLint zero warnings
- Python: ruff line-length 120, mypy strict
- All async handlers, no blocking in event loop
- No external API calls for embeddings/inference (100% local)
- Zero telemetry, no cloud sync
- Desktop: Windows 10+, macOS 12+, Ubuntu 20.04+

---

## Current Codebase Structure

```
Cortex-Workspace/
├── backend/app/           # FastAPI application
│   ├── main.py            # Entry point
│   ├── core/              # Config, security, Redis, middleware, vector_db, websocket, rate_limit
│   ├── auth/              # Auth system (complete, httpOnly cookies)
│   ├── db/                # Bootstrap, session factory
│   ├── models/            # User, AuthEvent, StorageRegistry
│   ├── schemas/           # Pydantic models
│   ├── services/          # Business logic, embedding_service
│   ├── tasks/             # arq task queue worker
│   ├── intelligence/      # KnowledgeEntry model only
│   └── api/               # Routers
├── frontend/              # Next.js 15, Neural Dark UI
│   ├── app/               # Pages (App Router)
│   └── src/shared/        # Components, auth, design tokens
├── migrations/            # Alembic (PostgreSQL)
├── tests/                 # 115 pytest tests (106 backend + 9 frontend)
├── cli/                   # Commander.js CLI (stubs)
├── docker-compose.yml     # PostgreSQL + Redis + Qdrant
└── .agents/plans/         # This directory
```

---

## Key Design Decisions

1. **Qdrant over pgvector**: Supports tens of millions vectors, hybrid search, distributed scaling
2. **Tauri v2 over Electron**: Smaller binary (~10MB vs ~150MB), Rust native, system tray
3. **PostgreSQL over Neo4j**: Apache AGE extension gives graph capability within same DB
4. **tree-sitter for code intelligence**: Multi-language AST parsing, incremental, WASM-compatible
5. **Embedded sidecar pattern**: postgres, qdrant, llama.cpp run as Tauri sidecars
6. **Mock embeddings fallback**: ONNX model download on first run, deterministic hash-based mock for testing

---

## Execution Options

**Prerequisite First:** Complete all items in prerequisite.md before any plan execution.

**Option 1: Subagent-Driven (recommended)**
- Dispatch a fresh subagent per task
- Review between tasks
- Fast iteration, isolated failures

**Option 2: Inline Execution**
- Execute tasks in session
- Batch execution with checkpoints
- Good for smaller changes

---

## Success Metrics

| Metric | Target |
|--------|--------|
| Cold start | < 2s |
| Binary size | < 50MB |
| Test coverage | > 80% |
| Vector search latency | < 100ms |
| Agent execution | < 30s per task |
| Memory usage | < 500MB idle |
