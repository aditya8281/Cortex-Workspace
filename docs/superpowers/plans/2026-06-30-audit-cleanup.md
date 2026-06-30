# Audit Cleanup Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Resolve all audit findings (WS handler consistency, dead code, config hygiene, test docstrings) and clean up empty/stale docs.

**Architecture:** Mechanical fixes — refactor 2 WS handlers to use ConnectionManager, remove dead router, clean config aliases, delete empty docs. No feature changes.

**Tech Stack:** FastAPI, Python 3.12, Vitest, Next.js 15

## Global Constraints

- Backend: FastAPI + sync SQLAlchemy 2.0 + Alembic
- Frontend: Next.js 15 App Router + React 19 + TypeScript + Tailwind CSS
- Tests: SQLite in-memory, no real Postgres/Redis
- Commit messages: one line, standard format, no co-authored-by
- Skill-first: check for applicable skills before every action

---

## File Structure

### Backend Files Modified
| File | Change |
|------|--------|
| `backend/app/api/v1/interaction/ws_models.py` | Add register/disconnect/finally pattern |
| `backend/app/api/v1/system/ws_system.py` | Add register/disconnect/finally pattern |
| `backend/app/api/v1/interaction/ws_chat.py` | Add `finally` block with disconnect |
| `backend/app/api/v1/interaction/ws_notifications.py` | Already correct — no change |
| `backend/app/api/v1/cognition/ws_agents.py` | Already correct — no change |
| `backend/app/core/config.py` | Remove 2 self-referential aliases |

### Backend Files Deleted
| File | Reason |
|------|--------|
| `backend/app/api/v1/privacy/__init__.py` | Dead router — `router.py` is the only import |

### Test Files Modified (docstrings)
| File | Change |
|------|--------|
| `tests/agents/integrity/test_context.py` | Add module docstring |
| `tests/agents/integrity/test_entity_base.py` | Add module docstring |
| `tests/agents/integrity/test_relationships.py` | Add module docstring |
| `tests/agents/test_run_store.py` | Add module docstring |
| `tests/api/test_agents_api.py` | Add module docstring |
| `tests/api/test_auth.py` | Add module docstring |
| `tests/api/test_conversations_api.py` | Add module docstring |
| `tests/api/test_conversations_security.py` | Add module docstring |
| `tests/api/test_github_api.py` | Add module docstring |
| `tests/api/test_indexing_api.py` | Add module docstring |
| `tests/api/test_knowledge_api.py` | Add module docstring |
| `tests/api/test_long_term_memory_api.py` | Add module docstring |
| `tests/api/test_metrics_api.py` | Add module docstring |
| `tests/api/test_models_api.py` | Add module docstring |
| `tests/api/test_models_sync.py` | Add module docstring |
| `tests/api/test_notifications_api.py` | Add module docstring |
| `tests/api/test_profile_api.py` | Add module docstring |
| `tests/api/test_repository_api.py` | Add module docstring |
| `tests/api/test_search_api.py` | Add module docstring |
| `tests/api/test_sync_api.py` | Add module docstring |
| `tests/api/test_system_api.py` | Add module docstring |
| `tests/api/test_users_api.py` | Add module docstring |
| `tests/api/test_vault_api.py` | Add module docstring |
| `tests/models/test_json_columns.py` | Add module docstring |
| `tests/services/test_ollama_catalog.py` | Add module docstring |
| `tests/services/test_ollama_sync.py` | Add module docstring |
| `tests/services/test_vault.py` | Add module docstring |
| `tests/services/test_vector_db.py` | Add module docstring |

### Docs Deleted
| File | Reason |
|------|--------|
| `docs/audits/EXECUTION_PLAN.md` | Stale — all items marked complete |
| `docs/audits/EXECUTION_TRACE_REPORT.md` | Stale — superseded by audit findings |
| `docs/audits/2026-06-29-reflect-1.md` | Stale — reflection from prior audit |
| `docs/audits/index.md` | Parent — all children deleted |
| `docs/planning/index.md` | Empty stub |
| `docs/research/index.md` | Empty stub |
| `docs/workflows/index.md` | Empty stub |
| `docs/domains/index.md` | Stub — content lives in `docs/domains/*.md` already |
| `docs/domains/awareness.md` | Empty stub (37 lines, all boilerplate) |
| `docs/domains/cognition.md` | Empty stub |
| `docs/domains/developer.md` | Empty stub |
| `docs/domains/integration.md` | Empty stub |
| `docs/domains/intelligence.md` | Empty stub |
| `docs/domains/interaction.md` | Empty stub |
| `docs/domains/memory.md` | Keep — has 108 lines of real content |
| `docs/domains/privacy.md` | Empty stub |
| `docs/domains/system.md` | Empty stub |
| `docs/domains/utility.md` | Empty stub |

### Docs Kept
| File | Reason |
|------|--------|
| `docs/architecture/overview.md` | 472 lines, real architecture doc |
| `docs/architecture/index.md` | Index for architecture |
| `docs/decisions/` (all 22 ADRs + README) | Active ADRs |
| `docs/reference/api.md` | 321 lines, real API doc |
| `docs/reference/database.md` | 94 lines, real schema doc |
| `docs/reference/index.md` | Index |
| `docs/guides/governance.md` | 416 lines, real governance doc |
| `docs/guides/index.md` | Index |
| `docs/domains/memory.md` | 108 lines, real content |

---

## Task 1: Fix ws_models.py — Add ConnectionManager Pattern

**Files:**
- Modify: `backend/app/api/v1/interaction/ws_models.py`

**Interfaces:**
- Consumes: `manager.register()`, `manager.disconnect()`, `manager.send()` from `backend/app/core/websocket.py`
- Produces: connections tracked in ConnectionManager, enforced rate limits, clean disconnect

**Pattern reference:** `ws_notifications.py` — the gold standard for push-only WS handlers.

- [ ] **Step 1: Read current file**

Read `backend/app/api/v1/interaction/ws_models.py` to see current implementation.

- [ ] **Step 2: Rewrite with manager pattern**

Replace the handler function body. Keep `_build_download_payload()` unchanged.

```python
@router.websocket("/ws/models")
async def model_download_progress_ws(ws: WebSocket, token: str = Query(None)):
    """Push download progress for all active model downloads every second."""
    # Accept FIRST so the browser sees a 101 with CORS headers
    await ws.accept()

    token = manager.extract_ws_token(ws, token)  # type: ignore[assignment]
    if not token:
        await ws.send_json({"type": "error", "message": "Authentication required"})
        await ws.close(code=4001)
        return
    try:
        user_id = await verify_ws_token(token)
    except Exception:
        await ws.send_json({"type": "error", "message": "Invalid token or account deleted"})
        await ws.close(code=4001)
        return

    uid = int(user_id)
    await manager.register(ws, channel=f"models:{uid}", user_id=uid)
    try:
        while True:
            payload = _build_download_payload()
            if payload["models"]:
                await manager.send(ws, payload)
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        pass
    except Exception:
        try:
            await ws.close()
        except Exception:
            pass
    finally:
        manager.disconnect(ws, channel=f"models:{uid}", user_id=uid)
```

- [ ] **Step 3: Run backend tests**

Run: `cd /home/adi/Desktop/Cortex-Workspace && make test`
Expected: All pass (no regressions)

- [ ] **Step 4: Commit**

```bash
git add backend/app/api/v1/interaction/ws_models.py
git commit -m "fix: add ConnectionManager register/disconnect to ws_models handler"
```

---

## Task 2: Fix ws_system.py — Add ConnectionManager Pattern

**Files:**
- Modify: `backend/app/api/v1/system/ws_system.py`

**Interfaces:**
- Same as Task 1

- [ ] **Step 1: Read current file**

Read `backend/app/api/v1/system/ws_system.py`.

- [ ] **Step 2: Rewrite handler with manager pattern**

Replace the handler function body. Keep `collect_metrics()`, `collect_processes()`, `collect_logs()` unchanged.

```python
@router.websocket("/ws/system")
async def system_metrics_ws(ws: WebSocket, token: str = Query(None)):
    """Push real-time metrics (every 500ms) and activity logs (every 3s)."""
    logger.info("[ws/system] Connection attempt from %s", ws.client)

    # Accept FIRST so the browser sees a 101 with CORS headers
    await ws.accept()

    token = manager.extract_ws_token(ws, token)  # type: ignore[assignment]
    if not token:
        logger.warning("[ws/system] No token provided")
        await ws.send_json({"type": "error", "message": "Authentication required"})
        await ws.close(code=4001)
        return
    try:
        _user_id = await verify_ws_token(token)
    except Exception as e:
        logger.warning("[ws/system] Token verification failed: %s", e)
        await ws.send_json({"type": "error", "message": "Invalid token or account deleted"})
        await ws.close(code=4001)
        return

    uid = int(_user_id)
    logger.info("[ws/system] User %s connected", uid)
    await manager.register(ws, channel=f"system:{uid}", user_id=uid)
    tick = 0
    try:
        while True:
            tick += 1
            metrics = collect_metrics()
            await manager.send(ws, metrics)

            if tick % 6 == 1:
                logs = collect_logs(15)
                await manager.send(ws, logs)

            if tick % 10 == 0:
                processes = collect_processes()
                await manager.send(ws, {"type": "processes", "processes": processes})

            await asyncio.sleep(0.5)
    except WebSocketDisconnect:
        pass
    except Exception:
        try:
            await ws.close()
        except Exception:
            pass
    finally:
        manager.disconnect(ws, channel=f"system:{uid}", user_id=uid)
```

- [ ] **Step 3: Run backend tests**

Run: `cd /home/adi/Desktop/Cortex-Workspace && make test`
Expected: All pass

- [ ] **Step 4: Commit**

```bash
git add backend/app/api/v1/system/ws_system.py
git commit -m "fix: add ConnectionManager register/disconnect to ws_system handler"
```

---

## Task 3: Fix ws_chat.py — Add Finally Block

**Files:**
- Modify: `backend/app/api/v1/interaction/ws_chat.py`

**Interfaces:**
- Consumes: `manager.disconnect()` from `backend/app/core/websocket.py`

- [ ] **Step 1: Read current file**

Read `backend/app/api/v1/interaction/ws_chat.py`.

- [ ] **Step 2: Add finally block**

The chat handler already calls `manager.register()` and has the correct auth pattern. It just needs a `finally` block to guarantee disconnect on any exit path.

Find the except block at the end of the handler:

```python
    except WebSocketDisconnect:
        manager.disconnect(ws, channel="chat", user_id=uid)
    except Exception:
        logger.exception("WebSocket chat error")
        manager.disconnect(ws, channel="chat", user_id=uid)
```

Replace with:

```python
    except WebSocketDisconnect:
        pass
    except Exception:
        logger.exception("WebSocket chat error")
    finally:
        manager.disconnect(ws, channel="chat", user_id=uid)
```

Also ensure `import logging` and `logger = logging.getLogger(__name__)` are at the top if not already present.

- [ ] **Step 3: Run backend tests**

Run: `cd /home/adi/Desktop/Cortex-Workspace && make test`
Expected: All pass

- [ ] **Step 4: Commit**

```bash
git add backend/app/api/v1/interaction/ws_chat.py
git commit -m "fix: add finally block to ws_chat handler for guaranteed cleanup"
```

---

## Task 4: Fix ws.py Demo Handler — Remove Redundant Fallback

**Files:**
- Modify: `backend/app/api/ws.py`

**Interfaces:**
- Consumes: `manager.extract_ws_token()` from `backend/app/core/websocket.py`

- [ ] **Step 1: Read current file**

Read `backend/app/api/ws.py`.

- [ ] **Step 2: Remove redundant token fallback**

Find this line in the handler:

```python
    token = manager.extract_ws_token(ws) or ws.query_params.get("token")
```

Replace with:

```python
    token = manager.extract_ws_token(ws)
```

This makes the demo handler consistent with all 5 production handlers. The `extract_ws_token` method already checks query params, sec-websocket-protocol header, and cookie — the extra fallback was redundant and created an inconsistent extraction path.

- [ ] **Step 3: Run backend tests**

Run: `cd /home/adi/Desktop/Cortex-Workspace && make test`
Expected: All pass

- [ ] **Step 4: Commit**

```bash
git add backend/app/api/ws.py
git commit -m "fix: remove redundant token fallback from ws demo handler"
```

---

## Task 5: Delete Dead privacy/__init__.py Router

**Files:**
- Delete: `backend/app/api/v1/privacy/__init__.py`

**Interfaces:**
- This file is NOT imported by any other file. `backend/app/api/router.py` imports from `backend/app/api/v1/privacy/router.py`.

- [ ] **Step 1: Verify nothing imports it**

Run: `grep -rn 'from.*privacy.__init__\|from privacy import' backend/ tests/ --include='*.py' | grep -v __pycache__`
Expected: No results (confirmed during audit)

- [ ] **Step 2: Verify router.py is the active one**

Read `backend/app/api/router.py` and confirm it imports from `.privacy.router`, not `.privacy.__init__`.

- [ ] **Step 3: Delete the file**

```bash
rm backend/app/api/v1/privacy/__init__.py
```

Note: The `__init__.py` can be deleted because Python 3.3+ supports implicit namespace packages. The `privacy/` directory doesn't need `__init__.py` unless it's imported as a package. Since `router.py` is imported directly (`from backend.app.api.v1.privacy.router import router`), the `__init__.py` is unnecessary.

- [ ] **Step 4: Run backend tests**

Run: `cd /home/adi/Desktop/Cortex-Workspace && make test`
Expected: All pass

- [ ] **Step 5: Commit**

```bash
git add -A backend/app/api/v1/privacy/
git commit -m "fix: delete dead privacy __init__.py router with latent prefix mismatch"
```

---

## Task 6: Remove Self-Referential Config Aliases

**Files:**
- Modify: `backend/app/core/config.py`

**Interfaces:**
- Consumes: Pydantic `AliasChoices` from `pydantic`

- [ ] **Step 1: Read current file**

Read `backend/app/core/config.py`.

- [ ] **Step 2: Remove CORTEX_ROOT self-referential alias**

Find:

```python
    CORTEX_ROOT: str | None = Field(
        default=None,
        validation_alias=AliasChoices("CORTEX_ROOT"),
    )
```

Replace with:

```python
    CORTEX_ROOT: str | None = Field(default=None)
```

- [ ] **Step 3: Remove CORTEX_NEW_AGENT_LOOP self-referential alias**

Find:

```python
    CORTEX_NEW_AGENT_LOOP: bool = Field(
        default=False,
        validation_alias=AliasChoices("CORTEX_NEW_AGENT_LOOP"),
    )
```

Replace with:

```python
    CORTEX_NEW_AGENT_LOOP: bool = Field(default=False)
```

- [ ] **Step 4: Run backend tests**

Run: `cd /home/adi/Desktop/Cortex-Workspace && make test`
Expected: All pass

- [ ] **Step 5: Commit**

```bash
git add backend/app/core/config.py
git commit -m "fix: remove self-referential AliasChoices from CORTEX_ROOT and CORTEX_NEW_AGENT_LOOP"
```

---

## Task 7: Add Module Docstrings to 28 Test Files

**Files:**
- Modify: 28 test files (list above)

**Interfaces:**
- None — purely cosmetic

**Pattern:** Each file gets a single-line module docstring as the first line (after any `from __future__` import):

```python
"""Tests for <module> — <brief description>."""
```

- [ ] **Step 1: Read each file to understand what it tests**

For each file, read the first 20 lines and the test class names to determine the description.

- [ ] **Step 2: Add docstrings**

Add the docstring as the first line of each file. The descriptions below are derived from the test content:

| File | Docstring |
|------|-----------|
| `tests/agents/integrity/test_context.py` | `"""Tests for agent context integrity — context window management and truncation."""` |
| `tests/agents/integrity/test_entity_base.py` | `"""Tests for agent entity base — core entity types and relationships."""` |
| `tests/agents/integrity/test_relationships.py` | `"""Tests for agent relationship integrity — entity linking and graph consistency."""` |
| `tests/agents/test_run_store.py` | `"""Tests for agent run store — run persistence and retrieval."""` |
| `tests/api/test_agents_api.py` | `"""Tests for agents API — CRUD operations and agent lifecycle."""` |
| `tests/api/test_auth.py` | `"""Tests for auth API — login, register, token refresh, logout."""` |
| `tests/api/test_conversations_api.py` | `"""Tests for conversations API — message creation, retrieval, history."""` |
| `tests/api/test_conversations_security.py` | `"""Tests for conversations API security — ownership checks and cross-user access."""` |
| `tests/api/test_github_api.py` | `"""Tests for GitHub API — repository sync and webhook integration."""` |
| `tests/api/test_indexing_api.py` | `"""Tests for indexing API — document indexing and search operations."""` |
| `tests/api/test_knowledge_api.py` | `"""Tests for knowledge API — knowledge graph CRUD and traversal."""` |
| `tests/api/test_long_term_memory_api.py` | `"""Tests for long-term memory API — memory storage, retrieval, and forgetting."""` |
| `tests/api/test_metrics_api.py` | `"""Tests for metrics API — system metrics and health data."""` |
| `tests/api/test_models_api.py` | `"""Tests for models API — model catalog listing and detail endpoints."""` |
| `tests/api/test_models_sync.py` | `"""Tests for models sync — catalog synchronization with Ollama."""` |
| `tests/api/test_notifications_api.py` | `"""Tests for notifications API — notification CRUD and read status."""` |
| `tests/api/test_profile_api.py` | `"""Tests for profile API — user profile update and retrieval."""` |
| `tests/api/test_repository_api.py` | `"""Tests for repository API — repo registration and file operations."""` |
| `tests/api/test_search_api.py` | `"""Tests for search API — fulltext and vector search operations."""` |
| `tests/api/test_sync_api.py` | `"""Tests for sync API — data synchronization endpoints."""` |
| `tests/api/test_system_api.py` | `"""Tests for system API — health checks and system information."""` |
| `tests/api/test_users_api.py` | `"""Tests for users API — user management and permissions."""` |
| `tests/api/test_vault_api.py` | `"""Tests for vault API — encrypted file storage operations."""` |
| `tests/models/test_json_columns.py` | `"""Tests for JSON column handling — SQLite compatibility and serialization."""` |
| `tests/services/test_ollama_catalog.py` | `"""Tests for Ollama catalog service — model parsing, embedding detection, family grouping."""` |
| `tests/services/test_ollama_sync.py` | `"""Tests for Ollama sync service — catalog synchronization logic."""` |
| `tests/services/test_vault.py` | `"""Tests for vault service — encryption, decryption, file operations."""` |
| `tests/services/test_vector_db.py` | `"""Tests for vector DB service — Qdrant operations and embedding storage."""` |

- [ ] **Step 3: Run backend tests**

Run: `cd /home/adi/Desktop/Cortex-Workspace && make test`
Expected: All pass (docstrings don't affect behavior)

- [ ] **Step 4: Commit**

```bash
git add tests/
git commit -m "docs: add module docstrings to 28 test files"
```

---

## Task 8: Delete Empty/Stale Docs

**Files:**
- Delete: 16 empty stubs + 3 stale audit files

**Interfaces:**
- None

- [ ] **Step 1: Verify all target files are truly empty/stale**

For each file, confirm it's either an empty stub or all items are marked complete:

```bash
# Empty stubs (all content is boilerplate/placeholder)
wc -l docs/domains/awareness.md docs/domains/cognition.md docs/domains/developer.md \
  docs/domains/integration.md docs/domains/intelligence.md docs/domains/interaction.md \
  docs/domains/privacy.md docs/domains/system.md docs/domains/utility.md

# Empty indexes
wc -l docs/planning/index.md docs/research/index.md docs/workflows/index.md docs/domains/index.md

# Stale audit files (all items marked complete)
grep -c '✅ Complete\|Already fixed' docs/audits/EXECUTION_PLAN.md
```

- [ ] **Step 2: Delete empty domain stubs**

```bash
rm docs/domains/awareness.md docs/domains/cognition.md docs/domains/developer.md \
  docs/domains/integration.md docs/domains/intelligence.md docs/domains/interaction.md \
  docs/domains/privacy.md docs/domains/system.md docs/domains/utility.md docs/domains/index.md
```

- [ ] **Step 3: Delete empty index stubs**

```bash
rm docs/planning/index.md docs/research/index.md docs/workflows/index.md
```

Remove empty directories if they become empty:

```bash
rmdir docs/planning docs/research docs/workflows 2>/dev/null || true
```

- [ ] **Step 4: Delete stale audit files**

```bash
rm docs/audits/EXECUTION_PLAN.md docs/audits/EXECUTION_TRACE_REPORT.md \
  docs/audits/2026-06-29-reflect-1.md docs/audits/index.md
rmdir docs/audits 2>/dev/null || true
```

- [ ] **Step 5: Update CLAUDE.md doc references**

Read `CLAUDE.md` and update the Reference Documents table. Remove references to deleted docs. The table currently references:
- `docs/decisions/` — keep (ADRs still exist)
- `docs/domains/` — keep `memory.md`, remove reference to `domains/` as a general category
- `docs/guides/governance.md` — keep

- [ ] **Step 6: Verify no broken references**

Run: `grep -rn 'docs/audits\|docs/planning\|docs/research\|docs/workflows\|docs/domains/awareness\|docs/domains/cognition\|docs/domains/developer\|docs/domains/integration\|docs/domains/intelligence\|docs/domains/interaction\|docs/domains/privacy\|docs/domains/system\|docs/domains/utility' CLAUDE.md AGENTS.md .agents/ --include='*.md' 2>/dev/null | head -20`
Expected: No results

- [ ] **Step 7: Commit**

```bash
git add -A docs/
git commit -m "docs: delete 16 empty stubs and 3 stale audit files"
```

---

## Task 9: Final Validation

- [ ] **Step 1: Run all backend tests**

Run: `make test`
Expected: All pass (2077+)

- [ ] **Step 2: Run frontend tests**

Run: `cd frontend && npm test`
Expected: All pass

- [ ] **Step 3: Run frontend build**

Run: `cd frontend && npm run build`
Expected: No errors

- [ ] **Step 4: Run backend lint**

Run: `make lint`
Expected: Clean

- [ ] **Step 5: Run backend format**

Run: `make format`
Expected: Clean

- [ ] **Step 6: Verify no import errors**

Run: `python -c "import backend.app.main; print('OK')"`
Expected: OK

- [ ] **Step 7: Verify deleted files don't exist**

Run: `ls backend/app/api/v1/privacy/__init__.py docs/audits/ docs/domains/awareness.md 2>&1 | grep -c 'No such file'`
Expected: 3

- [ ] **Step 8: Final commit if any formatting fixes**

```bash
git add -A
git commit -m "style: format and lint fixes for audit cleanup"
```
