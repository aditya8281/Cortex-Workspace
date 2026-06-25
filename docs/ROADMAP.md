# CORTEX Roadmap

**Last updated:** 2026-06-25 (V1 phase names/statuses corrected)

## Current Status

| Area | State |
|------|-------|
| Tests | 928 passing |
| Frontend build | Passes |
| Linting | ruff + ESLint + mypy — all clean |
| Auth + vault backend | Production-quality foundation |
| Vault UI | Full file browser with table/list/grid views |
| Neural Dark redesign | Complete (warm dark, Neural Network background) |
| CLI | Scaffolded (command stubs) |
| LLM Integration | llama.cpp + Ollama with provider abstraction |
| Model Catalog | Full catalogue with providers, variants, benchmarks |
| Active Version | V1 — The Brain Works |

---

## Development Versions

Cortex development follows a 6-version system. Each version is a complete, releasable milestone.

| Version | Name | Duration | What It Delivers |
|---------|------|----------|------------------|
| **V1** | The Brain Works | 11–18 days | Agent loop, daemon lifecycle, CLI, streaming |
| **V2** | The Architecture | 17–25 days | Provider/MCP abstraction, plugin system, memory |
| **V3** | The Desktop | 22–31 days | Tauri shell, TUI, performance optimization |
| **V4** | The Automaton | 21–30 days | Scheduler, MCP server, research, sessions |
| **V5** | The Workspace | 27–38 days | Email, calendar, tasks, notes, documents, contacts |
| **V6** | The Ecosystem | 27–38 days | Marketplace, graph intelligence, cross-encoder, polish |

**Active version:** V1 — The Brain Works
**Phase plan location:** `.agents/plans/versions/vX/Phase-N.md`
**Progress tracking:** `.agents/plans/versions/vX/progress.md`

### V1: The Brain Works

| Phase | Name | Status |
|-------|------|--------|
| Phase 1 | Daemon Foundation | ✅ Complete |
| Phase 2 | Agent Loop Rebuild | 🟢 ACTIVE |
| Phase 3 | CLI + Bug Fixes | ⬜ Pending |

### V2: The Architecture

| Phase | Name | Status |
|-------|------|--------|
| Phase 1 | Event Bus & Workflow | ⬜ Pending |
| Phase 2 | MCP Client & Plugins | ⬜ Pending |
| Phase 3 | Context Providers | ⬜ Pending |

### V3: The Desktop

| Phase | Name | Status |
|-------|------|--------|
| Phase 1 | Tauri Desktop Shell | ⬜ Pending |
| Phase 2 | TUI | ⬜ Pending |
| Phase 3 | Desktop Integration | ⬜ Pending |

### V4: The Automaton

| Phase | Name | Status |
|-------|------|--------|
| Phase 1 | Scheduler & Automation | ⬜ Pending |
| Phase 2 | MCP Server | ⬜ Pending |
| Phase 3 | Daily Life Tools | ⬜ Pending |

### V5: The Workspace

| Phase | Name | Status |
|-------|------|--------|
| Phase 1 | Design System | ⬜ Pending |
| Phase 2 | Accessibility | ⬜ Pending |
| Phase 3 | Mobile | ⬜ Pending |

### V6: The Ecosystem

| Phase | Name | Status |
|-------|------|--------|
| Phase 1 | Plugin Marketplace | ⬜ Pending |
| Phase 2 | Graph Intelligence | ⬜ Pending |
| Phase 3 | Production Hardening | ⬜ Pending |

---

## Improvement Roadmap

### Consolidation

- [ ] Remove legacy `cortexApi.ts` — migrate all imports to `client.ts` domain modules
- [ ] Standardize API response envelope: `{ data: T, error: null } | { data: null, error: { code, message } }`
- [ ] Add `response_model=` to all v1 endpoints for OpenAPI schema completeness
- [ ] Replace manual session creation with `Depends(get_db)` everywhere

### Quality

- [ ] Achieve 80%+ backend test coverage (focus on services)
- [ ] Achieve 60%+ frontend test coverage (focus on hooks and API modules)
- [ ] Add E2E tests (Playwright or Cypress) for auth flow, vault, chat

### Security Hardening

- [ ] Account lockout after 5 consecutive failed login attempts
- [ ] Input sanitization audit (XSS, SQL injection, path traversal)
- [ ] API key authentication for programmatic access
- [ ] Audit logging for all state-changing operations

### Performance

- [ ] Redis caching for frequently queried data (model catalog, user settings)
- [ ] Response caching headers for static assets
- [ ] Query optimization (prefetch related objects, pagination cursors)
- [ ] Frontend bundle analysis and code splitting

### Observability

- [ ] Structured logging with correlation IDs (partially done via `RequestIdFilter`)
- [ ] Metrics export (Prometheus `/metrics` endpoint exists, needs expansion)
- [ ] Distributed tracing (OpenTelemetry)
- [ ] Health check deep probes (database, Redis, Qdrant, LLM)

---

## Previous Development History

For pre-V1 development history (Phase 1–6.5), see [`PREVIOUS_DEVELOPMENT_HISTORY.md`](PREVIOUS_DEVELOPMENT_HISTORY.md).
