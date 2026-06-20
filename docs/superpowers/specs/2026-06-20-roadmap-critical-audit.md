# Cortex Roadmap — Critical Audit Report

> **Date:** 2026-06-20
> **Reviewers:** CTO, Principal Architect, Staff Engineer, Product Architect, DevOps Lead, QA Lead, Systems Designer
> **Scope:** All 10 phase plans, INDEX.md, README.md, DESIGN.md, roadmap audit spec

---

## Executive Summary

**The roadmap is directionally correct but tactically flawed.** The vision is sound, the phase ordering is mostly right, and the architecture decisions are reasonable. However, the implementation plans have two critical problems:

1. **Phase 4A-4B contain 11 CRITICAL code errors** that would cause immediate crashes (wrong imports, wrong method signatures, non-existent attributes)
2. **Phases 6-10 are product outlines, not implementation plans** — they lack the code depth needed for an agent to execute

**Verdict:** The roadmap needs a 2-3 day refinement pass before execution begins. The fixes are mechanical (correcting imports, adding code depth) — not architectural.

---

## Scores

| Dimension | Score | Notes |
|-----------|-------|-------|
| **Architecture Quality** | 7/10 | Sound decisions, but some over-engineering (model registry) |
| **Execution Quality** | 4/10 | Phase 4A has bugs; Phases 6-10 are outlines |
| **Maintainability** | 7/10 | Clean abstractions, but dual API clients are debt |
| **Scalability** | 6/10 | Works for single-user; concurrent users need work |
| **Tauri Readiness** | 5/10 | Phase 7 is too early and too thin |
| **Rust Readiness** | 4/10 | No Rust boundaries defined; crates are orphaned |
| **Production Readiness** | 3/10 | No tests, no security hardening, no CI/CD details |
| **Risk Level** | MEDIUM-HIGH | Bugs are fixable; outline phases need rewriting |
| **Roadmap Quality** | 6/10 | Vision is right; execution plans need depth |

---

## Critical Issues (Must Fix Before Execution)

### C1. Wrong Import Paths (Phase 4A)

**Location:** `08-PHASE-4A-LLM-INTEGRATION.md` Task 2, Step 1

```python
# WRONG:
from backend.app.api.deps import get_current_user, get_db

# CORRECT:
from backend.app.core.db import get_current_user, get_db
```

**Impact:** ImportError on every API endpoint. `backend/app/api/deps.py` does not exist.

### C2. LLMProvider ABC Rewritten (Phase 4A)

**Location:** `08-PHASE-4A-LLM-INTEGRATION.md` Task 1

The plan completely rewrites the `LLMProvider` ABC with new signatures (`LLMMessage`, `LLMResponse` dataclasses). The actual ABC at `backend/app/services/llm/provider.py` has a different interface. This breaks all existing consumers.

**Fix:** Extend the existing ABC, don't rewrite it. Add `LLMMessage`/`LLMResponse` as new dataclasses alongside the existing interface.

### C3. Async/Sync Mismatch (Phase 4A)

**Location:** `08-PHASE-4A-LLM-INTEGRATION.md` AI Answer endpoint

```python
# WRONG — CrossFileSearch.search() is synchronous:
code_results = await search.search(...)

# CORRECT:
code_results = search.search(...)
```

**Impact:** TypeError at runtime.

### C4. Wrong Method Names (Phase 4B)

**Location:** `09-PHASE-4B-SMART-INDEXING.md` Hybrid Retrieval

```python
# WRONG:
GraphNode.kind == GraphNodeKind.SYMBOL
e.kind.value

# CORRECT:
GraphNode.node_type == "symbol"
e.edge_type
```

**Impact:** AttributeError. `GraphNode` has `node_type`, not `kind`. `GraphEdge` has `edge_type`, not `kind`. No `GraphNodeKind` enum exists.

### C5. Phantom Method Modified (Phase 4B)

**Location:** `09-PHASE-4B-SMART-INDEXING.md` Task 1, Step 4

The plan modifies `_should_index_file()` on `IncrementalIndexer`, but this method doesn't exist. The indexer uses `_walk_repository()` with `SKIP_DIRS` filtering.

**Impact:** Integration rules are created but never applied.

### C6. File Watcher Has No File Watching (Phase 4B)

**Location:** `09-PHASE-4B-SMART-INDEXING.md` Task 3

`FileWatcher` has a debounce loop and `record_change()` method, but nothing calls `record_change()`. There's no actual file system watcher (inotify, watchdog, etc.).

**Impact:** File changes are never detected. The "File Watcher Integration" is a change accumulator with no producer.

### C7. Wrong Task Signature (Phase 4B)

**Location:** `09-PHASE-4B-SMART-INDEXING.md` Task 3, Step 2

```python
# WRONG:
await enqueue_task(index_repo_task, repo_path, config["repo_id"])

# CORRECT:
await enqueue_task("index_repo_task", config["repo_id"])
```

**Impact:** `enqueue_task` expects a task name string, not a function reference. `index_repo_task` only takes `repo_id`, not `repo_path`.

### C8. Memory Search Return Type Mismatch (Phase 4A)

**Location:** `08-PHASE-4A-LLM-INTEGRATION.md` AI Answer endpoint

```python
# WRONG — search returns list of dicts, not ORM objects:
for r in memory_results:
    context_parts.append(f"[Memory: {r.title}]\n{r.content[:500]}")

# CORRECT:
for r in memory_results:
    entry = r.get("entry") or {}
    context_parts.append(f"[Memory: {entry.get('title', '')}]\n{entry.get('content', '')[:500]}")
```

### C9. Wrong Search Class Name (Phase 4A)

**Location:** `08-PHASE-4A-LLM-INTEGRATION.md` AI Answer endpoint

```python
# WRONG:
payload: SearchPayload

# CORRECT:
payload: SearchRequest
```

### C10. Missing __init__.py (Phase 4A)

**Location:** `08-PHASE-4A-LLM-INTEGRATION.md` Task 1

Creates files in `backend/app/services/llm/` but never creates `__init__.py`. Python won't recognize it as a package.

### C11. Missing Dependencies (Phase 4A)

**Location:** `08-PHASE-4A-LLM-INTEGRATION.md` Task 2, Step 5

`psutil` and `llama-cpp-python` are not in `pyproject.toml`. Hardware detection and model loading will fail.

---

## High-Severity Issues

### H1. Quality Cliff Between Phases

| Phase | Lines | Code Blocks | Actionable? |
|-------|-------|-------------|-------------|
| 4A | 1,567 | ~25 | Yes (with fixes) |
| 4B | 887 | ~15 | Yes (with fixes) |
| 5 | 588 | ~8 | Mostly |
| 6 | 133 | 0 | **No** |
| 7 | 90 | 0 | **No** |
| 8 | 125 | 0 | **No** |
| 9 | 101 | 0 | **No** |
| 10 | 141 | 0 | **No** |

**Phases 6-10 are ~10% the depth of Phase 4A.** An agent given Phase 6 would stall or produce non-integrating code.

### H2. Observability Comes Too Late

Phase 9 is at position 9/10, but metrics collection should start in Phase 4A. Without early observability:
- Can't measure LLM token usage
- Can't track indexing performance
- Can't detect agent failures

**Fix:** Add basic metrics (token tracking, latency, health) as part of Phase 4A Task 1.

### H3. Desktop Preparation Too Early

Phase 7 proposes service abstraction and Tauri stubs now, but the real Tauri implementation will likely need to rewrite these abstractions. This is speculative engineering.

**Fix:** Move to position 9, or merge into Phase 10.

### H4. Keyword Search Uses ILIKE

`09-PHASE-4B-SMART-INDEXING.md` uses `CodeChunk.content.ilike(f"%{query}%")` — a full table scan. For 100k+ chunks, this is O(n).

**Fix:** Use PostgreSQL `tsvector`/`tsquery` full-text search. Add a `search_vector` column to `code_chunks`.

### H5. LLM Serial Inference Lock

`08-PHASE-4A-LLM-INTEGRATION.md` uses `asyncio.Lock()` on the LLM provider — only one inference request at a time. Concurrent users will block each other.

**Fix:** llama.cpp supports concurrent `create_chat_completion` calls. Remove the lock or use a semaphore with fair scheduling.

### H6. Model Registry Over-Engineered

7 hardcoded models in a PostgreSQL table with 15 columns. Ollama already manages models.

**Fix:** Use a JSON catalog file for recommendations, Ollama `/api/tags` for actual model listing. Keep download progress in memory.

### H7. No Migration Chain for Phases 6-10

Phase 6 creates `workflow.py` model but no migration. Phase 8 creates `long_term_memory.py` but no migration. The chain would break.

### H8. StorageResolver Singleton Bug

`paths.py:36-44` — the singleton ignores mode parameter after first call. If called with "web" then "tauri", it returns "web" forever. Phase 7 should fix this but doesn't identify it.

### H9. Shell Exec Security (Phase 6)

`shell_exec` tool described as "sandboxed" with no sandbox implementation. This is an RCE vector.

### H10. No Tests Anywhere

Zero test files across all 10 phases. Phase 10 mentions tests but provides none.

---

## Sequencing Issues

### Current Order (Corrected)
```
4A (LLM) → 4B (Indexing) → 5 (Conversation) → 6 (Agent Intel) → 
7 (Desktop Prep) → 8 (Learning) → 9 (Observability) → 10 (Production)
```

### Recommended Order
```
4A (LLM + basic metrics) → 4B-early (rules + watcher, no LLM dep) → 
5 (Conversation, parallel with 4B) → 4B-late (hybrid retrieval + reranking) → 
6a (Agent tool calling, simplified) → 8 (Learning, renamed) → 
9 (Observability dashboards) → 10 (Production + Desktop prep)
```

**Key changes:**
1. Split 4B — indexing rules don't need LLM, can run in parallel
2. Move Desktop Prep to end — premature now
3. Simplify Phase 6 — full workflow engine is too much
4. Add observability incrementally from Phase 4A

---

## Missing from Roadmap

| Gap | Impact | Recommendation |
|-----|--------|----------------|
| Data migration/rollback strategy | Schema changes could lose data | Add rollback validation to each phase |
| Multi-user concurrency | Two users indexing same repo | Add locking strategy in Phase 4B |
| Model disk management | Users download 50GB+ of models | Add disk quota and cleanup policy |
| Qdrant backup | Vector data loss is unrecoverable | Add Qdrant snapshot to backup.sh |
| Offline mode | Model downloads require internet | Pre-bundle a small model or graceful fallback |
| Cross-repo search | Search is per-repository | Add in Phase 8 (Learning) |
| Token counting for conversations | Context window overflow | Add to Phase 5 |
| Concurrent LLM requests | Single inference lock | Fix in Phase 4A |

---

## What's Right About the Roadmap

1. **Vision is clear and compelling** — "machine intelligence layer" is well-defined
2. **LLM integration first** — correctly identified as the biggest unlock
3. **Local-first architecture** — no external API dependencies
4. **Incremental phases** — each phase delivers standalone value
5. **Existing foundation is solid** — auth, vault, memory, indexing, agents all work
6. **UI refactor was successful** — warm dark theme, DashboardShell, component library
7. **Design system is coherent** — tokens, CSS, components are consistent
8. **Docker infrastructure works** — PostgreSQL, Redis, Qdrant all containerized
9. **Alembic migrations are clean** — 14 migrations with alphabetical naming
10. **Security foundations are strong** — JWT cookies, CSRF, rate limiting, path traversal protection

---

## Action Items (Priority Order)

### Before Phase 4A Execution
1. Fix all 11 CRITICAL issues in Phase 4A-4B
2. Add `__init__.py` to `backend/app/services/llm/`
3. Add `psutil` and `llama-cpp-python` to `pyproject.toml`
4. Correct import paths (`deps` → `core.db`)
5. Extend existing `LLMProvider` ABC, don't rewrite
6. Fix async/sync mismatches
7. Fix `GraphNode`/`GraphEdge` attribute names

### Before Phase 6 Execution
8. Rewrite Phase 6 with complete code (current version is outline-only)
9. Define shell_exec security model (or defer to Phase 10)
10. Add migration files for all new models

### Before Phase 7-10 Execution
11. Rewrite Phases 7-10 with complete code implementations
12. Add test files for all new endpoints
13. Add `tsvector` column to `code_chunks` for full-text search
14. Fix `StorageResolver` singleton mode switching bug

### Infrastructure Debt Sprint (2-3 days)
15. Unify API clients (remove `cortexApi.ts` duplicates)
16. Add Next.js middleware for auth
17. Remove Three.js from bundle (~2MB savings)
18. Fix `agentApi.list()` return type mismatch

---

## Final Assessment

**The roadmap will produce a production-ready Cortex if the issues above are addressed.** The vision is right, the architecture is sound, and the existing foundation is solid. The problems are mechanical — wrong imports, missing code depth, incorrect sequencing — not fundamental design flaws.

**Estimated timeline impact of fixes:** 2-3 days of plan refinement before execution begins. This investment prevents weeks of rework during implementation.

**Recommended next step:** Fix the 11 CRITICAL issues in Phase 4A-4B, rewrite Phases 6-10 to Phase 4A depth, then begin execution.

---

*Audit conducted 2026-06-20. Based on review of all 16 planning documents, 50+ backend files, 20+ frontend files, and infrastructure configuration.*
