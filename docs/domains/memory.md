Last updated: 2026-06-30

# Memory Domain — CORTEX

**Domain:** Memory
**Status:** Implemented (v1.03 Memory Foundation)
**Version:** v1.03 (Foundation), v1.07 (Evolution — future)

---

## Overview

The Memory domain provides CORTEX with persistent, multi-modal memory: episodic experiences, semantic knowledge, session-scoped working memory, a polymorphic knowledge graph, multi-signal search, and Ebbinghaus-style forgetting. All services are synchronous (sync SQLAlchemy 2.0) and constructor-injected with a `Session`.

## Architecture

Memory sits in `backend/app/services/memory/` as domain services, exposed via REST endpoints in `backend/app/api/v1/memory/cortex_*.py`. The `MemoryServiceFactory` provides lazy-initialized access to all services from a single DB session.

Legacy memory systems (`knowledge.py`, `long_term_memory.py`) coexist under the same router. New Cortex endpoints are prefixed `cortex_` in filenames to avoid collisions with code-intelligence modules (`graph.py`, `search.py`).

```
backend/app/api/v1/memory/
├── cortex_episodic.py    # CRUD + search
├── cortex_semantic.py    # CRUD + dedup + categories
├── cortex_working.py     # Session-scoped slots + TTL
├── cortex_graph.py       # Nodes, edges, BFS traversal
├── cortex_search.py      # Cross-type search + forgetting
├── cortex_router.py      # Aggregates all cortex routers
└── router.py             # Aggregates legacy + cortex
```

## Services

| Service | File | Purpose |
|---------|------|---------|
| `EpisodicMemoryService` | `episodic.py` | Experience/event storage with importance, emotion, recency |
| `SemanticMemoryService` | `semantic.py` | Facts/knowledge with category, confidence, deduplication |
| `WorkingMemoryService` | `working.py` | Session-scoped context buffer (active/buffer/archive slots, TTL) |
| `MemoryGraphService` | `memory_graph_service.py` | Polymorphic graph: nodes linked to any memory type, edges with weights, BFS path-finding |
| `AutoConnectionService` | `auto_connect.py` | Keyword-based automatic edge creation between related memories |
| `MemorySearchService` | `memory_search.py` | Cross-type search with multi-signal scoring (text, recency, importance, access, graph centrality) |
| `ForgettingService` | `decay.py` | Ebbinghaus-style decay with importance damping and garbage collection |
| `TemporalScoring` | `temporal.py` | Exponential decay, access frequency weighting, time-of-day similarity |

**Search scoring formula:** `0.30 * text_relevance + 0.25 * recency + 0.20 * importance + 0.15 * access_frequency + 0.10 * graph_centrality`

**Forgetting formula:** `effective_rate = base_rate / max(1.0, access_count * 0.1)`, damped by `0.5 + importance * 0.5`

## Models

| Model | Table | Purpose |
|-------|-------|---------|
| `EpisodicMemory` | `episodic_memories` | Experiences, events, conversations |
| `SemanticMemory` | `semantic_memories` | Facts, knowledge, rules |
| `WorkingMemory` | `working_memories` | Session-scoped volatile context |
| `MemoryNode` | `memory_nodes` | Graph nodes (polymorphic: links to any memory type) |
| `MemoryEdge` | `memory_edges` | Graph edges with weight and type |

## API Endpoints

All endpoints require JWT auth (`Bearer` token). CSRF bypass for Bearer-authenticated requests.

| Route | Method | Purpose |
|-------|--------|---------|
| `/api/v1/episodic` | POST | Create episodic memory |
| `/api/v1/episodic` | GET | List recent (paginated) |
| `/api/v1/episodic/search` | GET | Search by content |
| `/api/v1/episodic/{id}` | GET/PATCH/DELETE | Retrieve/update/delete |
| `/api/v1/semantic` | POST | Create (dedup on exact content) |
| `/api/v1/semantic` | GET | List (filter by category) |
| `/api/v1/semantic/categories` | GET | Get all categories with counts |
| `/api/v1/semantic/search` | GET | Search by content |
| `/api/v1/semantic/{id}` | GET/PATCH/DELETE | Retrieve/update/delete |
| `/api/v1/working` | POST | Add to working memory |
| `/api/v1/working` | GET | Get active items (by session) |
| `/api/v1/working/{id}/promote` | POST | Promote to active slot |
| `/api/v1/working/{id}/archive` | POST | Archive item |
| `/api/v1/working/{id}/demote` | POST | Demote to buffer |
| `/api/v1/working/{id}` | DELETE | Remove item |
| `/api/v1/working/session/{id}` | DELETE | Clear entire session |
| `/api/v1/working/session/{id}/summary` | GET | Session stats |
| `/api/v1/graph/node` | POST | Create graph node |
| `/api/v1/graph/edge` | POST | Create graph edge |
| `/api/v1/graph/stats` | GET | Graph statistics |
| `/api/v1/graph/strongest` | GET | Strongest edges |
| `/api/v1/graph/node/{id}/connections` | GET | BFS neighbors |
| `/api/v1/graph/path/{src}/{dst}` | GET | Shortest path |
| `/api/v1/graph/edge/{id}/strengthen` | POST | Strengthen edge weight |
| `/api/v1/graph/edge/{id}` | DELETE | Delete edge |
| `/api/v1/cortex-search` | GET | Cross-type search |
| `/api/v1/cortex-search/related` | GET | Graph-related memories |
| `/api/v1/cortex-search/importance` | GET | Search by importance |
| `/api/v1/cortex-search/recency` | GET | Search by recency |
| `/api/v1/forget` | POST | Apply forgetting decay |
| `/api/v1/forget/stats` | GET | Forgetting statistics |

## Dependencies

- `backend.app.core.db`: `get_current_user`, `get_db`
- `backend.app.models.memory.*`: ORM models
- `backend.app.schemas.memory.*`: Pydantic v2 schemas with `from_attributes`

## Testing

- Unit tests: `tests/services/test_memory_services.py` (74 tests across 10 classes)
- API integration tests: `tests/test_cortex_memory_api.py` (33 tests)
- All use SQLite in-memory with `conftest.py` JSONB→JSON compilation
- 1,589 total tests passing
