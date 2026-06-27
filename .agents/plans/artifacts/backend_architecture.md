# Backend Architecture — CORTEX

**Document:** Backend Software Architecture Design
**Authority:** Stage 5 — Repository & Architecture Restructure
**Date:** 2026-06-27

---

## Purpose

This document defines the backend architecture for Cortex. It specifies the layer structure, service boundaries, data ownership, event flow, and dependency direction. This is the definitive backend architecture that all future implementation follows.

---

## Layer Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      API LAYER                              │
│  Routers → Request Parsing → Auth → Response Formatting     │
│  Owner: INF (Infrastructure)                                │
│  Files: backend/app/api/v1/*.py                             │
├─────────────────────────────────────────────────────────────┤
│                    SERVICE LAYER                            │
│  Business logic, domain rules, orchestration                │
│  Owner: Domain-specific (M, A, C, E, L, I, D, U, X, P)    │
│  Files: backend/app/services/{domain}/*.py                  │
├─────────────────────────────────────────────────────────────┤
│                    AGENT LAYER                              │
│  Agent loop, tools, integrity, planning, reasoning          │
│  Owner: C (Cognition)                                       │
│  Files: backend/app/agents/*.py                             │
├─────────────────────────────────────────────────────────────┤
│                  INTELLIGENCE LAYER                         │
│  Embeddings, search, RAG, knowledge graph, memory           │
│  Owner: INF (Infrastructure)                                │
│  Files: backend/app/intelligence/*.py                       │
├─────────────────────────────────────────────────────────────┤
│                  INFRASTRUCTURE LAYER                       │
│  Database, Redis, middleware, daemon, auth, config           │
│  Owner: INF (Infrastructure)                                │
│  Files: backend/app/core/*.py, backend/app/daemon/*.py      │
└─────────────────────────────────────────────────────────────┘
```

### Dependency Rule

Dependencies flow strictly downward:
```
API → Service → Agent → Intelligence → Infrastructure
```

**Never:** A lower layer imports from a higher layer.
**Never:** Two layers at the same level import from each other (use events instead).

---

## Service Boundaries

Each domain has its own service directory with clear ownership:

### Memory Domain (M)

```
backend/app/services/memory/
├── episodic.py         # EpisodicMemoryService
│   ├── create_event(event_data) → EpisodicMemory
│   ├── get_event(event_id) → EpisodicMemory
│   ├── search_events(query, filters) → List[EpisodicMemory]
│   └── get_events_by_timeframe(start, end) → List[EpisodicMemory]
│
├── semantic.py         # SemanticMemoryService
│   ├── create_knowledge(knowledge_data) → SemanticMemory
│   ├── get_knowledge(knowledge_id) → SemanticMemory
│   ├── search_knowledge(query) → List[SemanticMemory]
│   └── update_knowledge(knowledge_id, updates) → SemanticMemory
│
├── working.py          # WorkingMemoryService
│   ├── set_context(key, value) → void
│   ├── get_context(key) → Any
│   ├── clear_context() → void
│   └── get_snapshot() → dict
│
├── graph.py            # MemoryGraphService
│   ├── add_node(node_data) → Node
│   ├── add_edge(edge_data) → Edge
│   ├── query_graph(query) → GraphResult
│   ├── get_neighbors(node_id) → List[Node]
│   └── traverse(start, depth) → Subgraph
│
├── search.py           # MemorySearchService
│   ├── search(query, options) → SearchResults
│   ├── semantic_search(query) → List[Result]
│   ├── graph_search(query) → List[Result]
│   └── hybrid_search(query) → List[Result]
│
├── consolidation.py    # ConsolidationService
│   ├── consolidate() → ConsolidationResult
│   ├── strengthen(memory_id) → void
│   ├── weaken(memory_id) → void
│   └── merge(memories) → Memory
│
└── forgetting.py       # ForgettingService
    ├── calculate_relevance(memory_id) → float
    ├── fade(memory_id, factor) → void
    └── forget(memory_id) → void
```

### Awareness Domain (A)

```
backend/app/services/awareness/
├── filesystem.py       # FilesystemAwarenessService
│   ├── index_directory(path) → IndexResult
│   ├── get_file_context(path) → FileContext
│   ├── watch_directory(path) → Stream[FileEvent]
│   └── get_organization_patterns() → Patterns
│
├── repository.py       # RepositoryAwarenessService
│   ├── analyze_repository(path) → RepositoryContext
│   ├── get_structure(path) → Structure
│   ├── get_history(path) → History
│   └── get_health(path) → HealthReport
│
├── project.py          # ProjectAwarenessService
│   ├── get_project_context(project_id) → ProjectContext
│   ├── track_progress(project_id) → Progress
│   └── identify_blockers(project_id) → List[Blocker]
│
├── workspace.py        # WorkspaceAwarenessService
│   ├── synthesize() → WorkspaceState
│   ├── get_active_context() → ActiveContext
│   └── get_focus_areas() → List[FocusArea]
│
└── system_health.py    # SystemHealthService
    ├── get_system_status() → SystemStatus
    ├── get_resource_usage() → ResourceUsage
    ├── get_errors() → List[Error]
    └── predict_issues() → List[PredictedIssue]
```

### Intelligence Layer

```
backend/app/intelligence/
├── embeddings.py       # EmbeddingService
│   ├── generate(text) → Vector
│   ├── batch_generate(texts) → List[Vector]
│   └── get_model_info() → ModelInfo
│
├── search.py           # SearchService
│   ├── vector_search(query, options) → List[SearchResult]
│   ├── fulltext_search(query, options) → List[SearchResult]
│   ├── graph_search(query, options) → List[SearchResult]
│   └── hybrid_search(query, options) → List[SearchResult]
│
├── rag.py              # RAGService
│   ├── retrieve(query, options) → List[Document]
│   ├── generate(query, context) → Response
│   └── hybrid_retrieve(query) → List[Document]
│
└── knowledge_graph.py  # KnowledgeGraphService
    ├── add_entity(entity) → Entity
    ├── add_relationship(relationship) → Relationship
    ├── query(query) → GraphResult
    └── get_subgraph(entity_id, depth) → Subgraph
```

### Agent Layer

```
backend/app/agents/
├── loop.py             # AgentLoop
│   ├── run(task) → AsyncGenerator[AgentEvent]
│   ├── step(context) → StepResult
│   └── should_continue(context) → bool
│
├── tools/              # Tool Registry
│   ├── registry.py     # ToolRegistry
│   │   ├── register(tool) → void
│   │   ├── get(name) → Tool
│   │   ├── list() → List[Tool]
│   │   └── execute(name, params) → ToolResult
│   ├── filesystem.py   # FileTool
│   ├── search.py       # SearchTool
│   ├── memory.py       # MemoryTool
│   ├── knowledge.py    # KnowledgeTool
│   └── code.py         # CodeTool
│
└── integrity/          # Integrity System
    ├── architecture.py # Architecture compliance
    ├── code_quality.py # Code quality
    └── ...
```

---

## Data Ownership

Each domain owns its database tables:

| Domain | Tables | Access Pattern |
|--------|--------|----------------|
| Memory | episodic_memories, semantic_memories, working_memories, memory_nodes, memory_edges | Read-heavy, write on events |
| Awareness | file_indexes, repository_indexes, project_contexts | Write-heavy, read on query |
| Cognition | agent_runs, tool_calls, plans, task_decompositions | Write on execution, read for history |
| Execution | tasks, task_runs, execution_history, workflows | Write on execution, read for status |
| Learning | preferences, workflow_patterns, feedback_logs | Write on learning, read for personalization |
| Interaction | conversations, messages, notifications | Write on interaction, read for display |
| Developer | repositories, code_indexes, reviews, documentation | Write on indexing, read for intelligence |
| Utility | calendar_events, emails, tasks, notes, documents | Write on management, read for context |
| Integration | tool_connections, service_configs, sync_states | Write on connection, read for status |
| Privacy | consents, audit_logs, vault_entries | Write on action, read for audit |

---

## Event Flow

```
User Action → API → Service → Publishes Event → Event Bus
                                                      ↓
                                            Other Services Subscribe
                                                      ↓
                                            Update Their State
                                                      ↓
                                            (Optional) Background Task
```

### Event Types

| Event | Publisher | Subscribers |
|-------|-----------|-------------|
| `memory.created` | Memory Service | Awareness, Learning |
| `memory.updated` | Memory Service | Search, Learning |
| `memory.consolidated` | Consolidation Service | Learning, Interaction |
| `awareness.file_changed` | Filesystem Awareness | Memory, Developer |
| `awareness.repo_updated` | Repository Awareness | Developer, Memory |
| `agent.run.started` | Agent Service | Interaction |
| `agent.run.completed` | Agent Service | Memory, Learning |
| `agent.tool.called` | Tool Registry | Memory, Execution |
| `task.scheduled` | Task Service | Execution |
| `task.completed` | Task Service | Memory, Learning |
| `notification.created` | Notification Service | Interaction |
| `user.action` | API | Learning |

---

## Background Workers

| Worker | Purpose | Frequency |
|--------|---------|-----------|
| Memory Consolidation | Reviews and strengthens memories | Hourly |
| Forgetting | Fades less-relevant memories | Daily |
| Awareness Update | Updates filesystem/repo awareness | On file change |
| Learning Pipeline | Processes feedback and patterns | On interaction |
| Knowledge Evolution | Updates knowledge graph | Daily |
| Health Monitor | Checks system health | Every 5 minutes |
| Task Scheduler | Runs scheduled tasks | Every minute |

---

## Dependency Injection

Services are injected via FastAPI's dependency injection:

```python
# backend/app/api/v1/memory.py
from fastapi import APIRouter, Depends
from backend.app.services.memory.search import MemorySearchService
from backend.app.core.dependencies import get_memory_search_service

router = APIRouter()

@router.post("/memory/search")
async def search_memory(
    query: str,
    service: MemorySearchService = Depends(get_memory_search_service),
):
    return service.search(query)
```

Global singletons (via `core/dependencies.py`):
- `llm_manager` — LLM provider management
- `redis_cache` — Redis connection
- `download_manager` — Model downloads

---

## API Versioning

All endpoints are versioned: `/v1/...`

When breaking changes are needed:
1. Create `/v2/` endpoints
2. Maintain `/v1/` for backward compatibility
3. Deprecate `/v1/` with clear timeline
4. Remove `/v1/` after migration period

---

## Storage Strategy

| Data | Storage | Rationale |
|------|---------|-----------|
| Structured data | PostgreSQL 16 | ACID, relations, JSONB |
| Embeddings | Qdrant (embedded) | Vector search, performance |
| Cache | Redis 7 | Speed, TTL, pub/sub |
| Files | Local filesystem | Local-first, no cloud dependency |
| Vault | Fernet-encrypted files | Security, local-first |
| Sessions | PostgreSQL | Persistence, ACID |
| Audit logs | PostgreSQL | Queryability, retention |

---

## Repository Backend Structure

The repository is organized around **domains**, not technologies. Each of Cortex's 10 capability domains has a clear home in both backend and frontend. A contributor should understand the project by browsing folders.

### Top-Level Repository Structure

```
cortex/
├── backend/                    # Python FastAPI application
│   ├── app/                    # Application code
│   │   ├── core/               # Infrastructure: config, DB, Redis, middleware
│   │   ├── daemon/             # Daemon lifecycle, PID, health, shutdown
│   │   ├── auth/               # JWT, CSRF, session management
│   │   ├── models/             # SQLAlchemy models
│   │   ├── schemas/            # Pydantic schemas
│   │   ├── api/                # API routers
│   │   │   └── v1/             # Versioned API endpoints
│   │   ├── services/           # Business logic services
│   │   ├── agents/             # Agent system: loop, tools, integrity
│   │   ├── tasks/              # Background tasks
│   │   ├── intelligence/       # Embeddings, search, RAG
│   │   └── db/                 # Database utilities
│   ├── migrations/             # Alembic migrations
│   └── tests/                  # Backend tests
├── frontend/                   # Next.js 15 application
├── crates/                     # Rust code intelligence
├── cli/                        # Python CLI tool
├── cortex/                     # Cortex runtime core
├── docs/                       # Documentation
├── tests/                      # Integration and E2E tests
├── scripts/                    # Build, deploy, and utility scripts
├── .agents/                    # Planning and governance
├── .claude/                    # Claude Code integration
├── .github/                    # GitHub Actions, templates
├── Makefile                    # Build commands
├── docker-compose.yml          # Development services
├── pyproject.toml              # Python project config
├── start.sh                    # Self-contained launcher
├── DESIGN.md                   # Design system reference
├── CLAUDE.md                   # Execution contract
├── AGENTS.md                   # Agent behavior rules
└── README.md                   # Project overview
```

**Current state:** 20 top-level directories, 114K+ lines of code
**Target state:** Same top-level, reorganized internals for domain clarity

### Backend File Organization

```
backend/app/
├── core/                       # Infrastructure (Layer 5)
│   ├── config.py               # Application configuration
│   ├── database.py             # SQLAlchemy setup, session factory
│   ├── redis.py                # Redis connection and caching
│   ├── security.py             # Password hashing, token generation
│   ├── middleware.py            # CORS, rate limiting, GZip, CSRF
│   └── events.py               # Event bus (internal pub/sub)
│
├── daemon/                     # Daemon lifecycle (Layer 5)
│   ├── entrypoint.py           # cortexd entry
│   ├── lifecycle.py            # Startup, shutdown, sleep/wake
│   ├── pid.py                  # PID management
│   └── health.py               # Health checks (3-level)
│
├── auth/                       # Authentication (Layer 5)
│   ├── routes.py               # Auth endpoints
│   ├── jwt.py                  # JWT creation and verification
│   ├── csrf.py                 # CSRF double-submit
│   └── sessions.py             # Session management
│
├── models/                     # Data models (Layer 4)
│   ├── user.py                 # User model
│   ├── memory.py               # Memory models (episodic, semantic, working)
│   ├── conversation.py         # Conversation models
│   ├── knowledge.py            # Knowledge graph models
│   ├── document.py             # Document and indexing models
│   ├── repository.py           # Repository models
│   ├── agent.py                # Agent run and tool call models
│   ├── task.py                 # Background task models
│   ├── notification.py         # Notification models
│   └── settings.py             # User settings models
│
├── schemas/                    # API schemas (Layer 4)
│   ├── user.py                 # User request/response schemas
│   ├── memory.py               # Memory schemas
│   ├── conversation.py         # Conversation schemas
│   ├── knowledge.py            # Knowledge graph schemas
│   ├── agent.py                # Agent schemas
│   ├── task.py                 # Task schemas
│   └── common.py               # Shared schemas (pagination, errors)
│
├── api/                        # API layer (Layer 1)
│   └── v1/                     # Versioned endpoints
│       ├── auth.py             # /auth/* endpoints
│       ├── users.py            # /users/* endpoints
│       ├── memory.py           # /memory/* endpoints
│       ├── conversations.py    # /conversations/* endpoints
│       ├── knowledge.py        # /knowledge/* endpoints
│       ├── documents.py        # /documents/* endpoints
│       ├── repositories.py     # /repositories/* endpoints
│       ├── models.py           # /models/* endpoints
│       ├── search.py           # /search/* endpoints
│       ├── agents.py           # /agents/* endpoints
│       ├── tasks.py            # /tasks/* endpoints
│       ├── notifications.py    # /notifications/* endpoints
│       ├── settings.py         # /settings/* endpoints
│       ├── vault.py            # /vault/* endpoints
│       ├── health.py           # /health/* endpoints
│       ├── github.py           # /github/* endpoints
│       ├── downloads.py        # /downloads/* endpoints
│       └── system.py           # /system/* endpoints
│
├── services/                   # Business logic (Layer 3)
│   ├── memory/                 # Memory domain services
│   │   ├── episodic.py         # Episodic memory
│   │   ├── semantic.py         # Semantic memory
│   │   ├── working.py          # Working memory
│   │   ├── graph.py            # Memory graph
│   │   ├── search.py           # Memory search
│   │   ├── consolidation.py    # Memory consolidation
│   │   └── forgetting.py       # Forgetting/fading
│   ├── awareness/              # Awareness domain services
│   │   ├── filesystem.py       # Filesystem awareness
│   │   ├── repository.py       # Repository awareness
│   │   ├── project.py          # Project awareness
│   │   ├── workspace.py        # Workspace awareness
│   │   └── system_health.py    # System health awareness
│   ├── intelligence/           # Intelligence domain services
│   │   ├── embeddings.py       # ONNX/Ollama embeddings
│   │   ├── search.py           # Hybrid search (vector + fulltext + graph)
│   │   ├── rag.py              # RAG pipeline
│   │   └── knowledge_graph.py  # Knowledge graph operations
│   ├── agent/                  # Agent domain services
│   │   ├── loop.py             # Agent loop (single async generator)
│   │   ├── tools.py            # Tool registry and execution
│   │   ├── run_manager.py      # Run tracking
│   │   └── stall_detection.py  # Stall detection
│   ├── llm/                    # LLM services
│   │   ├── manager.py          # LLM manager (singleton)
│   │   ├── providers/          # Provider implementations
│   │   └── parsers/            # Response parsers
│   ├── sync/                   # Sync services
│   │   ├── manager.py          # Sync manager
│   │   └── conflict.py         # Conflict resolution
│   └── download/               # Download services
│       └── manager.py          # Download manager
│
├── agents/                     # Agent system (Layer 2)
│   ├── loop.py                 # Core agent loop
│   ├── tools/                  # Agent tools
│   │   ├── filesystem.py       # File operations
│   │   ├── search.py           # Search tools
│   │   ├── memory.py           # Memory tools
│   │   ├── knowledge.py        # Knowledge graph tools
│   │   ├── code.py             # Code intelligence tools
│   │   └── ...
│   └── integrity/              # Integrity system (10 engines)
│       ├── architecture.py     # Architecture compliance
│       ├── code_quality.py     # Code quality checks
│       └── ...
│
├── tasks/                      # Background tasks (Layer 2)
│   ├── background.py           # Task queue
│   ├── scheduler.py            # Scheduled tasks
│   └── workers.py              # Task workers
│
├── intelligence/               # Intelligence infrastructure (Layer 4)
│   ├── embeddings.py           # Embedding generation
│   ├── search.py               # Search engine
│   ├── rag.py                  # RAG pipeline
│   └── knowledge_graph.py      # Graph operations
│
└── db/                         # Database utilities (Layer 5)
    ├── session.py              # Session factory
    ├── migrations.py           # Migration runner
    └── seed.py                 # Database seeding
```

### API Organization

All endpoints follow this pattern:
```
/v1/{domain}/{resource}
```

Examples:
```
GET    /v1/memory/episodic           # List episodic memories
POST   /v1/memory/episodic           # Create episodic memory
GET    /v1/memory/episodic/{id}      # Get episodic memory
PUT    /v1/memory/episodic/{id}      # Update episodic memory
DELETE /v1/memory/episodic/{id}      # Delete episodic memory
POST   /v1/memory/search             # Search memories
POST   /v1/memory/consolidate        # Trigger consolidation
GET    /v1/knowledge/graph           # Get knowledge graph
POST   /v1/knowledge/graph/query     # Query knowledge graph
GET    /v1/awareness/filesystem      # Get filesystem awareness
POST   /v1/agents/run                # Start agent run
GET    /v1/agents/run/{id}           # Get agent run status
POST   /v1/tasks/schedule            # Schedule background task
```

### Migration Path

This architecture is designed to evolve from the current repository with minimal disruption:

#### Phase 1: Reorganize Backend
1. Move `backend/app/services/` → organize into domain subdirectories
2. Move `backend/app/models/` → split into domain-specific model files
3. Move `backend/app/api/v1/` → reorganize by domain
4. Add `backend/app/core/events.py` for event bus

#### Phase 2: Reorganize Frontend
1. Move `frontend/src/shared/components/` → organize into feature directories
2. Add `frontend/src/features/` for domain-specific components
3. Add `frontend/src/design/` for design system

#### Phase 3: Add Domain Modules
1. Create service stubs for each domain
2. Create model stubs for each domain
3. Create API endpoint stubs for each domain

**Migration complexity:** Medium. Most changes are file moves, not rewrites.
