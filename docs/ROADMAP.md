# CORTEX Roadmap

## Current Status

| Area | State |
|------|-------|
| Tests | 486+ passing (backend pytest + frontend vitest) |
| Frontend build | Passes |
| Linting | ruff + ESLint + mypy — all clean |
| Auth + vault backend | Production-quality foundation |
| Vault UI | Full file browser with table/list/grid views |
| Neural Dark redesign | Complete (warm dark, Neural Network background) |
| CLI | Scaffolded (command stubs) |
| LLM Integration | llama.cpp + Ollama with provider abstraction |
| Model Catalog | Full catalogue with providers, variants, benchmarks |

---

## Phase History

### Phase 1: Identity + Secure Storage ✅ Complete

- Multi-user authentication with JWT and refresh tokens
- Encrypted private vault per user (separate password)
- Profile management and GitHub account linking
- Admin user management
- Cookie-based authentication with automatic refresh
- Spring-physics animations, command palette, glass morphism UI

### Phase 2: Indexing & Knowledge Graph ✅ Complete

- Incremental indexer (hash-based change detection)
- Knowledge graph (graph_nodes, graph_edges)
- Cross-file search (vector + graph enrichment)
- Unified search API
- Repository management API (CRUD + indexing triggers)
- Background tasks: index_repo, build_graph

### Phase 3: Unified Search & Agents ✅ Complete

- Agent system (base agent, planner, executor)
- Agent run manager with step tracking
- Agent CRUD API + run/step/feedback API
- Frontend: Agent chat interface, Agents management page

### Phase 4A: LLM Integration & Local Models 🟡 Partial

- LLM manager with provider abstraction (llama.cpp, Ollama) ✅
- Model catalog with providers, variants, capabilities, benchmarks ✅
- Hardware detection and quantization recommendations ✅
- Model download manager with progress tracking ✅
- User model settings (persisted per-user) ✅
- Frontend: Models page with catalogue, installed models, download queue ✅
- Conversation-to-memory pipeline ✅
- Long-term memory with decay ✅

### Phase 4B: Smart Indexing & Retrieval 🟡 Partial

- Semantic chunker with language-aware splitting ✅
- Indexing configuration (include/exclude paths, file types) ✅
- Full-text search (PostgreSQL ts_vector) ✅
- Hybrid retrieval (vector + keyword + graph) ✅
- Document indexer for non-code files ✅
- Retrieval quality metrics ✅
- File watcher v2 with sync state persistence ✅
- Batch indexer for bulk operations ✅

### Phase 5: Conversation & Context 🟡 Partial

- Conversation model with message history and token tracking ✅
- Conversation-to-memory pipeline ✅
- Long-term memory model with decay, confidence, and access tracking ✅
- SSE streaming for real-time agent responses ✅
- Conversation service with context building ✅

### Phase 6: Agent Intelligence 🟡 Partial

- Agent SSE streaming ✅
- Expanded tool registry ✅
- RAG pipeline integration ✅
- Entity extraction service ✅
- Search clustering and recommendations ✅

---

## Upcoming Phases

| Phase | Name | Focus | Status |
|-------|------|-------|--------|
| 6.5 | Agentic Ecosystem | Development operating system, governance, workflows, validation | ✅ Complete |
| 7 | Desktop Preparation | Service abstraction, filesystem abstraction, Tauri readiness | ⬜ Next |
| 8 | Learning Loop | Pattern recognition, correction tracking, proactive assistant | ⬜ |
| 9 | Observability & Monitoring | Dashboards, metrics, health monitoring | ⬜ |
| 10 | Production Hardening | Test coverage, security, performance, Docker, CI/CD | ⬜ |

### Phase 6.5: Agentic Ecosystem ✅ Complete

- Governance docs (docs/GOVERNANCE.md)
- Workflow definitions (docs/WORKFLOWS.md)
- Decision tracking (docs/decisions/)
- Audit tracking (docs/audits/)
- Enhanced CLAUDE.md with ecosystem integration
- Enhanced AGENTS.md with workflow and skill rules
- ADR for ecosystem design (docs/decisions/001-agentic-ecosystem.md)

---

## Improvement Roadmap

### Phase 1: Consolidation

- [ ] Remove legacy `cortexApi.ts` — migrate all imports to `client.ts` domain modules
- [ ] Standardize API response envelope: `{ data: T, error: null } | { data: null, error: { code, message } }`
- [ ] Add `response_model=` to all v1 endpoints for OpenAPI schema completeness
- [ ] Replace manual session creation with `Depends(get_db)` everywhere

### Phase 2: Quality

- [ ] Achieve 80%+ backend test coverage (focus on services)
- [ ] Achieve 60%+ frontend test coverage (focus on hooks and API modules)
- [ ] Add E2E tests (Playwright or Cypress) for auth flow, vault, chat

### Phase 3: Security Hardening

- [ ] Account lockout after 5 consecutive failed login attempts
- [ ] Input sanitization audit (XSS, SQL injection, path traversal)
- [ ] API key authentication for programmatic access
- [ ] Audit logging for all state-changing operations

### Phase 4: Performance

- [ ] Redis caching for frequently queried data (model catalog, user settings)
- [ ] Response caching headers for static assets
- [ ] Query optimization (prefetch related objects, pagination cursors)
- [ ] Frontend bundle analysis and code splitting

### Phase 5: Observability

- [ ] Structured logging with correlation IDs (partially done via `RequestIdFilter`)
- [ ] Metrics export (Prometheus `/metrics` endpoint exists, needs expansion)
- [ ] Distributed tracing (OpenTelemetry)
- [ ] Health check deep probes (database, Redis, Qdrant, LLM)
