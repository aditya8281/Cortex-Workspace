# CORTEX Current State — Factual Inventory

**Date:** 2026-06-25
**Purpose:** Establish exact reality of what exists, what works, what doesn't.

---

## 1. Codebase Statistics

| Metric | Value |
|--------|-------|
| Backend Python files | 170 |
| Backend total lines | ~21,000 |
| Frontend TS/TSX files | 48 |
| Frontend total lines | ~21,800 |
| Test files | 42 |
| Test functions | 341 |
| SQLAlchemy models | 33 |
| API endpoints | ~50 across 18 routers |
| CLI command stubs | 15 (all unimplemented, 158 total lines) |
| Rust crate lines | ~83 (scaffolding only) |
| Git commits this month | 448 |
| Active branches | 1 (main, clean) |

---

## 2. Backend — What Exists

### 2.1 Core Infrastructure (`backend/app/core/`, 16 files, ~1,512 lines)

| Component | Status | Lines | Notes |
|-----------|--------|-------|-------|
| Config (Pydantic Settings) | ✅ Working | 114 | 30+ fields, auto-generates SECRET_KEY |
| Security (Argon2 + JWT) | ✅ Working | 266 | Access (30min) + refresh (7-day rotation) tokens, HMAC key rotation |
| Redis wrapper | ✅ Working | 109 | Graceful degradation — returns None on failure |
| CSRF (double-submit) | ✅ Working | 63 | Exempts auth/health/ws |
| Rate limiting | ✅ Working | 72 | Sliding window via Redis with in-memory fallback |
| Request logging | ✅ Working | 100 | Structured logging, RequestIdFilter, 500-entry in-memory buffer |
| Vector DB (Qdrant) | ✅ Working | 85 | upsert, search, delete, list_collections |
| WebSocket manager | ✅ Working | 77 | Connection management |
| System paths | ✅ Working | 225 | Canonical paths, blocked paths, traversal prevention |
| System info | ✅ Working | 197 | Hardware detection |
| Storage abstraction | ✅ Working | 142 | Path validation + directory management |
| HTTPS redirect | ✅ Working | 37 | Middleware |
| Service base | ⚠️ Empty | 18 | Base class with no methods |

### 2.2 API Layer (`backend/app/api/`, 18 routers)

| Router | Endpoints | Status |
|--------|-----------|--------|
| auth | register, login, logout, refresh, me, change-password, delete-account | ✅ Complete |
| users | user CRUD | ✅ |
| profile | user profile | ✅ |
| vault | lock/unlock, CRUD, rename, move, search, export | ✅ Complete |
| memory | CRUD, search, scan-repo | ✅ |
| search | unified search, graph data, node context, LLM answer | ✅ |
| repos | CRUD, index, status, build graph | ✅ |
| agents | CRUD, run/start/stream/feedback | ✅ |
| conversations | CRUD, rename | ✅ |
| models | catalog, hardware, download/progress/cancel, recommended, search, compare, sync, settings, usage | ✅ Complete |
| long-term-memory | CRUD, decay, reinforce | ✅ |
| knowledge | health, stats | ✅ |
| indexing | config, preview, status | ✅ |
| sync | file watcher management | ✅ |
| notifications | CRUD | ✅ |
| system | health, info, metrics | ✅ |
| WebSocket | real-time events | ✅ |

### 2.3 Agent System (`backend/app/agents/`, 4 files)

| File | Lines | Status | Reality |
|------|-------|--------|---------|
| planner.py | 101 | ✅ Working | Creates structured plan via LLM. Max 3 plan items. Falls back to keyword matching when no LLM. |
| executor.py | 316 | ✅ Working | Executes plan steps via tool calling. Max 10 iterations. Calls `llm_manager.chat()` directly. |
| tools.py | 218 | ✅ Working | 5 tools: `exec_command`, `git_log`, `git_diff`, `web_fetch`, `ask_user`. 3 require HMAC approval. Has SSRF protection, path traversal prevention, blocked commands, 30s timeout. |
| run_manager.py | 273 | ✅ Working | Orchestrates plan→execute→record. Creates AgentRun/AgentStep DB records. Supports SSE streaming callbacks. |
| background.py | 54 | ✅ Working | Background execution with in-memory asyncio.Queue for SSE events. |

**Agent System Summary:**
- 5 tools total (exec_command, git_log, git_diff, web_fetch, ask_user)
- NO parameter schemas on any tool
- Planner→Executor two-agent pattern
- Max 10 iterations (hardcoded)
- No context compaction
- No prompt security
- No MCP integration
- No detached runs
- No intent classification
- No loop-breaker
- Approval state in-memory only (lost on restart)

### 2.4 Services (`backend/app/services/`, 26+ files, ~10,049 lines)

**Implemented and working:**

| Service | Lines | What It Does |
|---------|-------|-------------|
| vault_service | 806 | Fernet encryption, SecurePasswordCache, per-file salt |
| ollama_catalog | 693 | Three-source catalog (OCI + Cloud API + Local API) |
| recommendation | 525 | Hardware-aware model recommendations |
| model_downloader | 520 | Background download with progress, retry, pause/resume |
| document_indexer | 448 | MIME-based indexing, 15 parsers, embedding, Qdrant |
| graph_builder | 412 | Knowledge graph from code (import/call/inheritance) |
| llm/manager | 369 | LLM routing, retry with backoff, usage tracking |
| incremental_indexer | 345 | Skip unchanged files, batch+real-time tracks |
| hardware | 359 | GPU, RAM, disk detection |
| hybrid_retrieval | 307 | RRF merge + MMR diversity across vector/fulltext/graph |
| catalogue | 298 | Model catalog DB operations |
| seed_data | 295 | Model catalog seed data |
| fulltext_search | 286 | PostgreSQL tsvector/tsquery, BM25, snippets |
| path_index | 276 | File path resolution |
| repo_scanner | 237 | Directory scanning for indexed files |
| entity_extractor | 220 | Regex-based entity extraction from code |
| chunker | 235 | Code-aware chunking (function/class/module) |
| embedding_service | 204 | Three-tier: ONNX → Ollama → mock |
| conversation_service | 201 | CRUD, context window, LLM title/insight extraction |
| model_comparison | 197 | Model comparison logic |
| model_detail_scraper | 264 | Scrapes Ollama model details |
| semantic_chunker | 206 | Semantic text chunking |
| memory_manager | 263 | KnowledgeEntry CRUD + Qdrant search |
| long_term_memory | 113 | Confidence decay (0.95x/30d), reinforcement |
| ollama_sync | 157 | Syncs Ollama models to catalog |
| user_service | 169 | User CRUD, auth helpers |
| cross_file_search | 166 | Cross-file reference search |
| deletion_pipeline | 155 | Cascading deletion |
| batch_indexer | 172 | Batch document embedding |
| embedding_cache | 150 | Embedding cache with TTL |
| retrieval_metrics | 90 | Retrieval quality metrics |
| indexing_orchestrator | 99 | Scan → index → graph pipeline |
| indexing_rules | 187 | File include/exclude rules |
| notification_service | 78 | In-memory notifications |
| storage_registry | 41 | Per-user storage registration |
| sync_service | 210 | Background catalog sync |
| usage_tracker | 65 | LLM token tracking |
| quantization_db | 131 | Quantization metadata |
| document_statistics | 172 | Document collection stats |

**Stubs:**
| File | Lines | Status |
|------|-------|--------|
| file_staleness | 19 | ⚠️ Stub — minimal |

**15 Document Parsers (all working):** PDF, Markdown, DOCX, HTML, EPUB, PPTX, XLSX, notebook, media, archive, font, iCal, vCard, OpenDocument, GIS

**4 Embedding Providers (all working):** HuggingFace (378 lines), Ollama (139), base (114), registry (90)

### 2.5 Background Tasks (`backend/app/tasks/`, 3 files, 200 lines)

| Task | What It Does |
|------|-------------|
| embed_memory_task | Embed memory entries |
| scan_repo_task | Scan repository for new files |
| bulk_embed_task | Bulk embedding |
| index_repo_task | Index repository |
| build_graph_task | Build knowledge graph |

Worker: arq with Redis, cron health check every 30min, 1-hour result retention.

### 2.6 Middleware

No `middleware/` directory exists despite CLAUDE.md mentioning it. All middleware lives in `core/`:
- `core/middleware.py` — RequestLogging + security headers
- `core/csrf.py` — Double-submit CSRF
- `core/rate_limit.py` — Sliding window rate limiting
- `core/https_redirect.py` — HTTPS redirect

---

## 3. Frontend — What Exists

| Component | Lines | Status | Reality |
|-----------|-------|--------|---------|
| 14 page routes | ~8,000+ | ✅ All real | auth, app, chat, memory, models, vault, search, settings, admin, agents, downloads, profile |
| 18 UI components | ~1,500+ | ✅ All real | Button, Card, Modal, CommandPalette, NeuralNetwork (560-line Canvas 2D), etc. |
| 11 API client modules | ~900 | ✅ All real | Every method maps to backend routes |
| Auth system | ~672 | ✅ Complete | Cookie-based, CSRF, auto-refresh, session cache |
| Vault module (file manager) | ~2,000+ | ✅ Complex | 6 custom hooks, multi-select, preview, lock screen |
| Models module | ~3,000+ | ✅ Feature-rich | 30+ API methods, catalog, download, recommendations |
| Agent module | ~1,000+ | ✅ Real SSE | Builder, runner, streaming |
| Design tokens | 70 | ✅ Real | "Warm Neural Dark" theme |
| Types | 800 | ✅ Comprehensive | 60+ interfaces mapping to backend |
| Tests | 10 files | ⚠️ Thin | 9 of 14 pages tested |

**Dual API client problem:** `cortexApi.ts` (536 lines, monolithic) exists alongside modular `src/shared/api/` (900 lines, clean). Both real. Legacy duplication.

---

## 4. CLI — What Exists

| Component | Lines | Status |
|-----------|-------|--------|
| Commander.js routing | 116 | ✅ Real — 15 commands wired |
| All 15 command implementations | 42 | 🔴 All stubs — "not yet implemented" |

**Zero CLI functionality.** The skeleton is designed but nothing works.

---

## 5. Rust Crates — What Exists

| Crate | Lines | Status |
|-------|-------|--------|
| cortex-code-intel | 51 | ⚠️ Minimal — only Python parsing via tree-sitter. JS/TS grammars in deps but not wired. |
| cortex-file-watcher | 32 | ⚠️ Minimal — standalone binary, no IPC, no CORTEX integration |

---

## 6. Database — What Exists

| Component | Count | Status |
|-----------|-------|--------|
| Active migrations | 6 (baseline + 5 chain) | ✅ Clean chain |
| Archived migrations | 26 | Historical record |
| Tables | 33 | All with FK constraints, soft deletes, timestamps |
| Schema debt | 4 duplicate columns in model_variants | Documented in c00000000005 |

---

## 7. Infrastructure — What Exists

| Component | Status | Notes |
|-----------|--------|-------|
| Docker Compose | ✅ | PG 16, Redis 7, Qdrant v1.18 — all localhost-only |
| Dockerfile | ✅ | Multi-stage build, non-root user, healthcheck |
| Makefile | ✅ | 30+ targets covering all workflows |
| Pre-commit hooks | ✅ | ruff, secrets, formatting |
| Custom hook system | ✅ | 11 hooks across 4 phases (pre-commit, push, merge, on-change) |
| start.sh | ✅ | 4-phase pipeline: PG → deps → migrations → frontend |
| CI (GitHub Actions) | ✅ | .github/workflows/ci.yml |

---

## 8. Documentation — What Exists

| File | Lines | Status |
|------|-------|--------|
| README.md | 177 | ✅ Concise, accurate |
| CLAUDE.md | 263 | ✅ Comprehensive AI agent guidance |
| AGENTS.md | 104 | ✅ Agent rules |
| DESIGN.md | 207 | ✅ Design system |
| docs/ARCHITECTURE.md | 261 | ✅ System architecture |
| docs/ROADMAP.md | 142 | ✅ 10-phase roadmap |
| docs/GOVERNANCE.md | 319 | ✅ Governance rules |
| docs/WORKFLOWS.md | 460 | ✅ 10 workflow definitions |
| docs/DEVELOPER_GUIDE.md | 504 | ✅ Agentic dev guide |
| docs/DATABASE.md | 87 | ✅ Schema reference |
| docs/SECURITY.md | 97 | ✅ Security patterns |
| docs/API.md | 174 | ✅ API reference |
| docs/decisions/001 | 91 | ✅ Only ADR |
| docs/agents/ | 3 files | ✅ Domain, issue-tracker, triage-labels |

---

## 9. Planning Documents — What Exists

| Document | Lines | Purpose |
|----------|-------|---------|
| Desktop-First Reorientation Design | 492 | Strategic design spec |
| Desktop-First Implementation Plan | 1,898 | 7-phase TDD plan |
| Reference Repo Master Plan | 836 | All findings from 10 repos |
| Odysseus Integration Plan | 784 | Odysseus deep audit |
| Strategic Command System Spec | 318 | 7 slash commands design |
| Strategic Command Implementation | 1,026 | 11-task TDD plan |
| Reference Repo Gap Analysis | 293 | 73 gaps |
| Reference Repo Recommendations | 968 | 72 recommendations |
| Reference Repo Phase Impact | 397 | 4 workstreams |
| Reference Repo Action Items | 295 | 15 implementation items |

---

## 10. Skills — What Exists

65 skills installed in `.agents/skills/`. No lock file. Mix of development, design, and utility skills.
