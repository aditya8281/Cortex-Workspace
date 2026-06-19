# Cortex Execution Guide

> **Purpose:** Step-by-step instructions for executing the Cortex 90-day roadmap.
> This is the single entry point for any agent or developer working on Cortex.

---

## Quick Start

```
1. Read this guide completely
2. Read prerequisite.md (ALL ITEMS COMPLETE)
3. Start with Phase 1: Memory (Weeks 3-4)
4. Execute phases in order
5. Verify at each checkpoint before proceeding
```

---

## Document Map

| Document | Purpose | Read Order |
|----------|---------|------------|
| `GUIDE.md` | This file — execution instructions | 1st |
| `prerequisite.md` | What must be done before Phase 2 | 2nd |
| `INDEX.md` | Master plan index, dependency graph | 3rd |
| `01-WEEK-3-4-MEMORY.md` | Memory & vector DB plan | 4th |
| `02-WEEK-5-6-INDEXING.md` | Code indexing plan | 5th |
| `03-WEEK-7-8-AGENTS.md` | Agent runtime plan | 6th |
| `04-WEEK-9-10-INTELLIGENCE.md` | Intelligence & planning plan | 7th |
| `05-WEEK-11-12-LAUNCH.md` | Desktop V1 & launch plan | 8th |

---

## Phase 0: Prerequisites — COMPLETE

**Status:** All prerequisite items have been completed. See [prerequisite.md](../prerequisite.md) for details.

Completed:
- [x] Critical fixes (plan alignment, FK constraints, TypeScript strict)
- [x] Required refactors (vault decomposition, token consolidation, async auth, JSONB)
- [x] Missing foundations (task queue, vector DB, embeddings, WebSocket, rate limiting)
- [x] Security improvements (JWT cookies, CSP, soft delete)
- [x] Production readiness (TLS, logging, metrics, backups, frontend tests)
- [x] Plan file updates

**Proceed to Phase 1: Memory →**

---

## Phase 1: Memory (Weeks 3-4)

**Prerequisites:** Phase 0 complete (VectorDB, EmbeddingService, TaskQueue ready)
**Plan:** `01-WEEK-3-4-MEMORY.md`

### Step 1.1: Vector DB Service (Days 1-3)

**What to do:**
1. Create `backend/app/services/memory_manager.py` — Memory CRUD
2. Create `backend/app/services/vector_service.py` — Vector operations
3. Create `backend/app/api/v1/memory.py` — Memory REST API
4. Add Qdrant collections for memories

**Files to create/modify:**
- `backend/app/services/memory_manager.py`
- `backend/app/services/vector_service.py`
- `backend/app/api/v1/memory.py`
- `backend/app/api/router.py` — Register memory router

**Verification:**
```bash
PYTHONPATH=. pytest tests/test_memory*.py -v
curl http://localhost:8000/api/v1/memory  # Returns empty list
```

---

### Step 1.2: Embedding Pipeline (Days 4-6)

**What to do:**
1. Integrate BGE-M3 ONNX model
2. Create embedding pipeline with batching
3. Add mock fallback for testing
4. Create background task for bulk embedding

**Files to modify:**
- `backend/app/services/embedding_service.py` — Real model loading
- `backend/app/tasks/embedding_tasks.py` — Background embedding

**Verification:**
```bash
PYTHONPATH=. pytest tests/test_embedding*.py -v
# Embed a test string
curl -X POST http://localhost:8000/api/v1/memory -d '{"content": "test memory"}'
```

---

### Step 1.3: Repository Scanner (Days 7-9)

**What to do:**
1. Create git-aware repository scanner
2. Detect file types, languages, structures
3. Extract code symbols (functions, classes)
4. Store scan results in knowledge entries

**Files to create:**
- `backend/app/services/repo_scanner.py`
- `backend/app/tasks/scan_tasks.py`

**Verification:**
```bash
PYTHONPATH=. pytest tests/test_repo_scanner.py -v
# Scan current repo
curl -X POST http://localhost:8000/api/v1/memory/scan -d '{"path": "."}'
```

---

### Step 1.4: Memory Frontend (Days 10-14)

**What to do:**
1. Create memory browser UI
2. Add search interface
3. Add memory creation/editing
4. Add category filtering

**Files to create:**
- `frontend/app/memory/page.tsx`
- `frontend/app/memory/MemoryList.tsx`
- `frontend/app/memory/MemorySearch.tsx`
- `frontend/app/memory/MemoryEditor.tsx`

**Verification:**
```bash
cd frontend && npm run build  # Build succeeds
cd frontend && npx tsc --noEmit  # No type errors
```

---

### Checkpoint: Phase 1 Complete

```bash
# All tests pass
PYTHONPATH=. pytest tests/ -v

# Frontend builds
cd frontend && npm run build

# Memory API works
curl http://localhost:8000/api/v1/memory  # Returns memories
curl -X POST http://localhost:8000/api/v1/memory -d '{"content": "test"}'  # Creates memory

# Vector search works
curl -X POST http://localhost:8000/api/v1/memory/search -d '{"query": "test"}'  # Returns results
```

---

## Phase 2: Indexing (Weeks 5-6)

**Prerequisites:** Phase 1 complete (VectorDB, RepoScanner, EmbeddingService)
**Plan:** `02-WEEK-5-6-INDEXING.md`

### Step 2.1: Code Intelligence (Days 1-5)

**What to do:**
1. Add tree-sitter for AST parsing
2. Create code intelligence service
3. Extract functions, classes, imports
4. Build code symbol index

**Files to create:**
- `backend/app/services/code_intelligence.py`
- `backend/app/models/code_symbol.py`
- `migrations/versions/xxxx_add_code_symbols.py`

**Verification:**
```bash
PYTHONPATH=. pytest tests/test_code_intelligence.py -v
# Index a file
curl -X POST http://localhost:8000/api/v1/index/file -d '{"path": "backend/app/main.py"}'
```

---

### Step 2.2: Knowledge Graph (Days 6-8)

**What to do:**
1. Create knowledge graph service (PostgreSQL adjacency list)
2. Add nodes: files, functions, classes, concepts
3. Add edges: calls, imports, contains, relates_to
4. Create graph query API

**Files to create:**
- `backend/app/services/knowledge_graph.py`
- `backend/app/models/graph_node.py`
- `backend/app/models/graph_edge.py`
- `backend/app/api/v1/graph.py`

**Verification:**
```bash
PYTHONPATH=. pytest tests/test_knowledge_graph.py -v
curl http://localhost:8000/api/v1/graph  # Returns graph data
```

---

### Step 2.3: ColBERT Code Embeddings (Days 9-10)

**What to do:**
1. Add ColBERT model for code embeddings
2. Create code-specific embedding pipeline
3. Index all code symbols

**Files to modify:**
- `backend/app/services/embedding_service.py` — ColBERT support
- `backend/app/tasks/embedding_tasks.py` — Code embedding task

**Verification:**
```bash
PYTHONPATH=. pytest tests/test_colbert.py -v
```

---

### Step 2.4: Graph Visualization (Days 11-14)

**What to do:**
1. Add Cytoscape.js to frontend
2. Create graph visualization component
3. Add interactive node exploration
4. Add search and filter

**Files to create:**
- `frontend/app/graph/page.tsx`
- `frontend/app/graph/GraphView.tsx`
- `frontend/app/graph/NodeDetails.tsx`

**Verification:**
```bash
cd frontend && npm run build
# Graph renders in browser
```

---

### Checkpoint: Phase 2 Complete

```bash
PYTHONPATH=. pytest tests/ -v
cd frontend && npm run build

# Code indexing works
curl -X POST http://localhost:8000/api/v1/index/repo -d '{"path": "."}'

# Knowledge graph populated
curl http://localhost:8000/api/v1/graph/stats

# Graph visualization renders
# Open http://localhost:3000/graph in browser
```

---

## Phase 3: Agents (Weeks 7-8)

**Prerequisites:** Phase 2 complete (VectorDB, CodeIntelligence, TaskQueue)
**Plan:** `03-WEEK-7-8-AGENTS.md`

### Step 3.1: Unified Search (Days 1-3)

**What to do:**
1. Create search service with reciprocal rank fusion
2. Combine vector search, keyword search, graph search
3. Add search API endpoint

**Files to create:**
- `backend/app/services/search_service.py`
- `backend/app/api/v1/search.py`

---

### Step 3.2: Agent Runtime (Days 4-7)

**What to do:**
1. Create agent runtime with tool-use loop
2. Add tool registry
3. Add local model support (GGUF, llama.cpp)
4. Create agent task execution

**Files to create:**
- `backend/app/services/agent_runtime.py`
- `backend/app/services/tool_registry.py`
- `backend/app/models/agent_task.py`
- `backend/app/tasks/agent_tasks.py`

---

### Step 3.3: Coder Agent (Days 8-10)

**What to do:**
1. Create Coder agent with file read/write/execute
2. Add code generation capabilities
3. Add file system tools

**Files to create:**
- `backend/app/agents/coder.py`
- `backend/app/tools/file_tools.py`
- `backend/app/tools/exec_tools.py`

---

### Step 3.4: Researcher Agent (Days 11-12)

**What to do:**
1. Create Researcher agent with search/browse
2. Add web search capabilities
3. Add information synthesis

**Files to create:**
- `backend/app/agents/researcher.py`
- `backend/app/tools/search_tools.py`

---

### Step 3.5: Agent Frontend (Days 13-14)

**What to do:**
1. Create agent chat UI
2. Add streaming output display
3. Add tool execution visualization

**Files to create:**
- `frontend/app/agents/page.tsx`
- `frontend/app/agents/AgentChat.tsx`
- `frontend/app/agents/ToolOutput.tsx`

---

### Checkpoint: Phase 3 Complete

```bash
PYTHONPATH=. pytest tests/ -v
cd frontend && npm run build

# Search works
curl -X POST http://localhost:8000/api/v1/search -d '{"query": "auth function"}'

# Agent executes
curl -X POST http://localhost:8000/api/v1/agents/execute -d '{"task": "find all auth functions"}'
```

---

## Phase 4: Intelligence (Weeks 9-10)

**Prerequisites:** Phase 3 complete (AgentRuntime, ToolRegistry)
**Plan:** `04-WEEK-9-10-INTELLIGENCE.md`

### Step 4.1: Reasoning Engine (Days 1-5)

**What to do:**
1. Create chain-of-thought reasoning
2. Add reflection and self-correction
3. Add reasoning trace storage

---

### Step 4.2: Planning Engine (Days 6-8)

**What to do:**
1. Create task DAG planning
2. Add dependency resolution
3. Add plan execution tracking

---

### Step 4.3: Multi-Agent Orchestration (Days 9-12)

**What to do:**
1. Create orchestrator agent
2. Add agent communication
3. Add task delegation

---

### Step 4.4: Intelligence Frontend (Days 13-14)

**What to do:**
1. Create planning UI
2. Add reasoning trace visualization
3. Add agent status dashboard

---

### Checkpoint: Phase 4 Complete

```bash
PYTHONPATH=. pytest tests/ -v
cd frontend && npm run build

# Reasoning works
curl -X POST http://localhost:8000/api/v1/reason -d '{"question": "How does auth work?"}'

# Planning works
curl -X POST http://localhost:8000/api/v1/plan -d '{"task": "add new feature"}'
```

---

## Phase 5: Launch (Weeks 11-12)

**Prerequisites:** Phase 4 complete
**Plan:** `05-WEEK-11-12-LAUNCH.md`

### Step 5.1: System Understanding (Days 1-3)

**What to do:**
1. Create codebase analysis service
2. Add system health monitoring
3. Add performance metrics

---

### Step 5.2: Learning Loop (Days 4-5)

**What to do:**
1. Create feedback collection
2. Add model fine-tuning pipeline
3. Add metrics tracking

---

### Step 5.3: Desktop V1 (Days 6-10)

**What to do:**
1. Initialize Tauri v2 project
2. Bundle PostgreSQL, Qdrant, llama.cpp as sidecars
3. Add system tray
4. Add global shortcuts
5. Add auto-update

---

### Step 5.4: CI/CD for Desktop (Days 11-12)

**What to do:**
1. Add GitHub Actions for Windows/macOS/Linux
2. Add code signing
3. Add release automation

---

### Step 5.5: Final Polish (Days 13-14)

**What to do:**
1. Performance optimization
2. Bug fixes
3. Documentation
4. Release preparation

---

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

---

## Execution Rules

### Rule 1: Prerequisites First
Never start Phase 1-5 without completing Phase 0. The codebase must be aligned.

### Rule 2: Verify Before Proceeding
Always run the verification commands at each checkpoint. Fix failures before continuing.

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

---

## Common Pitfalls

### Pitfall 1: Skipping Prerequisites
**Problem:** Starting Memory plan without VectorDB or EmbeddingService.
**Solution:** Complete prerequisite 3.2 and 3.3 first.

### Pitfall 2: Not Verifying Checkpoints
**Problem:** Moving to next phase with failing tests.
**Solution:** Always run verification commands. Fix failures.

### Pitfall 3: Ignoring TypeScript Errors
**Problem:** Building frontend with type errors.
**Solution:** Run `npx tsc --noEmit` and fix all errors.

### Pitfall 4: Creating Duplicate Code
**Problem:** Recreating files that already exist.
**Solution:** Check existing codebase before creating new files.

### Pitfall 5: Forgetting Migrations
**Problem:** Adding models without migrations.
**Solution:** Always create Alembic migrations for new models.

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

---

## Success Criteria

### Phase 0 (Prerequisites) — COMPLETE
- [x] All plan paths correct
- [x] FK constraints added
- [x] TypeScript strict mode enabled
- [x] Vault decomposed (< 200 lines)
- [x] Token functions consolidated
- [x] Auth service async
- [x] JSONB columns
- [x] Task queue running
- [x] Vector DB integrated
- [x] Embedding service working
- [x] WebSocket available
- [x] Rate limiting active
- [x] JWT in cookies
- [x] CSP tightened
- [x] Soft delete working
- [x] TLS documented
- [x] Correlation IDs in logs
- [x] Metrics endpoint
- [x] Backups documented
- [x] Frontend tests passing

### Phase 1 (Memory)
- [ ] Memory CRUD API
- [ ] Vector search working
- [ ] Embedding pipeline
- [ ] Repository scanner
- [ ] Memory frontend UI

### Phase 2 (Indexing)
- [ ] Code intelligence (tree-sitter)
- [ ] Knowledge graph
- [ ] ColBERT embeddings
- [ ] Graph visualization

### Phase 3 (Agents)
- [ ] Unified search
- [ ] Agent runtime
- [ ] Coder agent
- [ ] Researcher agent
- [ ] Agent frontend

### Phase 4 (Intelligence)
- [ ] Reasoning engine
- [ ] Planning engine
- [ ] Multi-agent orchestration
- [ ] Intelligence frontend

### Phase 5 (Launch)
- [ ] System understanding
- [ ] Learning loop
- [ ] Desktop V1 (Tauri)
- [ ] CI/CD for all platforms
- [ ] Binary < 50MB
- [ ] Cold start < 2s

---

## Final Notes

1. **This guide is the source of truth** for execution order
2. **Follow the checkpoints** — never skip verification
3. **Reference the plan files** for detailed implementation
4. **Update this guide** as things change
5. **The vision is unchanged** — local-first, zero telemetry, desktop V1

---

*Last updated: 2026-06-19*
