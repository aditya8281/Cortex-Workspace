# V3 Phase 2: CLI TUI + Notifications + Native Integration

**Duration estimate:** 7-10 days
**Dependencies:** V3 Phase 1 (Tauri shell, embedded DBs)
**Risk:** Medium — TUI is new territory, native integration varies by platform

---

## Goals

Build CLI TUI (Ink-based terminal interface) for power users who prefer terminal over GUI. Add desktop notification system. Add native file system integration (watcher events → notifications, drag-and-drop). Make the desktop feel like a native app, not a wrapped web page.

## Deliverables

1. CLI TUI with Ink (React for terminals)
2. Real-time agent output in terminal
3. Interactive memory browser in terminal
4. Desktop notification system (agent done, memory consolidated, etc.)
5. File system integration (watcher → notifications)
6. Drag-and-drop file import
7. Native context menus
8. Keyboard shortcuts system

## Architectural Changes

```
BEFORE:
  CLI = 15 command stubs (TypeScript/Commander.js)
  Notifications = none
  File integration = manual import only

AFTER:
  CLI TUI = Ink-based interactive terminal (agent, memory, search)
  CLI commands = still work (non-interactive mode)
  Notifications = native desktop notifications via Tauri
  File integration = drag-and-drop, file watcher → auto-import
  Keyboard = global shortcuts system
```

## Backend Changes

### New Files

| File | Purpose |
|------|---------|
| `cli/src/tui/` | TUI package root |
| `cli/src/tui/app.tsx` | Main TUI app (Ink) |
| `cli/src/tui/components/agent.tsx` | Agent chat TUI |
| `cli/src/tui/components/memory.tsx` | Memory browser TUI |
| `cli/src/tui/components/search.tsx` | Search TUI |
| `cli/src/tui/components/status.tsx` | System status TUI |
| `cli/src/tui/hooks/useAgent.ts` | Agent streaming hook |
| `cli/src/tui/hooks/useMemory.ts` | Memory operations hook |
| `cli/src/tui/hooks/useSearch.ts` | Search hook |
| `cli/src/tui/theme.ts` | Terminal color theme |
| `backend/app/core/desktop/shortcuts.py` | Keyboard shortcut registry |
| `backend/app/core/desktop/menus.py` | Context menu definitions |
| `backend/app/core/desktop/dragdrop.py` | Drag-and-drop handler |

### CLI TUI Design

```bash
# Interactive modes
cortex tui                    # Full TUI with sidebar
cortex tui agent              # Agent chat only
cortex tui memory             # Memory browser only
cortex tui search             # Search interface only

# Non-interactive modes (still work)
cortex agent run "query"      # One-shot agent
cortex memory recall "topic"  # One-shot memory recall
cortex search "query"         # One-shot search
```

### Notification System

Events that trigger notifications:
- Agent run complete
- Memory consolidation complete
- File import complete
- Background task error
- System health warning

### Keyboard Shortcuts

Global shortcuts (system-wide):
- `Ctrl+Shift+Space`: Open/focus Cortex window
- `Ctrl+Shift+C`: Open command palette
- `Ctrl+Shift+M`: Quick memory recall
- `Ctrl+Shift+A`: Quick agent query

In-app shortcuts:
- Standard navigation (Ctrl+K, Ctrl+P, etc.)
- Vim keybindings option

## Frontend Changes

| Page | Change |
|------|--------|
| All pages | Keyboard shortcut hints in tooltips |
| Dashboard | Drag-and-drop zone for file import |
| Settings | New "Shortcuts" section for customizing keybindings |
| Settings | New "Notifications" section for notification preferences |

## Memory Changes

No changes. Memory system (V2) is complete.

## Retrieval Changes

No changes. Context providers (V2) are complete.

## Agent Changes

No changes. Agent loop (V1) is stable. TUI is a new interface, not a new agent behavior.

## Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Ink complexity | Medium | Medium | Start with simple TUI, iterate. Non-interactive CLI always available. |
| Platform shortcut conflicts | Medium | Low | Allow shortcut customization. Ship with safe defaults. |
| Notification spam | Low | Medium | Rate limiting. User-configurable per event type. |
| Drag-and-drop edge cases | Medium | Low | Graceful fallback to file picker dialog. |
| TUI accessibility | Medium | Medium | High contrast theme. Screen reader support where possible. |

## Exit Criteria

- [ ] `cortex tui` launches interactive terminal interface
- [ ] Agent chat works in TUI with streaming output
- [ ] Memory browser shows memories with search/filter
- [ ] Desktop notifications fire on agent completion
- [ ] Drag-and-drop imports files into vault
- [ ] Global hotkey opens/focuses app
- [ ] Context menus work on right-click
- [ ] All keyboard shortcuts work
- [ ] All V1-V3 Phase 1 tests pass
- [ ] New TUI tests (component + integration)
- [ ] `make lint` + `make format` clean
