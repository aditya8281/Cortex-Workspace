# V3 Phase 1: Tauri Desktop Shell + Embedded Database

**Duration estimate:** 10-14 days
**Dependencies:** V2 complete (service abstraction, MCP, memory)
**Risk:** HIGH — Tauri integration + embedded DB migration

---

## Goals

Create Tauri 2.x desktop shell that wraps the existing web frontend. Replace Docker PostgreSQL with embedded user-space PostgreSQL. Replace Docker Qdrant with in-process vector store. Desktop app feels native — system tray, global hotkey, window management.

## Deliverables

1. Tauri 2.x desktop application shell
2. Embedded PostgreSQL (user-space, no Docker required)
3. Embedded vector store (in-process, no Qdrant required)
4. System tray integration
5. Global hotkey (Ctrl+Shift+Space → command palette)
6. Window management (minimize to tray, always-on-top option)
7. Auto-update mechanism
8. Native file dialogs
9. Desktop notifications

## Architectural Changes

```
BEFORE:
  Backend = Docker (PG + Redis + Qdrant) + uvicorn
  Frontend = Next.js dev server
  Communication = HTTP (localhost:3000 → localhost:8000)

AFTER:
  Backend = Embedded PG + in-process vectors + embedded Redis (or in-memory)
  Frontend = Tauri webview (built Next.js)
  Communication = Unix socket (primary) + HTTP (fallback)
  Desktop = System tray, global hotkey, native menus
```

## Backend Changes

### New Files

| File | Purpose |
|------|---------|
| `backend/app/core/embedded/__init__.py` | Embedded services package |
| `backend/app/core/embedded/postgres.py` | User-space PostgreSQL lifecycle |
| `backend/app/core/embedded/vectors.py` | In-process vector store |
| `backend/app/core/embedded/redis.py` | In-process cache (or SQLite-based) |
| `backend/app/core/embedded/lifecycle.py` | Start/stop all embedded services |
| `backend/app/core/ipc/__init__.py` | IPC package |
| `backend/app/core/ipc/socket.py` | Unix socket server |
| `backend/app/core/ipc/protocol.py` | IPC message protocol |
| `backend/app/core/desktop/__init__.py` | Desktop integration |
| `backend/app/core/desktop/notifications.py` | Native notification bridge |
| `backend/app/core/desktop/file_dialogs.py` | Native file dialog bridge |
| `backend/app/core/desktop/tray.py` | System tray management |

### New Root Files

| File | Purpose |
|------|---------|
| `src-tauri/` | Tauri project root |
| `src-tauri/Cargo.toml` | Tauri Rust dependencies |
| `src-tauri/src/main.rs` | Tauri app entry point |
| `src-tauri/src/lib.rs` | Tauri commands (IPC handlers) |
| `src-tauri/tauri.conf.json` | Tauri configuration |
| `src-tauri/icons/` | App icons |

### Embedded PostgreSQL

User-space PostgreSQL (no Docker):
- Use `local-postgres` or embed PostgreSQL binary
- Data directory: `~/.cortex/data/postgres/`
- Port: dynamically assigned (or Unix socket)
- Startup: launch PG process on app start, wait for ready
- Shutdown: graceful shutdown on app exit
- Migration: run Alembic on startup (existing `bootstrap_database()`)

### Embedded Vector Store

Replace Qdrant with in-process:
- Option A: Use `hnswlib` for pure in-process vectors
- Option B: Use SQLite + `sqlite-vss` extension
- Option C: Use `usearch` (high-performance, in-process)
- Data directory: `~/.cortex/data/vectors/`
- Same Protocol[VectorStore] interface from V2

### Unix Socket IPC

Primary communication channel (replaces HTTP for local):
- Socket path: `~/.cortex/cortex.sock`
- Binary protocol (MessagePack or JSON)
- Request/response pattern with request IDs
- Fallback to HTTP for remote/API access
- Connection multiplexing

### Migration

No Alembic migration needed — embedded PG uses same schema. The migration is in the startup logic, not the database schema.

## Frontend Changes

### Tauri Integration

| Change | Detail |
|--------|--------|
| Tauri wrapper | Next.js app loaded in Tauri webview |
| Build config | `next build` → static output → Tauri bundles |
| API calls | Route through Tauri IPC or direct HTTP |
| File access | Tauri dialog APIs for file pickers |
| Notifications | Tauri notification API |
| System tray | Tauri tray API |

### No UI Changes

The web UI itself doesn't change in Phase 1. It runs inside Tauri's webview instead of a browser.

## Memory Changes

No changes. Memory consolidation (V2) is complete.

## Retrieval Changes

Vector store backend swaps from Qdrant to in-process. Protocol[VectorStore] abstraction from V2 makes this transparent.

## Agent Changes

No agent changes. Agent loop (V1) is stable.

## Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Embedded PG reliability | Medium | High | Thorough lifecycle management. Health checks. Auto-restart. |
| In-process vector quality | Medium | High | Benchmark against Qdrant. Fallback to Qdrant if quality drops. |
| Unix socket complexity | Low | Medium | Start with HTTP, add Unix socket as optimization. |
| Tauri build complexity | Medium | Medium | Follow Tauri 2.x recipes. Start with minimal shell. |
| Platform differences | Medium | Medium | Test on Linux, macOS, Windows. Abstract platform-specific code. |
| Data migration from Docker PG | Medium | High | Provide migration script. Support both modes during transition. |

## Exit Criteria

- [ ] Tauri app launches and shows existing web UI
- [ ] System tray icon appears with menu (Show, Quit)
- [ ] Global hotkey opens command palette (or window)
- [ ] Embedded PostgreSQL starts without Docker
- [ ] Embedded vector store works (search quality matches Qdrant)
- [ ] Unix socket IPC works (faster than HTTP for local)
- [ ] Window minimizes to tray
- [ ] Auto-update mechanism works
- [ ] All V1 + V2 tests pass
- [ ] New embedded service tests
- [ ] `make lint` + `make format` clean
- [ ] App builds for Linux, macOS, Windows
