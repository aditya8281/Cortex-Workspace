# Cortex Master Plan Index

> **For agentic workers:** This is the master index. Read prerequisite.md first, then follow the execution order below.

**Goal:** Build Cortex — a local-first, autonomous AI operating system with reasoning, planning, and multi-agent intelligence — from architecture alignment to production-ready desktop app.

**Architecture:** FastAPI + PostgreSQL backend, Next.js 15 + React 19 frontend, Qdrant for vectors, Tauri v2 for desktop. All data local, zero telemetry. Rust for code intelligence and file watching. llama.cpp/Ollama for local LLM inference.

**Status:** Phases 0-A through 3 + UI Refactor complete. Phase 4A (LLM Integration) is next.

---

## Completed Phases

| Phase | File | Focus | Status |
|-------|------|-------|--------|
| 0-A | `prerequisite.md` | Repository alignment | ✅ COMPLETE |
| 0-B | `01-PHASE-0B-ARCHITECTURE.md` | Bug fixes, architecture, Rust setup | ✅ COMPLETE |
| 1 | `02-PHASE-1-MEMORY.md` | Memory system, embeddings, repo scanner | ✅ COMPLETE |
| 2 | `03-PHASE-2-INDEXING.md` | Indexing, knowledge graph, graph search | ✅ COMPLETE |
| 3 | `04-PHASE-3-AGENTS.md` | Unified search, agent runtime | ✅ COMPLETE |
| UI | `docs/superpowers/plans/2026-06-20-ui-refactor.md` | UI redesign, DashboardShell, warm dark theme | ✅ COMPLETE |

---

## Active Phases

| Phase | File | Focus | Status |
|-------|------|-------|--------|
| 4A | `08-PHASE-4A-LLM-INTEGRATION.md` | LLM providers, local models, model management | ⬜ NOT STARTED |
| 4B | `09-PHASE-4B-SMART-INDEXING.md` | Intelligent indexing, sync, retrieval quality | ⬜ NOT STARTED |

---

## Future Phases

| Phase | File | Focus | Status |
|-------|------|-------|--------|
| 5 | `10-PHASE-5-CONVERSATION.md` | Conversation memory, SSE streaming, chat experience | ⬜ NOT STARTED |
| 6 | `11-PHASE-6-AGENT-INTELLIGENCE.md` | Tool registry, SSE streaming, agent metrics, dashboard | ⬜ NOT STARTED |
| 7 | `12-PHASE-7-DESKTOP-PREPARATION.md` | StorageResolver fix, service abstraction, native hooks | ⬜ NOT STARTED |
| 8 | `13-PHASE-8-LEARNING-LOOP.md` | Long-term memory, patterns, corrections, proactive assist | ⬜ NOT STARTED |
| 9 | `14-PHASE-9-OBSERVABILITY.md` | Metrics collector, health API, health dashboard | ⬜ NOT STARTED |
| 10 | `15-PHASE-10-PRODUCTION.md` | Tests, security, performance, Docker, CI/CD | ⬜ NOT STARTED |

---

## Execution Order

```
Phase 0-A: Prerequisites ──────────────────── ✅ COMPLETE
    │
Phase 0-B: Architecture Alignment ─────────── ✅ COMPLETE
    │
Phase 1: Memory System ────────────────────── ✅ COMPLETE
    │
Phase 2: Indexing & Knowledge Graph ───────── ✅ COMPLETE
    │
Phase 3: Unified Search & Agents ──────────── ✅ COMPLETE
    │
    ├──► Phase 4A: LLM Integration & Local Models + Basic Metrics
    │        │
    │        ├──► Phase 4B: Smart Indexing & Retrieval
    │        │        │                     │
    │        │        │                     ├──► Phase 5: Conversation (parallel with 4B)
    │        │        │                     │
    │        │        ├──► Phase 6: Agent Intelligence
    │        │        │        │
    │        │        │        ├──► Phase 8: Learning Loop
    │        │        │        │        │
    │        │        │        │        ├──► Phase 7: Desktop Preparation
    │        │        │        │        │        │
    │        │        │        │        │        ├──► Phase 9: Observability Dashboards
    │        │        │        │        │        │        │
    │        │        │        │        │        │        ├──► Phase 10: Production
    │        │        │        │        │        │
    │        │        │        │        │        └──► (can run parallel)
    │        │        │        │        └──►
    │        │        │        └──►
    │        │        └──►
    │        └──►
    └──► (Phase 4A begins immediately after Phase 3)
```

**Sequencing rationale:**
- Phase 4A includes basic metrics (token tracking, latency) — observability from day one
- Phase 5 (Conversation) is independent of 4B — can run in parallel
- Phase 7 (Desktop Prep) moved later — premature abstractions get rewritten anyway
- Phase 9 is dashboards only — data collection happens in earlier phases
- Each phase includes: code → compile check → integration test → git commit

---

## Dependency Graph

```
Phase 0-A ─┐
            ├──► Phase 0-B ──┐
Phase 1 ────┘                │
                             ├──► Phase 2 ──┐
                             │              │
                             │              ├──► Phase 3 ──┐
                             │              │              │
                             │              │              ├──► Phase 4A ──┐
                             │              │              │               │
                             │              │              │               ├──► Phase 4B ──┐
                             │              │              │               │               │
                             │              │              │               │               ├──► Phase 5 (parallel with 4B)
                             │              │              │               │               │
                             │              │              │               │               ├──► Phase 6 ──┐
                             │              │              │               │               │              │
                             │              │              │               │               │              ├──► Phase 8 ──┐
                             │              │              │               │               │              │              │
                             │              │              │               │               │              │              ├──► Phase 7 ──┐
                             │              │              │               │               │              │              │              │
                             │              │              │               │               │              │              │              ├──► Phase 9 ──┐
                             │              │              │               │               │              │              │              │              │
                             │              │              │               │               │              │              │              │              ├──► Phase 10
                             └──────────────┴──────────────┴───────────────┴───────────────┴──────────────┴──────────────┴──────────────┘
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
| **LLM** | llama.cpp / Ollama | latest |
| **Task Queue** | arq | Redis-based |
| **Code Intel** | Rust | tree-sitter |
| **File Watcher** | Rust | notify crate |

---

## Global Constraints

- Python 3.12+, Node.js 20+, Rust 2024 edition
- TypeScript strict mode, ESLint zero warnings
- Python: ruff line-length 120, mypy strict
- All async handlers, no blocking in event loop
- No external API calls for embeddings/inference (100% local)
- Zero telemetry, no cloud sync
- Desktop: Windows 10+, macOS 12+, Ubuntu 20.04+
- Every phase includes frontend + backend + integration + validation

---

## Key Design Decisions

1. **Qdrant over pgvector**: Supports tens of millions vectors, hybrid search, distributed scaling
2. **Tauri v2 over Electron**: Smaller binary (~10MB vs ~150MB), Rust native, system tray
3. **PostgreSQL adjacency lists over Apache AGE**: Simpler deployment, sufficient for knowledge graph
4. **tree-sitter for code intelligence**: Multi-language AST parsing, incremental, WASM-compatible
5. **Embedded sidecar pattern**: postgres, qdrant, llama.cpp run as Tauri sidecars
6. **Mock embeddings fallback**: ONNX model download on first run, deterministic hash-based mock for testing
7. **Service abstraction layer**: All services implement protocol for HTTP/Tauri dual consumption
8. **Single storage resolver**: Replaces hardcoded paths for Tauri portability
9. **llama.cpp as primary LLM backend**: Local CPU/GPU inference, no external API dependency
10. **Ollama as optional frontend**: Model management UI, pull/run/stop, hardware detection
11. **Intelligent indexing with exclusion rules**: Skip node_modules, .git, build artifacts, caches
12. **Hybrid retrieval**: Vector + keyword + graph combined, with reranking

---

## Success Metrics

| Metric | Target |
|--------|--------|
| Cold start | < 2s |
| Binary size | < 50MB (web app), < 200MB (desktop with bundled models) |
| Test coverage | > 80% |
| Vector search latency | < 100ms |
| Agent execution | < 30s per task |
| Memory usage | < 500MB idle |
| LLM inference (local) | < 2s first token, > 30 tokens/s |
| Indexing speed | > 1000 files/second |
| File sync latency | < 500ms |

---

*Last updated: 2026-06-20*
