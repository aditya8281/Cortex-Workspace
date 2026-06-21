# Cortex Strategic Master Plan

> **This is the authoritative plan.** It supersedes the individual phase plans where they conflict. It synthesizes the engineering audit findings, the product vision, and enhanced phase sequencing into a single coherent strategy.

**Author:** Cortex Architecture Review (Audit-Driven)
**Date:** 2026-06-21
**Status:** ACTIVE

---

## Part I: The Vision (Enhanced)

### What Cortex Is

Cortex is a **local-first machine intelligence layer** — a system that continuously understands a computer and lets the user interact with it through natural language, without needing to know filenames, paths, or system internals.

### What Cortex Is Not

- Not a chatbot with RAG bolted on
- Not a GitHub Copilot clone
- Not a generic AI assistant
- Not a cloud service with local caching

### The Product Experience We're Building

**Phase A — "It Works"**: Cortex indexes your code, lets you search it, and answers questions about it. Every feature is real, every endpoint is wired, every screen shows live data.

**Phase B — "It Thinks"**: Cortex has a brain. It reasons about your code, executes multi-step tasks, maintains conversation context, and synthesizes answers from your entire codebase.

**Phase C — "It Knows"**: Cortex learns from you. It recognizes patterns, tracks corrections, proactively suggests actions, and builds a persistent understanding of your machine.

**Phase D — "It Lives Here"**: Cortex is your machine's native intelligence. It runs as a desktop app, integrates with your OS, and works offline with local models.

### The Three Breakthroughs

1. **Zero-Configuration Intelligence**: Cortex should work immediately after install. No model downloads required for basic functionality. Graceful degradation chain: local LLM → Ollama → API fallback → mock responses that still make sense.

2. **Privacy as Architecture**: Everything local. No telemetry. No cloud sync. Vaults encrypted with user-provided passwords. The architecture itself guarantees privacy — not just a policy.

3. **Compound Learning**: Cortex gets better the more you use it. Not through fine-tuning, but through pattern recognition, preference tracking, and context accumulation. After a week of use, Cortex should feel like it "knows you."

---

## Part II: Audit Findings (What Must Be Fixed)

### Critical Bugs (Production Blockers)

| # | Severity | Location | Issue | Fix Phase |
|---|----------|----------|-------|-----------|
| 1 | **CRITICAL** | `embedding_service.py:130` | ONNX tokenizer is a complete stub — returns `{"input_ids": [[0]], "attention_mask": [[1]]}`. ONNX embeddings are garbage. | FIX-0 |
| 2 | **CRITICAL** | `cross_file_search.py:138` | Imports non-existent `HybridRetrieval` (should be `HybridRetrievalV2`). `hybrid_search()` always fails with ImportError. | FIX-0 |
| 3 | **HIGH** | `embedding_service.py:82` | `asyncio.get_event_loop().run_until_complete()` is deprecated/broken in async contexts. | FIX-0 |
| 4 | **HIGH** | `rag_pipeline.py:137-144` | Global `_rag_pipeline` singleton bound to first db session — stale connections on subsequent calls. | FIX-0 |
| 5 | **HIGH** | `ws.py`, `ws_models.py`, `ws_system.py` | 3 WebSocket endpoints have NO authentication. Anyone can connect and receive system metrics. | FIX-0 |
| 6 | **HIGH** | `system.py:33,62` | `/system/metrics` and `/system/logs` have NO authentication. Expose system info to unauthenticated users. | FIX-0 |
| 7 | **MEDIUM** | `models.py:108,225,482,528` | DB sessions leaked — `next(get_db())` called without closing. | FIX-0 |
| 8 | **MEDIUM** | `llm/manager.py:181` | `SessionLocal()` created inline for usage tracking — no proper lifecycle. | FIX-0 |
| 9 | **MEDIUM** | `rate_limit.py:42` | Silently passes through on Redis failure — rate limiting bypassed when Redis is down. | FIX-0 |
| 10 | **LOW** | `main.py:154` | Dead WebSocket echo endpoint. | FIX-0 |

### Architectural Issues

| # | Issue | Impact | Fix Phase |
|---|-------|--------|-----------|
| 1 | **Duplicate API clients** — `cortexApi` and typed `api` client both exist | Maintenance burden, confusion | FIX-0 |
| 2 | **Inconsistent router mounting** — 5 files hardcode paths, 14 use relative | Routing confusion | FIX-0 |
| 3 | **No `response_model`** on most endpoints | No output validation | FIX-1 |
| 4 | **CI mypy/lint `continue-on-error: true`** | Quality gates don't actually gate | FIX-0 |
| 5 | **Duplicate conftest.py** — root and backend are identical | Maintenance burden | FIX-0 |
| 6 | **~20 backend endpoints have no frontend consumer** | Dead code, maintenance | FIX-1 |
| 10 | **~10 frontend type mismatches** with backend | Runtime errors | FIX-1 |
| 7 | **Frontend test coverage: 13%** (2/15 pages) | No confidence in UI | FIX-1 |
| 8 | **API endpoint test coverage: 20%** (3/15 routers) | No confidence in API | FIX-1 |
| 9 | **0% E2E tests** | No full-stack confidence | FIX-2 |

### Test Coverage Gaps

**Services without tests:** `conversation_service`, `health_service`, `graph_builder`, `notification_service`, `user_service`, `usage_tracker`, `retrieval_metrics`, `incremental_indexer`, `cross_file_search`, `hf_discovery`, `indexing_rules`, `storage_registry`

**Frontend pages without tests:** Dashboard, Chat, Models, Vault, Memory, Settings, Search, Agents, Admin, Profile (10 pages)

**API routers without tests:** Profile, GitHub, Notifications, System, Search, Repository, Agents, Models, Indexing, Sync, Conversations, Knowledge, Metrics (12 routers)

---

## Part III: Enhanced Phase Sequencing

The existing plans are granular implementation plans. This master plan reorganizes them by **product value** and **dependency order**, incorporating audit fixes.

### Overview

```
FIX-0: Foundation Repair ──────────────────── (1-2 days)
  │
  ├──► P1: "It Works" ────────────────────── (3-5 days)
  │       │
  │       ├──► P2: "It Thinks" ───────────── (5-7 days)
  │       │       │
  │       │       ├──► P3: "It Knows" ────── (5-7 days)
  │       │       │       │
  │       │       │       ├──► P4: "It Lives Here" (7-10 days)
  │       │       │       │
  │       │       │       └──► P5: Production ──── (3-5 days)
  │       │       │
  │       │       └──► (P3 can start after P2 core)
  │       │
  │       └──► (P2 can start after P1 core)
  │
  └──► (FIX-0 must complete first)
```

---

### FIX-0: Foundation Repair (Prerequisite)

**Goal:** Fix all critical bugs, security holes, and architectural inconsistencies before building anything new.

**Duration:** 1-2 days
**Priority:** BLOCKING — nothing else proceeds until this is done.

#### Task 0.1: Fix Embedding Service

**File:** `backend/app/services/embedding_service.py`

- Fix ONNX tokenizer stub (line 130) — implement real tokenization using `tokenizers` library or remove ONNX path entirely
- Fix `asyncio.get_event_loop().run_until_complete()` (line 82) — make method async or use `asyncio.get_running_loop()`
- Verify Ollama embedding path works
- Verify mock fallback is clearly documented as non-production

**Validation:** `pytest tests/test_embedding_service.py -v` passes.

#### Task 0.2: Fix Cross-File Search

**File:** `backend/app/services/cross_file_search.py`

- Fix import at line 138: change `HybridRetrieval` to `HybridRetrievalV2`
- Verify `hybrid_search()` method works

**Validation:** `pytest tests/test_hybrid_retrieval_v2.py -v` passes.

#### Task 0.3: Fix Security Holes

**Files:** `backend/app/api/v1/ws_models.py`, `backend/app/api/v1/ws_system.py`, `backend/app/api/v1/system.py`, `backend/app/api/ws.py`

- Add authentication to WebSocket endpoints (`ws_models`, `ws_system`)
- Add authentication to `system.py` endpoints
- Remove or gate the dead `/ws` echo endpoint in `main.py`

**Validation:** Unauthenticated requests to `/system/metrics` return 401.

#### Task 0.4: Fix DB Session Leaks

**File:** `backend/app/api/v1/models.py`

- Replace `next(get_db())` calls (lines 108, 225, 482, 528) with proper `Depends(get_db)` usage
- Fix `SessionLocal()` in `llm/manager.py:181`

**Validation:** No `next(get_db())` calls remain in API files.

#### Task 0.5: Fix Rate Limiter Fail-Open

**File:** `backend/app/core/rate_limit.py`

- Change silent pass-through on Redis failure to fail-closed (return 429)
- Or make it configurable with a setting

**Validation:** Rate limiter returns 429 when Redis is unavailable.

#### Task 0.6: Consolidate API Clients

**Files:** `frontend/src/shared/auth/cortexApi.ts`, `frontend/src/shared/api/client.ts`

- Merge `cortexApi` vault/memory functions into the typed API modules
- Delete `frontend/src/shared/api/vault.ts` and `frontend/src/shared/api/memory.ts` (unused) or consolidate
- Standardize on one client pattern

**Validation:** `cd frontend && npx tsc --noEmit` passes.

#### Task 0.7: Fix CI Quality Gates

**File:** `.github/workflows/ci.yml`

- Remove `continue-on-error: true` from mypy and lint steps
- Merge duplicate `conftest.py` files

**Validation:** CI pipeline blocks on lint/type errors.

#### Task 0.8: Fix Dead Code

**Files:** `backend/app/main.py` (remove `/ws` echo), `backend/app/api/v1/models.py` (stub `GET /models/updates`)

- Remove or properly implement the `/ws` echo endpoint
- Either implement `GET /models/updates` or remove it

**Validation:** No stub endpoints remain.

---

### P1: "It Works" — Every Feature Is Real

**Goal:** Every visible feature has meaningful backend support. No mocks, no stubs, no placeholder data. Every screen shows live data from the real backend.

**Duration:** 3-5 days
**Depends on:** FIX-0

#### P1.1: Backend Contract Alignment

- Fix all ~10 frontend type mismatches with backend
- Add `response_model` to all API endpoints
- Standardize error response format across all endpoints
- Consume orphaned backend endpoints (model health, metrics, autocomplete, knowledge stats)

**Files to modify:**
- `frontend/src/shared/types.ts` — align with backend schemas
- `backend/app/api/v1/*.py` — add `response_model` to all endpoints
- `frontend/src/shared/api/*.ts` — fix type definitions

#### P1.2: Conversation System (from Phase 5 plan)

The conversation system is the most user-facing feature and should be prioritized.

- Create `Conversation` and `ConversationMessage` models
- Create `ConversationService` with context window management
- Create conversation API with SSE streaming
- Create chat UI with streaming support
- Wire into LLM manager

**Key improvement over existing plan:** Use the LLM manager's `chat_stream()` method directly instead of reimplementing streaming. Add proper context window management that considers token budgets.

#### P1.3: Frontend Test Coverage

Add tests for the 10 untested pages. Priority order:
1. Chat page (most complex)
2. Vault page (most critical)
3. Models page (download flow)
4. Memory page (CRUD)
5. Settings page (preferences)
6. Search page (results display)
7. Agents page (CRUD + chat)
8. Dashboard page (metrics)
9. Profile page (photo upload)
10. Admin page (user management)

**Target:** 80% frontend page coverage.

#### P1.4: API Endpoint Test Coverage

Add tests for the 12 untested routers. Priority order:
1. Conversations (CRUD + streaming)
2. Agents (CRUD + runs)
3. Models (list + download)
4. Search (hybrid retrieval)
5. Repository (CRUD + indexing)
6. Sync (status + start/stop)
7. Indexing (config + preview)
8. Profile (get/update/photo)
9. Notifications (list/read)
10. System (metrics)
11. Knowledge (health/stats)
12. GitHub (connect/disconnect)

**Target:** 80% API endpoint coverage.

#### P1.5: Indexing Intelligence (from Phase 4B plan)

- Create `IndexingConfig` model and `IndexingRules` service
- Add indexing configuration API and UI
- Integrate rules into incremental indexer
- Add file watcher integration
- Add sync status to dashboard

**Key improvement:** Use the existing `file_watcher_v2.py` (watchdog-based) instead of creating a new polling-based watcher. The v2 watcher is already implemented and more efficient.

---

### P2: "It Thinks" — Real Intelligence

**Goal:** Cortex has a brain that works. Agents reason, search synthesizes, chat conversations are useful, code can be explained.

**Duration:** 5-7 days
**Depends on:** P1 (conversation system must exist)

#### P2.1: LLM Integration (from Phase 4A plan)

The LLM integration is already mostly implemented. What's needed:

- Verify ONNX embedding path works after FIX-0
- Verify LLM manager health checks work end-to-end
- Add proper error messages when no LLM is available
- Wire LLM into search answer synthesis
- Wire LLM into agent executor
- Add model selection UI to chat page

**Key improvement:** Add a "model selector" dropdown to the chat page that lets users choose which model to use. Show model status (available/unavailable) in real-time.

#### P2.2: Agent Intelligence (from Phase 6 plan)

- Expand tool registry (shell, git, web fetch)
- Add SSE streaming for agent steps
- Add tool execution safety (sandboxed shell commands)
- Add agent performance metrics
- Improve agent chat UI with step visualization

**Key improvement over existing plan:** Add a **tool permission system**. Before executing shell commands or writing files, agents should ask for user confirmation. This is critical for safety.

**New concept: Agent Sandboxing**
- Shell commands run in a configurable working directory
- Write operations require user approval
- File access is restricted to indexed repositories
- Network access is logged and rate-limited

#### P2.3: Hybrid Retrieval Quality

- Fix the RAG pipeline singleton bug
- Improve keyword search with proper PostgreSQL full-text search (tsvector/tsquery)
- Improve graph search with weighted edge traversal
- Add result deduplication and source attribution
- Add retrieval quality metrics (precision, recall, latency)

**Key improvement:** Add **source attribution** to search results. Every result should show which file it came from, with a clickable link to open the file.

#### P2.4: Code Intelligence

- Wire tree-sitter crate into Python backend (via PyO3 or subprocess)
- Add proper AST-based code parsing (replacing regex-based extraction)
- Add dependency graph visualization
- Add code complexity metrics
- Add "explain this code" agent tool

---

### P3: "It Knows" — Learning & Memory

**Goal:** Cortex learns from interactions and builds persistent understanding.

**Duration:** 5-7 days
**Depends on:** P2 (LLM must be working for learning)

#### P3.1: Long-Term Memory (from Phase 8 plan)

- Create `LongTermMemory` model with confidence-based relevance
- Create long-term memory service with reinforcement/decay
- Add pattern recognizer for coding style
- Add correction tracker
- Add proactive suggestion engine
- Create learning API and dashboard

**Key improvement:** Add **memory categories** that align with the product vision:
- `preference` — user preferences (editor, language, style)
- `pattern` — recurring coding patterns
- `correction` — when user corrects Cortex's output
- `fact` — discovered facts about the codebase
- `context` — contextual information (current project, task)

#### P3.2: Proactive Intelligence

- **Change watcher**: When files change, Cortex proactively re-indexes and offers to explain what changed
- **Pattern suggestions**: "I notice you always use X pattern. Would you like me to apply it automatically?"
- **Error prediction**: "This function might have a race condition based on similar patterns I've seen."
- **Dependency alerts**: "A package you use has a security update."

#### P3.3: Context Building

- Build context from workspace state (open files, recent changes, project structure)
- Build context from conversation history
- Build context from long-term memory
- Build context from knowledge graph
- Use context to improve all AI responses

---

### P4: "It Lives Here" — Desktop & Integration

**Goal:** Cortex becomes the machine's native intelligence layer.

**Duration:** 7-10 days
**Depends on:** P2 (core intelligence must work)

#### P4.1: Desktop Preparation (from Phase 7 plan)

- Fix StorageResolver singleton bug
- Complete service abstraction layer
- Add filesystem abstraction for Tauri
- Create native integration hooks
- Add offline capabilities

**Key improvement:** Don't abstract everything. Focus on the **three things Tauri can't do through HTTP**:
1. File system access (native file dialogs, filesystem watching)
2. System tray integration
3. Auto-updates

Everything else (API calls, database, vector DB) stays as HTTP services.

#### P4.2: Observability (from Phase 9 plan)

- Create metrics collector service
- Add health check aggregation
- Create system health dashboard
- Add agent performance metrics
- Add retrieval quality metrics
- Add resource usage monitoring

**Key improvement:** Don't build a separate dashboard. Integrate observability into the existing dashboard:
- Add a "System Health" tab to the dashboard
- Show real-time metrics (CPU, RAM, disk, vector DB size)
- Show agent performance (success rate, avg duration, token usage)
- Show retrieval quality (search latency, zero-result rate)

#### P4.3: Production Hardening (from Phase 10 plan)

- Add comprehensive test suite (target: 80% coverage)
- Security hardening (headers, rate limiting, input validation)
- Performance optimization (connection pooling, response compression)
- Docker packaging (multi-stage build, health checks)
- CI/CD pipeline (lint, type check, test, build, deploy)

**Key improvement:** Add **performance benchmarks** as part of the test suite:
- Embedding latency: < 100ms
- Search latency: < 200ms
- Chat first token: < 2s
- Indexing speed: > 1000 files/second

---

### P5: The Experience Layer

**Goal:** Make Cortex feel alive, not just functional.

**Duration:** Ongoing (can start after P2)

#### P5.1: Onboarding Experience

- First-run wizard that discovers the system
- Automatic repo detection and indexing
- Model recommendation based on hardware
- "What can I do?" tutorial
- Progressive disclosure of features

#### P5.2: Command Palette Enhancement

The `⌘K` command palette should be the primary interaction method:
- Search across all data types
- Quick actions (index repo, download model, start chat)
- Navigation (jump to any page)
- Agent commands (run agent, check status)
- System commands (restart, backup, settings)

#### P5.3: Notification Intelligence

- Proactive notifications for important events
- Learning progress updates
- Indexing completion alerts
- Security notifications
- Model update availability

---

## Part IV: Product Design Principles

### 1. The 3-Second Rule

Every action should complete in under 3 seconds. If it takes longer, show progress. If it's background, show it's working.

### 2. The Trust Rule

Cortex should never surprise the user with destructive actions. Always confirm before:
- Deleting files
- Running shell commands
- Modifying code
- Sending data anywhere

### 3. The Graceful Degradation Rule

Cortex should work at every capability level:
- **No LLM**: Search, indexing, and vault work. Chat shows "LLM not available" message.
- **No GPU**: CPU inference works, just slower. Show expected speed.
- **No Internet**: Everything works offline. No cloud dependencies.
- **No Database**: Fallback to file-based storage for basic functionality.

### 4. The Privacy Rule

- No telemetry by default
- No cloud sync by default
- No external API calls by default
- All data stays on the machine
- Vaults are encrypted with user-provided passwords
- User can audit all data Cortex stores

### 5. The Composability Rule

Every feature should work independently:
- Chat works without search
- Search works without agents
- Agents work without learning
- Learning works without chat
- Desktop works without all of the above

---

## Part V: Success Metrics

### Functional Metrics

| Metric | Target | Current |
|--------|--------|---------|
| Pages with real backend | 12/12 (100%) | 12/12 ✅ |
| API endpoints with auth | 100% | ~95% ❌ |
| Frontend test coverage | >80% | ~13% ❌ |
| API test coverage | >80% | ~20% ❌ |
| E2E test coverage | >50% | 0% ❌ |
| Critical bugs | 0 | 10 ❌ |

### Performance Metrics

| Metric | Target | Current |
|--------|--------|---------|
| Cold start | < 2s | Unknown |
| Embedding latency | < 100ms | Unknown |
| Search latency | < 200ms | Unknown |
| Chat first token | < 2s | Unknown |
| Indexing speed | >1000 files/s | Unknown |
| Memory usage (idle) | < 500MB | Unknown |

### Product Metrics

| Metric | Target | Current |
|--------|--------|---------|
| Time to first search | < 30s after install | Unknown |
| Time to first chat | < 2min after install | Unknown |
| Conversations that complete | >90% | Unknown |
| Search zero-result rate | <10% | Unknown |
| Agent task success rate | >80% | Unknown |

---

## Part VI: What the Existing Plans Get Right

The existing phase plans are excellent implementation guides. They get right:

1. **Granular step-by-step tasks** — each task is independently testable
2. **Code-first approach** — every step includes actual code, not just descriptions
3. **Commit discipline** — each task ends with a git commit
4. **Build verification** — compile checks and build verification at each step
5. **Interface documentation** — clear "consumes/produces" blocks

### What They Miss

1. **No audit-driven prioritization** — they assume the current code is correct
2. **No product experience thinking** — they focus on features, not user journeys
3. **No graceful degradation** — they don't plan for when things fail
4. **No learning/feedback loops** — they're one-directional implementations
5. **No cross-cutting concerns** — security, performance, and observability are afterthoughts

### How to Use This Plan

1. **Start with FIX-0** — fix all critical bugs before anything else
2. **Follow P1-P5 in order** — each phase builds on the previous
3. **Use existing phase plans for implementation details** — they're excellent for that
4. **Apply the design principles** — every decision should pass the 5 rules
5. **Measure everything** — don't guess, measure

---

## Part VII: Risk Assessment

### High Risk

| Risk | Impact | Mitigation |
|------|--------|------------|
| ONNX tokenizer fix is complex | Blocks embedding quality | May need to remove ONNX path entirely and rely on Ollama |
| Agent safety (shell execution) | Security vulnerability | Add permission system before enabling shell tools |
| Tauri migration complexity | Major rewrite | Keep HTTP service boundary clean, don't over-abstract |

### Medium Risk

| Risk | Impact | Mitigation |
|------|--------|------------|
| Test coverage gaps | Regression risk | Prioritize integration tests over unit tests |
| Frontend type mismatches | Runtime errors | Add type generation from backend schemas |
| Memory decay tuning | Learning quality | Start with simple time-based decay, tune later |

### Low Risk

| Risk | Impact | Mitigation |
|------|--------|------------|
| Performance optimization | User experience | Profile before optimizing, don't premature optimize |
| Desktop packaging | Distribution | Can defer to after web version is solid |

---

## Appendix A: Existing Plan File Mapping

| This Plan | Existing Plan File | Notes |
|-----------|-------------------|-------|
| FIX-0 | (new — derived from audit) | No existing plan covers this |
| P1.2 | `10-PHASE-5-CONVERSATION.md` | Use as-is, apply design principles |
| P1.5 | `09-PHASE-4B-SMART-INDEXING.md` | Use existing `file_watcher_v2.py` instead |
| P2.1 | `08-PHASE-4A-LLM-INTEGRATION.md` | Already implemented, needs verification |
| P2.2 | `11-PHASE-6-AGENT-INTELLIGENCE.md` | Add safety/permission system |
| P3.1 | `13-PHASE-8-LEARNING-LOOP.md` | Use as-is, add memory categories |
| P4.1 | `12-PHASE-7-DESKTOP-PREPARATION.md` | Simplify — focus on 3 Tauri capabilities |
| P4.2 | `14-PHASE-9-OBSERVABILITY.md` | Integrate into existing dashboard |
| P4.3 | `15-PHASE-10-PRODUCTION.md` | Add performance benchmarks |

---

## Appendix B: File Change Summary

### Files to Create (New)

| File | Phase | Purpose |
|------|-------|---------|
| `backend/app/models/long_term_memory.py` | P3 | Long-term memory model |
| `backend/app/services/long_term_memory.py` | P3 | Long-term memory service |
| `backend/app/services/metrics_collector.py` | P4 | Metrics collection |
| `backend/app/agents/tools/__init__.py` | P2 | Tool registry |
| `backend/app/agents/tools/shell.py` | P2 | Shell execution tool |
| `backend/app/agents/tools/git_tools.py` | P2 | Git tools |
| `backend/app/agents/tools/web_fetch.py` | P2 | Web fetch tool |
| `backend/app/api/v1/agent_stream.py` | P2 | SSE agent streaming |
| `tests/test_api_*.py` (12 files) | P1 | API endpoint tests |

### Files to Modify (Critical)

| File | Phase | Change |
|------|-------|--------|
| `backend/app/services/embedding_service.py` | FIX-0 | Fix ONNX tokenizer, fix async |
| `backend/app/services/cross_file_search.py` | FIX-0 | Fix import |
| `backend/app/api/v1/ws_models.py` | FIX-0 | Add auth |
| `backend/app/api/v1/ws_system.py` | FIX-0 | Add auth |
| `backend/app/api/v1/system.py` | FIX-0 | Add auth |
| `backend/app/api/v1/models.py` | FIX-0 | Fix session leaks |
| `backend/app/core/rate_limit.py` | FIX-0 | Fail-closed |
| `backend/app/main.py` | FIX-0 | Remove dead WS |
| `.github/workflows/ci.yml` | FIX-0 | Remove continue-on-error |
| `frontend/src/shared/types.ts` | P1 | Fix type mismatches |
| `frontend/src/shared/api/client.ts` | P1 | Consolidate clients |

### Files to Delete

| File | Phase | Reason |
|------|-------|--------|
| `backend/tests/conftest.py` | FIX-0 | Duplicate of root conftest |
| `frontend/src/shared/api/vault.ts` | P1 | Unused (cortexApi used instead) |
| `frontend/src/shared/api/memory.ts` | P1 | Unused (cortexApi used instead) |

---

*This plan is a living document. Update it as phases complete and new findings emerge.*
