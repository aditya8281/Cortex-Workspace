# /project:audit — Codebase Audit

Deep code-level scan for runtime errors, dead code, integration issues, broken imports, placeholders, and technical debt. Includes systems forensics for WebSocket auth lifecycle, ghost routes, config deprecation, frontend data validation, token refresh correctness, and test hygiene.

**Scope:** Code-level analysis. For broad ecosystem health (skills, docs, governance), use `/project:health` instead.

## Instructions

### 1. Read Scope

Invoke `cortex-repo-discovery` then `cortex-repository-intelligence`. Invoke `cortex-planning-ecosystem`.

Read the active phase plan to know what components are in scope.

### 2. Baseline

Invoke `cortex-system-validation`.

### 3. Runtime Errors

Scan for code that will crash at runtime:

- **Imports:** Find missing module references. Run `python -c "import backend.app.main"`. Check all service files import dependencies correctly.
- **Singletons:** Verify global singletons (llm_manager, redis_cache, download_manager) are properly initialized.
- **API patterns:** Check all endpoints for missing `response_model=`, missing ownership checks, wrong route order.

### 4. Dead Code

Find functions/classes/modules never imported or called. For each candidate, apply the **UNIQUE CAPABILITIES TEST:** Is it imported anywhere? If not, does it provide a capability not covered elsewhere? If unique → KEEP. If no unique capability and not imported → flag for deletion.

### 5. Integration Issues

- **Service chains:** Verify dependency chains (file_watcher_v2 → indexing_orchestrator → incremental_indexer, etc.)
- **Mock patches:** Verify all patches in `tests/conftest.py` match actual service imports.
- **Model imports:** Verify all models imported in `migrations/env.py` for Alembic autogenerate.

### 6. Placeholders

Scan for TODO, FIXME, HACK, XXX, TBD, NotImplementedError, bare `pass` in non-trivial functions, mock return values in production code.

### 7. Consistency

- Cross-reference CLAUDE.md claims vs actual codebase
- Check docs/ references are valid
- Verify migration chain: `make migrate`

---

## Systems Forensics

The following sections probe deeper security and correctness issues that standard static analysis misses.

### 8. WebSocket Auth Lifecycle

The WebSocket auth surface is distinct from HTTP auth and has unique attack vectors. Audit each layer:

**Token Extraction Chain:**
- Verify `extract_ws_token` in `backend/app/core/websocket.py` — confirm the token priority order is documented and consistent: (1) explicit `token` argument, (2) `sec-websocket-protocol` header, (3) `cortex_access` cookie.
- Check every WS handler (`ws/chat`, `ws/models`, `ws/notifications`, `ws/system`, `ws/agents`, `ws/demo`) uses the manager's `extract_ws_token`, not a local ad-hoc implementation.
- Flag any handler that bypasses the manager and reads `query_params.get("token")` directly — this is inconsistent with the standard extraction path and may leak tokens in server logs.

**verify_ws_token Integrity:**
- Confirm `verify_ws_token` in `backend/app/core/db.py` checks all three conditions: (1) JWT signature valid, (2) JTI not revoked against any known secret key, (3) user exists and is not soft-deleted.
- Verify the function returns `user_id` (int) on success and raises on failure — no silent `None` returns that would skip auth.
- Check that WS handlers actually call `verify_ws_token` AFTER `accept()` — a handler that registers a connection before verification creates a ghost connection.

**BaseHTTPMiddleware WS Bypass:**
- `BaseHTTPMiddleware` in Starlette breaks WebSocket upgrades. All middleware that should NOT apply to WebSocket upgrades must have an explicit bypass check (`if scope["type"] == "websocket": return`).
- Verify these middlewares have the bypass: `rate_limit.py`, `csrf.py`, `https_redirect.py`, and the request-logging middleware in `main.py`.
- **Negative check:** Confirm no middleware in the stack calls `call_next()` or `dispatch()` on WebSocket scope — this would cause `RuntimeError: No response returned`.

**WS Connection Cleanup:**
- Verify every handler has a `finally` block that calls `manager.disconnect(websocket, user_id)`.
- Check that the demo handler (`backend/app/api/ws.py`) follows the same cleanup pattern as production handlers.

### 9. Ghost Routes (Duplicate Router Includes)

Ghost routes are endpoints registered twice via separate `include_router` calls, causing ambiguous dispatch or shadowed handlers.

**Known Risk — Privacy Router:**
- `backend/app/api/v1/privacy/__init__.py` defines its own `router` with sub-routers at `/audit`, `/consent`, `/export`, `/transparency`, `/access`.
- `backend/app/api/v1/privacy/router.py` defines a separate `router` with overlapping sub-routers at `/audit`, `/consent`, `/export`, `/transparency`, `/access-control`.
- Only `router.py` is imported by the API router (`backend/app/api/router.py`). The `__init__.py` router is dead code — verify nothing imports it (including tests).
- **Prefix mismatch:** `/access` in `__init__.py` vs `/access-control` in `router.py`. If the `__init__.py` router were ever accidentally registered, it would create a conflicting endpoint.

**Route Registration Audit:**
- Build the complete route table: enumerate all 36 `include_router` calls across the backend, resolving prefixes.
- Check for duplicate path+method combinations. FastAPI silently allows duplicates — the last registration wins, which may not be the intended one.
- Verify `backend/app/api/ws.py` exposes `/ws/demo` at root level (outside `/api/v1` prefix) — confirm this is intentional for dev-only use and not accessible in production.
- Verify route registration order within each router: specific paths before parameterized (e.g., `/models/health` before `/models/{model_id}`).

**Include_router Count:**
- Expected: ~31 active `include_router` calls (excluding the dead `privacy/__init__.py` calls).
- Any count above this indicates a potential double-registration.

### 10. Config Alias Deprecation

Legacy env var aliases create invisible configuration drift — a deploy may silently use an old alias while the new field name is set to its default.

**Self-Referential Aliases:**
- `CORTEX_ROOT` has `AliasChoices("CORTEX_ROOT")` — this is a no-op since Pydantic reads the field name by default. Flag for removal.
- `CORTEX_NEW_AGENT_LOOP` has `AliasChoices("CORTEX_NEW_AGENT_LOOP")` — same issue. Flag for removal.

**Deprecation Warnings:**
- `CORTEX_STORAGE_ROOT` → `CORTEX_ROOT`: verify the `model_post_init` deprecation warning fires correctly and the value propagates.
- `CORTEX_NEW_AGENT` → `CORTEX_NEW_AGENT_LOOP`: verify the same.
- **Check:** Are these deprecated aliases tested? If not, they may break silently.

**Alias Hygiene:**
- For each remaining alias (`CORTEX_MEMORY_PATH`, `CORTEX_VAULT_PATH`), verify a comment or docstring explains why the alias exists (backward compat) and when it can be removed.
- Check if any test fixtures or CI configs still use the deprecated names — this would mask failures.

### 11. Frontend WebSocket Data Validation

WebSocket messages are untyped by default. Without runtime validation, a malformed server message causes silent data corruption or runtime crashes.

**Guard Coverage Audit:**
- `MetricsProvider.tsx` has `isLiveMetrics()`, `isProcessInfo()`, `isSystemLog()` guards.
- `DownloadProvider.tsx` has `isDownloadModel()` guard.
- **Gap check:** `useChatTyping.ts`, `useWebSocket.ts` (agent runs), and `DownloadProvider.tsx` receive `Record<string, unknown>` from WS. Verify each consumer either (a) validates the payload before use, or (b) the server contract is enforced at a single point.
- Check that all `isXxx()` guards validate both presence AND type of required fields (e.g., `typeof value === "number"`, not just `value !== undefined`).

**Missing Guards:**
- `useChatTyping.ts` — does it validate the typing indicator payload structure?
- Agent run messages in `features/agents/page.tsx` — does it validate the WS message before destructuring?
- Any other `onMessage` callback that reads `data.field` without checking if `data` has that field.

**WebSocket Hook Safety:**
- `useWebSocket.ts` — confirm the `onMessage` callback receives typed data (not raw `MessageEvent.data` as string). If it parses JSON, verify the parse is wrapped in try/catch.
- Check that the reconnection logic does not accumulate event listeners or create memory leaks on repeated connect/disconnect cycles.

### 12. Token Refresh Race Conditions

Concurrent requests that all receive 401 simultaneously can trigger a refresh stampede or stale-token retry.

**Frontend Refresh Deduplication:**
- `shared/api/client.ts` uses a module-level `refreshPromise` to coalesce concurrent 401-triggered refreshes. Verify:
  1. The promise is cleared after both success AND failure (not just success).
  2. A failed refresh does not leave a stale promise that future 401s wait on indefinitely.
  3. The `_retryDepth` counter prevents infinite retry loops — confirm `MAX_RETRIES = 1` and the loop terminates.

**Concurrent Refresh Safety:**
- When two requests get 401 concurrently, both await the same `doRefresh()`. The first retry succeeds with the new token. The second retry reads the new access token from cookies (shared per-domain). Verify this cookie-based flow is actually safe — check that `apiFetch` does not cache the old token in a closure.

**Refresh-on-Auth-Page Guard:**
- `AuthProvider.tsx` uses raw `fetch` (not `apiFetch`) to call `/api/v1/auth/me`. Verify this prevents the 401→refresh→redirect loop that would occur if `apiFetch` intercepted the auth check.

**WebSocket Token Refresh:**
- The `/api/v1/auth/ws-token` endpoint returns the current access token without performing a refresh. If the token is expired, the WS connection will fail auth.
- Check the frontend `useWebSocket.ts` hook — does it refresh the access token BEFORE calling `/ws-token`? If not, a stale access token causes silent WS auth failure and infinite reconnect loops.

### 13. Module Docstrings for Test-Only Files

Test files serve as documentation. Module docstrings describe what a test file covers and why.

**Scan Scope:** All files under `tests/` that are NOT `__init__.py` or `conftest.py`.

**Files Missing Docstrings (known findings):**
- `tests/api/test_agents_api.py`
- `tests/api/test_auth.py` (has a comment, not a docstring)
- `tests/api/test_conversations_api.py`
- `tests/api/test_conversations_security.py`
- `tests/api/test_github_api.py`
- `tests/api/test_indexing_api.py`
- `tests/api/test_knowledge_api.py`
- `tests/api/test_long_term_memory_api.py`
- `tests/api/test_metrics_api.py`
- `tests/api/test_models_api.py`
- `tests/api/test_models_sync.py`
- `tests/api/test_notifications_api.py`
- `tests/api/test_profile_api.py`
- `tests/api/test_repository_api.py`
- `tests/api/test_search_api.py`
- `tests/api/test_sync_api.py`
- `tests/api/test_system_api.py`
- `tests/api/test_users_api.py`
- `tests/api/test_vault_api.py`
- `tests/agents/test_run_store.py`
- `tests/services/test_ollama_sync.py`
- `tests/services/test_vault.py`
- `tests/services/test_vector_db.py`

**Expected format:**
```python
"""Tests for <module> — <brief description of what is covered>."""
```

**Verify:** Re-scan to confirm no new test files have been added without docstrings since this baseline was established.

---

## Feedback Loop

**On entry:** Read `.claude/ecosystem/feedback.json`, filter last 10 entries where `command` matches this command name. If learnings exist, incorporate them into the audit scope. Specifically:
- If previous runs found persistent issues in a section, increase that section's depth.
- If a suggestion from a previous run was implemented, verify it and remove from the suggestion pool.
- If the command previously failed or was partial, investigate what caused the failure and address it first.

**On exit:** After completing the audit, append an entry to `.claude/ecosystem/feedback.json`:
```json
{
  "timestamp": "<ISO-8601>",
  "command": "/project:audit",
  "run_id": "<uuid>",
  "outcome": "success|failure|partial",
  "learnings": ["<what was discovered>"],
  "suggestions": ["<improvements for next run>"],
  "duration_ms": 0
}
```

**Outcome definitions:**
- `success`: All sections completed, findings documented, no tool failures.
- `partial`: Some sections skipped or incomplete (note which in `learnings`).
- `failure`: Audit could not complete (note blocker in `learnings`).

**Learning format:** Specific, actionable statements. Bad: "found some issues." Good: "privacy `__init__.py` router is dead code — `router.py` is the only import path."

**Suggestion format:** Concrete improvements. Bad: "improve the audit." Good: "add a check that `refreshPromise` is cleared on both success and failure paths."

---

## Output

```markdown
## Audit: [date]

### Baseline (Tests/Lint)
### Runtime Errors
| # | Severity | File:Line | Issue | Fix |
### Dead Code
| # | File:Line | Verdict | Reason |
### Integration Issues
| # | Severity | Issue | Fix |
### Placeholders
| # | File:Line | Type | Content |
### Consistency
| # | Issue | Fix |

---

### Systems Forensics

#### WebSocket Auth Lifecycle
| # | Severity | File:Line | Issue | Fix |

#### Ghost Routes
| # | Severity | File:Line | Issue | Fix |

#### Config Alias Deprecation
| # | Severity | File:Line | Issue | Fix |

#### Frontend WS Data Validation
| # | Severity | File:Line | Issue | Fix |

#### Token Refresh Race Conditions
| # | Severity | File:Line | Issue | Fix |

#### Test Module Docstrings
| # | File | Status | Fix |

### Summary
Runtime errors: N, Dead code: N, Integration issues: N, Placeholders: N, Consistency gaps: N
Forensics: WS auth: N, Ghost routes: N, Config aliases: N, WS validation: N, Token refresh: N, Test docstrings: N
```
