# ADR-006: Next.js 15 + React 19 Frontend

**Status:** Accepted
**Date:** 2026-06-24
**Deciders:** Adi + Claude Code

## Context

Cortex needs a web frontend for the management UI, chat interface, and knowledge graph visualization. The frontend must support SSE streaming, dark-only design, and responsive layouts.

## Decision

Use Next.js 15 App Router with React 19, TypeScript 5.8, Tailwind 3.4.

## Consequences

### Positive
- Modern, well-supported stack
- SSR/SSG for performance
- TypeScript for type safety
- Tailwind for rapid styling

### Negative
- React ecosystem complexity
- Node.js runtime required

## Alternatives Considered

1. **SvelteKit** — Rejected. Open WebUI uses it, but Cortex already invested in React.
2. **Vanilla JS** — Rejected. Too primitive for complex UIs.

## Related

- `frontend/` — Next.js application
- `DESIGN.md` — Design system
