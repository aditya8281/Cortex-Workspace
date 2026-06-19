# Cortex Master Plan Index

> **For agentic workers:** This is the master index. Read prerequisite.md first, then follow the execution order below.

**Goal:** Build Cortex — a local-first, autonomous AI workspace with reasoning, planning, and multi-agent intelligence — from architecture alignment to Desktop V1.

**Architecture:** FastAPI + PostgreSQL backend, Next.js 15 + React 19 frontend, Qdrant for vectors, Tauri v2 for desktop. All data local, zero telemetry. Rust for code intelligence and file watching.

**Status:** Phase 0-A (Prerequisites) complete. Phase 0-B (Architecture Alignment) complete. Phase 1 (Memory) complete. Phase 2 (Indexing & Knowledge Graph) complete. Phase 3 (Unified Search & Agents) ready to start.

---

## Prerequisites — COMPLETE

All items in `prerequisite.md` have been completed. See [prerequisite.md](../prerequisite.md).

---

## Plan Files

| Phase | File | Focus | Status |
|-------|------|-------|--------|
| 0-A | `prerequisite.md` | Repository alignment | COMPLETE |
| 0-B | [01-PHASE-0B-ARCHITECTURE.md](./01-PHASE-0B-ARCHITECTURE.md) | Bug fixes, architecture, Rust setup | COMPLETE |
| 1 | [02-PHASE-1-MEMORY.md](./02-PHASE-1-MEMORY.md) | Memory system, embeddings, repo scanner | COMPLETE |
| 2 | [03-PHASE-2-INDEXING.md](./03-PHASE-2-INDEXING.md) | Indexing, knowledge graph, graph search | COMPLETE |
| 3 | [04-PHASE-3-AGENTS.md](./04-PHASE-3-AGENTS.md) | Unified search, agent runtime | NOT STARTED |
| 4 | [05-PHASE-4-INTELLIGENCE.md](./05-PHASE-4-INTELLIGENCE.md) | Context, learning, workspace understanding | NOT STARTED |
| 5 | [06-PHASE-5-DESKTOP.md](./06-PHASE-5-DESKTOP.md) | Tauri v2, sidecar, offline, file system | NOT STARTED |
| 6 | [07-PHASE-6-LEARNING.md](./07-PHASE-6-LEARNING.md) | Long-term memory, patterns, proactive assist | NOT STARTED |

---

## Execution Order

```
Phase 0-A: Prerequisites
    ├── All items in prerequisite.md
    └── Status: COMPLETE ✓

Phase 0-B: Architecture Alignment
    ├── Depends on: Phase 0-A
    ├── Bug fixes (memory search, profile photo, FK constraints)
    ├── Architecture standardization (API versioning, service abstraction)
    ├── Code quality (VECTOR_SIZE, test consolidation)
    ├── Rust infrastructure setup
    └── Status: COMPLETE ✓

Phase 1: Memory System
    ├── Depends on: Phase 0-A
    ├── Status: COMPLETE ✓
    └── (Note: Phase 0-B fixes bugs found in this phase)

Phase 2: Indexing & Knowledge Graph
    ├── Depends on: Phase 0-B, Phase 1
    ├── Database schema (graph nodes, edges, file tracking)
    ├── Incremental indexer (hash-based change detection)
    ├── Graph builder (nodes + edges from code analysis)
    ├── Cross-file search (vector + graph enrichment)
    ├── Unified search API
    ├── Repository management API
    ├── Frontend (SearchFilters, SearchResults, GraphView)
    └── Status: COMPLETE ✓

Phase 3: Unified Search & Agents
    ├── Depends on: Phase 2, Phase 0-B
    ├── Agent database schema
    ├── Planner agent (task decomposition)
    ├── Executor agent (tool-use loop)
    ├── Agent run manager
    ├── Agent API
    └── Frontend (AgentChat, SearchResults enhancements)

Phase 4: Intelligence
    ├── Depends on: Phase 3, Phase 2
    ├── Context builder (workspace state + past conversations)
    ├── Conversation memory (semantic search over history)
    ├── Learning loop (feedback processing)
    ├── Workspace understanding (call graphs, summaries)
    ├── Enhanced executor with context
    ├── Conversation history API
    └── Frontend (ContextPanel, MemoryTimeline)

Phase 5: Desktop V1 (Tauri v2)
    ├── Depends on: Phase 0-B, Phase 4, Phase 3
    ├── Tauri v2 project setup
    ├── Backend sidecar
    ├── Tauri Rust plugins (tray, window, fs, dialog, updater)
    ├── Frontend Tauri adapter
    ├── Offline capabilities (IndexedDB, service worker)
    ├── File system integration
    └── Auto-updates

Phase 6: System Understanding & Learning
    ├── Depends on: Phase 4, Phase 5, Phase 2
    ├── Long-term memory (semantic + decay)
    ├── Pattern recognition (coding style, workflow)
    ├── Correction tracker
    ├── Proactive assistant (suggestions)
    ├── Learning API
    └── Frontend (LearningDashboard, ProactiveSuggestions)
```

---

## Dependency Graph

```
Phase 0-A (Prerequisites) ──┐
                             ├──► Phase 0-B ──┐
Phase 1 (Memory) ────────────┘                │
                                               ├──► Phase 2 ──┐
                                               │              │
                                               │              ├──► Phase 3 ──┐
                                               │              │              │
                                               │              │              ├──► Phase 4 ──┐
                                               │              │              │              │
                                               │              │              │              ├──► Phase 5
                                               │              │              │              │
                                               │              │              │              └──► Phase 6
                                               │              │              │
                                               └──────────────┴──────────────┘
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

---

*Last updated: 2026-06-20*
