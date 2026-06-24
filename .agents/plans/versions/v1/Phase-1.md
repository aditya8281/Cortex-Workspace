# V1 Phase 1: Daemon Foundation

**Duration estimate:** 3-5 days
**Dependencies:** None (starts from current codebase)
**Risk:** Low — wrapping existing code in lifecycle management

---

## Goals

Extract a `cortexd` entrypoint from the existing FastAPI app. Add PID management, health checks, graceful shutdown, and sleep/wake. The web UI continues working exactly as before. No user-visible changes — only internal decoupling.

## Deliverables

1. `cortexd` CLI entrypoint (Python click/typer)
2. PID file management with stale detection
3. Health check system (DB, Redis, Qdrant probing)
4. Graceful shutdown (drain in-flight, flush state)
5. Sleep/wake lifecycle
6. All existing tests pass unchanged

## Architectural Changes

```
BEFORE:
  make dev → uvicorn backend.app.main:app

AFTER:
  cortexd start → PID file → uvicorn (same app) → health checks → lifecycle hooks
  cortexd stop → signal handler → graceful shutdown → PID cleanup
  cortexd status → read PID file → probe health → report
```

The daemon is the existing FastAPI app wrapped in lifecycle management. Zero business logic changes.

## Backend Changes

### New Files

| File | Purpose |
|------|---------|
| `backend/app/daemon/__init__.py` | Package init |
| `backend/app/daemon/cli.py` | `cortexd` CLI entrypoint (click/typer): start, stop, status, logs |
| `backend/app/daemon/lifecycle.py` | Lifecycle manager: startup hooks, shutdown hooks, state flush |
| `backend/app/daemon/pid.py` | PID file management: create, read, validate, cleanup stale |
| `backend/app/daemon/health.py` | Health checks: DB connectivity, Redis connectivity, Qdrant connectivity |
| `backend/app/daemon/sleep.py` | Sleep/wake: idle detection, sleep mode, wake on trigger |
| `backend/app/daemon/signals.py` | Signal handlers: SIGTERM, SIGINT, SIGHUP |

### Modified Files

| File | Change |
|------|--------|
| `backend/app/main.py` | Add `create_daemon_app()` factory that returns FastAPI app + lifecycle hooks. Keep existing `app` for backward compatibility. |
| `Makefile` | Add `make daemon` target: `cortexd start` |
| `pyproject.toml` | Add click/typer dependency. Add `[project.scripts] cortexd = "backend.app.daemon.cli:main"` |

### Implementation Details

**PID Management (`pid.py`):**
- PID file at `~/.cortex/cortexd.pid`
- On start: check if PID exists, if process alive → refuse (already running). If stale → cleanup and proceed.
- On shutdown: remove PID file.
- PID file contains: PID, start timestamp, version.

**Health Checks (`health.py`):**
- Probe DB: `SELECT 1` via SQLAlchemy
- Probe Redis: `PING` via redis wrapper (graceful if None)
- Probe Qdrant: `GET /collections` (graceful if unavailable)
- Health endpoint: `GET /api/v1/health/live` (existing) + `GET /api/v1/health/ready` (new, returns dependency status)
- Periodic check: background task every 30s, logs warnings on failure.

**Sleep/Wake (`sleep.py`):**
- Configurable idle timeout (default: 15 minutes)
- Idle detection: timestamp of last API request, last user message, last background job
- On sleep: pause background tasks, release non-essential connections, reduce logging
- On wake: resume background tasks, reconnect, catch up on missed events
- Wake triggers: API call, CLI command, file change, webhook

**Graceful Shutdown (`signals.py`):**
- SIGTERM/SIGINT: set shutdown flag, drain in-flight requests (30s timeout), flush state, close connections, remove PID file, exit
- SIGHUP: reload configuration (re-read env vars, re-connect if needed)

**CLI (`cli.py`):**
```
cortexd start [--daemon] [--config PATH]   # Start daemon (daemonize or foreground)
cortexd stop                                # Graceful stop
cortexd status                              # Health + dependency status
cortexd logs [--tail N] [--follow]          # View daemon logs
cortexd restart                             # Stop + start
```

## Frontend Changes

**No frontend changes in this phase.** Web UI continues working exactly as before. The daemon is an internal restructuring.

## Memory Changes

**No memory changes.** Existing memory system unchanged.

## Retrieval Changes

**No retrieval changes.** Existing hybrid retrieval unchanged.

## Agent Changes

**No agent changes in this phase.** Agent loop rebuild is Phase 2.

## Dependencies

| Dependency | Action |
|-----------|--------|
| click or typer | Add to pyproject.toml |
| Existing FastAPI app | Preserved unchanged |
| PostgreSQL | Still required (Docker or user-space) |
| Redis | Still required (Docker or in-memory fallback) |
| Qdrant | Still required (Docker) |

## Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Daemonize complexity | Low | Medium | Start with foreground mode. Daemonize later. |
| Sleep/wake edge cases | Medium | Low | Simple idle timeout first. Complex triggers deferred. |
| Signal handling on Windows | Medium | Low | SIGTERM not available on Windows. Use platform-specific handling. |
| PID file races | Low | Low | Atomic write + stale detection |

## Exit Criteria

- [ ] `cortexd start` launches daemon in foreground
- [ ] `cortexd stop` gracefully shuts down (drains in-flight, removes PID)
- [ ] `cortexd status` reports health of DB, Redis, Qdrant
- [ ] `cortexd logs` shows daemon output
- [ ] PID file created on start, removed on stop
- [ ] Stale PID detection works (kill daemon externally, restart)
- [ ] Health endpoint `/api/v1/health/ready` returns dependency status
- [ ] Sleep after idle timeout works
- [ ] Wake on API call works
- [ ] All 341+ existing tests pass
- [ ] Web UI unchanged
- [ ] `make lint` + `make format` clean
