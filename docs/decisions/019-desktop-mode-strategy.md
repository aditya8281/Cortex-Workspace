Last updated: 2026-06-28

# ADR-019: Desktop Mode Strategy

**Status:** Proposed
**Date:** 2026-06-24
**Deciders:** Adi + Claude Code
**Phase:** V3-V5

## Context

Cortex is currently server-mode only (Docker Compose). Desktop-first reorientation requires embedded databases, a native shell, and offline-first operation. The design spec exists but no formal ADR.

## Decision

- **Embedded by default:** SQLite + embedded Qdrant for desktop mode
- **Docker for power users:** Docker Compose remains for server/development
- **Tauri for shell:** Native desktop shell via Tauri (Rust + webview)
- **CLI for automation:** Command-line interface as primary automation surface

## Consequences

### Positive
- No Docker required for basic usage
- Offline-first by default
- Native desktop experience via Tauri

### Negative
- Two deployment modes to maintain
- Embedded databases have different characteristics than Docker services

## Related

- `docs/superpowers/specs/2026-06-25-cortex-reorientation-design.md` — Design spec
- `docs/decisions/019-desktop-mode-strategy.md` — This ADR
