# Cortex Execution Guide

> **Purpose:** Single entry point for executing the Cortex roadmap. Track progress, verify at checkpoints, and know exactly what to do next.

---

## Quick Start

```
1. Read this guide completely
2. Read prerequisite.md (ALL ITEMS COMPLETE)
3. Check current phase status below
4. Start with the next unfinished phase
5. Verify at each checkpoint before proceeding
```

---

## Document Map

| Document | Purpose | Read Order |
|----------|---------|------------|
| `GUIDE.md` | This file — execution instructions + tracking | 1st |
| `prerequisite.md` | What was done before Phase 2 | 2nd |
| `INDEX.md` | Master plan index, dependency graph | 3rd |
| `01-PHASE-0B-ARCHITECTURE.md` | Bug fixes + architecture alignment | 4th |
| `02-PHASE-1-MEMORY.md` | Memory system (status marker) | — |
| `03-PHASE-2-INDEXING.md` | Indexing + knowledge graph | 5th |
| `04-PHASE-3-AGENTS.md` | Unified search + agents | 6th |
| `05-PHASE-4-INTELLIGENCE.md` | Context + learning + workspace understanding | 7th |
| `06-PHASE-5-DESKTOP.md` | Tauri v2 desktop app | 8th |
| `07-PHASE-6-LEARNING.md` | Long-term memory + patterns + proactive assist | 9th |

---

## Progress Tracker

### Phase 0-A: Prerequisites — ✓ COMPLETE
- [x] Critical fixes (plan alignment, FK constraints, TypeScript strict)
- [x] Required refactors (vault decomposition, token consolidation, async auth)
- [x] Missing foundations (task queue, vector DB, embeddings, WebSocket, rate limiting)
- [x] Security improvements (JWT cookies, CSP, soft delete)
- [x] Production readiness (TLS, logging, metrics, backups, frontend tests)
- [x] Plan file updates

### Phase 0-B: Architecture Alignment — ✓ COMPLETE
- [x] Fix memory search (ID extraction bug, wrong key mapping)
- [x] Fix MemorySearchResult TypeScript type
- [x] Fix profile photo save/serve mismatch
- [x] Add FK ondelete clauses (notification, repo_index)
- [x] Fix User model type annotations
- [ ] Fix Knowledge Entry tags column type (kept as Text, consistent with current impl)
- [x] Standardize API versioning to /api/v1/
- [x] Create frontend API client abstraction
- [x] Create service abstraction protocol
- [x] Create storage path resolver
- [x] Create LLM provider interface
- [x] Decouple VECTOR_SIZE from EMBEDDING_DIM
- [x] Cache failed model load in embedding service
- [x] Make ALLOWED_ORIGINS a proper list
- [ ] Consolidate test directories (low priority, optional)
- [x] Add __init__.py to test directories
- [x] Create Rust crates directory + workspace
- [x] Create code-intel crate (tree-sitter + PyO3)
- [x] Create file-watcher crate (notify)

### Phase 1: Memory System — ✓ COMPLETE
- [x] Memory CRUD API
- [x] Vector search working
- [x] Embedding pipeline
- [x] Repository scanner
- [x] Memory frontend UI
- [x] Background effects
- [x] Auth toggle animation fixed
- [x] Browse button fallback
- [x] Vault 403 error fixed
- [x] Design system (Neural Dark) implemented

### Phase 2: Indexing & Knowledge Graph
- [ ] Graph database schema (GraphNode, GraphEdge, IndexedFile)
- [ ] Incremental indexer (hash-based change detection)
- [ ] Graph builder (nodes + edges from code)
- [ ] Cross-file search (vector + graph enrichment)
- [ ] Unified search API (/api/v1/search/)
- [ ] Repository management API (/api/v1/repository/)
- [ ] SearchFilters component
- [ ] SearchResults component
- [ ] GraphView component

### Phase 3: Unified Search & Agents
- [ ] Agent database schema (Agent, AgentRun, AgentStep, AgentFeedback)
- [ ] Planner agent (task decomposition)
- [ ] Executor agent (tool-use loop)
- [ ] Agent run manager
- [ ] Agent API (/api/v1/agents/)
- [ ] AgentChat component
- [ ] SearchResults enhancements

### Phase 4: Intelligence
- [ ] Context builder (workspace state + past conversations)
- [ ] Conversation memory (semantic search over history)
- [ ] Learning loop (feedback processing)
- [ ] Workspace understanding (call graphs, summaries)
- [ ] Enhanced executor with context
- [ ] Conversation history API (/api/v1/conversations/)
- [ ] ContextPanel component
- [ ] MemoryTimeline component

### Phase 5: Desktop V1 (Tauri v2)
- [ ] Tauri v2 project setup with plugins
- [ ] Backend sidecar entry point
- [ ] Tauri Rust plugins (tray, window, fs, dialog, updater)
- [ ] Frontend Tauri adapter
- [ ] Custom window controls
- [ ] Offline capabilities (IndexedDB, service worker)
- [ ] File system integration
- [ ] Auto-updater

### Phase 6: System Understanding & Learning
- [ ] Long-term memory model + service
- [ ] Pattern recognizer
- [ ] Correction tracker
- [ ] Proactive assistant
- [ ] Learning API (/api/v1/learning/)
- [ ] LearningDashboard component
- [ ] ProactiveSuggestions component

---

## Execution Rules

### Rule 1: Prerequisites First
Never start a phase without completing its dependencies. Check the dependency graph in INDEX.md.

### Rule 2: Verify Before Proceeding
Always run verification commands at each checkpoint. Fix failures before continuing.

### Rule 3: One Phase at a Time
Complete each phase fully before starting the next. Phases build on each other.

### Rule 4: Test Everything
Every new feature must have tests. Run `PYTHONPATH=. pytest tests/ -v` after each change.

### Rule 5: Build Frontend After Changes
Run `cd frontend && npm run build` after any frontend modification.

### Rule 6: Check Types
Run `cd frontend && npx tsc --noEmit` after any TypeScript change.

### Rule 7: Lint Code
Run `uv run ruff check backend/` after any Python change.

### Rule 8: Create Migrations
For every model change: `alembic revision --autogenerate -m "description"` then `alembic upgrade head`.

---

## Checkpoints

### Checkpoint: Phase 0-B Complete

```bash
# Backend
uv run ruff check backend/ tests/
PYTHONPATH=. pytest tests/ -v

# Frontend
cd frontend && npx tsc --noEmit
cd frontend && npx next lint
cd frontend && npm run build

# Rust
cd crates && cargo check

# Verify specific fixes
# 1. Memory search works (create + search returns correct results)
# 2. Profile photo uploads and serves correctly
# 3. All FK constraints have ondelete clauses
# 4. API routes use /api/v1/ prefix
```

### Checkpoint: Phase 2 Complete

```bash
PYTHONPATH=. pytest tests/ -v
cd frontend && npx tsc --noEmit
cd frontend && npm run build

# Code indexing works
curl -X POST http://localhost:8000/api/v1/repository/repos -d '{"name": "test", "path": "."}'
curl -X POST http://localhost:8000/api/v1/repository/repos/1/index

# Knowledge graph populated
curl http://localhost:8000/api/v1/repository/repos/1/status

# Unified search works
curl "http://localhost:8000/api/v1/search/?q=function"
```

### Checkpoint: Phase 3 Complete

```bash
PYTHONPATH=. pytest tests/ -v
cd frontend && npm run build

# Agent API works
curl http://localhost:8000/api/v1/agents/
curl -X POST http://localhost:8000/api/v1/agents/runs -d '{"agent_id": 1, "input": "find all auth functions"}'
```

### Checkpoint: Phase 4 Complete

```bash
PYTHONPATH=. pytest tests/ -v
cd frontend && npm run build

# Context builder works
curl "http://localhost:8000/api/v1/conversations/timeline"

# Learning API works
curl http://localhost:8000/api/v1/learning/patterns
curl http://localhost:8000/api/v1/learning/suggestions
```

### Checkpoint: Phase 5 Complete

```bash
# Desktop builds
cd frontend/src-tauri && cargo build --release

# All tests pass
PYTHONPATH=. pytest tests/ -v
cd frontend && npm run build

# Binary size < 50MB
ls -lh frontend/src-tauri/target/release/cortex

# Cold start < 2s
time ./frontend/src-tauri/target/release/cortex
```

### Checkpoint: Phase 6 Complete

```bash
PYTHONPATH=. pytest tests/ -v
cd frontend && npm run build

# Long-term memory works
curl -X POST http://localhost:8000/api/v1/learning/longterm -d '{"content": "user prefers dark mode", "type": "preference"}'
curl "http://localhost:8000/api/v1/learning/longterm?query=dark+mode"

# Proactive suggestions work
curl http://localhost:8000/api/v1/learning/suggestions
```

---

## Common Pitfalls

### Pitfall 1: Skipping Phase 0-B
**Problem:** Starting Phase 2 with broken memory search.
**Solution:** Complete all Phase 0-B items first. The memory search bug will cause all search results to return null.

### Pitfall 2: Not Running Migrations
**Problem:** Adding models without Alembic migrations.
**Solution:** Always run `alembic revision --autogenerate` after model changes.

### Pitfall 3: Ignoring TypeScript Errors
**Problem:** Building frontend with type errors.
**Solution:** Run `npx tsc --noEmit` and fix all errors before committing.

### Pitfall 4: Hardcoding Paths
**Problem:** Using hardcoded `./CortexMemory` paths.
**Solution:** Use `StorageResolver` from `backend/app/core/paths.py` (created in Phase 0-B).

### Pitfall 5: Duplicating Embedding Service
**Problem:** Creating a second `embedding_service.py` in agents plan.
**Solution:** Reuse existing `backend/app/services/embedding_service.py`. Import it.

---

## Troubleshooting

### Backend won't start
```bash
# Check PostgreSQL
pg_isready -h localhost -p 5435

# Check Redis
redis-cli ping

# Check logs
tail -f backend/logs/cortex.log
```

### Frontend build fails
```bash
# Check types
cd frontend && npx tsc --noEmit

# Check lint
cd frontend && npx next lint

# Clear cache
cd frontend && rm -rf .next && npm run build
```

### Tests fail
```bash
# Run specific test
PYTHONPATH=. pytest tests/test_auth.py -v

# Run with pdb
PYTHONPATH=. pytest tests/test_auth.py --pdb

# Check test database
psql -h localhost -p 5435 -U cortex -d cortex_test
```

### Vector DB not responding
```bash
# Check Qdrant
curl http://localhost:6333/health

# Check docker
docker ps | grep qdrant

# Restart Qdrant
docker restart qdrant
```

### Rust build fails
```bash
# Check Rust toolchain
rustc --version
cargo --version

# Clean and rebuild
cd crates && cargo clean && cargo check
```

---

## Final Notes

1. **This guide is the source of truth** for execution order and progress tracking
2. **Follow the checkpoints** — never skip verification
3. **Reference the plan files** for detailed implementation
4. **Update this guide** as phases complete
5. **The vision is unchanged** — local-first, zero telemetry, desktop V1

---

*Last updated: 2026-06-20*
