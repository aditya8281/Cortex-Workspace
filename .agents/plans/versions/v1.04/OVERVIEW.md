# v1.04: Awareness Foundation — CORTEX

**Document:** Version 1.04 Overview
**Authority:** Stage 6 — Master Versioned Implementation Roadmap
**Date:** 2026-06-27
**Type:** Capability Delivery

---

## Objective

Build the foundational awareness system: filesystem watching, repository scanning, project detection, device information, environment scanning, and system health monitoring. This version gives Cortex the ability to perceive its environment — the prerequisite for all context-aware behavior.

---

## Question

"Can Cortex perceive its environment?"

---

## What This Version Delivers

After completing v1.04, Cortex can perceive:

- **Filesystem changes** — Watches directories for file creation, modification, and deletion. Maintains an index with content hashes for change detection. Supports incremental scanning.
- **Repository structure** — Detects programming languages, frameworks, dependencies, and project statistics (file count, line count). Builds a searchable repository index.
- **Project context** — Identifies project type (Python, Node, Rust, Go, etc.), detects frameworks (Next.js, Django, FastAPI), loads key configuration values.
- **Device information** — Reports hostname, OS, CPU, memory, disk usage. Updated on each check for real-time resource monitoring.
- **Environment variables** — Returns safe, non-secret environment variables and system paths. Never exposes API keys, passwords, or tokens.
- **System health** — Monitors backend, database, Redis, and other services. Tracks response times and error messages. Provides a health dashboard.

---

## reference architecture Feature Traceability

| reference architecture Feature | Cortex Implementation | Notes |
|------------------|----------------------|-------|
| File system awareness | Filesystem Watcher Service | reference architecture had basic file watching via polling; we use content-hash-based incremental indexing |
| Project detection | Project Scanner Service | reference architecture detected project type via file extensions; we add framework detection and configuration loading |
| Device info | Device Info Service | reference architecture had no device awareness; this is a new capability |
| System health monitoring | System Health Service | reference architecture had basic health checks; we add response time tracking and persistent health history |
| Environment awareness | Environment Scanner Service | reference architecture had no environment scanning; this is a new capability |
| Repository structure analysis | Repository Scanner Service | reference architecture had no repo analysis; this is a new capability |
| Code intelligence (AST parsing) | Deferred to v1.12 | AST parsing and symbol extraction are in Developer Intelligence version |

---

## Capability Mapping (120-Capability Model)

This version implements 6 of the 120 total capabilities, all in the **Awareness** domain:

| ID | Name | Domain | Priority | Capabilities Remaining After This |
|----|------|--------|----------|----------------------------------|
| A1 | Filesystem Awareness | Awareness | Foundation | 106 |
| A2 | Repository Awareness | Awareness | Foundation | 105 |
| A3 | Project Awareness | Awareness | Foundation | 104 |
| A9 | Device Awareness | Awareness | Foundation | 103 |
| A14 | Environment Awareness | Awareness | Foundation | 102 |
| A15 | System Health Awareness | Awareness | Foundation | 101 |

**Total: 6 capabilities (cumulative with v1.03: 13/120)**

### Downstream Capability Dependencies

These future capabilities directly depend on v1.04 capabilities:

| Future Capability | Depends On (v1.04) | Delivered In |
|-------------------|---------------------|--------------|
| A4: Code Structure Awareness | A2 | v1.08 |
| A5: Dependency Awareness | A2, A3 | v1.08 |
| A6: Build System Awareness | A3 | v1.08 |
| A7: Version Control Awareness | A2 | v1.08 |
| A8: Configuration Awareness | A3, A14 | v1.08 |
| A10: Network Awareness | A9, A15 | v1.08 |
| A11: Process Awareness | A9 | v1.08 |
| A12: Storage Awareness | A9, A15 | v1.08 |
| A13: Time Awareness | A9 | v1.08 |
| A16: Security Awareness | A15 | v1.08 |
| C4: Context Awareness | A1, A2, A3 | v1.06 |
| C5: Situational Awareness | A9, A14, A15 | v1.06 |
| P3: Resource Awareness | A9, A15 | v1.10 |

---

## Phases

| Phase | Name | Focus | Complexity | Capabilities Delivered |
|-------|------|-------|------------|----------------------|
| P01 | Awareness Models & Schema | Database models, Pydantic schemas, migrations | Medium | Foundation for all |
| P02 | Filesystem & Repository | File watching, repo scanning, change detection | Medium | A1, A2 |
| P03 | Project & Device | Project detection, device info, environment, health | Medium | A3, A9, A14, A15 |
| P04 | API & Integration | REST endpoints, frontend hooks, dashboard, E2E | Medium | Integration |

---

## Dependencies

**Depends on:**
- v1.02 (Backend Architecture — event system, domain services, middleware pipeline, auth system)
- v1.01 (Repository Structure — file placement conventions, `models/awareness/` package structure)

**Blocks:**
- v1.08 (Awareness Expansion — code structure, dependency, build system, version control awareness)
- v1.06 (Cognition & Execution Core — needs filesystem and repository awareness for context-aware reasoning)

---

## Architecture Principle Cross-References

| Principle | How v1.04 Satisfies It |
|-----------|----------------------|
| **AD-001: Domain-Driven Architecture** | Awareness is a distinct bounded context with its own models, services, and API surface. No imports from memory or cognition domains. |
| **AD-002: Event-Driven Communication** | Filesystem watcher emits events on file changes. Repository scanner emits events on scan completion. Health checks emit events on status changes. |
| **AD-003: Privacy as Architecture** | Environment scanner only returns safe variables. File paths are scoped by user. No cross-user file access. |
| **AD-004: Memory-First Intelligence** | Awareness data feeds into memory system. File changes create episodic memories. Repository structure creates semantic memories. |
| **AD-008: Gradual Capability Expansion** | 6 capabilities in 4 phases. Basic file watching first, advanced code intelligence in v1.08. |
| **AD-011: Simplicity Over Completeness** | Filesystem watching uses content hashing, not real-time OS-level watchers. Repository scanning uses file extension counting, not AST parsing. |
| **AD-012: Architectural Evolution** | Schema design allows adding columns (e.g., `content_hash` for new hash algorithms) without breaking changes. |

---

## Risk Matrix

| Risk | Likelihood | Impact | Mitigation | Phase |
|------|-----------|--------|------------|-------|
| Filesystem watcher misses events (OS-level) | Medium | Medium | Content-hash-based change detection catches missed events on next scan. Not real-time in v1.04. | P02 |
| Repository scanner slow on large repos | Medium | Medium | Skip `.git`, `node_modules`, `__pycache__`. Limit to 100K files. Async scanning. | P02 |
| Device info permissions denied | Low | Low | Graceful fallback to partial info. Log warning. Never crash. | P03 |
| Environment scanner exposes secrets | Low | Critical | Strict allowlist of safe variables. Never return full env. Code review mandatory. | P03 |
| System health check causes cascade failure | Low | High | Timeout on each health check (5s). Independent checks. No shared state. | P03 |
| File index grows unbounded | Medium | Medium | TTL-based cleanup. Old entries pruned on scan. Max 100K files per user. | P02 |
| SQLite vs PostgreSQL JSON column divergence | Medium | Low | `conftest.py` compiles JSONB → JSON. Tests run on SQLite. | P01 |
| Migration conflicts with v1.02/v1.03 models | Low | High | Separate `awareness/` model package. No shared tables. | P01 |
| psutil not available on all platforms | Low | Low | Fallback to platform module for basic info. psutil is optional enhancement. | P03 |
| Race condition on concurrent scans | Medium | Low | Database-level locking on unique constraints. Idempotent upserts. | P02 |

---

## Downstream Dependency Impact

If v1.04 fails or is significantly delayed:

| Affected Version | Impact | Recovery |
|------------------|--------|----------|
| **v1.08 (Awareness Expansion)** | Cannot start. Code structure, dependency, and build awareness all depend on foundation models. | Must complete v1.04 first. No workaround. |
| **v1.06 (Cognition & Execution)** | Reasoning lacks environmental context. Agent cannot understand what files exist, what project it's working on. | Partial: can hardcode project paths, loses dynamic awareness. |
| **v1.10 (Planning & Orchestration)** | Planning cannot assess available resources or project structure. | Degrades to manual planning without environmental awareness. |
| **v1.11 (Interaction & Communication)** | Chat cannot reference file system context. Loses "show me files like X" capability. | Partial: text-only responses without file context. |
| **v1.12 (Developer Intelligence)** | Code intelligence needs repository awareness as input. Cannot analyze code structure. | Must complete v1.04 first. |

---

## Estimated Duration

4-5 days (2 developers) or 6-8 days (1 developer).

---

## Security Considerations

- **Path traversal prevention:** All file operations validate paths are within allowed directories. No `../` traversal.
- **Secret exclusion:** Environment scanner uses strict allowlist. Never returns `SECRET_KEY`, `DATABASE_URL`, `PASSWORD`, `TOKEN`, or `API_KEY`.
- **User isolation:** File indices are scoped by `user_id`. No cross-user file access.
- **Health check authorization:** System health endpoints require authentication. Health data is not publicly accessible.
- **File content hashing:** SHA-256 used for change detection. No file content stored in database (only hash).
- **Scan rate limiting:** Filesystem scans rate-limited to prevent resource exhaustion (1 scan per minute per directory).
- **Binary file handling:** Binary files are indexed by metadata only (path, size, hash). Content is never read for binary files.

---

## Performance Targets

| Metric | Target | Measurement |
|--------|--------|-------------|
| File index scan (1000 files) | < 10s | p95 from scan start to completion |
| Change detection (100 files) | < 2s | p95 for delta computation |
| Repository scan (10K files) | < 30s | p95 from scan start to completion |
| Device info query | < 100ms | p95 from API call to response |
| System health check (single) | < 5s | Timeout per check |
| System health check (all) | < 10s | Parallel execution |
| API endpoint response | < 200ms | p95 excluding scan operations |

---

## Integration Tests

This version requires the following integration test suites:

1. **File Indexing Lifecycle** — Scan → Detect changes → Re-scan → Verify delta
2. **Repository Scanning** — Scan repo → Verify languages, framework, dependencies detected
3. **Project Detection** — Scan project → Verify type, frameworks, configuration detected
4. **Device Info** — Get device info → Verify OS, CPU, memory, disk values reasonable
5. **Environment Safety** — Get environment → Verify no secrets in response
6. **System Health** — Check services → Verify status, response times recorded
7. **API Authentication** — Unauthenticated requests → 401. Wrong user → 403.
8. **Migration Roundtrip** — `make migrate` → `alembic downgrade -1` → `make migrate` → No errors

---

## Definition of Done

- [ ] All 6 awareness capabilities implemented and tested
- [ ] Awareness services in `backend/app/services/awareness/` (4 modules: file_watcher, repository, project, device/environment/health)
- [ ] Awareness models in `backend/app/models/awareness/` (5 model files + __init__)
- [ ] Awareness schemas in `backend/app/schemas/awareness/` (5 schema files + __init__)
- [ ] Awareness API endpoints in `backend/app/api/v1/awareness/` (4 route files + __init__)
- [ ] Frontend API client in `frontend/features/awareness/api.ts`
- [ ] Frontend hooks in `frontend/features/awareness/hooks/`
- [ ] Unit tests: 90%+ coverage on awareness services
- [ ] Integration tests: all 8 test suites passing
- [ ] Migration applies cleanly and rolls back cleanly
- [ ] `make test` passes (0 failures)
- [ ] `make lint` passes (0 errors)
- [ ] OpenAPI schema shows all awareness endpoints at `/docs`
- [ ] Performance targets met (benchmarked)
- [ ] Security review: no path traversal, no secret leakage, no cross-user access

---

## Readiness for Next Version

v1.04 is complete when all awareness capabilities are implemented and tested. The following versions can now begin:
- **v1.05 (Privacy & Trust)** — Can start in parallel (no awareness dependency)
- **v1.06 (Cognition & Execution)** — Can use awareness data for context-aware reasoning
- **v1.08 (Awareness Expansion)** — Can build on foundation with code structure, dependency, and build awareness
