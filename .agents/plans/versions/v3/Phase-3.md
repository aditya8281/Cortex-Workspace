# V3 Phase 3: Performance Optimization + Platform Polish

**Duration estimate:** 5-7 days
**Dependencies:** V3 Phase 1 (Tauri, embedded DBs), V3 Phase 2 (TUI, notifications)
**Risk:** Low — optimization and polish work

---

## Goals

Optimize startup time, memory usage, and IPC performance. Polish cross-platform behavior. Add offline mode. Add data export/import. Final testing and hardening for production desktop use.

## Deliverables

1. Startup time optimization (< 3s cold start)
2. Memory usage optimization (< 200MB idle)
3. IPC performance optimization (Unix socket < 5ms round-trip)
4. Offline mode (no internet required for core features)
5. Data export/import (backup, migrate between machines)
6. Cross-platform testing (Linux, macOS, Windows)
7. Crash reporting and recovery
8. Performance monitoring dashboard

## Architectural Changes

```
BEFORE:
  Startup = launch PG → wait → launch vectors → wait → start backend → wait → start frontend
  Memory = ~500MB+ idle (Docker + backend + frontend)
  IPC = HTTP (localhost:8000)

AFTER:
  Startup = parallel init (PG + vectors + backend + frontend) → < 3s
  Memory = < 200MB idle (embedded, no Docker)
  IPC = Unix socket (< 5ms) with HTTP fallback
  Offline = core features work without internet
```

## Backend Changes

### Modified Files

| File | Change |
|------|--------|
| `backend/app/core/embedded/lifecycle.py` | Parallel startup, health gating |
| `backend/app/core/embedded/postgres.py` | Connection pooling, WAL optimization |
| `backend/app/core/embedded/vectors.py` | Memory-mapped indices, lazy loading |
| `backend/app/core/ipc/socket.py` | Connection pooling, binary protocol |
| `backend/app/main.py` | Startup optimization, graceful degradation |
| `backend/app/core/config.py` | Offline mode settings |

### New Files

| File | Purpose |
|------|---------|
| `backend/app/core/backup/__init__.py` | Backup package |
| `backend/app/core/backup/exporter.py` | Data export (PG dump + vector snapshot) |
| `backend/app/core/backup/importer.py` | Data import (restore from backup) |
| `backend/app/core/monitoring/__init__.py` | Monitoring package |
| `backend/app/core/monitoring/health.py` | System health dashboard data |
| `backend/app/core/monitoring/metrics.py` | Performance metrics collection |
| `backend/app/core/offline/__init__.py` | Offline mode |
| `backend/app/core/offline/manager.py` | Offline detection + degradation |

### Startup Optimization

Parallel initialization:
```
Phase 1 (parallel):
  ├─ Start embedded PostgreSQL (user-space)
  ├─ Initialize in-process vector store
  └─ Load configuration

Phase 2 (after PG ready):
  ├─ Run migrations
  ├─ Initialize services
  └─ Start event bus

Phase 3 (after services ready):
  ├─ Start IPC server
  ├─ Start HTTP server (fallback)
  └─ Load Tauri webview
```

### Offline Mode

Core features without internet:
- Agent chat (local LLM only)
- Memory operations
- Graph operations
- Search (local indices)
- Vault operations

Features requiring internet:
- External LLM providers (OpenAI, Anthropic)
- MCP remote servers
- Web search
- File downloads

### Backup/Export

```bash
cortex backup create          # Full backup (PG + vectors + vault)
cortex backup create --vault  # Vault only
cortex backup restore <file>  # Restore from backup
cortex backup list            # List available backups
```

## Frontend Changes

| Page | Change |
|------|--------|
| Settings | New "Backup" section (create, restore, schedule) |
| Settings | New "Performance" section (startup time, memory usage, IPC stats) |
| Settings | New "Offline" indicator (green when online, yellow when offline) |
| Dashboard | Performance metrics panel (optional, for power users) |

## Memory Changes

No changes.

## Retrieval Changes

No changes.

## Agent Changes

Agent uses local LLM in offline mode. Falls back gracefully when external providers unavailable.

## Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Startup optimization breaks things | Low | High | Feature flag for parallel vs sequential startup. |
| Offline mode incomplete | Medium | Medium | Clear UI indicators for what works offline. |
| Backup corruption | Low | High | Checksums. Test restore regularly. Cross-version compatibility. |
| Platform-specific bugs | Medium | Medium | CI/CD on all 3 platforms. Automated testing. |

## Exit Criteria

- [ ] Cold start < 3 seconds
- [ ] Idle memory < 200MB
- [ ] Unix socket round-trip < 5ms
- [ ] Offline mode works (local LLM + memory + search)
- [ ] Backup create/restore works
- [ ] App tested on Linux, macOS, Windows
- [ ] Crash recovery works (PID file cleanup, data integrity)
- [ ] All V1-V3 tests pass
- [ ] `make lint` + `make format` clean
- [ ] Performance benchmarks documented
