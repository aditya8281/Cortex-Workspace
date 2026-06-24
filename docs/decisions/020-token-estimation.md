# ADR-020: Token Estimation

**Status:** Proposed
**Date:** 2026-06-24
**Deciders:** Adi + Claude Code
**Phase:** V2 Phase 2

## Context

Cortex currently estimates tokens with `len(text) // 4` — a rough character-based approximation. Different tokenizers produce different counts, and compaction timing depends on accurate counting.

## Decision

Install tiktoken. Use cl100k_base encoding as default. Add 10% safety margin.

## Consequences

### Positive
- Accurate token counting
- Proper compaction timing
- Model-agnostic (cl100k_base works for GPT-4, Claude, etc.)

### Negative
- tiktoken is a compiled dependency (Rust)
- 10% safety margin means slightly earlier compaction

## Related

- Compaction system (V2-V3)
