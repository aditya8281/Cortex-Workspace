# v1.08: Awareness Expansion — CORTEX

**Document:** Version 1.08 Overview
**Authority:** Stage 6 — Master Versioned Implementation Roadmap
**Date:** 2026-06-27
**Type:** Capability Delivery

---

## Objective

Expand awareness to cover desktop, terminal, browser, clipboard, workspace, notification, calendar, email, running applications, and system resources. Build a comprehensive environmental perception layer where Cortex sees everything the user sees — their open windows, active terminals, browser tabs, clipboard contents, workspace structure, incoming notifications, calendar schedule, email activity, running applications, and system health — enabling truly context-aware assistance.

---

## Question

"Can Cortex see everything it needs to see?"

---

## What This Version Delivers

After completing v1.08, Cortex can perceive:

- **Desktop state** — Window list, focused application, window layout, screen resolution, desktop environment. Uses `xdotool` on Linux, `osascript` on macOS.
- **Terminal sessions** — Active shell processes (bash/zsh/fish), recent command history, working directories. Reads shell history files directly.
- **Browser activity** — Open tabs across Chrome/Firefox, current page URL and title. Connects via Chrome DevTools Protocol (CDP) or Firefox remote debugging.
- **Clipboard content** — Current clipboard text, clipboard change watching via polling. Uses `xclip` on Linux, `pbpaste`/`pbcopy` on macOS.
- **Workspace organization** — Directory structure, recently modified files, file types, project layout. OS-native filesystem access.
- **Notification events** — System notification recording, read/unread tracking, notification history. Event-driven via desktop notification APIs.
- **Calendar events** — Upcoming events, event details, time conflict detection. Pluggable provider architecture for CalDAV/Google Calendar.
- **Email summaries** — Recent emails, unread count, email search. Pluggable provider architecture for IMAP/Exchange.
- **Running applications** — Process list, resource usage, application focus tracking. Cross-platform via `ps`/`Task Manager`.
- **System resources** — CPU usage, memory pressure, disk space, network status. Native OS monitoring.

---

## Capabilities Delivered

| ID | Name | Domain | Priority | Architecture Principle |
|----|------|--------|----------|----------------------|
| A4 | Desktop Awareness | Awareness | Core | 1.3 (Daemon-First) — background polling, not blocking |
| A5 | Terminal Awareness | Awareness | Core | 1.4 (Separation of Concerns) — terminal service boundary |
| A6 | Browser Awareness | Awareness | Core | 1.2 (Graceful Degradation) — CDP unavailable → empty tabs |
| A7 | Clipboard Awareness | Awareness | Core | 1.1 (Local-First) — OS-native, no cloud dependency |
| A8 | Workspace Awareness | Awareness | Core | 1.4 (Separation of Concerns) — workspace service boundary |
| A10 | Notification Awareness | Awareness | Core | 1.3 (Daemon-First) — background notification listener |
| A11 | Calendar Awareness | Awareness | Core | 1.5 (Plugin Boundaries) — pluggable calendar providers |
| A12 | Email Awareness | Awareness | Core | 1.5 (Plugin Boundaries) — pluggable email providers |
| A13 | Running Application Awareness | Awareness | Core | 1.3 (Daemon-First) — background process monitoring |
| A16 | System Resource Awareness | Awareness | Core | 1.7 (Incremental Safety) — resource limits prevent runaway |

**Total: 10 capabilities**

---

## reference architecture Feature Traceability

| reference architecture Feature | Cortex Mapping | v1.08 Coverage |
|-----------------|----------------|----------------|
| Desktop state monitoring | A4 (Desktop Awareness) | Full — window list, focus, layout via OS tools |
| Terminal session tracking | A5 (Terminal Awareness) | Full — process list, history file parsing |
| Browser tab awareness | A6 (Browser Awareness) | Full — CDP integration for Chrome, remote debugging for Firefox |
| Clipboard watching | A7 (Clipboard Awareness) | Full — read/write/poll for Linux and macOS |
| File system awareness | A8 (Workspace Awareness) | Full — directory structure, recent files, file types |
| Notification awareness | A10 (Notification Awareness) | Full — event recording, read tracking |
| Calendar awareness | A11 (Calendar Awareness) | Full — pluggable provider, upcoming events |
| Email awareness | A12 (Email Awareness) | Full — pluggable provider, search, unread count |
| System resource monitoring | A16 (System Resource Awareness) | Full — CPU, memory, disk, network |

**reference architecture coverage for this version: 9 features, all fully covered.**

---

## Capability Mapping

```
v1.08 Awareness Expansion
├── P01: Desktop & Terminal (A4, A5)
│   ├── DesktopAwarenessService (xdotool/osascript integration)
│   ├── TerminalAwarenessService (ps parsing, history files)
│   ├── Cross-platform OS detection and fallback
│   └── Process timeout handling (5s max)
├── P02: Browser & Clipboard (A6, A7)
│   ├── BrowserAwarenessService (CDP, Firefox remote debugging)
│   ├── ClipboardAwarenessService (xclip/pbpaste, polling watcher)
│   ├── Platform-specific clipboard commands
│   └── Browser connection resilience
├── P03: Workspace & Notifications (A8, A10)
│   ├── WorkspaceAwarenessService (directory walker, file stats)
│   ├── NotificationAwarenessService (event recording, read tracking)
│   ├── Hidden directory filtering (node_modules, __pycache__)
│   └── Notification history management
├── P04: Calendar & Email (A11, A12)
│   ├── CalendarAwarenessService (pluggable provider, event management)
│   ├── EmailAwarenessService (pluggable provider, search)
│   ├── Provider protocol interfaces
│   └── In-memory stub providers for development
└── P05: API & Integration (all)
    ├── Awareness API endpoints (desktop, terminal, clipboard, etc.)
    ├── Awareness dashboard frontend
    ├── Real-time code analysis hooks
    ├── Cross-domain integration (awareness + memory + cognition)
    └── Comprehensive test suite
```

---

## Strengthened Definition of Done

- [ ] All 10 awareness expansion capabilities implemented and tested
- [ ] `DesktopAwarenessService` works on Linux (xdotool) and macOS (osascript)
- [ ] `TerminalAwarenessService` reads bash, zsh, and fish history files
- [ ] `BrowserAwarenessService` connects to Chrome via CDP and Firefox via remote debugging
- [ ] `ClipboardAwarenessService` reads/writes clipboard on Linux (xclip) and macOS (pbpaste/pbcopy)
- [ ] `WorkspaceAwarenessService` walks directories, filters hidden/irrelevant dirs
- [ ] `NotificationAwarenessService` records, retrieves, and tracks read status
- [ ] `CalendarAwarenessService` uses pluggable provider protocol (Protocol class)
- [ ] `EmailAwarenessService` uses pluggable provider protocol (Protocol class)
- [ ] All services have graceful degradation (subprocess timeout, file not found, connection refused)
- [ ] All subprocess calls have 5-second timeout to prevent blocking
- [ ] API endpoints have `response_model=` decorators per Architecture Principle 1.10
- [ ] Ownership checks on all user-scoped endpoints
- [ ] Frontend API client typed with TypeScript interfaces
- [ ] All existing tests pass (zero regression)
- [ ] New test coverage ≥ 80% for all new services
- [ ] `make lint` + `make format` clean
- [ ] `make hooks-merge` passes

---

## Expanded Risk Matrix

| Risk | Likelihood | Impact | Mitigation | Phase |
|------|-----------|--------|------------|-------|
| `xdotool` not installed on user's Linux system | High | Medium | Graceful fallback: return `{"status": "monitoring unavailable"}`; check tool availability at startup | P01 |
| Chrome DevTools Protocol connection refused | High | Medium | Try/except with 3s timeout; fallback to empty tabs; log warning | P02 |
| Shell history file permissions deny access | Medium | Low | Catch `PermissionError`; return empty list; log info message | P01 |
| Clipboard polling causes CPU spin | Low | Medium | 1-second interval minimum; asyncio.sleep yields control; configurable interval | P02 |
| Deep directory traversal causes performance issues on large workspaces | Medium | High | Max depth of 3 levels; skip `.git`, `node_modules`, `__pycache__`; limit results to 1000 files | P03 |
| Calendar/Email provider connection timeout blocks daemon | Medium | High | 10-second timeout on provider calls; run in background task; circuit breaker pattern | P04 |
| Subprocess injection via unsanitized shell commands | Low | Critical | Never pass user input to subprocess. All commands are hardcoded strings. Input validation on all API parameters. | P01-P04 |
| System resource monitoring reveals sensitive process information | Medium | Medium | Filter out system processes; only return user-owned processes; respect OS privacy settings | P05 |
| Browser extension privacy concerns (tab data) | Medium | High | All data local-only; no external transmission; user opt-in for browser monitoring; clear privacy notice | P02 |

---

## Architecture Principle Cross-References

| Principle | How v1.08 Adheres |
|-----------|-------------------|
| **1.1 Local-First** | All awareness data collected locally via OS-native tools. No cloud APIs for desktop, terminal, clipboard, or workspace monitoring. Calendar/Email providers connect to user's own accounts. |
| **1.2 Graceful Degradation** | Every awareness service has try/except with fallback. If `xdotool` missing → `{"status": "unavailable"}`. If Chrome CDP refused → empty tabs. If history file unreadable → empty list. No awareness failure crashes the daemon. |
| **1.3 Daemon-All services run as background tasks within the daemon process. No blocking on main event loop. Clipboard watcher uses asyncio.sleep. Calendar/email polling via arq jobs. |
| **1.4 Separation of Concerns** | Each awareness domain is its own service class. Desktop ≠ Terminal ≠ Browser ≠ Clipboard. Clean interfaces between services. No cross-service dependencies within the awareness layer. |
| **1.5 Plugin Boundaries** | Calendar and Email use `CalendarProviderProtocol` and `EmailProviderProtocol` (Python Protocol classes). Pluggable providers: CalDAV, Google Calendar, IMAP, Exchange. Stub providers for development. |
| **1.6 Evidence Over Opinion** | Awareness data is factual (window titles, file paths, process names). No interpretation layer in v1.08. Raw data only. |
| **1.7 Incremental Safety** | Each awareness service is independently testable. Subprocess calls have timeouts. File reads catch permission errors. No privilege escalation. System resource monitoring respects OS limits. |

---

## Downstream Dependency Impact

### Directly Blocked Versions

| Version | What It Needs from v1.08 | Impact if Delayed |
|---------|-------------------------|-------------------|
| **v1.11 (Interaction)** | Desktop/terminal/browser awareness for proactive suggestions. "I see you're editing config.py — need help?" | Cannot provide context-aware proactive assistance |
| **v1.13 (Autonomous Agents)** | Workspace and terminal awareness for agent execution context | Agents operate without environmental awareness |

### Indirect Dependencies

| Version | Why v1.08 Matters | Workaround |
|---------|-------------------|------------|
| **v1.09 (Learning Foundation)** | Awareness events feed into preference learning (which apps user uses, when they work) | Manual preference entry only |
| **v1.10 (Planning & Orchestration)** | Calendar awareness enables time-aware planning | User manually reports availability |
| **v1.12 (Developer Tools)** | Terminal and workspace awareness for dev context | Separate monitoring tools |
| **v1.14 (Advanced Intelligence)** | Multi-source awareness feeds into cross-domain reasoning | Single-source reasoning only |

### Integration Points with Other Versions

- **v1.04 (Awareness Foundation)** — v1.08 extends the base awareness layer with new provider services. Base polling infrastructure reused.
- **v1.07 (Memory Evolution)** — Awareness events become graph nodes. Desktop/terminal/browser events link to memories via cross-domain edges.
- **v1.09 (Learning Foundation)** — Awareness data feeds into preference learning (which apps, which hours, which patterns). User behavior extracted from awareness events.
- **v1.02 (Backend Architecture)** — Services use constructor injection pattern. Background polling uses arq + Redis job queue.

---

## Phases

| Phase | Name | Focus | Complexity | Duration | Capabilities |
|-------|------|-------|------------|----------|-------------|
| P01 | Desktop & Terminal | Desktop state detection, terminal session monitoring | High | 5-6 hours | A4, A5 |
| P02 | Browser & Clipboard | Browser tab monitoring, clipboard watching | Medium | 4-5 hours | A6, A7 |
| P03 | Workspace & Notifications | Workspace organization, notification hooks | Medium | 3-4 hours | A8, A10 |
| P04 | Calendar & Email | Calendar integration, email summaries | High | 4-5 hours | A11, A12 |
| P05 | API & Integration | All endpoints, frontend dashboard, cross-domain integration | Medium | 4-5 hours | A13, A16, all |

**Total estimated: 20-25 hours (3-4 days focused development)**

---

## Dependencies

**Depends on:** v1.04 (Awareness Foundation) — base awareness polling infrastructure
**Blocks:** v1.11 (Interaction — needs awareness for proactive suggestions), v1.13 (Autonomous Agents — needs awareness for execution context)

**External dependencies:**
- `xdotool` (Linux desktop interaction)
- `osascript` (macOS automation)
- Chrome DevTools Protocol (browser integration)
- `xclip`/`pbpaste` (clipboard access)
- Python `psutil` (system resource monitoring) — install via pip

**System requirements:**
- Linux: X11 display server (Wayland support limited)
- macOS: Accessibility permissions for `osascript`
- Chrome: `--remote-debugging-port=9222` flag enabled
- Firefox: `devtools.debugger.remote-enabled=true` in about:config

---

## Estimated Duration

6-7 days (20-25 hours focused development).

---

## Implementation Notes

### Service Protocol Interfaces

```python
# services/awareness/protocols.py

from typing import Protocol, List, Dict, Optional
from datetime import datetime

class CalendarProvider(Protocol):
    """Protocol for calendar providers."""
    async def get_events(self, start: datetime, end: datetime) -> List[Dict]: ...
    async def create_event(self, title: str, start: datetime, end: datetime, **kwargs) -> Dict: ...
    async def delete_event(self, event_id: str) -> bool: ...

class EmailProvider(Protocol):
    """Protocol for email providers."""
    async def get_recent(self, limit: int = 20) -> List[Dict]: ...
    async def search(self, query: str) -> List[Dict]: ...
    async def get_unread_count(self) -> int: ...

class SystemMonitor(Protocol):
    """Protocol for system resource monitoring."""
    async def get_cpu_usage(self) -> float: ...
    async def get_memory_usage(self) -> Dict: ...
    async def get_disk_usage(self) -> Dict: ...
```

### Subprocess Safety Pattern

All subprocess calls follow this pattern:

```python
import subprocess
import asyncio
from typing import Optional

async def safe_subprocess(cmd: list, timeout: float = 5.0) -> Optional[str]:
    """Run subprocess with timeout and error handling."""
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout
        )
        return result.stdout if result.returncode == 0 else None
    except (subprocess.TimeoutExpired, FileNotFoundError, PermissionError):
        return None
```

---

## Definition of Done

- [ ] All 10 awareness expansion capabilities implemented
- [ ] Awareness services in `services/awareness/`
- [ ] Cross-platform support (Linux + macOS)
- [ ] Graceful degradation on all external tool failures
- [ ] Subprocess calls have 5-second timeouts
- [ ] Calendar/Email use pluggable provider protocols
- [ ] API endpoints with ownership checks
- [ ] Frontend API client typed with TypeScript
- [ ] All tests passing (existing + new)
- [ ] `make lint` + `make format` clean
- [ ] `make hooks-merge` passes

---

## Readiness for Next Version

v1.08 is complete when Cortex has comprehensive environmental awareness. The following versions can proceed:

- **v1.11 (Interaction)** can build proactive suggestions on awareness data
- **v1.13 (Autonomous Agents)** can execute with full environmental context
- **v1.09 (Learning Foundation)** can extract user preferences from awareness patterns
- **v1.14 (Advanced Intelligence)** can reason across awareness + memory + learning
