# CORTEX Desktop-First Reorientation — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Transform CORTEX from a browser-first web application into a daemon-centric intelligence platform with multiple interfaces.

**Architecture:** The current FastAPI backend becomes the kernel of a background daemon (`cortexd`). Services get clean abstraction boundaries. An event bus decouples communication. A dedicated job system manages background work. The CLI becomes a first-class interface. A Tauri desktop shell replaces the browser as the primary surface. The web UI becomes a secondary access point.

**Tech Stack:** Python 3.12+, FastAPI, SQLAlchemy 2.0, Alembic, PostgreSQL 16 (embedded or Docker), Qdrant, Redis (optional), TypeScript/Commander.js (CLI), Tauri/Rust (desktop shell), ONNX Runtime (embeddings).

## Global Constraints

- All daemon code lives in `backend/app/` — no separate daemon repository
- Existing tests must pass after every phase — no regressions
- Service abstractions use Python Protocol classes (PEP 544)
- Event bus is in-process only (no external broker dependency)
- Job system uses SQLite for persistence (lightweight, no extra infra)
- CLI connects to daemon via HTTP (existing FastAPI endpoints)
- Desktop shell uses Tauri v2 (Rust backend, web frontend)
- API endpoints stay under `/api/v1/` — versioning is about contract stability, not URL changes
- All new code follows existing patterns: constructor injection, factory functions, Pydantic schemas
- TDD: write failing test first, implement, verify pass, commit

---

## File Structure

### Phase 1: Daemon Foundation

```
backend/app/
├── daemon/
│   ├── __init__.py
│   ├── cli.py              # Daemon CLI (start/stop/status/restart)
│   ├── lifecycle.py         # Startup/shutdown/sleep/wake orchestration
│   ├── health.py            # Health monitoring + dependency checks
│   └── config.py            # Daemon-specific config (PID file, sockets, etc.)
├── main.py                  # MODIFY: extract app creation, keep lifespan
├── core/
│   ├── config.py            # MODIFY: add daemon settings
│   └── pid.py               # CREATE: PID file management

tests/
├── daemon/
│   ├── __init__.py
│   ├── test_cli.py
│   ├── test_lifecycle.py
│   └── test_health.py
```

### Phase 2: Service Abstraction

```
backend/app/
├── services/
│   ├── abstraction/
│   │   ├── __init__.py
│   │   ├── base.py          # Protocol classes for all services
│   │   ├── database.py      # DatabaseProvider Protocol
│   │   ├── vector_store.py  # VectorStoreProvider Protocol
│   │   ├── cache.py         # CacheProvider Protocol
│   │   ├── llm.py           # LLMProvider Protocol (extend existing)
│   │   └── embedding.py     # EmbeddingProvider Protocol (extend existing)
│   ├── providers/
│   │   ├── __init__.py
│   │   ├── postgres.py      # PostgreSQL implementation
│   │   ├── sqlite.py        # SQLite fallback implementation
│   │   ├── qdrant_provider.py  # Qdrant implementation
│   │   ├── memory_cache.py  # In-memory cache implementation
│   │   └── redis_cache.py   # Redis cache implementation
│   └── registry.py          # Service registry (get/set providers)
├── core/
│   └── provider_loader.py   # Load provider from config

tests/
├── services/
│   ├── test_abstraction.py
│   └── test_providers.py
```

### Phase 3: Event Bus & Job System

```
backend/app/
├── core/
│   ├── events/
│   │   ├── __init__.py
│   │   ├── bus.py           # In-process event bus
│   │   ├── types.py         # Event type definitions
│   │   └── tracing.py       # Event tracing for observability
│   └── jobs/
│       ├── __init__.py
│       ├── engine.py         # Job execution engine
│       ├── queue.py          # Job queue with persistence
│       ├── models.py         # Job state models
│       └── observers.py      # Job event observers (tracing, metrics)
├── services/
│   └── knowledge_graph.py   # MODIFY: extract as explicit service boundary

tests/
├── core/
│   ├── test_events.py
│   └── test_jobs.py
```

### Phase 4: CLI Completion

```
cli/
├── src/
│   ├── index.ts              # MODIFY: add daemon-aware commands
│   ├── commands/
│   │   ├── search.ts         # IMPLEMENT: cortex search
│   │   ├── remember.ts       # IMPLEMENT: cortex remember
│   │   ├── memory.ts         # IMPLEMENT: cortex memory (list/get/delete)
│   │   ├── status.ts         # IMPLEMENT: cortex status (daemon + services)
│   │   ├── agent.ts          # IMPLEMENT: cortex agent (run/list)
│   │   ├── config.ts         # IMPLEMENT: cortex config (get/set/list)
│   │   ├── index.ts          # IMPLEMENT: cortex index (repo management)
│   │   ├── conversation.ts   # IMPLEMENT: cortex conversation
│   │   ├── model.ts          # IMPLEMENT: cortex model (list/install)
│   │   ├── vault.ts          # IMPLEMENT: cortex vault
│   │   ├── health.ts         # IMPLEMENT: cortex health
│   │   ├── start.ts          # MODIFY: connect to daemon lifecycle
│   │   ├── stop.ts           # MODIFY: connect to daemon lifecycle
│   │   ├── doctor.ts         # IMPLEMENT: cortex doctor
│   │   └── logs.ts           # IMPLEMENT: cortex logs
│   ├── client/
│   │   ├── api.ts            # HTTP client for daemon API
│   │   └── types.ts          # TypeScript types matching backend schemas
│   └── utils/
│       ├── output.ts         # Formatting, colors, tables
│       └── auth.ts           # Token management

tests/
├── cli/
│   ├── search.test.ts
│   ├── remember.test.ts
│   ├── status.test.ts
│   └── ...
```

### Phase 5: API Stabilization

```
docs/
├── API.md                    # REWRITE: comprehensive API documentation
├── PLUGIN.md                 # CREATE: plugin/extension authoring guide
└── MIGRATION.md              # CREATE: deprecation policy + migration paths

backend/app/
├── api/
│   ├── v1/
│   │   └── router.py         # MODIFY: add deprecation headers
│   └── middleware/
│       └── deprecation.py    # CREATE: deprecation warning middleware
```

### Phase 6: Desktop Shell

```
desktop/
├── src-tauri/
│   ├── Cargo.toml
│   ├── tauri.conf.json
│   ├── src/
│   │   ├── main.rs           # Tauri app entry
│   │   ├── daemon.rs         # Daemon lifecycle management
│   │   ├── tray.rs           # System tray
│   │   ├── hotkey.rs         # Global hotkey
│   │   └── notifications.rs  # System notifications
│   └── capabilities/
├── src/
│   ├── App.tsx               # Main app shell
│   ├── components/
│   │   ├── TrayMenu.tsx
│   │   ├── CommandPalette.tsx
│   │   ├── MemoryBrowser.tsx
│   │   └── Settings.tsx
│   └── hooks/
│       ├── useDaemon.ts
│       └── useHotkey.ts
└── package.json

tests/
├── desktop/
│   ├── tray.test.ts
│   ├── hotkey.test.ts
│   └── notifications.test.ts
```

### Phase 7: Web UI Transition

No new files — scope reduction only. Document in `docs/WEB_UI.md` what's maintained vs. deprecated.

---

## Phase 1: Daemon Foundation

### Task 1.1: Daemon CLI Entry Point

**Files:**
- Create: `backend/app/daemon/__init__.py`
- Create: `backend/app/daemon/cli.py`
- Create: `tests/daemon/__init__.py`
- Create: `tests/daemon/test_cli.py`

**Interfaces:**
- Consumes: `backend.app.main:app` (FastAPI app instance)
- Produces: `daemon.cli.main()` — CLI entry point for `cortexd`

- [ ] **Step 1: Create daemon package**

```python
# backend/app/daemon/__init__.py
"""CORTEX daemon — background intelligence layer."""
```

- [ ] **Step 2: Create daemon CLI module**

```python
# backend/app/daemon/cli.py
"""Daemon CLI — start/stop/status/restart cortexd."""
import sys
import signal
import subprocess
from pathlib import Path

PID_FILE = Path.home() / ".cortex" / "daemon.pid"
SOCKET_FILE = Path.home() / ".cortex" / "daemon.sock"


def get_pid() -> int | None:
    """Read PID from file, return None if not running."""
    if not PID_FILE.exists():
        return None
    try:
        pid = int(PID_FILE.read_text().strip())
        # Check if process is actually running
        os.kill(pid, 0)
        return pid
    except (ValueError, ProcessLookupError, PermissionError):
        PID_FILE.unlink(missing_ok=True)
        return None


def start_daemon(host: str = "127.0.0.1", port: int = 8000) -> None:
    """Start cortexd as a background process."""
    if get_pid() is not None:
        print("Daemon already running")
        sys.exit(1)

    PID_FILE.parent.mkdir(parents=True, exist_ok=True)

    # Start uvicorn in background
    process = subprocess.Popen(
        [
            sys.executable, "-m", "uvicorn",
            "backend.app.main:app",
            "--host", host,
            "--port", str(port),
            "--log-level", "info",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )

    PID_FILE.write_text(str(process.pid))
    print(f"Daemon started (PID: {process.pid})")


def stop_daemon() -> None:
    """Stop cortexd gracefully."""
    pid = get_pid()
    if pid is None:
        print("Daemon not running")
        sys.exit(1)

    try:
        os.kill(pid, signal.SIGTERM)
        # Wait up to 10 seconds for graceful shutdown
        for _ in range(100):
            try:
                os.kill(pid, 0)
                import time
                time.sleep(0.1)
            except ProcessLookupError:
                break
        else:
            # Force kill if still running
            os.kill(pid, signal.SIGKILL)
            print("Daemon force-killed")
    except ProcessLookupError:
        pass
    finally:
        PID_FILE.unlink(missing_ok=True)
        print("Daemon stopped")


def daemon_status() -> None:
    """Print daemon status."""
    pid = get_pid()
    if pid is None:
        print("Daemon: not running")
        sys.exit(1)
    print(f"Daemon: running (PID: {pid})")
```

- [ ] **Step 3: Write failing test for CLI**

```python
# tests/daemon/test_cli.py
"""Tests for daemon CLI."""
import os
import signal
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

from backend.app.daemon.cli import get_pid, start_daemon, stop_daemon, PID_FILE


class TestGetPid:
    def test_returns_none_when_no_pid_file(self, tmp_path):
        with patch("backend.app.daemon.cli.PID_FILE", tmp_path / "daemon.pid"):
            assert get_pid() is None

    def test_returns_none_when_stale_pid(self, tmp_path):
        pid_file = tmp_path / "daemon.pid"
        pid_file.write_text("999999999")  # Non-existent PID
        with patch("backend.app.daemon.cli.PID_FILE", pid_file):
            assert get_pid() is None

    def test_returns_pid_when_running(self, tmp_path):
        pid_file = tmp_path / "daemon.pid"
        pid_file.write_text(str(os.getpid()))  # Current process is running
        with patch("backend.app.daemon.cli.PID_FILE", pid_file):
            assert get_pid() == os.getpid()
```

- [ ] **Step 4: Run test to verify it fails**

Run: `uv run python -m pytest tests/daemon/test_cli.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'backend.app.daemon'`

- [ ] **Step 5: Implement `get_pid` function**

Already done in Step 2 — the implementation is complete.

- [ ] **Step 6: Run test to verify it passes**

Run: `uv run python -m pytest tests/daemon/test_cli.py -v`
Expected: PASS (3 tests)

- [ ] **Step 7: Commit**

```bash
git add backend/app/daemon/ tests/daemon/
git commit -m "feat(daemon): add CLI entry point with PID management"
```

---

### Task 1.2: Daemon Lifecycle Manager

**Files:**
- Create: `backend/app/daemon/lifecycle.py`
- Create: `tests/daemon/test_lifecycle.py`

**Interfaces:**
- Consumes: FastAPI app lifespan, service initialization functions
- Produces: `DaemonLifecycle` class with `start()`, `stop()`, `sleep()`, `wake()`, `health_check()`

- [ ] **Step 1: Write failing test for lifecycle**

```python
# tests/daemon/test_lifecycle.py
"""Tests for daemon lifecycle management."""
import asyncio
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from backend.app.daemon.lifecycle import DaemonLifecycle


class TestDaemonLifecycle:
    @pytest.fixture
    def lifecycle(self):
        return DaemonLifecycle()

    def test_initial_state(self, lifecycle):
        assert lifecycle.state == "stopped"
        assert lifecycle.started_at is None

    @pytest.mark.asyncio
    async def test_start_sets_state(self, lifecycle):
        with patch.object(lifecycle, "_init_services", new_callable=AsyncMock):
            with patch.object(lifecycle, "_start_background_tasks", new_callable=AsyncMock):
                await lifecycle.start()
                assert lifecycle.state == "running"
                assert lifecycle.started_at is not None

    @pytest.mark.asyncio
    async def test_stop_sets_state(self, lifecycle):
        lifecycle.state = "running"
        with patch.object(lifecycle, "_cleanup", new_callable=AsyncMock):
            await lifecycle.stop()
            assert lifecycle.state == "stopped"

    @pytest.mark.asyncio
    async def test_sleep_pauses_background(self, lifecycle):
        lifecycle.state = "running"
        with patch.object(lifecycle, "_pause_background", new_callable=AsyncMock):
            await lifecycle.sleep()
            assert lifecycle.state == "sleeping"

    @pytest.mark.asyncio
    async def test_wake_resumes_from_sleep(self, lifecycle):
        lifecycle.state = "sleeping"
        with patch.object(lifecycle, "_resume_background", new_callable=AsyncMock):
            await lifecycle.wake()
            assert lifecycle.state == "running"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run python -m pytest tests/daemon/test_lifecycle.py -v`
Expected: FAIL with `ImportError: cannot import name 'DaemonLifecycle'`

- [ ] **Step 3: Implement DaemonLifecycle**

```python
# backend/app/daemon/lifecycle.py
"""Daemon lifecycle — startup, shutdown, sleep, wake."""
import asyncio
import time
from enum import Enum
from typing import Any, Callable


class DaemonState(str, Enum):
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    SLEEPING = "sleeping"
    STOPPING = "stopping"


class DaemonLifecycle:
    """Manages daemon process lifecycle."""

    def __init__(self):
        self.state: DaemonState = DaemonState.STOPPED
        self.started_at: float | None = None
        self._shutdown_event = asyncio.Event()
        self._background_tasks: list[asyncio.Task] = []

    async def start(self) -> None:
        """Start the daemon and all services."""
        self.state = DaemonState.STARTING
        self.started_at = time.time()

        await self._init_services()
        await self._start_background_tasks()

        self.state = DaemonState.RUNNING

    async def stop(self) -> None:
        """Stop the daemon gracefully."""
        self.state = DaemonState.STOPPING
        self._shutdown_event.set()

        # Cancel background tasks
        for task in self._background_tasks:
            task.cancel()
        if self._background_tasks:
            await asyncio.gather(*self._background_tasks, return_exceptions=True)
        self._background_tasks.clear()

        await self._cleanup()
        self.state = DaemonState.STOPPED

    async def sleep(self) -> None:
        """Pause background work, maintain minimal state."""
        if self.state != DaemonState.RUNNING:
            return
        await self._pause_background()
        self.state = DaemonState.SLEEPING

    async def wake(self) -> None:
        """Resume background work."""
        if self.state != DaemonState.SLEEPING:
            return
        await self._resume_background()
        self.state = DaemonState.RUNNING

    async def health_check(self) -> dict[str, Any]:
        """Check daemon and service health."""
        return {
            "state": self.state.value,
            "uptime": time.time() - self.started_at if self.started_at else 0,
            "services": await self._check_services(),
        }

    async def _init_services(self) -> None:
        """Initialize all daemon services."""
        pass  # Will be implemented in Phase 2

    async def _start_background_tasks(self) -> None:
        """Start background monitoring tasks."""
        pass  # Will be implemented in Phase 3

    async def _cleanup(self) -> None:
        """Clean up resources on shutdown."""
        pass

    async def _pause_background(self) -> None:
        """Pause background tasks."""
        pass

    async def _resume_background(self) -> None:
        """Resume background tasks."""
        pass

    async def _check_services(self) -> dict[str, bool]:
        """Check health of all services."""
        return {}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run python -m pytest tests/daemon/test_lifecycle.py -v`
Expected: PASS (4 tests)

- [ ] **Step 5: Commit**

```bash
git add backend/app/daemon/lifecycle.py tests/daemon/test_lifecycle.py
git commit -m "feat(daemon): add lifecycle manager with state transitions"
```

---

### Task 1.3: Daemon Health Monitor

**Files:**
- Create: `backend/app/daemon/health.py`
- Create: `tests/daemon/test_health.py`

**Interfaces:**
- Consumes: Service registry (Phase 2), database connections, Redis, Qdrant
- Produces: `DaemonHealth` class with `check_all()`, `check_service()`, `recovery_action()`

- [ ] **Step 1: Write failing test for health monitor**

```python
# tests/daemon/test_health.py
"""Tests for daemon health monitoring."""
import pytest
from unittest.mock import AsyncMock, MagicMock

from backend.app.daemon.health import DaemonHealth, HealthStatus


class TestDaemonHealth:
    @pytest.fixture
    def health(self):
        return DaemonHealth()

    def test_initial_status(self, health):
        status = health.get_status()
        assert status.overall == HealthStatus.UNKNOWN
        assert len(status.services) == 0

    @pytest.mark.asyncio
    async def test_check_all_aggregates(self, health):
        health.register_service("db", AsyncMock(return_value=True))
        health.register_service("redis", AsyncMock(return_value=False))

        status = await health.check_all()
        assert status.overall == HealthStatus.DEGRADED
        assert status.services["db"].healthy is True
        assert status.services["redis"].healthy is False

    @pytest.mark.asyncio
    async def test_recovery_action_triggered(self, health):
        recovery = AsyncMock()
        health.register_service(
            "db",
            AsyncMock(return_value=False),
            on_failure=recovery,
        )
        await health.check_all()
        recovery.assert_called_once()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run python -m pytest tests/daemon/test_health.py -v`
Expected: FAIL with `ImportError: cannot import name 'DaemonHealth'`

- [ ] **Step 3: Implement DaemonHealth**

```python
# backend/app/daemon/health.py
"""Daemon health monitoring and recovery."""
import asyncio
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Awaitable


class HealthStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class ServiceHealth:
    name: str
    healthy: bool
    message: str = ""
    latency_ms: float = 0


@dataclass
class HealthReport:
    overall: HealthStatus
    services: dict[str, ServiceHealth] = field(default_factory=dict)
    uptime: float = 0


class DaemonHealth:
    """Monitor health of all daemon services."""

    def __init__(self):
        self._services: dict[str, tuple[Callable[[], Awaitable[bool]], Callable[[], Awaitable[None]] | None]] = {}
        self._report = HealthReport(overall=HealthStatus.UNKNOWN)

    def register_service(
        self,
        name: str,
        check: Callable[[], Awaitable[bool]],
        on_failure: Callable[[], Awaitable[None]] | None = None,
    ) -> None:
        """Register a service health check."""
        self._services[name] = (check, on_failure)

    def get_status(self) -> HealthReport:
        """Get current health status."""
        return self._report

    async def check_all(self) -> HealthReport:
        """Run all health checks and aggregate."""
        services = {}
        all_healthy = True

        for name, (check, on_failure) in self._services.items():
            try:
                start = asyncio.get_event_loop().time()
                healthy = await check()
                latency = (asyncio.get_event_loop().time() - start) * 1000
                services[name] = ServiceHealth(
                    name=name,
                    healthy=healthy,
                    latency_ms=latency,
                )
                if not healthy:
                    all_healthy = False
                    if on_failure:
                        await on_failure()
            except Exception as e:
                services[name] = ServiceHealth(
                    name=name,
                    healthy=False,
                    message=str(e),
                )
                all_healthy = False

        overall = HealthStatus.HEALTHY if all_healthy else HealthStatus.DEGRADED
        if not services:
            overall = HealthStatus.UNKNOWN

        self._report = HealthReport(overall=overall, services=services)
        return self._report
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run python -m pytest tests/daemon/test_health.py -v`
Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
git add backend/app/daemon/health.py tests/daemon/test_health.py
git commit -m "feat(daemon): add health monitoring with service checks"
```

---

### Task 1.4: Daemon Config and PID Management

**Files:**
- Create: `backend/app/daemon/config.py`
- Create: `backend/app/core/pid.py`
- Create: `tests/daemon/test_config.py`

**Interfaces:**
- Consumes: Environment variables, `~/.cortex/` directory
- Produces: `DaemonConfig` dataclass, `PIDManager` class

- [ ] **Step 1: Write failing test for config**

```python
# tests/daemon/test_config.py
"""Tests for daemon configuration."""
import os
import pytest
from unittest.mock import patch

from backend.app.daemon.config import DaemonConfig


class TestDaemonConfig:
    def test_default_values(self):
        config = DaemonConfig()
        assert config.host == "127.0.0.1"
        assert config.port == 8000
        assert config.log_level == "info"

    def test_from_env(self):
        with patch.dict(os.environ, {
            "CORTEX_DAEMON_HOST": "0.0.0.0",
            "CORTEX_DAEMON_PORT": "9000",
        }):
            config = DaemonConfig.from_env()
            assert config.host == "0.0.0.0"
            assert config.port == 9000

    def test_data_dir_default(self, tmp_path):
        with patch("pathlib.Path.home", return_value=tmp_path):
            config = DaemonConfig()
            assert config.data_dir == tmp_path / ".cortex"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run python -m pytest tests/daemon/test_config.py -v`
Expected: FAIL with `ImportError: cannot import name 'DaemonConfig'`

- [ ] **Step 3: Implement DaemonConfig**

```python
# backend/app/daemon/config.py
"""Daemon configuration."""
import os
from dataclasses import dataclass
from pathlib import Path


@dataclass
class DaemonConfig:
    """Configuration for cortexd daemon."""
    host: str = "127.0.0.1"
    port: int = 8000
    log_level: str = "info"
    data_dir: Path = None
    pid_file: Path = None
    socket_file: Path = None

    def __post_init__(self):
        if self.data_dir is None:
            self.data_dir = Path.home() / ".cortex"
        if self.pid_file is None:
            self.pid_file = self.data_dir / "daemon.pid"
        if self.socket_file is None:
            self.socket_file = self.data_dir / "daemon.sock"

    @classmethod
    def from_env(cls) -> "DaemonConfig":
        """Load config from environment variables."""
        return cls(
            host=os.getenv("CORTEX_DAEMON_HOST", "127.0.0.1"),
            port=int(os.getenv("CORTEX_DAEMON_PORT", "8000")),
            log_level=os.getenv("CORTEX_LOG_LEVEL", "info"),
        )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run python -m pytest tests/daemon/test_config.py -v`
Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
git add backend/app/daemon/config.py tests/daemon/test_config.py
git commit -m "feat(daemon): add daemon configuration with env support"
```

---

### Task 1.5: Integrate Daemon with FastAPI Lifespan

**Files:**
- Modify: `backend/app/main.py` (lines 1-50: lifespan)
- Modify: `Makefile` (add `make daemon` target)
- Create: `tests/daemon/test_integration.py`

**Interfaces:**
- Consumes: `DaemonLifecycle`, `DaemonConfig`, existing lifespan functions
- Produces: Modified `main.py` that uses `DaemonLifecycle` for startup/shutdown

- [ ] **Step 1: Write failing test for integration**

```python
# tests/daemon/test_integration.py
"""Tests for daemon-FastAPI integration."""
import pytest
from unittest.mock import AsyncMock, patch

from backend.app.daemon.lifecycle import DaemonLifecycle


class TestDaemonIntegration:
    @pytest.mark.asyncio
    async def test_lifecycle_starts_on_app_startup(self):
        lifecycle = DaemonLifecycle()
        with patch.object(lifecycle, "_init_services", new_callable=AsyncMock):
            with patch.object(lifecycle, "_start_background_tasks", new_callable=AsyncMock):
                await lifecycle.start()
                assert lifecycle.state == "running"

    @pytest.mark.asyncio
    async def test_lifecycle_stops_on_app_shutdown(self):
        lifecycle = DaemonLifecycle()
        lifecycle.state = "running"
        with patch.object(lifecycle, "_cleanup", new_callable=AsyncMock):
            await lifecycle.stop()
            assert lifecycle.state == "stopped"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run python -m pytest tests/daemon/test_integration.py -v`
Expected: FAIL (integration not wired yet)

- [ ] **Step 3: Modify main.py lifespan to use DaemonLifecycle**

```python
# backend/app/main.py — ADD at top of lifespan
from backend.app.daemon.lifecycle import DaemonLifecycle

# INSIDE lifespan function, after existing startup code:
    # Initialize daemon lifecycle
    lifecycle = DaemonLifecycle()
    await lifecycle.start()
    yield
    # Shutdown
    await lifecycle.stop()
```

- [ ] **Step 4: Add `make daemon` target to Makefile**

```makefile
# Makefile — ADD after existing targets
daemon:  ## Start cortexd daemon
	uv run python -m backend.app.daemon.cli start

daemon-stop:  ## Stop cortexd daemon
	uv run python -m backend.app.daemon.cli stop

daemon-status:  ## Check daemon status
	uv run python -m backend.app.daemon.cli status
```

- [ ] **Step 5: Run test to verify it passes**

Run: `uv run python -m pytest tests/daemon/test_integration.py -v`
Expected: PASS (2 tests)

- [ ] **Step 6: Run full test suite to verify no regressions**

Run: `uv run python -m pytest tests/ -v --tb=short`
Expected: All existing tests pass

- [ ] **Step 7: Commit**

```bash
git add backend/app/main.py Makefile tests/daemon/test_integration.py
git commit -m "feat(daemon): integrate lifecycle with FastAPI lifespan"
```

---

## Phase 2: Service Abstraction

### Task 2.1: Define Service Protocols

**Files:**
- Create: `backend/app/services/abstraction/__init__.py`
- Create: `backend/app/services/abstraction/base.py`
- Create: `backend/app/services/abstraction/database.py`
- Create: `backend/app/services/abstraction/vector_store.py`
- Create: `backend/app/services/abstraction/cache.py`
- Create: `tests/services/test_abstraction.py`

**Interfaces:**
- Consumes: Python Protocol (PEP 544)
- Produces: Protocol classes for Database, VectorStore, Cache

- [ ] **Step 1: Create abstraction package**

```python
# backend/app/services/abstraction/__init__.py
"""Service abstraction layer — Protocol-based interfaces."""
```

- [ ] **Step 2: Write failing test for protocols**

```python
# tests/services/test_abstraction.py
"""Tests for service abstraction protocols."""
import pytest
from backend.app.services.abstraction.database import DatabaseProvider
from backend.app.services.abstraction.vector_store import VectorStoreProvider
from backend.app.services.abstraction.cache import CacheProvider


class TestDatabaseProtocol:
    def test_protocol_has_required_methods(self):
        assert hasattr(DatabaseProvider, "execute")
        assert hasattr(DatabaseProvider, "fetch_one")
        assert hasattr(DatabaseProvider, "fetch_all")


class TestVectorStoreProtocol:
    def test_protocol_has_required_methods(self):
        assert hasattr(VectorStoreProvider, "search")
        assert hasattr(VectorStoreProvider, "upsert")
        assert hasattr(VectorStoreProvider, "delete")


class TestCacheProtocol:
    def test_protocol_has_required_methods(self):
        assert hasattr(CacheProvider, "get")
        assert hasattr(CacheProvider, "set")
        assert hasattr(CacheProvider, "delete")
```

- [ ] **Step 3: Run test to verify it fails**

Run: `uv run python -m pytest tests/services/test_abstraction.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 4: Implement DatabaseProvider Protocol**

```python
# backend/app/services/abstraction/database.py
"""Database provider protocol."""
from typing import Protocol, Any, Sequence


class DatabaseProvider(Protocol):
    """Interface for database operations."""

    async def execute(self, query: str, params: dict | None = None) -> Any:
        """Execute a query."""
        ...

    async def fetch_one(self, query: str, params: dict | None = None) -> dict | None:
        """Fetch a single row."""
        ...

    async def fetch_all(self, query: str, params: dict | None = None) -> Sequence[dict]:
        """Fetch all rows."""
        ...

    async def health_check(self) -> bool:
        """Check if database is healthy."""
        ...
```

- [ ] **Step 5: Implement VectorStoreProvider Protocol**

```python
# backend/app/services/abstraction/vector_store.py
"""Vector store provider protocol."""
from typing import Protocol, Any


class VectorStoreProvider(Protocol):
    """Interface for vector store operations."""

    async def search(
        self,
        vector: list[float],
        limit: int = 10,
        filter: dict | None = None,
    ) -> list[dict]:
        """Search for similar vectors."""
        ...

    async def upsert(
        self,
        id: str,
        vector: list[float],
        payload: dict | None = None,
    ) -> None:
        """Insert or update a vector."""
        ...

    async def delete(self, id: str) -> None:
        """Delete a vector."""
        ...

    async def health_check(self) -> bool:
        """Check if vector store is healthy."""
        ...
```

- [ ] **Step 6: Implement CacheProvider Protocol**

```python
# backend/app/services/abstraction/cache.py
"""Cache provider protocol."""
from typing import Protocol


class CacheProvider(Protocol):
    """Interface for cache operations."""

    async def get(self, key: str) -> str | None:
        """Get value by key."""
        ...

    async def set(self, key: str, value: str, ttl: int | None = None) -> None:
        """Set key-value pair with optional TTL."""
        ...

    async def delete(self, key: str) -> None:
        """Delete key."""
        ...

    async def health_check(self) -> bool:
        """Check if cache is healthy."""
        ...
```

- [ ] **Step 7: Run test to verify it passes**

Run: `uv run python -m pytest tests/services/test_abstraction.py -v`
Expected: PASS (3 tests)

- [ ] **Step 8: Commit**

```bash
git add backend/app/services/abstraction/ tests/services/test_abstraction.py
git commit -m "feat(abstraction): define service protocols for database, vector store, cache"
```

---

### Task 2.2: Create Service Registry

**Files:**
- Create: `backend/app/services/registry.py`
- Create: `tests/services/test_registry.py`

**Interfaces:**
- Consumes: Protocol classes from Task 2.1
- Produces: `ServiceRegistry` singleton with `get()`, `register()`, `configure()`

- [ ] **Step 1: Write failing test for registry**

```python
# tests/services/test_registry.py
"""Tests for service registry."""
import pytest
from backend.app.services.registry import ServiceRegistry
from backend.app.services.abstraction.database import DatabaseProvider


class TestServiceRegistry:
    @pytest.fixture
    def registry(self):
        return ServiceRegistry()

    def test_register_and_get(self, registry):
        mock_db = object()
        registry.register("database", mock_db)
        assert registry.get("database") is mock_db

    def test_get_unknown_returns_none(self, registry):
        assert registry.get("unknown") is None

    def test_configure_loads_from_config(self, registry):
        config = {"database": {"provider": "sqlite", "path": ":memory:"}}
        # This will fail until we implement configure()
        with pytest.raises(NotImplementedError):
            registry.configure(config)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run python -m pytest tests/services/test_registry.py -v`
Expected: FAIL with `ImportError`

- [ ] **Step 3: Implement ServiceRegistry**

```python
# backend/app/services/registry.py
"""Service registry — manages provider instances."""
from typing import Any


class ServiceRegistry:
    """Central registry for service provider instances."""

    def __init__(self):
        self._services: dict[str, Any] = {}

    def register(self, name: str, instance: Any) -> None:
        """Register a service provider instance."""
        self._services[name] = instance

    def get(self, name: str) -> Any | None:
        """Get a registered service provider."""
        return self._services.get(name)

    def configure(self, config: dict) -> None:
        """Configure services from config dict."""
        # Phase 2: will load providers from config
        raise NotImplementedError("Configure will be implemented with provider loading")

    def list_services(self) -> list[str]:
        """List all registered services."""
        return list(self._services.keys())


# Global singleton
_service_registry: ServiceRegistry | None = None


def get_service_registry() -> ServiceRegistry:
    """Get the global service registry."""
    global _service_registry
    if _service_registry is None:
        _service_registry = ServiceRegistry()
    return _service_registry
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run python -m pytest tests/services/test_registry.py -v`
Expected: PASS (3 tests, one raises NotImplementedError as expected)

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/registry.py tests/services/test_registry.py
git commit -m "feat(abstraction): add service registry for provider management"
```

---

## Phase 3: Event Bus & Job System

### Task 3.1: Event Bus Core

**Files:**
- Create: `backend/app/core/events/__init__.py`
- Create: `backend/app/core/events/bus.py`
- Create: `backend/app/core/events/types.py`
- Create: `tests/core/test_events.py`

**Interfaces:**
- Consumes: Python asyncio
- Produces: `EventBus` class with `publish()`, `subscribe()`, `unsubscribe()`

- [ ] **Step 1: Write failing test for event bus**

```python
# tests/core/test_events.py
"""Tests for in-process event bus."""
import asyncio
import pytest
from backend.app.core.events.bus import EventBus
from backend.app.core.events.types import Event


class TestEventBus:
    @pytest.fixture
    def bus(self):
        return EventBus()

    @pytest.mark.asyncio
    async def test_publish_subscribes(self, bus):
        received = []

        async def handler(event: Event):
            received.append(event)

        bus.subscribe("test.event", handler)
        await bus.publish(Event(type="test.event", data={"key": "value"}))
        assert len(received) == 1
        assert received[0].data == {"key": "value"}

    @pytest.mark.asyncio
    async def test_unsubscribe(self, bus):
        received = []

        async def handler(event: Event):
            received.append(event)

        bus.subscribe("test.event", handler)
        bus.unsubscribe("test.event", handler)
        await bus.publish(Event(type="test.event", data={}))
        assert len(received) == 0

    @pytest.mark.asyncio
    async def test_multiple_subscribers(self, bus):
        results = {"a": False, "b": False}

        async def handler_a(event: Event):
            results["a"] = True

        async def handler_b(event: Event):
            results["b"] = True

        bus.subscribe("test.event", handler_a)
        bus.subscribe("test.event", handler_b)
        await bus.publish(Event(type="test.event", data={}))
        assert results["a"] is True
        assert results["b"] is True
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run python -m pytest tests/core/test_events.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Implement Event type**

```python
# backend/app/core/events/types.py
"""Event type definitions."""
from dataclasses import dataclass, field
from typing import Any
import time


@dataclass
class Event:
    """Base event type."""
    type: str
    data: dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    source: str = ""
```

- [ ] **Step 4: Implement EventBus**

```python
# backend/app/core/events/bus.py
"""In-process event bus."""
import asyncio
from typing import Callable, Awaitable
from backend.app.core.events.types import Event


class EventBus:
    """Pub/sub event bus for in-process communication."""

    def __init__(self):
        self._subscribers: dict[str, list[Callable[[Event], Awaitable[None]]]] = {}

    def subscribe(self, event_type: str, handler: Callable[[Event], Awaitable[None]]) -> None:
        """Subscribe to an event type."""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(handler)

    def unsubscribe(self, event_type: str, handler: Callable[[Event], Awaitable[None]]) -> None:
        """Unsubscribe from an event type."""
        if event_type in self._subscribers:
            self._subscribers[event_type] = [
                h for h in self._subscribers[event_type] if h != handler
            ]

    async def publish(self, event: Event) -> None:
        """Publish an event to all subscribers."""
        handlers = self._subscribers.get(event.type, [])
        for handler in handlers:
            await handler(event)


# Global singleton
_event_bus: EventBus | None = None


def get_event_bus() -> EventBus:
    """Get the global event bus."""
    global _event_bus
    if _event_bus is None:
        _event_bus = EventBus()
    return _event_bus
```

- [ ] **Step 5: Run test to verify it passes**

Run: `uv run python -m pytest tests/core/test_events.py -v`
Expected: PASS (3 tests)

- [ ] **Step 6: Commit**

```bash
git add backend/app/core/events/ tests/core/test_events.py
git commit -m "feat(events): add in-process event bus with pub/sub"
```

---

### Task 3.2: Job System Core

**Files:**
- Create: `backend/app/core/jobs/__init__.py`
- Create: `backend/app/core/jobs/engine.py`
- Create: `backend/app/core/jobs/queue.py`
- Create: `backend/app/core/jobs/models.py`
- Create: `tests/core/test_jobs.py`

**Interfaces:**
- Consumes: SQLite for persistence, asyncio for execution
- Produces: `JobEngine` class with `submit()`, `cancel()`, `list_jobs()`

- [ ] **Step 1: Write failing test for job engine**

```python
# tests/core/test_jobs.py
"""Tests for job execution engine."""
import asyncio
import pytest
from backend.app.core.jobs.engine import JobEngine
from backend.app.core.jobs.models import Job, JobStatus


class TestJobEngine:
    @pytest.fixture
    async def engine(self, tmp_path):
        db_path = tmp_path / "jobs.db"
        return await JobEngine.create(str(db_path))

    @pytest.mark.asyncio
    async def test_submit_job(self, engine):
        async def dummy_task():
            return "done"

        job = await engine.submit("test.task", dummy_task)
        assert job.status == JobStatus.PENDING
        assert job.task_name == "test.task"

    @pytest.mark.asyncio
    async def test_cancel_job(self, engine):
        async def slow_task():
            await asyncio.sleep(100)
            return "done"

        job = await engine.submit("test.slow", slow_task)
        await engine.cancel(job.id)
        assert job.status == JobStatus.CANCELLED

    @pytest.mark.asyncio
    async def test_list_jobs(self, engine):
        async def dummy():
            return "done"

        await engine.submit("task1", dummy)
        await engine.submit("task2", dummy)
        jobs = await engine.list_jobs()
        assert len(jobs) == 2
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run python -m pytest tests/core/test_jobs.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Implement Job models**

```python
# backend/app/core/jobs/models.py
"""Job state models."""
from dataclasses import dataclass, field
from enum import Enum
from typing import Any
import time
import uuid


class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Job:
    """Represents a background job."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    task_name: str = ""
    status: JobStatus = JobStatus.PENDING
    created_at: float = field(default_factory=time.time)
    started_at: float | None = None
    completed_at: float | None = None
    result: Any = None
    error: str | None = None
    progress: float = 0.0
```

- [ ] **Step 4: Implement JobEngine**

```python
# backend/app/core/jobs/engine.py
"""Job execution engine."""
import asyncio
import sqlite3
from typing import Any, Callable, Awaitable
from backend.app.core.jobs.models import Job, JobStatus


class JobEngine:
    """Execute background jobs with persistence."""

    def __init__(self, db_path: str):
        self._db_path = db_path
        self._tasks: dict[str, asyncio.Task] = {}
        self._conn = sqlite3.connect(db_path)
        self._init_db()

    def _init_db(self):
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                id TEXT PRIMARY KEY,
                task_name TEXT,
                status TEXT,
                created_at REAL,
                started_at REAL,
                completed_at REAL,
                result TEXT,
                error TEXT,
                progress REAL
            )
        """)
        self._conn.commit()

    @classmethod
    async def create(cls, db_path: str) -> "JobEngine":
        """Create a new job engine instance."""
        return cls(db_path)

    async def submit(
        self,
        task_name: str,
        func: Callable[[], Awaitable[Any]],
        **kwargs,
    ) -> Job:
        """Submit a new job for execution."""
        job = Job(task_name=task_name)
        self._save_job(job)

        # Create asyncio task
        task = asyncio.create_task(self._run_job(job, func))
        self._tasks[job.id] = task

        return job

    async def cancel(self, job_id: str) -> None:
        """Cancel a running job."""
        if job_id in self._tasks:
            self._tasks[job_id].cancel()
            job = self._load_job(job_id)
            if job:
                job.status = JobStatus.CANCELLED
                self._save_job(job)

    async def list_jobs(self, status: JobStatus | None = None) -> list[Job]:
        """List all jobs, optionally filtered by status."""
        if status:
            cursor = self._conn.execute(
                "SELECT * FROM jobs WHERE status = ?", (status.value,)
            )
        else:
            cursor = self._conn.execute("SELECT * FROM jobs")
        rows = cursor.fetchall()
        return [self._row_to_job(row) for row in rows]

    async def _run_job(self, job: Job, func: Callable) -> None:
        """Run a job and update its status."""
        job.status = JobStatus.RUNNING
        job.started_at = __import__("time").time()
        self._save_job(job)

        try:
            result = await func()
            job.result = result
            job.status = JobStatus.COMPLETED
        except asyncio.CancelledError:
            job.status = JobStatus.CANCELLED
        except Exception as e:
            job.error = str(e)
            job.status = JobStatus.FAILED
        finally:
            job.completed_at = __import__("time").time()
            self._save_job(job)

    def _save_job(self, job: Job) -> None:
        """Save job to SQLite."""
        self._conn.execute(
            """INSERT OR REPLACE INTO jobs
            (id, task_name, status, created_at, started_at, completed_at, result, error, progress)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (job.id, job.task_name, job.status.value, job.created_at,
             job.started_at, job.completed_at, job.result, job.error, job.progress),
        )
        self._conn.commit()

    def _load_job(self, job_id: str) -> Job | None:
        """Load job from SQLite."""
        cursor = self._conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,))
        row = cursor.fetchone()
        if row:
            return self._row_to_job(row)
        return None

    def _row_to_job(self, row) -> Job:
        """Convert SQLite row to Job."""
        return Job(
            id=row[0],
            task_name=row[1],
            status=JobStatus(row[2]),
            created_at=row[3],
            started_at=row[4],
            completed_at=row[5],
            result=row[6],
            error=row[7],
            progress=row[8],
        )
```

- [ ] **Step 5: Run test to verify it passes**

Run: `uv run python -m pytest tests/core/test_jobs.py -v`
Expected: PASS (3 tests)

- [ ] **Step 6: Commit**

```bash
git add backend/app/core/jobs/ tests/core/test_jobs.py
git commit -m "feat(jobs): add job execution engine with SQLite persistence"
```

---

## Phase 4: CLI Completion

### Task 4.1: CLI API Client

**Files:**
- Create: `cli/src/client/api.ts`
- Create: `cli/src/client/types.ts`
- Create: `tests/cli/client.test.ts`

**Interfaces:**
- Consumes: HTTP fetch, daemon API endpoints
- Produces: `CortexClient` class with methods for all API endpoints

- [ ] **Step 1: Create client package**

```typescript
// cli/src/client/api.ts
import { CortexConfig, SearchResults, MemoryItem, JobStatus } from "./types";

export class CortexClient {
  private baseUrl: string;
  private token: string | null = null;

  constructor(config: CortexConfig) {
    this.baseUrl = config.apiUrl || "http://127.0.0.1:8000";
  }

  async search(query: string, limit: number = 10): Promise<SearchResults> {
    const response = await fetch(`${this.baseUrl}/api/v1/search`, {
      method: "POST",
      headers: this.getHeaders(),
      body: JSON.stringify({ query, limit }),
    });
    return response.json();
  }

  async remember(content: string, metadata?: Record<string, any>): Promise<MemoryItem> {
    const response = await fetch(`${this.baseUrl}/api/v1/memory`, {
      method: "POST",
      headers: this.getHeaders(),
      body: JSON.stringify({ content, metadata }),
    });
    return response.json();
  }

  async status(): Promise<JobStatus> {
    const response = await fetch(`${this.baseUrl}/api/v1/health`, {
      headers: this.getHeaders(),
    });
    return response.json();
  }

  private getHeaders(): Record<string, string> {
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
    };
    if (this.token) {
      headers["Authorization"] = `Bearer ${this.token}`;
    }
    return headers;
  }
}
```

- [ ] **Step 2: Create types**

```typescript
// cli/src/client/types.ts
export interface CortexConfig {
  apiUrl?: string;
  token?: string;
}

export interface SearchResults {
  results: Array<{
    id: string;
    content: string;
    score: number;
    source: string;
  }>;
}

export interface MemoryItem {
  id: string;
  content: string;
  metadata: Record<string, any>;
  created_at: string;
}

export interface JobStatus {
  state: string;
  uptime: number;
  services: Record<string, boolean>;
}
```

- [ ] **Step 3: Write test for client**

```typescript
// tests/cli/client.test.ts
import { describe, it, expect, vi } from "vitest";
import { CortexClient } from "../../cli/src/client/api";

describe("CortexClient", () => {
  it("creates client with default config", () => {
    const client = new CortexClient({});
    expect(client).toBeDefined();
  });

  it("uses custom API URL", () => {
    const client = new CortexClient({ apiUrl: "http://localhost:9000" });
    expect(client).toBeDefined();
  });
});
```

- [ ] **Step 4: Run test**

Run: `cd frontend && npx vitest run tests/cli/client.test.ts`
Expected: PASS (2 tests)

- [ ] **Step 5: Commit**

```bash
git add cli/src/client/ tests/cli/client.test.ts
git commit -m "feat(cli): add API client for daemon communication"
```

---

## Phase 5: API Stabilization

### Task 5.1: Deprecation Middleware

**Files:**
- Create: `backend/app/api/middleware/deprecation.py`
- Create: `tests/api/test_deprecation.py`

**Interfaces:**
- Consumes: FastAPI middleware
- Produces: `DeprecationMiddleware` that adds headers to deprecated endpoints

- [ ] **Step 1: Write failing test**

```python
# tests/api/test_deprecation.py
"""Tests for deprecation middleware."""
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from backend.app.api.middleware.deprecation import deprecation_middleware


class TestDeprecationMiddleware:
    def test_deprecated_endpoint_has_headers(self):
        app = FastAPI()
        app.middleware("http")(deprecation_middleware)

        @app.get("/old-endpoint")
        async def old_endpoint():
            return {"status": "deprecated"}

        client = TestClient(app)
        response = client.get("/old-endpoint")
        assert "Deprecation" in response.headers
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run python -m pytest tests/api/test_deprecation.py -v`
Expected: FAIL with `ImportError`

- [ ] **Step 3: Implement deprecation middleware**

```python
# backend/app/api/middleware/deprecation.py
"""Deprecation warning middleware."""
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class DeprecationMiddleware(BaseHTTPMiddleware):
    """Add deprecation headers to marked endpoints."""

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)

        # Check if endpoint is marked as deprecated
        if hasattr(request.scope.get("route"), "deprecated"):
            if request.scope["route"].deprecated:
                response.headers["Deprecation"] = "true"
                response.headers["Sunset"] = "2027-01-01"

        return response


# Convenience function for endpoint decorator
def deprecated(reason: str = "", sunset: str = "2027-01-01"):
    """Mark an endpoint as deprecated."""
    def decorator(func):
        func.deprecated = True
        func.deprecation_reason = reason
        func.sunset = sunset
        return func
    return decorator
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run python -m pytest tests/api/test_deprecation.py -v`
Expected: PASS (1 test)

- [ ] **Step 5: Commit**

```bash
git add backend/app/api/middleware/deprecation.py tests/api/test_deprecation.py
git commit -m "feat(api): add deprecation middleware for versioning"
```

---

## Phase 6: Desktop Shell

### Task 6.1: Tauri Project Setup

**Files:**
- Create: `desktop/` directory structure
- Create: `desktop/src-tauri/Cargo.toml`
- Create: `desktop/src-tauri/tauri.conf.json`
- Create: `desktop/src-tauri/src/main.rs`

**Interfaces:**
- Consumes: Tauri v2, Rust
- Produces: Basic Tauri app shell

- [ ] **Step 1: Initialize Tauri project**

Run: `cd desktop && npm create tauri-app@latest .`
Select: React + TypeScript

- [ ] **Step 2: Create basic main.rs**

```rust
// desktop/src-tauri/src/main.rs
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

fn main() {
    tauri::Builder::default()
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
```

- [ ] **Step 3: Verify build**

Run: `cd desktop && npm run tauri build`
Expected: Build succeeds

- [ ] **Step 4: Commit**

```bash
git add desktop/
git commit -m "feat(desktop): initialize Tauri project shell"
```

---

## Phase 7: Web UI Transition

### Task 7.1: Document Maintenance Scope

**Files:**
- Create: `docs/WEB_UI.md`

- [ ] **Step 1: Create maintenance document**

```markdown
# Web UI Maintenance Policy

## Scope

The web UI (Next.js frontend) is maintained as a secondary access surface. It remains fully functional for remote access scenarios but is no longer the primary development target.

## What's Maintained

- Bug fixes for existing functionality
- Security patches
- Compatibility updates (Next.js, React, TypeScript)
- Documentation updates

## What's NOT Added

- New major features (go to desktop shell or CLI first)
- New pages or routes
- New design system components
- New API integrations beyond existing functionality

## Future

When the desktop shell reaches feature parity, the web UI may be:
1. Reduced to a read-only dashboard
2. Moved to a separate repository
3. Deprecated entirely

## Last Updated
2026-06-25
```

- [ ] **Step 2: Commit**

```bash
git add docs/WEB_UI.md
git commit -m "docs(web): add web UI maintenance policy"
```

---

## Verification

After each phase:
1. Run `uv run python -m pytest tests/ -v` — all tests pass
2. Run `make lint` — no new linting errors
3. Run `make format` — code formatted
4. Web UI still works (`npm run dev` in frontend/)
5. Daemon starts/stops (`make daemon` / `make daemon-stop`)
6. CLI connects to daemon and returns results
