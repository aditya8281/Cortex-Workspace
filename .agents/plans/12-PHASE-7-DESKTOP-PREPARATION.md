# Phase 7: Desktop Preparation

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Prepare the architecture for Tauri v2 desktop packaging without actually building the desktop app. Fix the StorageResolver singleton bug, complete service abstraction, add filesystem hooks, and create native integration stubs.

**Architecture:** StorageResolver singleton supports mode switching, all services work via both direct Python call and HTTP API, native integration hooks ready for Tauri OS calls.

**Tech Stack:** Python 3.12+, pytest, httpx (for HTTP adapter tests)

---

## Task 1: Fix StorageResolver Singleton Bug

**Bug:** `paths.py:36-44` — `get_storage_resolver(mode)` ignores the `mode` parameter after the first call. If called with `mode="web"`, then later with `mode="tauri"`, the second call returns the `"web"` resolver.

**Files:**
- Modify: `backend/app/core/paths.py`
- Create: `backend/tests/test_storage_resolver.py`

### Step 1.1: Fix `get_storage_resolver` to support mode switching

Replace the singleton logic in `backend/app/core/paths.py:36-44` with:

```python
_storage_resolver: StorageResolver | None = None
_storage_resolver_mode: str = "web"


def get_storage_resolver(mode: str = "web") -> StorageResolver:
    """Get or create the global StorageResolver singleton.

    If the requested mode differs from the current mode, the singleton
    is recreated with the new mode. Call ``reset_storage_resolver()``
    to force a fresh instance on the next call.
    """
    global _storage_resolver, _storage_resolver_mode
    if _storage_resolver is None or _storage_resolver_mode != mode:
        _storage_resolver = StorageResolver(mode)
        _storage_resolver_mode = mode
    return _storage_resolver


def reset_storage_resolver() -> None:
    """Reset the global StorageResolver so the next call to
    ``get_storage_resolver()`` creates a fresh instance.

    Useful in tests and when switching between web/tauri modes at runtime.
    """
    global _storage_resolver, _storage_resolver_mode
    _storage_resolver = None
    _storage_resolver_mode = "web"
```

### Step 1.2: Create tests for mode switching

Create `backend/tests/test_storage_resolver.py`:

```python
"""Tests for StorageResolver singleton and mode switching."""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import patch

import pytest

from backend.app.core.paths import (
    StorageResolver,
    get_storage_resolver,
    reset_storage_resolver,
)


@pytest.fixture(autouse=True)
def _clean_singleton():
    """Reset singleton before and after every test."""
    reset_storage_resolver()
    yield
    reset_storage_resolver()


class TestStorageResolver:
    def test_web_mode_returns_cwd_relative_path(self):
        resolver = StorageResolver("web")
        result = resolver.resolve()
        assert result == Path("./CortexMemory").resolve()

    def test_tauri_mode_uses_env_var(self):
        with patch.dict(os.environ, {"CORTEX_DATA_DIR": "/tmp/test-cortex"}):
            resolver = StorageResolver("tauri")
            result = resolver.resolve()
            assert result == Path("/tmp/test-cortex")

    def test_tauri_mode_default_without_env(self):
        os.environ.pop("CORTEX_DATA_DIR", None)
        resolver = StorageResolver("tauri")
        result = resolver.resolve()
        assert result == Path("./CortexMemory")

    def test_models_dir_property(self):
        resolver = StorageResolver("web")
        assert resolver.models_dir == resolver.resolve() / "models"

    def test_qdrant_dir_property(self):
        resolver = StorageResolver("web")
        assert resolver.qdrant_dir == resolver.resolve() / "qdrant"

    def test_profile_dir_property(self):
        resolver = StorageResolver("web")
        assert resolver.profile_dir == resolver.resolve() / "profile"


class TestGetStorageResolverSingleton:
    def test_first_call_creates_singleton(self):
        resolver = get_storage_resolver("web")
        assert isinstance(resolver, StorageResolver)
        assert resolver._mode == "web"

    def test_second_call_returns_same_instance(self):
        r1 = get_storage_resolver("web")
        r2 = get_storage_resolver("web")
        assert r1 is r2

    def test_mode_switch_creates_new_instance(self):
        r1 = get_storage_resolver("web")
        r2 = get_storage_resolver("tauri")
        assert r1 is not r2
        assert r2._mode == "tauri"

    def test_switch_back_to_web(self):
        r1 = get_storage_resolver("web")
        r2 = get_storage_resolver("tauri")
        r3 = get_storage_resolver("web")
        assert r1 is not r2
        assert r2 is not r3
        assert r3._mode == "web"

    def test_reset_clears_singleton(self):
        r1 = get_storage_resolver("web")
        reset_storage_resolver()
        r2 = get_storage_resolver("web")
        assert r1 is not r2

    def test_reset_then_switch(self):
        r1 = get_storage_resolver("tauri")
        reset_storage_resolver()
        r2 = get_storage_resolver("web")
        assert r1 is not r2
        assert r2._mode == "web"

    def test_default_mode_is_web(self):
        resolver = get_storage_resolver()
        assert resolver._mode == "web"
```

### Step 1.3: Run tests

```bash
cd /home/adi/Desktop/Cortex-Workspace && python -m pytest backend/tests/test_storage_resolver.py -v
```

---

## Task 2: Service Abstraction Audit & HTTP Adapter

**Goal:** Ensure every service can be consumed via both direct Python call and HTTP API. Create an HTTP adapter that wraps service calls for Tauri IPC or remote access.

**Files:**
- Modify: `backend/app/core/service_base.py`
- Create: `backend/app/services/adapters/__init__.py`
- Create: `backend/app/services/adapters/http_adapter.py`
- Create: `backend/tests/test_http_adapter.py`

### Step 2.1: Audit findings

After reading every service file, here is the path resolution status:

| Service | Path Resolution | Status |
|---|---|---|
| `vault_service.py` | Uses `get_registry_for_user()` via `storage_registry` — **clean** | OK |
| `storage_registry.py` | Pure DB lookup — **clean** | OK |
| `memory_manager.py` | No filesystem paths — **clean** | OK |
| `notification_service.py` | No filesystem paths — **clean** | OK |
| `user_service.py` | No filesystem paths — **clean** | OK |
| `health_service.py` | No filesystem paths — **clean** | OK |
| `embedding_service.py` | Uses `model_path` param, defaults to mock — **clean** | OK |
| `repo_scanner.py` | Takes `repo_path` as caller-provided param — **clean** | OK |
| `chunker.py` | Pure computation — **clean** | OK |
| `cross_file_search.py` | DB/vector queries — **clean** | OK |
| `graph_builder.py` | DB queries — **clean** | OK |
| `incremental_indexer.py` | Uses `repo_scanner` — **clean** | OK |

**Conclusion:** No services use hardcoded filesystem paths. All path resolution goes through `storage_registry.get_registry_for_user()` or is caller-provided. The `StorageResolver` from Task 1 is the single point of truth for system paths.

### Step 2.2: Enhance `ServiceProtocol` with action registry

Modify `backend/app/core/service_base.py`:

```python
"""Base protocol for services that can be consumed via HTTP or Tauri IPC."""

from abc import ABC, abstractmethod
from typing import Any


class ServiceProtocol(ABC):
    """Base protocol for services that can be consumed via HTTP or Tauri IPC.

    Every service that needs to be callable from both Python and Tauri IPC
    should inherit from this class. The ``execute`` method provides a
    unified entry point for action dispatch.
    """

    @abstractmethod
    async def execute(self, action: str, params: dict[str, Any]) -> dict[str, Any]:
        """Execute a service action with given parameters.

        Actions are string identifiers (e.g. "create", "list", "search").
        Each service defines its own action vocabulary.
        """
        ...

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the service is healthy."""
        ...

    def list_actions(self) -> list[str]:
        """Return the list of supported action names.

        Override this method to advertise available actions for
        auto-discovery and documentation.
        """
        return []
```

### Step 2.3: Create the adapters package

Create `backend/app/services/adapters/__init__.py`:

```python
"""Service adapters for dual-mode (HTTP + Tauri IPC) consumption."""

from backend.app.services.adapters.http_adapter import HTTPServiceAdapter

__all__ = ["HTTPServiceAdapter"]
```

### Step 2.4: Create the HTTP adapter

Create `backend/app/services/adapters/http_adapter.py`:

```python
"""HTTP adapter that wraps a ServiceProtocol for remote / IPC consumption.

This adapter exposes a service's actions as HTTP endpoints.  In web mode
the FastAPI router handles these natively; in Tauri mode the same adapter
can be fronted by Tauri's HTTP shell or IPC bridge.

Usage::

    from backend.app.services.adapters import HTTPServiceAdapter
    from backend.app.services.memory_manager import MemoryManager

    adapter = HTTPServiceAdapter(service=memory_manager, prefix="/api/v1/memory")
    router = adapter.build_router()
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.app.core.service_base import ServiceProtocol

logger = logging.getLogger(__name__)


class ExecuteRequest(BaseModel):
    """Generic request body for the unified execute endpoint."""

    action: str
    params: dict[str, Any] = {}


class HTTPServiceAdapter:
    """Wraps a ServiceProtocol as a FastAPI router.

    The adapter creates two endpoints:
    - ``POST /execute`` — dispatch to ``service.execute(action, params)``
    - ``GET  /health``  — dispatch to ``service.health_check()``

    If the service provides ``list_actions()``, an additional
    ``GET /actions`` endpoint returns the list.
    """

    def __init__(
        self,
        service: ServiceProtocol,
        prefix: str = "",
        tags: list[str] | None = None,
    ) -> None:
        self._service = service
        self._prefix = prefix.rstrip("/")
        self._tags = tags or []

    def build_router(self) -> APIRouter:
        """Build and return the FastAPI router for this service."""
        router = APIRouter(prefix=self._prefix, tags=self._tags)

        @router.post("/execute")
        async def execute(req: ExecuteRequest) -> dict[str, Any]:
            try:
                result = await self._service.execute(req.action, req.params)
                return {"ok": True, "data": result}
            except HTTPException:
                raise
            except ValueError as exc:
                raise HTTPException(status_code=400, detail=str(exc))
            except Exception as exc:
                logger.exception("Service execute failed: %s", exc)
                raise HTTPException(status_code=500, detail="Internal service error")

        @router.get("/health")
        async def health() -> dict[str, bool]:
            ok = await self._service.health_check()
            return {"healthy": ok}

        actions = self._service.list_actions()
        if actions:

            @router.get("/actions")
            async def actions_list() -> dict[str, list[str]]:
                return {"actions": actions}

        return router


class DirectServiceProxy:
    """In-process proxy that calls service methods directly.

    Used when running inside the same Python process (web mode or
    Tauri sidecar). Avoids HTTP overhead.
    """

    def __init__(self, service: ServiceProtocol) -> None:
        self._service = service

    async def execute(self, action: str, params: dict[str, Any]) -> dict[str, Any]:
        return await self._service.execute(action, params)

    async def health_check(self) -> bool:
        return await self._service.health_check()
```

### Step 2.5: Create HTTP adapter tests

Create `backend/tests/test_http_adapter.py`:

```python
"""Tests for HTTPServiceAdapter and DirectServiceProxy."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.app.core.service_base import ServiceProtocol
from backend.app.services.adapters.http_adapter import (
    DirectServiceProxy,
    ExecuteRequest,
    HTTPServiceAdapter,
)


class DummyService(ServiceProtocol):
    """Minimal service implementation for testing."""

    async def execute(self, action: str, params: dict[str, Any]) -> dict[str, Any]:
        if action == "echo":
            return {"echoed": params.get("message", "")}
        if action == "fail":
            raise ValueError("intentional failure")
        raise KeyError(f"unknown action: {action}")

    async def health_check(self) -> bool:
        return True

    def list_actions(self) -> list[str]:
        return ["echo", "fail"]


@pytest.fixture
def client():
    service = DummyService()
    adapter = HTTPServiceAdapter(service=service, prefix="/test", tags=["test"])
    app = FastAPI()
    app.include_router(adapter.build_router())
    return TestClient(app)


class TestHTTPServiceAdapter:
    def test_execute_echo(self, client):
        resp = client.post("/test/execute", json={"action": "echo", "params": {"message": "hi"}})
        assert resp.status_code == 200
        data = resp.json()
        assert data["ok"] is True
        assert data["data"]["echoed"] == "hi"

    def test_execute_without_params(self, client):
        resp = client.post("/test/execute", json={"action": "echo"})
        assert resp.status_code == 200
        assert resp.json()["data"]["echoed"] == ""

    def test_execute_value_error_returns_400(self, client):
        resp = client.post("/test/execute", json={"action": "fail"})
        assert resp.status_code == 400
        assert "intentional failure" in resp.json()["detail"]

    def test_execute_unknown_action_returns_500(self, client):
        resp = client.post("/test/execute", json={"action": "nonexistent"})
        assert resp.status_code == 500

    def test_health_endpoint(self, client):
        resp = client.get("/test/health")
        assert resp.status_code == 200
        assert resp.json()["healthy"] is True

    def test_actions_endpoint(self, client):
        resp = client.get("/test/actions")
        assert resp.status_code == 200
        assert resp.json()["actions"] == ["echo", "fail"]


class TestDirectServiceProxy:
    @pytest.mark.asyncio
    async def test_execute_delegates(self):
        service = DummyService()
        proxy = DirectServiceProxy(service)
        result = await proxy.execute("echo", {"message": "test"})
        assert result == {"echoed": "test"}

    @pytest.mark.asyncio
    async def test_health_check_delegates(self):
        service = DummyService()
        proxy = DirectServiceProxy(service)
        assert await proxy.health_check() is True
```

### Step 2.6: Run tests

```bash
cd /home/adi/Desktop/Cortex-Workspace && python -m pytest backend/tests/test_http_adapter.py -v
```

---

## Task 3: Native Integration Hooks

**Goal:** Create abstraction layers for OS-level features (notifications, clipboard, system tray) that work via WebSocket in web mode and native Tauri calls in desktop mode.

**Files:**
- Create: `backend/app/services/native/__init__.py`
- Create: `backend/app/services/native/notifications.py`
- Create: `backend/app/services/native/clipboard.py`
- Create: `backend/app/services/native/tray.py`
- Create: `backend/tests/test_native_hooks.py`

### Step 3.1: Create the native package

Create `backend/app/services/native/__init__.py`:

```python
"""Native integration hooks for Tauri desktop features.

These modules provide abstraction layers that work in both web and
desktop contexts:

- **notifications**: OS notifications (Tauri) or WebSocket push (web)
- **clipboard**: System clipboard access (Tauri) or JS fallback (web)
- **tray**: System tray management (Tauri only, stub in web)
"""

from backend.app.services.native.clipboard import ClipboardProvider, get_clipboard
from backend.app.services.native.notifications import (
    NativeNotificationProvider,
    get_notification_provider,
)
from backend.app.services.native.tray import TrayManager, get_tray_manager

__all__ = [
    "ClipboardProvider",
    "NativeNotificationProvider",
    "TrayManager",
    "get_clipboard",
    "get_notification_provider",
    "get_tray_manager",
]
```

### Step 3.2: Create notification abstraction

Create `backend/app/services/native/notifications.py`:

```python
"""Native notification abstraction.

In web mode, notifications are pushed via the existing WebSocket
ConnectionManager. In Tauri desktop mode, they use the OS notification
API via tauri-plugin-notification.

The provider is selected at import time based on the CORTEX_RUN_MODE
environment variable (or can be overridden for testing).
"""

from __future__ import annotations

import logging
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class NotificationPayload:
    """Data for a single notification."""

    title: str
    body: str
    channel: str = "default"
    icon: str | None = None
    action_url: str | None = None


class NativeNotificationProvider(ABC):
    """Abstract base for notification delivery."""

    @abstractmethod
    async def send(self, payload: NotificationPayload) -> bool:
        """Send a notification. Returns True on success."""
        ...

    @abstractmethod
    async def send_to_user(
        self,
        user_id: int,
        title: str,
        body: str,
        channel: str = "default",
    ) -> bool:
        """Send a notification scoped to a specific user."""
        ...


class WebSocketNotificationProvider(NativeNotificationProvider):
    """Web-mode provider: pushes notifications over the existing WebSocket."""

    def __init__(self) -> None:
        self._manager = None

    def _get_manager(self):
        if self._manager is None:
            from backend.app.core.websocket import manager

            self._manager = manager
        return self._manager

    async def send(self, payload: NotificationPayload) -> bool:
        try:
            mgr = self._get_manager()
            await mgr.broadcast(
                payload.channel,
                {
                    "type": "notification",
                    "title": payload.title,
                    "body": payload.body,
                    "icon": payload.icon,
                    "action_url": payload.action_url,
                },
            )
            return True
        except Exception as exc:
            logger.warning("WebSocket notification failed: %s", exc)
            return False

    async def send_to_user(
        self,
        user_id: int,
        title: str,
        body: str,
        channel: str = "default",
    ) -> bool:
        user_channel = f"user:{user_id}"
        payload = NotificationPayload(title=title, body=body, channel=user_channel)
        return await self.send(payload)


class TauriNotificationProvider(NativeNotificationProvider):
    """Desktop-mode provider: sends OS notifications via Tauri IPC.

    This provider is a stub that logs locally. The actual Tauri IPC
    bridge will be implemented when the desktop app is built. For now,
    it falls back to WebSocket notifications so the app works in both
    modes during development.
    """

    def __init__(self) -> None:
        self._fallback = WebSocketNotificationProvider()

    async def send(self, payload: NotificationPayload) -> bool:
        logger.info(
            "TAURI NOTIFY [%s]: %s — %s",
            payload.channel,
            payload.title,
            payload.body,
        )
        # In production this would call tauri-plugin-notification via IPC.
        # For now, also push via WebSocket so the web UI receives it.
        return await self._fallback.send(payload)

    async def send_to_user(
        self,
        user_id: int,
        title: str,
        body: str,
        channel: str = "default",
    ) -> bool:
        logger.info("TAURI NOTIFY [user:%d]: %s — %s", user_id, title, body)
        return await self._fallback.send_to_user(user_id, title, body, channel)


def get_notification_provider() -> NativeNotificationProvider:
    """Factory that returns the appropriate notification provider.

    Selects TauriNotificationProvider when CORTEX_RUN_MODE=tauri,
    otherwise returns WebSocketNotificationProvider.
    """
    mode = os.environ.get("CORTEX_RUN_MODE", "web")
    if mode == "tauri":
        return TauriNotificationProvider()
    return WebSocketNotificationProvider()
```

### Step 3.3: Create clipboard abstraction

Create `backend/app/services/native/clipboard.py`:

```python
"""Native clipboard abstraction.

In web mode, clipboard access is handled client-side via the JavaScript
Clipboard API. This backend module provides a server-side stub that the
frontend can call to read/write clipboard content when running in Tauri
desktop mode.

In Tauri, the Rust backend provides clipboard access via
tauri-plugin-clipboard. This module wraps that with a Python-friendly
interface.
"""

from __future__ import annotations

import logging
import os
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class ClipboardProvider(ABC):
    """Abstract base for clipboard operations."""

    @abstractmethod
    async def read_text(self) -> str | None:
        """Read text from the clipboard. Returns None if empty or unavailable."""
        ...

    @abstractmethod
    async def write_text(self, text: str) -> bool:
        """Write text to the clipboard. Returns True on success."""
        ...

    @abstractmethod
    async def read_image(self) -> bytes | None:
        """Read image data from the clipboard. Returns None if unavailable."""
        ...


class WebClipboardProvider(ClipboardProvider):
    """Web-mode stub: clipboard operations are handled client-side.

    Server-side calls return None / False since browsers don't allow
    server-side clipboard access. The frontend handles these via
    navigator.clipboard.
    """

    async def read_text(self) -> str | None:
        logger.debug("Clipboard read_text called in web mode — handled client-side")
        return None

    async def write_text(self, text: str) -> bool:
        logger.debug("Clipboard write_text called in web mode — handled client-side")
        return False

    async def read_image(self) -> bytes | None:
        logger.debug("Clipboard read_image called in web mode — handled client-side")
        return None


class TauriClipboardProvider(ClipboardProvider):
    """Desktop-mode provider: real clipboard access via Tauri IPC.

    This is a stub that will be connected to the Tauri IPC bridge.
    Falls back to web stub behavior during development.
    """

    async def read_text(self) -> str | None:
        logger.info("TAURI CLIPBOARD: read_text")
        # TODO: Call tauri-plugin-clipboard via IPC bridge
        return None

    async def write_text(self, text: str) -> bool:
        logger.info("TAURI CLIPBOARD: write_text (%d chars)", len(text))
        # TODO: Call tauri-plugin-clipboard via IPC bridge
        return False

    async def read_image(self) -> bytes | None:
        logger.info("TAURI CLIPBOARD: read_image")
        # TODO: Call tauri-plugin-clipboard via IPC bridge
        return None


def get_clipboard() -> ClipboardProvider:
    """Factory that returns the appropriate clipboard provider."""
    mode = os.environ.get("CORTEX_RUN_MODE", "web")
    if mode == "tauri":
        return TauriClipboardProvider()
    return WebClipboardProvider()
```

### Step 3.4: Create tray stub

Create `backend/app/services/native/tray.py`:

```python
"""System tray management stub for Tauri desktop.

The system tray is a Tauri-only feature. This module provides a Python
interface that will be called from the Tauri Rust backend via IPC.

In web mode, all methods are no-ops. In Tauri mode, they delegate to
the actual tray plugin.
"""

from __future__ import annotations

import logging
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class TrayMenuItem:
    """A single menu item in the system tray."""

    id: str
    label: str
    enabled: bool = True
    checked: bool = False
    separator: bool = False


@dataclass
class TrayConfig:
    """Configuration for the system tray icon."""

    tooltip: str = "Cortex Workspace"
    icon_path: str | None = None
    menu_items: list[TrayMenuItem] = field(default_factory=list)


class TrayManager(ABC):
    """Abstract base for system tray management."""

    @abstractmethod
    async def set_tooltip(self, tooltip: str) -> bool:
        """Update the tray icon tooltip."""
        ...

    @abstractmethod
    async def set_menu(self, items: list[TrayMenuItem]) -> bool:
        """Replace the tray context menu."""
        ...

    @abstractmethod
    async def set_icon(self, icon_path: str) -> bool:
        """Change the tray icon image."""
        ...

    @abstractmethod
    async def show_notification(self, title: str, body: str) -> bool:
        """Show a notification from the tray icon."""
        ...


class WebTrayManager(TrayManager):
    """No-op stub for web mode. System tray doesn't exist in browsers."""

    async def set_tooltip(self, tooltip: str) -> bool:
        return False

    async def set_menu(self, items: list[TrayMenuItem]) -> bool:
        return False

    async def set_icon(self, icon_path: str) -> bool:
        return False

    async def show_notification(self, title: str, body: str) -> bool:
        return False


class TauriTrayManager(TrayManager):
    """Desktop-mode tray manager via Tauri IPC.

    This is a stub. When the Tauri desktop app is built, these methods
    will call into the Rust backend via tauri-plugin-tray.
    """

    def __init__(self) -> None:
        self._config = TrayConfig()

    async def set_tooltip(self, tooltip: str) -> bool:
        self._config.tooltip = tooltip
        logger.info("TAURI TRAY: tooltip set to '%s'", tooltip)
        # TODO: IPC call to tauri-plugin-tray
        return True

    async def set_menu(self, items: list[TrayMenuItem]) -> bool:
        self._config.menu_items = items
        logger.info("TAURI TRAY: menu updated (%d items)", len(items))
        # TODO: IPC call to tauri-plugin-tray
        return True

    async def set_icon(self, icon_path: str) -> bool:
        self._config.icon_path = icon_path
        logger.info("TAURI TRAY: icon set to '%s'", icon_path)
        # TODO: IPC call to tauri-plugin-tray
        return True

    async def show_notification(self, title: str, body: str) -> bool:
        logger.info("TAURI TRAY NOTIFICATION: %s — %s", title, body)
        # TODO: IPC call to tauri-plugin-notification
        return True


def get_tray_manager() -> TrayManager:
    """Factory that returns the appropriate tray manager."""
    mode = os.environ.get("CORTEX_RUN_MODE", "web")
    if mode == "tauri":
        return TauriTrayManager()
    return WebTrayManager()
```

### Step 3.5: Create native hooks tests

Create `backend/tests/test_native_hooks.py`:

```python
"""Tests for native integration hooks."""

from __future__ import annotations

import os
from unittest.mock import AsyncMock, patch

import pytest

from backend.app.services.native.clipboard import (
    ClipboardProvider,
    WebClipboardProvider,
    get_clipboard,
)
from backend.app.services.native.notifications import (
    NativeNotificationProvider,
    NotificationPayload,
    WebSocketNotificationProvider,
    get_notification_provider,
)
from backend.app.services.native.tray import (
    TrayManager,
    TrayMenuItem,
    WebTrayManager,
    get_tray_manager,
)


# ── Notification tests ────────────────────────────────────────────────


class TestNotificationPayload:
    def test_defaults(self):
        p = NotificationPayload(title="Hi", body="World")
        assert p.channel == "default"
        assert p.icon is None
        assert p.action_url is None

    def test_custom_channel(self):
        p = NotificationPayload(title="Hi", body="World", channel="alerts")
        assert p.channel == "alerts"


class TestWebSocketNotificationProvider:
    @pytest.mark.asyncio
    async def test_send_broadcasts(self):
        provider = WebSocketNotificationProvider()
        mock_mgr = AsyncMock()
        provider._manager = mock_mgr

        payload = NotificationPayload(title="Test", body="Body", channel="ch")
        result = await provider.send(payload)
        assert result is True
        mock_mgr.broadcast.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_to_user_uses_user_channel(self):
        provider = WebSocketNotificationProvider()
        mock_mgr = AsyncMock()
        provider._manager = mock_mgr

        result = await provider.send_to_user(42, "Hello", "World")
        assert result is True
        call_args = mock_mgr.broadcast.call_args
        assert call_args[0][0] == "user:42"


class TestGetNotificationProvider:
    def test_web_mode(self):
        with patch.dict(os.environ, {"CORTEX_RUN_MODE": "web"}):
            provider = get_notification_provider()
            assert isinstance(provider, WebSocketNotificationProvider)

    def test_tauri_mode(self):
        with patch.dict(os.environ, {"CORTEX_RUN_MODE": "tauri"}):
            from backend.app.services.native.notifications import TauriNotificationProvider

            provider = get_notification_provider()
            assert isinstance(provider, TauriNotificationProvider)


# ── Clipboard tests ───────────────────────────────────────────────────


class TestWebClipboardProvider:
    @pytest.mark.asyncio
    async def test_read_text_returns_none(self):
        provider = WebClipboardProvider()
        assert await provider.read_text() is None

    @pytest.mark.asyncio
    async def test_write_text_returns_false(self):
        provider = WebClipboardProvider()
        assert await provider.write_text("hello") is False

    @pytest.mark.asyncio
    async def test_read_image_returns_none(self):
        provider = WebClipboardProvider()
        assert await provider.read_image() is None


class TestGetClipboard:
    def test_web_mode(self):
        with patch.dict(os.environ, {"CORTEX_RUN_MODE": "web"}):
            assert isinstance(get_clipboard(), WebClipboardProvider)

    def test_tauri_mode(self):
        with patch.dict(os.environ, {"CORTEX_RUN_MODE": "tauri"}):
            from backend.app.services.native.clipboard import TauriClipboardProvider

            assert isinstance(get_clipboard(), TauriClipboardProvider)


# ── Tray tests ────────────────────────────────────────────────────────


class TestTrayMenuItem:
    def test_defaults(self):
        item = TrayMenuItem(id="1", label="Test")
        assert item.enabled is True
        assert item.checked is False
        assert item.separator is False


class TestWebTrayManager:
    @pytest.mark.asyncio
    async def test_all_methods_return_false(self):
        mgr = WebTrayManager()
        assert await mgr.set_tooltip("x") is False
        assert await mgr.set_menu([]) is False
        assert await mgr.set_icon("x") is False
        assert await mgr.show_notification("x", "y") is False


class TestGetTrayManager:
    def test_web_mode(self):
        with patch.dict(os.environ, {"CORTEX_RUN_MODE": "web"}):
            assert isinstance(get_tray_manager(), WebTrayManager)

    def test_tauri_mode(self):
        with patch.dict(os.environ, {"CORTEX_RUN_MODE": "tauri"}):
            from backend.app.services.native.tray import TauriTrayManager

            assert isinstance(get_tray_manager(), TauriTrayManager)
```

### Step 3.6: Run tests

```bash
cd /home/adi/Desktop/Cortex-Workspace && python -m pytest backend/tests/test_native_hooks.py -v
```

---

## Final Verification

Run all Phase 7 tests together plus the existing test suite to confirm nothing is broken:

```bash
cd /home/adi/Desktop/Cortex-Workspace && python -m pytest backend/tests/test_storage_resolver.py backend/tests/test_http_adapter.py backend/tests/test_native_hooks.py -v
```

Then run the full existing test suite:

```bash
cd /home/adi/Desktop/Cortex-Workspace && python -m pytest backend/tests/ -v
```

If lint/typecheck tools are available:

```bash
cd /home/adi/Desktop/Cortex-Workspace && python -m ruff check backend/app/core/paths.py backend/app/core/service_base.py backend/app/services/adapters/ backend/app/services/native/
cd /home/adi/Desktop/Cortex-Workspace && python -m mypy backend/app/core/paths.py backend/app/core/service_base.py backend/app/services/adapters/ backend/app/services/native/ --ignore-missing-imports
```

---

## Exit Criteria

- [ ] `get_storage_resolver("tauri")` after `get_storage_resolver("web")` returns a tauri-mode resolver (not cached web)
- [ ] `reset_storage_resolver()` clears the singleton and forces re-creation
- [ ] All tests in `test_storage_resolver.py` pass
- [ ] `ServiceProtocol` has `list_actions()` method
- [ ] `HTTPServiceAdapter` wraps any `ServiceProtocol` as a FastAPI router with `/execute`, `/health`, `/actions`
- [ ] `DirectServiceProxy` wraps any `ServiceProtocol` for in-process calls
- [ ] All tests in `test_http_adapter.py` pass
- [ ] `backend/app/services/native/` package exists with `notifications.py`, `clipboard.py`, `tray.py`
- [ ] Each native module has a web-mode provider and a tauri-mode provider
- [ ] Factory functions (`get_notification_provider`, `get_clipboard`, `get_tray_manager`) select provider based on `CORTEX_RUN_MODE` env var
- [ ] All tests in `test_native_hooks.py` pass
- [ ] No hardcoded filesystem paths remain in any service file
- [ ] Architecture ready for Tauri v2 sidecar pattern
