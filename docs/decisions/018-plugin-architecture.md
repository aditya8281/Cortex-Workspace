# ADR-018: Plugin Architecture

**Status:** Proposed
**Date:** 2026-06-24
**Deciders:** Adi + Claude Code
**Phase:** V2-V3

## Context

Cortex has no plugin system. Reference repos show the value: Open WebUI has 6 layers, AnythingLLM has 5, Strands has @tool + dynamic loading. Plugins enable community extensibility without forking.

## Decision

Three plugin layers with Protocol-based interfaces:
1. **Provider plugins** — LLM providers, embedding providers, vector stores
2. **Tool plugins** — Agent tools (search, web, filesystem)
3. **Pipeline plugins** — Processing pipelines (extraction, summarization, indexing)

Dynamic loading via entry points or directory scanning.

## Consequences

### Positive
- Community extensibility
- Clean separation of concerns
- Protocol-based = type-safe

### Negative
- Plugin interface design is critical — breaking changes are expensive
- Loading/dynamic discovery adds complexity

## Related

- ADR-015 (Pluggable Provider)
- V2-V3 phase plans
