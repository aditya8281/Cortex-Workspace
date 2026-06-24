# V3 Backend: The Desktop

## Overview

V3 transforms Cortex from a Docker-dependent web service into a self-contained desktop application. Embedded databases replace Docker containers. Unix socket IPC replaces HTTP for local communication. System tray, notifications, and native file integration make it feel like a real desktop app.

## File Structure (V3 additions)

```
backend/app/
├── core/
│   ├── embedded/              # NEW: Embedded services
│   │   ├── __init__.py
│   │   ├── postgres.py        # User-space PostgreSQL lifecycle
│   │   ├── vectors.py         # In-process vector store (usearch/hnswlib)
│   │   ├── cache.py           # In-process cache (SQLite or in-memory)
│   │   └── lifecycle.py       # Start/stop/health all embedded services
│   ├── ipc/                   # NEW: Unix socket IPC
│   │   ├── __init__.py
│   │   ├── socket.py          # Unix socket server
│   │   └── protocol.py        # Message protocol (MessagePack)
│   ├── desktop/               # NEW: Desktop integration
│   │   ├── __init__.py
│   │   ├── notifications.py   # Native notification bridge
│   │   ├── file_dialogs.py    # Native file dialog bridge
│   │   ├── shortcuts.py       # Keyboard shortcut registry
│   │   ├── menus.py           # Context menu definitions
│   │   └── dragdrop.py        # Drag-and-drop handler
│   ├── backup/                # NEW: Data backup
│   │   ├── __init__.py
│   │   ├── exporter.py        # Full data export
│   │   └── importer.py        # Full data import
│   ├── monitoring/            # NEW: Performance monitoring
│   │   ├── __init__.py
│   │   ├── health.py          # System health dashboard data
│   │   └── metrics.py         # Performance metrics collection
│   └── offline/               # NEW: Offline mode
│       ├── __init__.py
│       └── manager.py         # Offline detection + degradation
├── services/
│   └── llm/
│       └── manager.py         # MODIFIED: offline fallback to local models
└── main.py                    # MODIFIED: parallel startup, embedded init
```

```
src-tauri/                      # NEW: Tauri project root
├── Cargo.toml
├── tauri.conf.json
├── src/
│   ├── main.rs                # Tauri entry point
│   └── lib.rs                 # Tauri commands (IPC handlers)
├── icons/
└── capabilities/
```

## Phase 1: Tauri Shell + Embedded DBs

### Tauri 2.x Configuration

```json
{
  "productName": "CORTEX",
  "identifier": "com.cortex.desktop",
  "build": {
    "frontendDist": "../frontend/out",
    "devUrl": "http://localhost:3000",
    "beforeDevCommand": "cd ../frontend && npm run dev",
    "beforeBuildCommand": "cd ../frontend && npm run build"
  },
  "app": {
    "windows": [{
      "title": "CORTEX",
      "width": 1200,
      "height": 800,
      "minWidth": 800,
      "minHeight": 600,
      "resizable": true,
      "decorations": true
    }],
    "trayIcon": {
      "iconPath": "icons/icon.png",
      "iconAsTemplate": true
    },
    "security": {
      "csp": null
    }
  }
}
```

### Embedded PostgreSQL

```python
class EmbeddedPostgres:
    """User-space PostgreSQL — no Docker required."""

    def __init__(self, data_dir: Path):
        self.data_dir = data_dir / "postgres"
        self.socket_dir = data_dir / "sockets"
        self.process: subprocess.Popen | None = None

    async def start(self) -> None:
        """Initialize and start PostgreSQL."""
        # Init database if not exists
        if not (self.data_dir / "PG_VERSION").exists():
            await self._init_db()

        # Start PostgreSQL
        self.process = await self._start_process()

        # Wait for ready
        await self._wait_for_ready(timeout=10)

    async def stop(self) -> None:
        """Graceful shutdown."""
        if self.process:
            self.process.terminate()
            await self._wait_for_exit(timeout=5)

    async def health(self) -> bool:
        """Check if PostgreSQL is accepting connections."""
        ...
```

### In-Process Vector Store

Using `usearch` (high-performance approximate nearest neighbor):
```python
class UsearchVectorStore:
    """In-process vector store — no Qdrant required."""

    def __init__(self, data_dir: Path):
        self.data_dir = data_dir / "vectors"
        self.indexes: dict[str, usearch.Index] = {}

    async def upsert(self, collection: str, vectors: list[Vector]) -> None:
        index = self._get_or_create_index(collection, dim=vectors[0].dim)
        index.add(vectors.ids, vectors.vectors)

    async def search(self, collection: str, query: list[float], top_k: int) -> list[SearchResult]:
        index = self._get_or_create_index(collection, dim=len(query))
        matches = index.search(query, top_k)
        return [SearchResult(id=m.id, score=m.distance) for m in matches]
```

### Unix Socket IPC

```python
class IPCServer:
    """Unix socket server for local IPC."""

    def __init__(self, socket_path: Path):
        self.socket_path = socket_path
        self.handlers: dict[str, Callable] = {}

    async def start(self) -> None:
        server = await asyncio.start_unix_server(self._handle_connection, path=self.socket_path)
        ...

    async def _handle_connection(self, reader, writer) -> None:
        while True:
            msg = await self._read_message(reader)
            response = await self._dispatch(msg)
            await self._write_message(writer, response)
```

## Phase 2: TUI + Notifications

### CLI TUI (Ink-based)

```
cortex tui                 → Full interactive TUI
cortex tui agent           → Agent chat only
cortex tui memory          → Memory browser only
cortex tui search          → Search interface only
```

Components rendered in terminal via Ink (React for CLIs):
- Agent: streaming chat with tool call visualization
- Memory: searchable list with category filters
- Search: query input + results with previews
- Status: system health, daemon status, model info

### Notification System

```python
class DesktopNotifier:
    """Bridge to Tauri notification API via IPC."""

    async def notify(self, title: str, body: str, category: str) -> None:
        await self.ipc.send("notification", {
            "title": title,
            "body": body,
            "category": category
        })
```

Events that trigger notifications:
- `agent_run_complete` → "Agent finished: [summary]"
- `memory_consolidation_complete` → "Memory updated: [N] new facts"
- `file_import_complete` → "File imported: [filename]"
- `background_task_error` → "Task failed: [error]"

## Phase 3: Performance + Polish

### Startup Optimization

Parallel initialization:
```
T=0.0s: Start PG process + init vector store + load config (parallel)
T=1.0s: PG ready → run migrations + init services
T=2.0s: Services ready → start IPC + HTTP servers
T=2.5s: Load Tauri webview
T=3.0s: App ready
```

### Memory Optimization

- PG connection pooling (max 5 connections)
- Vector index: memory-mapped, lazy-loaded per collection
- Cache: LRU with size limit
- HTTP server: only started as fallback (Unix socket primary)

### Offline Mode

```python
class OfflineManager:
    def __init__(self):
        self.is_online = True
        self.capabilities = {
            "local_llm": True,      # Always available
            "memory": True,          # Always available
            "graph": True,           # Always available
            "search": True,          # Always available (local indices)
            "vault": True,           # Always available
            "web_search": False,     # Requires internet
            "remote_mcp": False,     # Requires internet
            "external_llm": False,   # Requires internet
        }

    async def check_connectivity(self) -> None:
        self.is_online = await self._ping()
        for cap, requires_net in self._cap_requirements.items():
            if requires_net:
                self.capabilities[cap] = self.is_online
```

### Backup System

```bash
cortex backup create                    # Full backup
cortex backup create --vault            # Vault only
cortex backup create --memory           # Memory only
cortex backup restore backup-2026.tar   # Restore
cortex backup list                      # List backups
cortex backup schedule daily            # Auto-backup
```

Export format: tar archive containing:
- PG dump (SQL)
- Vector indices (binary)
- Vault files (encrypted)
- Config (JSON)

## Testing Strategy

| Test Category | Count Target | Approach |
|--------------|-------------|----------|
| Embedded PG lifecycle | 15+ | Start, stop, health, crash recovery |
| In-process vectors | 20+ | Insert, search, delete, persistence |
| Unix socket IPC | 20+ | Connect, request/response, error handling |
| TUI components | 30+ | Ink component rendering, user interaction |
| Notifications | 10+ | Event → notification mapping |
| Backup/restore | 15+ | Export, import, cross-version |
| Offline mode | 10+ | Capability degradation, reconnection |
| Performance | 10+ | Startup time, memory usage, IPC latency |
| **Total V3** | **130+** | |

## Performance Targets

- Cold start: < 3 seconds
- Idle memory: < 200MB
- Unix socket round-trip: < 5ms
- Vector search (in-process): < 10ms
- PG query (embedded): < 5ms
- Backup creation (100MB data): < 30s
- Backup restore: < 60s

## Platform-Specific Notes

| Platform | PG Binary | Vector Lib | Socket | Notes |
|----------|-----------|------------|--------|-------|
| Linux | apt/pg_ctl | usearch | Unix | Primary platform |
| macOS | brew/pg_ctl | usearch | Unix | Code signing required |
| Windows | bundled DLLs | usearch | Named pipe | Different IPC mechanism |
