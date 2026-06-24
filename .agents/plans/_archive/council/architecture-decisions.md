# CORTEX Architecture Decisions — Evidence-Based

**Date:** 2026-06-25
**Purpose:** Document every architectural decision — what was decided, why, what alternatives exist, and whether the decision should be revisited.

---

## 1. Decisions That Should Stand

### 1.1 PostgreSQL as Primary Database
- **Decision:** PostgreSQL 16 for all platform data.
- **Status:** ✅ Correct — no reason to change.
- **Evidence:** 33 tables, 25+ migrations, JSONB for flexible data, FK constraints, GIN indexes. Superior to SQLite (Odysseus, Mem0) and Prisma (AnythingLLM).
- **Alternatives considered:** SQLite (rejected — scale, reliability, concurrent access). Neo4j (rejected — separate process, Java runtime).
- **Revisit:** No.

### 1.2 Two-Password Auth Model
- **Decision:** Separate login password and vault password. JWT access + refresh tokens in httpOnly cookies. CSRF double-submit.
- **Status:** ✅ Correct — strong security model.
- **Evidence:** Auth flow tested (11 tests). Vault isolation means even a compromised session can't access files without vault password.
- **Alternatives considered:** Single password (Odysseus — weaker). Bearer tokens (Odysseus — less secure than httpOnly cookies).
- **Revisit:** No.

### 1.3 Fernet Encryption for Vault
- **Decision:** Fernet symmetric encryption with per-user vault password and per-file salt derivation.
- **Status:** ✅ Correct — battle-tested encryption.
- **Evidence:** vault_service.py (806 lines) with SecurePasswordCache that wipes passwords from memory.
- **Alternatives considered:** None — Fernet is the right choice for local-first file encryption.
- **Revisit:** No.

### 1.4 Hybrid Retrieval (Vector + Fulltext + Graph)
- **Decision:** Three-source retrieval merged via RRF with MMR diversity reranking.
- **Status:** ✅ Correct — best-in-class retrieval architecture.
- **Evidence:** hybrid_retrieval.py (307 lines). Better than Odysseus (ChromaDB only), Mem0 (triple-signal but no graph), AnythingLLM (single vector).
- **Alternatives considered:** Vector-only (too narrow). Fulltext-only (no semantic understanding). Graph-only (no content retrieval).
- **Revisit:** No — but enhance with adaptive scoring, entity boosting, composable recipes.

### 1.5 Next.js 15 + React 19 Frontend
- **Decision:** Next.js App Router with React 19, TypeScript 5.8, Tailwind 3.4.
- **Status:** ✅ Correct — modern, well-supported stack.
- **Evidence:** 21,800 lines of real production code. 14 routes, 18 components, SSE streaming.
- **Alternatives considered:** SvelteKit (Open WebUI uses it — rejected, Cortex already invested in React). Vanilla JS (Odysseus — rejected, too primitive).
- **Revisit:** No.

### 1.6 Three-Tier Embedding Fallback
- **Decision:** ONNX → Ollama → mock fallback chain.
- **Status:** ✅ Correct for current needs — but should become pluggable.
- **Evidence:** embedding_service.py (204 lines). Works without any external service (ONNX is local). Graceful degradation.
- **Alternatives considered:** Single provider (too fragile). Pluggable provider (right direction — see Decision 2.1).
- **Revisit:** Yes — replace with pluggable provider Protocol (Decision 2.1).

### 1.7 Arq for Background Tasks
- **Decision:** arq (Redis-based) for background task queue.
- **Status:** ✅ Correct — lightweight, async-native, Redis-backed.
- **Evidence:** tasks/worker.py registers 5 tasks. Cron health check every 30min.
- **Alternatives considered:** Celery (too heavy). Custom scheduler (Odysseus — adds complexity). asyncio tasks (current state — lost on restart).
- **Revisit:** No — but add event-driven triggers on top (Decision 2.5).

### 1.8 Docker Compose for Infrastructure
- **Decision:** PostgreSQL 16 + Redis 7 + Qdrant v1.18 in Docker Compose, localhost-only.
- **Status:** ✅ Correct — production-ready infrastructure.
- **Evidence:** docker-compose.yml with proper volume mounts, health checks, localhost binding.
- **Alternatives considered:** Embedded databases (future for desktop mode). Kubernetes (overkill for local-first).
- **Revisit:** No for server mode. Desktop mode needs embedded alternatives (Decision 2.6).

### 1.9 TDD with SQLite In-Memory Tests
- **Decision:** SQLite in-memory engine with JSONB→JSON compiler for tests. Transaction rollback isolation.
- **Status:** ✅ Correct — fast, isolated, no external dependencies.
- **Evidence:** 341 tests. conftest.py architecture is sophisticated. 13 blanket-mocked external services.
- **Alternatives considered:** PostgreSQL tests (slower, requires running DB). Mock-only tests (less realistic).
- **Revisit:** No.

### 1.10 Multi-Agent Governance Ecosystem
- **Decision:** 12 mandatory rules, 11 hooks, 10 workflows, 7 strategic commands.
- **Status:** ✅ Correct — industry-leading development process.
- **Evidence:** GOVERNANCE.md, WORKFLOWS.md, DEVELOPER_GUIDE.md — all comprehensive.
- **Alternatives considered:** None — this is unique to Cortex.
- **Revisit:** No — but add effectiveness metrics.

### 1.11 "Warm Neural Dark" Design System
- **Decision:** Dark-only glassmorphism with cyan accent, neural network animated background.
- **Status:** ✅ Correct — distinctive, cohesive visual identity.
- **Evidence:** DESIGN.md (207 lines), tokens.ts (70 lines), NeuralNetwork.tsx (560 lines).
- **Alternatives considered:** Light mode support (deferred — adds complexity). Different color scheme (no reason to change).
- **Revisit:** No.

### 1.12 Code-Aware Knowledge Graph
- **Decision:** Extract import, call, inheritance edges from code. Graph-enhanced retrieval via RRF.
- **Status:** ✅ Correct — unique capability no other repo has.
- **Evidence:** graph_builder.py (412 lines), entity_extractor.py (220 lines).
- **Alternatives considered:** Regex-only extraction (current — too brittle). LLM-only extraction (too expensive for code).
- **Revisit:** Yes — add LLM-based extraction for non-code content (conversations, documents, emails).

---

## 2. Decisions That Should Be Revisited

### 2.1 Embedding Service → Pluggable Provider
- **Current decision:** Hardcoded three-tier fallback (ONNX → Ollama → mock).
- **Problem:** Can't add new providers without forking. Can't configure per-vault.
- **Evidence:** embedding_service.py uses if/elif chain. Mem0 has 8 providers via base class. LlamaIndex has 70+ backends.
- **New decision:** Replace with Protocol-based provider registry. ONNX remains default. Community can add providers.
- **Phase:** Phase 2 (service abstraction).
- **Classification:** REPLACE (R3).

### 2.2 Vector Store → Abstracted Interface
- **Current decision:** Qdrant-only. Direct client calls in core/vector_db.py.
- **Problem:** Desktop mode requires Qdrant running. Can't swap backends.
- **Evidence:** core/vector_db.py (85 lines) — direct Qdrant calls. Mem0 has 24 backends. LlamaIndex has 70+.
- **New decision:** Protocol-based abstraction. Qdrant for server mode. turbovec for desktop mode.
- **Phase:** Phase 2 (abstraction) + Phase 6 (desktop implementation).
- **Classification:** REPLACE (R4).

### 2.3 Agent System → Unified Loop
- **Current decision:** Planner→Executor two-agent pattern.
- **Problem:** Adds latency, complexity. No compaction, no security, no MCP, no detached runs.
- **Evidence:** planner.py (101 lines) + executor.py (316 lines). Odysseus has single 3,485-line streaming loop. Continue has single tool-calling loop.
- **New decision:** Single streaming agent loop with tool-calling, policy, compaction, security. Planner becomes a planning tool, not a separate agent.
- **Phase:** Phase 2-3.
- **Classification:** REPLACE (R5).

### 2.4 Tool Registry → Decorator-Based
- **Current decision:** Hand-maintained TOOL_REGISTRY dict with 5 tools, no schemas.
- **Problem:** Can't extend without forking. No parameter schemas degrades LLM function-calling.
- **Evidence:** tools.py — `(name, description, handler)` tuples. Strands has @tool decorator with auto-schema. Odysseus has 60+ tools with JSON Schema.
- **New decision:** @tool decorator with auto-generated schema from type hints + docstrings. Policy hooks per tool.
- **Phase:** Phase 2.
- **Classification:** REPLACE (R7).

### 2.5 Background Tasks → Event-Driven Runner
- **Current decision:** arq tasks + in-process asyncio.Queue for SSE.
- **Problem:** asyncio tasks lost on restart. No event triggers. No persistence.
- **Evidence:** background.py (54 lines) — in-memory Queue. Odysseus has server-side runs with replay buffer.
- **New decision:** Event-driven runner with persistence, PID tracking, restart-safety. Keep arq for heavy jobs, add event bus for lightweight triggers.
- **Phase:** Phase 3.
- **Classification:** REPLACE (R6).

### 2.6 Context Management → Compaction + Security + Providers
- **Current decision:** Simple truncation. No security markers. Monolithic RAG pipeline.
- **Problem:** Long conversations lose context. Retrieved content can inject prompts. Can't add new context sources.
- **Evidence:** No compaction anywhere. No UNTRUSTED_SOURCE_DATA markers. Continue has 20+ IContextProvider implementations.
- **New decision:** Auto-compaction at 85% with structured summary. UNTRUSTED_SOURCE_DATA on all external content. Composable context providers.
- **Phase:** Phase 2-3.
- **Classification:** ADAPT (A10, AD14, AD16).

### 2.7 Middleware Location
- **Current decision:** Middleware in `core/` files (middleware.py, csrf.py, rate_limit.py, https_redirect.py).
- **Problem:** CLAUDE.md says `middleware/` directory. Documentation contradicts code.
- **Evidence:** CLAUDE.md line ~30 references non-existent directory.
- **New decision:** Either create `middleware/` directory and move files, or update CLAUDE.md to reflect reality. Moving is cleaner but adds churn. Updating docs is simpler.
- **Phase:** Documentation cleanup.
- **Classification:** Low priority fix.

---

## 3. Decisions That Need New ADRs

### 3.1 MCP Integration
- **No existing decision.** Cortex has zero MCP support.
- **Need:** ADR for MCP client (connect to external servers) vs MCP server (expose Cortex tools) vs both.
- **Evidence:** All 3 Batch 4 repos (Continue, Odysseus, Strands) have MCP. It's table stakes.
- **Recommendation:** Start with client only. Defer server to later.
- **Phase:** Phase 3.

### 3.2 Plugin Architecture
- **No existing decision.** Cortex has no plugin system.
- **Need:** ADR for plugin layers (providers, tools, pipelines) and loading mechanism.
- **Evidence:** Open WebUI has 6 layers. AnythingLLM has 5. Strands has @tool + dynamic loading.
- **Recommendation:** Start with 3 layers (providers, tools, pipelines). Protocol-based.
- **Phase:** Phase 2-3.

### 3.3 Desktop Mode Strategy
- **No existing decision.** Desktop-first reorientation is designed but not decided.
- **Need:** ADR for embedded vs Docker desktop, Tauri shell, CLI as primary interface.
- **Evidence:** Desktop-First Reorientation Design spec exists (492 lines) but no ADR.
- **Recommendation:** Embedded by default (PG + Qdrant embedded), Docker for power users. Tauri for shell. CLI for automation.
- **Phase:** Phase 6.

### 3.4 Token Estimation
- **No existing decision.** Uses `len(text) // 4`.
- **Need:** ADR for token counting strategy (tiktoken vs character approximation vs model-specific).
- **Evidence:** Different tokenizers produce different counts. Compaction timing depends on accurate counting.
- **Recommendation:** Install tiktoken. Use cl100k_base encoding as default. Add 10% safety margin.
- **Phase:** Phase 2 (when compaction is added).

### 3.5 Daily Productivity Tools Architecture
- **No existing decision.** Odysseus has 10 subsystems (~15,000 lines). User wants all of them.
- **Need:** ADR for how daily tools integrate with agent system, whether they're core or plugins, and how they're sequenced.
- **Evidence:** Odysseus implements them as routes + services + agent tools. Each is independent.
- **Recommendation:** Start with task scheduler + skills + webhooks (foundation). Add email/calendar/notes/documents/contacts later. Each is a separate module with its own routes, services, and models.
- **Phase:** Phase 4 (foundation), Phase 5+ (full tools).

---

## 4. Decision Conflict Matrix

| Topic | Decision A | Decision B | Conflict | Resolution |
|-------|-----------|-----------|----------|------------|
| **Embedding** | Three-tier fallback (current) | Pluggable provider (proposed) | Current is hardcoded, proposed is abstracted | REPLACE current with proposed (R3) |
| **Vector store** | Qdrant-only (current) | Abstracted interface (proposed) | Current is locked, proposed is swappable | REPLACE current with proposed (R4) |
| **Agent** | Planner→Executor (current) | Unified loop (proposed) | Current is two-agent, proposed is single | REPLACE current with proposed (R5) |
| **Tools** | TOOL_REGISTRY dict (current) | @tool decorator (proposed) | Current is manual, proposed is auto-schema | REPLACE current with proposed (R7) |
| **Background** | asyncio tasks (current) | Event-driven runner (proposed) | Current is in-memory, proposed is persistent | REPLACE current with proposed (R6) |
| **Context** | Truncation (current) | Compaction + security + providers (proposed) | Current is primitive, proposed is intelligent | ADAPT current to proposed (A10, AD14, AD16) |
| **Middleware** | In core/ (code) | In middleware/ (CLAUDE.md) | Documentation contradicts code | Update CLAUDE.md or move files |
| **Token estimation** | len(text)//4 (current) | tiktoken (proposed) | Current is inaccurate, proposed is precise | REPLACE with tiktoken |

---

## 5. Decision Debt

| Decision | Age | Impact of Not Revisiting | Priority |
|----------|-----|------------------------|----------|
| Agent system (Planner→Executor) | Since initial commit | Core functionality degraded | Critical |
| Tool registry (no schemas) | Since initial commit | LLM function-calling degraded | Critical |
| Embedding (hardcoded tiers) | Since initial commit | Can't extend providers | High |
| Vector store (Qdrant-only) | Since initial commit | Can't do desktop mode | High |
| Background tasks (asyncio) | Since initial commit | Can't do daemon mode | High |
| Context (no compaction) | Since initial commit | Long conversations lose context | High |
| Middleware location | Since initial commit | Documentation drift | Low |
| Token estimation | Since initial commit | Inaccurate token counting | Medium |
