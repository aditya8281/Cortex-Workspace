# ADR-012: "Warm Neural Dark" Design System

**Status:** Accepted
**Date:** 2026-06-24
**Deciders:** Adi + Claude Code

## Context

Cortex needs a distinctive visual identity. The frontend should feel like a neural interface — dark, warm, slightly futuristic.

## Decision

Dark-only glassmorphism design system:
- Cyan accent (#00d4ff) as primary
- Warm neutrals for text and backgrounds
- Glassmorphism with backdrop-blur
- NeuralNetwork animated canvas background

## Consequences

### Positive
- Distinctive, cohesive visual identity
- Dark-only simplifies design decisions
- Glassmorphism provides depth without heavy styling

### Negative
- Dark-only excludes light mode users
- Animated background may impact performance on low-end devices

## Related

- `DESIGN.md` — Full design system (207 lines)
- `frontend/src/styles/tokens.ts` — Design tokens
