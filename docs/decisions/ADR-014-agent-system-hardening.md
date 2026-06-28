Last updated: 2026-06-28

# ADR-014: Agent System Hardening (v1.02 P03)

**Date:** 2026-06-27
**Status:** Accepted
**Deciders:** Cortex Team

---

## Context

The agent system built in v1.01 had a solid foundation (streaming loop, tool parsing, stall detection, compaction, verification) but lacked structured outputs, per-turn policy control, and confidence-based completion verification. P03 enhances these components without rewriting the core loop.

## Decision

Enhance existing agent components with structured outputs and additional capabilities:

### 1. StallDetector Enhancement
- Added `StallDetection` dataclass for structured output
- Added timeout detection (wall clock, default 300s)
- Added repeated identical LLM response detection
- Added max iteration detection
- Combined `check()` method runs all checks in priority order
- Backward compatible: existing `is_stalled()` + `record_call()` still work

### 2. CompletionVerifier Enhancement
- Added `VerificationResult` dataclass with confidence score (0.0-1.0)
- Added `CompletionVerifier` class with stats tracking
- `verify_sync()` for heuristic verification (no LLM)
- `verify()` async for fresh-context LLM verification
- Legacy `verify_completion()` function preserved for backward compat

### 3. ContextCompactor Enhancement
- Added `CompactionResult` dataclass with structured output
- Added `ContextCompactor` class with stats tracking
- `should_compact()` check based on token count vs threshold
- `compact_sync()` for synchronous compaction
- `_parse_sections()` for Goal/Done/State/Pending parsing

### 4. ToolPolicy Enhancement
- Plan mode: `enable_plan_mode()` / `disable_plan_mode()` restricts to read-only tools
- MCP tool gating: `enable_mcp_tool()` / `disable_mcp_tool()` for MCP tools
- Approve/revoke flow: `approve()` / `revoke_approval()` for "ask" tools
- `reset()` clears all state (plan mode, approvals, MCP tools, rules)
- Evaluation order: plan mode → MCP gating → approvals → rules → usage limits → default

### 5. Integration Tests
- Tool call parsing (nested parens, multiple calls)
- Tool call stripping (preserves user-visible text)
- Argument type coercion (int, bool, None)
- Completion signal detection
- Agent loop flow (casual shortcircuit, max iterations enforced)

## Consequences

**Positive:**
- All components have structured outputs (dataclasses) for observability
- Tool policy supports fine-grained per-turn control
- Integration tests validate end-to-end agent loop behavior
- Backward compatible — existing code continues to work

**Negative:**
- ToolPolicy `default_policy()` changed: `write_file` and `web_fetch` now "allow" (was "ask")
- `reset()` on ToolPolicy clears rules (breaking for code that relied on reset only clearing counts)

**Mitigations:**
- Updated existing tests to match new defaults
- Documented breaking changes in ADR
