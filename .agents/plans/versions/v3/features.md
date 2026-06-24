# CORTEX V3: "The Desktop"

**Version:** 3
**Date:** 2026-06-25
**Status:** Planned

---

## 1. Goals

V3 makes CORTEX a native desktop application. Tauri shell, system tray, global hotkey, embedded databases, and a CLI TUI transform the experience from "server you access" to "application that lives on your machine."

This is the version where CORTEX fulfills its "local-first, native integration" pillar. The daemon is invisible. The desktop shell is the daily interface. The system tray is always available. Embedded databases eliminate Docker as a requirement.

### Primary Goals

1. **Tauri desktop shell** — System tray, global hotkey, command palette, settings, memory browser
2. **Embedded databases** — User-space PostgreSQL + in-process vectors. Docker optional, not required.
3. **CLI TUI** — Interactive terminal UI for power users (Ink-based)
4. **Unix socket IPC** — CLI and desktop shell connect via Unix socket (faster than HTTP for local)
5. **Desktop notifications** — System notifications for completed jobs, agent results, reminders

### Non-Goals (Explicitly Deferred)

- Daily productivity tools (V4)
- Task scheduler / automation (V4)
- MCP server (expose Cortex tools to others) (V5)
- Ecosystem features (V6)
- Community plugin marketplace (V5)

---

## 2. Scope

### 2.1 Tauri Desktop Shell

| Surface | V3 Implementation |
|---------|-------------------|
| System tray | Status icon (green/yellow/red). Quick actions: search, remember, ask. Mode toggle. |
| Global hotkey | Command palette summon (Cmd/Ctrl+Shift+Space). Clipboard capture. Quick search. |
| Command palette | Search across all indexed content. Natural language input. Trigger agent actions. |
| Settings | Provider selection, vault management, daemon configuration, notification preferences |
| Memory browser | Visual exploration of memory, graph, search results |
| Daemon status | Visual health indicators for all services |

**Design constraint:** The Tauri shell contains ZERO business logic. It is a presentation layer that connects to the daemon via IPC (Unix socket) or HTTP. If the daemon is down, the shell shows status — it does not attempt to work around it.

**Tech stack:** Tauri 2.x (Rust backend + web frontend). Uses existing Next.js components for the shell UI (shared design tokens, shared components).

### 2.2 Embedded Databases

| Service | Docker Mode (existing) | Embedded Mode (V3) |
|---------|----------------------|-------------------|
| PostgreSQL | PostgreSQL 16 in Docker | Embedded PostgreSQL (user-space, same port as start.sh) |
| Vector store | Qdrant in Docker | In-process vectors (turbovec-style scalar quantization) or embedded Qdrant |
| Cache | Redis in Docker | In-memory LRU (already works as fallback) |
| LLM | Ollama in Docker | llama.cpp / Ollama local (already works) |

**Scope boundary:** V3 makes Docker optional, not eliminated. Users who already run Docker can continue using containerized services. The default experience is zero-Docker.

**Benchmark requirement:** Before V3, benchmark embedded PostgreSQL vs SQLite for single-user desktop experience. Decision recorded in ADR.

### 2.3 CLI TUI (Ink-based)

| Feature | V3 Implementation |
|---------|-------------------|
| Interactive mode | `cortex` with no arguments launches TUI |
| Dashboard | Daemon status, recent activity, memory count, graph stats |
| Search | Interactive search with results display |
| Agent | Interactive chat with streaming output |
| Navigation | Arrow keys, tab completion, fuzzy find |

**Scope boundary:** TUI is additive. All V1 headless commands still work. TUI is for interactive use, headless is for scripting.

### 2.4 Unix Socket IPC

| Aspect | V3 Design |
|--------|----------|
| Socket path | `~/.cortex/cortexd.sock` |
| Protocol | HTTP over Unix socket (same FastAPI routes, different transport) |
| Fallback | HTTP (localhost) if socket unavailable |
| Security | File permissions on socket (owner-only) |

**Scope boundary:** Unix socket is an optimization for local connections. HTTP remains the default. CLI and Tauri shell prefer socket, fall back to HTTP.

### 2.5 Desktop Notifications

| Event | Notification |
|-------|-------------|
| Background job completed | "Index complete: 142 files processed" |
| Agent task completed | "Task complete: [summary]" |
| Memory decay | Silent (no notification) |
| Webhook received | "Webhook triggered: [name]" |
| Reminder | "Reminder: [content]" |
| Daemon error | "CORTEX: [error description]" |

**Scope boundary:** All notifications are opt-in. User controls which events generate notifications. Default: agent completion + errors only.

### 2.6 Additional V3 Capabilities

| Capability | Why |
|-----------|-----|
| Resource management | CPU/memory limits for daemon. Battery-aware throttling. |
| Sleep/wake triggers | Wake on: CLI command, API call, global hotkey, file change, webhook |
| Crash recovery UI | Desktop shell shows recovery status, offers manual restart |
| Version update notifications | Desktop shell checks for updates, notifies user |

---

## 3. Success Criteria

### Functional

| Criterion | Measure |
|-----------|---------|
| Tauri shell | Builds on Linux, macOS, Windows. System tray works on all platforms. |
| Global hotkey | Command palette appears in <100ms |
| Embedded databases | CORTEX starts without Docker. All features work. |
| CLI TUI | Interactive mode launches, displays dashboard, handles input |
| Unix socket | CLI connects via socket, falls back to HTTP |
| Notifications | System notifications fire for configured events |
| Zero regression | V1 + V2 functionality preserved. Web UI still works. |

### Quality

| Criterion | Measure |
|-----------|---------|
| Desktop startup | Shell launches in <500ms |
| Command palette | Appears in <100ms |
| Memory usage | Daemon + shell < 500MB total on idle |
| Battery | Daemon sleeps after configurable idle, wakes on trigger |
| Test count | V2 count + new desktop/CLI TUI tests |

---

## 4. User Impact

### Before V3

- CORTEX requires Docker to run (PostgreSQL, Redis, Qdrant)
- No desktop presence — browser-only interaction
- No system tray, no global hotkey, no native notifications
- CLI is headless only (no interactive TUI)
- User must manually start/stop services

### After V3

- CORTEX runs without Docker — embedded databases
- Desktop shell with system tray, global hotkey, command palette
- Native system notifications for background work
- CLI has interactive TUI for daily use
- Daemon auto-starts, sleeps when idle, wakes on trigger
- CORTEX feels like a native desktop application

### Who Benefits

| User | How |
|------|-----|
| Desktop users | Native experience, system tray, hotkey, notifications |
| Laptop users | Battery-aware, sleeps when idle, embedded (no Docker overhead) |
| Power users | CLI TUI, Unix socket, scriptable automation |
| Non-technical users | Zero-Docker installation, system tray simplicity |

---

## 5. Architecture Impact

### What Changes

```
V2:
  CLI → HTTP → daemon
  Browser → HTTP → daemon

V3:
  Tauri shell → Unix socket → daemon
  CLI (headless) → Unix socket → daemon
  CLI (TUI) → Unix socket → daemon
  Browser → HTTP → daemon (unchanged)
  Daemon → embedded PostgreSQL (no Docker)
  Daemon → in-process vectors (no Qdrant)
```

### New Components

| Component | Purpose |
|-----------|---------|
| Tauri crate (`crates/cortex-desktop/`) | Desktop shell, system tray, global hotkey |
| Unix socket server | FastAPI transport alongside HTTP |
| Embedded PostgreSQL adapter | User-space PostgreSQL (leveraging start.sh pattern) |
| In-process vector store | Scalar quantization, no external service |
| CLI TUI (Ink) | Interactive terminal interface |
| Notification service | System notification integration |
| Resource manager | CPU/memory limits, battery detection, throttling |

### What Stays

| Component | Why |
|-----------|-----|
| All V1 + V2 functionality | Daemon, agent, CLI, services, plugins, MCP |
| Web UI | Still works for remote access |
| Docker Compose | Still available for power users |
| HTTP API | Still the primary API transport |

---

## 6. UX Impact

### Surfaces (After V3)

| Surface | Status | Primary Use |
|---------|--------|-------------|
| Desktop shell (Tauri) | NEW | Daily interaction, settings, visual memory browser |
| CLI (headless) | Existing | Scripting, automation |
| CLI (TUI) | NEW | Interactive power-user interface |
| Command palette | NEW | Quick capture, search, trigger |
| Web UI | Existing | Remote access, complex visualizations |
| Local API | Existing | Integration, custom tooling |

### Interaction Model

| Before V3 | After V3 |
|-----------|----------|
| Open browser → navigate to localhost:3000 | Press hotkey → command palette appears instantly |
| `cortexd start` in terminal | Double-click app / auto-start on login |
| No notifications | System notifications for background work |
| Docker required | Zero-Docker installation |
| No visual memory exploration | Memory browser in desktop shell |

---

## 7. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Tauri build complexity | High | Medium | Start with minimal shell (tray + hotkey only). Add features incrementally. |
| Embedded database performance | Medium | High | Benchmark before implementation. SQLite fallback if PostgreSQL too heavy. |
| Cross-platform Tauri issues | Medium | Medium | Test on Linux, macOS, Windows early. Platform-specific quirks documented. |
| Unix socket permissions | Low | Low | Standard file permissions. Documented in setup guide. |
| Battery drain | Medium | Medium | Aggressive sleep policy. Configurable idle timeout. |
| Tauri + Next.js integration | Medium | Medium | Tauri webview uses existing Next.js build output. Shared design tokens. |

---

## 8. Exit Criteria (V3 Complete When)

- [ ] Tauri shell builds and runs on Linux, macOS, Windows
- [ ] System tray icon shows daemon status
- [ ] Global hotkey summons command palette
- [ ] Command palette searches across indexed content
- [ ] Embedded databases work (PostgreSQL + vectors without Docker)
- [ ] CLI TUI launches with dashboard
- [ ] Unix socket IPC works, HTTP fallback works
- [ ] Desktop notifications fire for configured events
- [ ] Daemon auto-starts on login (opt-in)
- [ ] Daemon sleeps after idle, wakes on trigger
- [ ] All V1 + V2 tests pass
- [ ] New desktop/CLI TUI tests
- [ ] Memory usage < 500MB (daemon + shell, idle)
- [ ] Command palette appears in <100ms
