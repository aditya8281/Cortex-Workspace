# Consolidated Audit Review — Cortex

**Generated:** 2026-06-22
**Sources:** 9 audit reports consolidated
**Total findings remaining:** ~180+ (after P0/P1 fixes already applied)

---

## Executive Summary

| Severity | Count | Category |
|----------|-------|----------|
| **Critical** | 4 | Feature broken or exploitable |
| **High** | ~35 | Data loss, security gaps, broken contracts |
| **Medium** | ~65 | Degraded functionality, code quality |
| **Low** | ~40 | Cleanup, hardening, cosmetic |

---

## CRITICAL — Fix Immediately

### C1: Agent Self-Approval Bypass (Security)
- **File:** `agents/executor.py:52-58`
- **Issue:** LLM can call `approve_tool()` itself, bypassing human approval for dangerous ops like `exec_command`
- **Risk:** Full system compromise via prompt injection → arbitrary command execution
- **Could break other code:** No — isolated fix to tool approval flow
- **Source:** security-audit-v2.md

### C2: Memory Router Not Registered (Feature Broken)
- **File:** `api/router.py` — missing import
- **Issue:** All 6 `/api/v1/memory` endpoints return 404. Short-term memory system is non-functional.
- **Risk:** Memory page is completely broken
- **Could break other code:** No — adding router import is safe
- **Source:** integration-trace-audit.md

### C3: Search Pagination Impossible (Feature Broken)
- **File:** `frontend/src/shared/types.ts:243-247`
- **Issue:** Frontend `SearchResponse` type lacks `next_cursor`/`has_more` fields that backend supports
- **Risk:** Pagination in search results is impossible from frontend
- **Could break other code:** No — type addition only
- **Source:** integration-trace-audit.md

### C4: Vault List Response Wrapping Mismatch (Feature Broken)
- **File:** `backend/app/api/v1/vault.py:127-137` vs `frontend/src/shared/auth/cortexApi.ts:245-249`
- **Issue:** Backend returns `{files: [...]}` but frontend expects flat `VaultFileEntry[]`
- **Risk:** Vault file browser fails to render
- **Could break other code:** Yes — vault page re-render behavior
- **Source:** integration-trace-audit.md (may already be fixed per cleanup-audit)

### C5: Missing `server_default` on 15+ Timestamp Columns (DB)
- **File:** `migrations/versions/b00000000000_baseline.py`
- **Issue:** NOT NULL timestamp columns without `server_default` — bulk/raw INSERT will fail
- **Risk:** Data integrity failures on any raw SQL or bulk insert
- **Could break other code:** Yes — any code path using bulk inserts
- **Source:** db-audit-v2.md

### C6: In-Memory Token Stores Not Process-Safe (Quality)
- **File:** `core/security.py:96-137`
- **Issue:** `_memory_active`/`_memory_revoked` dicts use `threading.Lock` but are not process-safe in multi-worker deployments
- **Risk:** Stale tokens accepted in multi-worker setups
- **Could break other code:** No — requires deployment change awareness
- **Source:** quality-issues-report.md

---

## HIGH — Fix Soon

### Security (10 items)

| # | Issue | File | Impact |
|---|-------|------|--------|
| H-S1 | Auth rate limiter key mismatch (`/api/auth` vs `/api/v1/auth`) | `core/rate_limit.py:33` | Auth endpoints not rate-limited |
| H-S2 | Refresh token reuse clears ALL users' tokens | `auth/service.py:190` | DoS — all users logged out |
| H-S3 | WebSocket tokens in URL query string | `api/ws.py:21` | Token leakage in logs/referer |
| H-S4 | Vault brute-force unprotected (5 attempts/min added but in-memory only) | `api/v1/vault.py` | Vault password bypass |
| H-S5 | GitHub token encryption uses deterministic key from SECRET_KEY | `api/v1/github.py:69-78` | SECRET_KEY compromise exposes all PATs |
| H-S6 | `/metrics` unauthenticated and rate-limit exempt | `api/metrics.py:32-69` | Information disclosure |
| H-S7 | Repository registration has no path restrictions | `api/v1/repository.py:85-104` | Arbitrary filesystem reading |
| H-S8 | HuggingFace token stored in plaintext | `api/v1/models.py:511-559` | DB compromise exposes HF tokens |
| H-S9 | Vault password re-encryption not atomic — crash mid-rotation = data loss | `services/vault_service.py:560-625` | Potential data loss |
| H-S10 | Rate limiting fails open on Redis outage | `core/rate_limit.py:47-49` | DoS protection disabled |

### Frontend-Backend Contract (14 items)

| # | Issue | Frontend | Backend | Impact |
|---|-------|----------|---------|--------|
| H-C1 | Sync status field name (`watching_count` vs `watching`) | `types.ts:712` | `sync.py:238-245` | Wrong field displayed |
| H-C2 | Sync `watched_paths` type (`string[]` vs `list[dict]`) | `types.ts:716` | `sync.py:399-409` | Type mismatch |
| H-C3 | Models `installed()` item shape (12 vs 6 fields) | `types.ts:572-588` | `models.py:199-253` | Missing fields |
| H-C4 | Models `downloadHistory` missing `speed_bytes_sec`/`eta_seconds` | `types.ts:535-546` | `models.py:612-643` | Data lost |
| H-C5 | Models `compare()` extra `models` field not typed | `types.ts:620-625` | `models.py:321-364` | Missed data |
| H-C6 | `DownloadProgressResponse.progress` type `dict` vs `float` | `types.ts:453-456` | `schemas/model.py:129-131` | Progress display breaks |
| H-C7 | `SyncTriggerResponse.job_id` type `str` vs frontend `number` | `types.ts:638-649` | `schemas/model.py:241-247` | Type confusion |
| H-C8 | Models `search()` result shape mismatch | `types.ts:607-610` | `models.py:265-318` | Missing fields |
| H-C9 | Chat timestamp client vs server clock drift | `chat/page.tsx` | `conversation.py:173` | Inconsistent timestamps |
| H-C10 | Vault upload returns encrypted size, not original | `cortexApi.ts:252-291` | `vault_service.py:405-409` | Wrong size displayed |
| H-C11 | Models `usageStats()` ignores `model_id` param | `models.ts:154-157` | `models.py:187-196` | Per-model filtering broken |
| H-C12 | Long-term memory `source_path` vs `source` field name | `types.ts:127` | `long_term_memory.py:22` | Undefined field |
| H-C13 | Search filter params `node_type`/`language` silently ignored | `search.ts:14-16` | `search.py:38-44` | Filters do nothing |
| H-C14 | Chat sources not persisted — disappear on reload | `types.ts:732-738` | `conversation.py:180` | Data loss on reload |

### Database (6 items)

| # | Issue | File | Impact |
|---|-------|------|--------|
| H-D1 | `ModelVariant` FKs missing `ondelete` | `models/model_catalog.py:83-84` | Provider deletion FK violations |
| H-D2 | `ModelDownload`/`ModelUsage` FKs missing `ondelete` | `models/model_catalog.py:104-105,123-125` | User/variant deletion FK violations |
| H-D3 | `Agent.user` missing `back_populates` | `models/agent.py:31` | ORM navigation breaks |
| H-D4 | `backref` usage in 3 relationships | `models/graph.py:33-34`, `file_index.py:30` | Untyped reverse sides |
| H-D5 | Schema-ORM field name mismatches (4 schemas) | `schemas/agent.py` | Data loss in API responses |
| H-D6 | 3 FK columns missing indexes in migration | `migrations/versions/b00000000000_baseline.py` | Slow JOIN queries |

### Quality (8 items)

| # | Issue | File | Impact |
|---|-------|------|--------|
| H-Q1 | LLM error messages leaked to clients | `conversations.py:166-170` | Internal path/error disclosure |
| H-Q2 | HTTP call with no timeout on model delete | `models.py:702` | Can hang indefinitely |
| H-Q3 | Rate limit bypass on Redis failure | `vault.py:112-113` | Brute-force protection bypass |
| H-Q4 | Token revocation silently ignored on logout | `auth/router.py:149-150` | Token stays valid |
| H-Q5 | Decryption failure silently returns encrypted data | `vault_service.py:426-427` | User gets gibberish |
| H-Q6 | No error handling around async task enqueue | `sync.py:337` | Crash on queue failure |
| H-Q7 | Arbitrary filesystem path accepted (indexing) | `indexing.py:82` | Path traversal |
| H-Q8 | Custom encryption scheme for GitHub tokens | `github.py:76-78` | Deterministic key derivation |

### Cleanup Dead Code (5 items)

| # | Issue | Files | Lines |
|---|-------|-------|-------|
| H-CL1 | Dead backend services (8 files) | `cross_file_search.py`, `search_clustering.py`, `threaded_scanner.py`, `batch_indexer.py`, `document_statistics.py`, `path_index.py`, `model_detail_scraper.py`, `indexing_orchestrator.py` | ~1000+ |
| H-CL2 | Dead frontend search components | `GraphView.tsx`, `SearchFilters.tsx`, `SearchResults.tsx` | 426 |
| H-CL3 | Duplicate memory API (`cortexApi.ts` vs `shared/api/memory.ts`) | — | Dual surface |
| H-CL4 | Entire CLI is stub code | `cli/src/commands/` (15 files) | 274 |
| H-CL5 | Dead services (`seed_data.py`, `deletion_pipeline.py`) | — | 400+ |

---

## MEDIUM — Fix When Touching

### Security (8 items)

| # | Issue | File |
|---|-------|------|
| M-S1 | CSRF exemption on vault endpoints incorrect | `core/csrf.py:26` |
| M-S2 | Password validation too weak (`password1` passes) | `core/security.py:30-35` |
| M-S3 | `run.error` stores internal exception messages | `agents/run_manager.py:168` |
| M-S4 | Vault password cached in plaintext in memory | `vault_service.py:40-87` |
| M-S5 | WebSocket connections have no per-user limits | `core/websocket.py` |
| M-S6 | CORS has no production origins configured | `core/config.py:30-37` |
| M-S7 | Error messages in conversation streaming leak internals | `conversations.py:166-170` |
| M-S8 | `validate_storage_path()` not called on storage registration updates | `storage_registry.py:17-37` |

### Frontend-Backend Contract (6 items)

| # | Issue |
|---|-------|
| M-C1 | Search nullable fields (`document_id`, `language`, `chunk_type`) — frontend required, backend nullable |
| M-C2 | Memory list `tags` field may be JSON string instead of parsed array |
| M-C3 | Long-term memory list response shape inconsistent with/without category filter |
| M-C4 | Agent `tools` type: JSON string vs array |
| M-C5 | Vault file list nullable `size` field |
| M-C6 | Models settings default value misalignment |

### Database (6 items)

| # | Issue |
|---|-------|
| M-D1 | `CodeChunk` missing unique constraint on `(repo_id, file_path, chunk_index)` |
| M-D2 | `DateTime` tz-aware/naive inconsistency across models |
| M-D3 | Default value mechanism inconsistency (Python vs server_default) |
| M-D4 | `User.deleted_at` missing index — slow soft-delete queries |
| M-D5 | `parameter_count` type mismatch across 6 schemas (`str` vs `float`) |
| M-D6 | `knowledge_entries` missing unique constraint on `(user_id, source_path, category)` |

### Quality (15+ items)

| # | Issue |
|---|-------|
| M-Q1 | Bare `except Exception` swallowing errors in `models.py:215,437,472` |
| M-Q2 | Too-broad exception catches in multiple files |
| M-Q3 | Missing input validation on API endpoints (conversations limit/offset, long_term_memory fields) |
| M-Q4 | Path traversal not validated on sync/validate-path endpoint |
| M-Q5 | HTTP calls without retry logic (model delete, embedding, download) |
| M-Q6 | Missing circuit breaker patterns (embedding service, vector DB) |
| M-Q7 | Race conditions in async code (`background.py`, `security.py`) |
| M-Q8 | Shared mutable state without locks (lazy singletons) |
| M-Q9 | Missing cleanup on error paths (vault rotation) |
| M-Q10 | Resource leaks (profile.py `SessionLocal()`, model_downloader.py) |
| M-Q11 | Missing timeout on HTTP requests (`models.py:702`) |
| M-Q12 | Missing connection pool configuration (Redis) |
| M-Q13 | Deep health check only checks database, not Redis/Ollama/Qdrant |
| M-Q14 | Missing graceful shutdown for download manager |
| M-Q15 | `file_watcher_v2.py:join()` blocks without timeout |

### Cleanup (8 items)

| # | Issue |
|---|-------|
| M-CL1 | Unused `service_base.py` (zero imports) |
| M-CL2 | Unused `path_index.py` model |
| M-CL3 | Redundant `auth/security.py` re-export |
| M-CL4 | Dead `tauri-adapter.ts` (abandoned Tauri experiment) |
| M-CL5 | Unused UI components (`Tooltip.tsx`, `StaggerChildren.tsx`, `Steps.tsx`) |
| M-CL6 | Duplicate `getCsrfToken` implementations |
| M-CL7 | Duplicate `api` vs `cortexApi` HTTP patterns |
| M-CL8 | `WorkloadRecommendations` imported but unused in memory page |

---

## LOW — Fix Opportunistically

### Security (12 items)

| # | Issue |
|---|-------|
| L-S1 | No `SECRET_KEY` rotation mechanism |
| L-S2 | Redis has no password in docker-compose |
| L-S3 | Repositories with `user_id=NULL` visible to all users |
| L-S4 | `SecurePasswordCache.get()` returns immutable strings (can't zero) |
| L-S5 | CSP dev mode allows `ws://localhost:*` |
| L-S6 | No `Cache-Control: no-store` on authenticated responses |
| L-S7 | No `Permissions-Policy` header |
| L-S8 | `x-xss-protection` header is deprecated |
| L-S9 | Hardcoded DB credentials as defaults |
| L-S10 | Vault extension allowlist includes `.env`, `.key`, `.pem` |
| L-S11 | `git_log` has no path restriction |
| L-S12 | Thread-safety of in-memory refresh token stores |

### Frontend (8 items)

| # | Issue |
|---|-------|
| L-F1 | Unused search sub-components (dead code) |
| L-F2 | Landing page GitHub link `href="#"` TODO placeholder |
| L-F3 | No tests for Landing page and Downloads page |
| L-F4 | Chat conversation list shows only title, no last message preview |
| L-F5 | Admin page — no pagination for user list |
| L-F6 | Dashboard process table limited to 20 rows, no pagination |
| L-F7 | Accent color preference saved but not applied globally |
| L-F8 | Notifications button shows "coming soon" placeholder |

### Database (8 items)

| # | Issue |
|---|-------|
| L-D1 | `TIMESTAMP` vs `TIMESTAMPTZ` inconsistency |
| L-D2 | Downgrade does not drop ENUM type with guard |
| L-D3 | `model_variants` has redundant/overlapping columns |
| L-D4 | GIN indexes use hardcoded `'english'` text search config |
| L-D5 | Index naming inconsistencies (migration vs ORM) |
| L-D6 | `models/__init__.py` exports only 13 of 28 model classes |
| L-D7 | `RepoIndex`/`CodeChunk` timestamps nullable inconsistency |
| L-D8 | `LongTermMemory.source_id` has no FK constraint (intentional) |

### Quality (6 items)

| # | Issue |
|---|-------|
| L-Q1 | PII (IP addresses) logged in plaintext |
| L-Q2 | Inconsistent log levels (security events at `warning` not `error`) |
| L-Q3 | Missing context in log messages (no user_id) |
| L-Q4 | `SECRET_KEY` defaults to empty string |
| L-Q5 | Missing `response_model` on logout endpoint |
| L-Q6 | Deprecated schema aliases in `user.py` |

### Cleanup (4 items)

| # | Issue |
|---|-------|
| L-CL1 | TODO/FIXME comments unresolved |
| L-CL2 | Empty `__init__.py` files (convention, not actionable) |
| L-CL3 | `file_watcher.py` superseded by v2 but kept |
| L-CL4 | Memory page 1310+ line monolith (should decompose) |

---

## Architecture Risks (from architecture-map.md)

| Risk | Severity | Impact |
|------|----------|--------|
| PostgreSQL failure | Critical | All data access fails |
| Qdrant failure | Critical | Vector search fails |
| LLM provider unavailable | High | Agent/chat degrade |
| Embedding service unavailable | High | Cannot create embeddings |
| Singleton dependencies | Medium | Testing requires careful patching |
| Mixed sync/async | Medium | Event loop issues |
| Agent execution blocking | Medium | Long runs block other requests |
| No horizontal scaling | Medium | File watchers/download managers process-local |
| CSRF complexity | Medium | 25 of 35 test failures are CSRF-related |
| No observability/APM | Medium | No tracing integration |
| No backup automation | Medium | pg_dump is manual |
| Circuit breaker missing | Medium | LLM retry but no circuit breaker |

---

## Fix Priority Roadmap

### Phase 1: Critical (1-2 days)
1. Register memory router (`api/router.py`)
2. Fix agent self-approval bypass
3. Add `server_default` to timestamp columns
4. Fix vault list response wrapping
5. Add search pagination fields to frontend

### Phase 2: High — Security (3-5 days)
6. Fix auth rate limiter key
7. Scope refresh token reuse to affected user
8. Move WebSocket tokens out of URL
9. Restrict repository paths
10. Authenticate `/metrics`
11. Encrypt HuggingFace tokens
12. Fix GitHub token encryption scope

### Phase 3: High — Contracts (3-5 days)
13. Fix all 14 frontend-backend contract mismatches
14. Add typed response models to untyped endpoints
15. Fix DB schema-ORM field name mismatches
16. Add missing FK `ondelete` clauses

### Phase 4: Medium — Quality (5-7 days)
17. Add error handling to bare except blocks
18. Add timeouts/retries to HTTP calls
19. Implement circuit breaker patterns
20. Add input validation to API endpoints
21. Fix lazy singleton thread safety
22. Add deep health checks for Redis/Ollama/Qdrant

### Phase 5: Cleanup (2-3 days)
23. Delete 8 dead backend services
24. Delete 3 dead frontend components
25. Remove CLI stub code
26. Consolidate API client pattern
27. Remove dead imports/re-exports

### Phase 6: Low (Opportunistic)
28. Harden security headers
29. Add missing tests
30. Resolve TODO comments
31. Add SECRET_KEY rotation
32. Add backup automation

---

*Consolidated from: architecture-map.md, frontend-page-audit.md, backend-capability-audit.md, integration-trace-audit.md, cleanup-audit.md, db-audit-v2.md, security-audit-v2.md, quality-issues-report.md, remaining-issues-report.md*
