# ADR-007: Three-Tier Embedding Fallback

**Status:** Revisiting
**Date:** 2026-06-24
**Deciders:** Adi + Claude Code
**See also:** ADR-015 (Pluggable Provider)

## Context

Cortex needs embeddings for vector search. A single provider creates a single point of failure. The system should work offline (local-first) but also support cloud providers.

## Decision

Use a hardcoded **three-tier embedding fallback** chain:
1. **ONNX** — local, default (no external dependencies)
2. **Ollama** — local, fallback (requires Ollama running)
3. **Mock** — development/testing only (returns zero vectors)

The system tries each tier in order and falls through on failure, ensuring local-first operation with graceful degradation.

## Current Decision

Hardcoded three-tier fallback:
1. ONNX (local, default)
2. Ollama (local, fallback)
3. Mock (development/testing)

## Proposed Revision (ADR-015)

Replace with Protocol-based provider registry:
- ONNX remains default
- Community can add providers
- Per-vault provider configuration

## Consequences

### Positive
- Works without external services (ONNX is local)
- Graceful degradation

### Negative
- Hardcoded — can't add new providers without forking
- Can't configure per-vault

## Related

- `backend/app/services/embedding_service.py` — Implementation (204 lines)
