# ADR-015: Pluggable Embedding Provider (Replaces ADR-007)

**Status:** Proposed
**Date:** 2026-06-24
**Deciders:** Adi + Claude Code
**Supersedes:** ADR-007 (Three-Tier Embedding Fallback)
**Phase:** V2 Phase 2 (service abstraction)

## Context

ADR-007 hardcoded a three-tier embedding fallback (ONNX → Ollama → mock). This can't be extended without forking and can't be configured per-vault. Reference repos (Mem0: 8 providers, LlamaIndex: 70+ backends) show the value of pluggable providers.

## Decision

Replace hardcoded fallback with Protocol-based provider registry:
- ONNX remains default
- Community can add providers
- Per-vault provider configuration

## Consequences

### Positive
- Extensible without forking
- Per-vault configuration
- Community contributions possible

### Negative
- More complex than hardcoded fallback
- Requires provider interface documentation

## Related

- `backend/app/services/embedding_service.py` — Current implementation (204 lines)
