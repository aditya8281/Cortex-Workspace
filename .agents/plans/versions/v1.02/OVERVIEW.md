# v1.02: Backend Architecture — reference architecture-Integrated Agent Foundation

**Document:** Version 1.02 Overview
**Authority:** Stage 6 — Master Versioned Implementation Roadmap
**Date:** 2026-06-27
**Type:** Architectural Improvement + Agent System Hardening
**Red Team Revision:** Restructured from 5 to 8 phases to incorporate all reference agent architecture features

---

## Objective

Transform the CORTEX backend from a monolithic architecture with a weak agent subsystem into a domain-organized, event-driven architecture with a hardened agent loop incorporating all 7 critical reference architecture-derived capabilities: streaming agent loop, context compaction, tool schemas, MCP integration, prompt security, per-turn tool policy, and detached runs.

---

## Question

"How do we transform a monolithic FastAPI backend with a weak agent subsystem into a domain-organized, event-driven architecture with a hardened agent loop that matches or exceeds the capabilities of the best reference implementations?"

---

## What This Version Delivers

After completing v1.02, CORTEX will have:

1. **Domain-organized API layer** — Endpoints grouped by business domain (memory, awareness, agent, workspace, cognition) instead of 22 flat router files
2. **Service boundary enforcement** — Clear ownership rules, dependency injection patterns, and inter-service communication contracts
3. **Event bus** — Internal pub/sub system for decoupled service communication with typed events
4. **Hardened agent loop** — Single streaming agent loop replacing Planner→Executor, with SSE streaming, tool call parsing, and response accumulation
5. **Context compaction** — Auto-compaction at 85% context window with structured Goal/Done/State/Pending summaries
6. **Tool schemas** — OpenAI-compatible JSON Schema definitions for all tools, enabling proper LLM function-calling
7. **Intent classification** — Casual message detection, intent routing (simple vs complex), greeting responses
8. **Stall/runaway detection** — Loop-breaker with iteration count, timeout detection, force-answer fallback
9. **Completion verification** — Fresh-context subagent to verify task completion with confidence scoring
10. **Detached agent runs** — Server-side persistence, replay buffer, subscriber fan-out for multi-device
11. **Per-turn tool policy** — Dynamic tool composition, plan mode restriction, MCP tool gating
12. **MCP integration** — Server discovery, tool wrapping, stdio/SSE transports, configuration management
13. **Tool infrastructure** — Registration, RAG-based selection, domain mapping, prompt security guards, execution sandbox
14. **Database schema updates** — Migration scripts with rollback, validation, performance indexes
15. **Observability foundation** — Token counting, TPS tracking, context usage, tool timing, structured logging

---

## Scope

### In Scope

- API router reorganization by domain (P01)
- Service boundary definitions and event bus (P02)
- Agent system hardening with all reference architecture features (P03) — **CRITICAL**
- MCP server integration lifecycle (P04)
- Tool infrastructure: registration, selection, security (P05)
- Database schema migrations and validation (P06)
- Observability: metrics, logging, baselines (P07)
- Integration testing, security scanning, performance benchmarks (P08)

### Out of Scope

- Frontend changes (v1.03+ concern)
- Memory subsystem rebuild (v1.03 concern)
- Desktop shell / Tauri integration (v1.03 concern)
- CLI surface expansion (v1.04 concern)
- Plugin system / marketplace (v1.05+ concern)
- Graph intelligence layer (v1.06+ concern)
- External MCP server implementations (consumption only)
- Production deployment configuration
- Cross-encoder reranking

---

## reference architecture Integration Reference

The following 7 critical features are derived from the reference architecture reference implementation (3,485-line streaming agent loop) and the CORTEX Constitution Sections 4.6 and 10.x. Each maps to one or more phases in this version.

| # | reference architecture Feature | Constitution Ref | Phase | Key Decision |
|---|-----------------|-----------------|-------|-------------|
| 1 | **Streaming Agent Loop** | 4.6, 10.1 | P03-T1 | Single async generator replacing Planner→Executor. Max 25 iterations. SSE streaming. |
| 2 | **Context Compaction** | 4.6, 10.4 | P03-T2 | Auto-compaction at 85% context window. Goal/Done/State/Pending structured summaries. |
| 3 | **Tool Schemas** | 4.6, 10.2 | P03-T3 | OpenAI-compatible JSON Schema for all tools. @tool decorator with auto-generated schemas from type hints. |
| 4 | **Prompt Security** | 4.6, 10.5 | P05-T4 | UNTRUSTED_SOURCE_DATA wrapping on all external content entering prompts. |
| 5 | **MCP Integration** | 4.6 | P04 | Server lifecycle management, tool wrapping, stdio + SSE transports. |
| 6 | **Detached Runs** | 4.6, 10.9 | P03-T7 | Server-side persistence with replay buffer. Survives daemon restart. Subscriber fan-out. |
| 7 | **Per-Turn Tool Policy** | 4.6, 10.3 | P03-T8 | Dynamic composition: allow/deny/ask per tool per turn. Replaces HMAC approval tokens. |

Additional hardening features (also reference architecture-derived):

| Feature | Constitution Ref | Phase | Description |
|---------|-----------------|-------|-------------|
| Intent Classification | 4.6, 10.6 | P03-T4 | Classify messages as casual/admin/agent/continuation before entering loop |
| Stall/Runaway Detection | 4.6, 10.7 | P03-T5 | Detect repeated identical tool calls, force answer after threshold |
| Completion Verification | 4.6, 10.8 | P03-T6 | Fresh-context subagent verifies task completion with confidence score |
| RAG-based Tool Selection | 10.2 | P05-T2 | Embed tool descriptions, vector similarity search for top-K tool retrieval |
| Tool Execution Sandbox | 10.2 | P05-T5 | Resource limits, timeouts, output size limits per tool |

---

## Phases

| Phase | Name | Focus | Dependencies | Est. Days | Complexity |
|-------|------|-------|-------------|-----------|------------|
| P01 | API Domain Reorganization | Move endpoints to domain routers | v1.01 | 3-4 | Medium |
| P02 | Service Boundaries + Event Bus | Domain services + typed event system | P01 | 4-5 | High |
| P03 | Agent System Hardening | Streaming loop, compaction, tool schemas, security | P02 | 7-10 | **Very High** |
| P04 | MCP Integration | Server discovery, tool wrapping, transports | P03 | 3-4 | High |
| P05 | Tool Infrastructure | Registration, RAG selection, prompt security | P03 | 4-5 | High |
| P06 | Database Schema Updates | Migrations, validation, indexes | P01 | 2-3 | Medium |
| P07 | Observability Foundation | Metrics, logging, baselines | P02, P03 | 3-4 | Medium |
| P08 | Integration & Testing | E2E tests, security scan, performance benchmarks | All | 4-5 | High |

---

## Detailed Dependency Diagram

```
v1.01 (Repository Restructure) [PREREQUISITE]
  │
  ▼
P01 (API Domain Reorganization) ─── 3-4 days
  │
  ├───► P02 (Service Boundaries + Event Bus) ─── 4-5 days
  │         │
  │         ├───► P03 (Agent System Hardening) ◄── CRITICAL PATH ── 7-10 days
  │         │         │
  │         │         ├───► P04 (MCP Integration) ──────────┐
  │         │         │                  3-4 days            │
  │         │         │                                     │
  │         │         ├───► P05 (Tool Infrastructure) ──────┤
  │         │         │                  4-5 days            │
  │         │         │                                     │
  │         │         └───► P07 (Observability Foundation) ──┤
  │         │                          3-4 days              │
  │         │                                               │
  │         └───► P06 (Database Schema Updates) ────────────┤
  │                       2-3 days                          │
  │                                                         │
  └─────────────────────────────────────────────────────────┘
                            │
                            ▼
               P08 (Integration & Testing) ─── 4-5 days
```

**Critical path:** P01 (4) → P02 (5) → P03 (10) → P07 (4) → P08 (5) = **28 days sequential**
**Parallel opportunities:** P04 ∥ P05 (both depend only on P03), P06 (depends only on P01)

---

## Capability Mapping

This version covers 25 of the 120 approved capabilities (21%). These are the foundational capabilities that enable all subsequent versions.

### Agent Domain (12 capabilities)

| # | Capability | Phase | Task | Constitution Ref |
|---|-----------|-------|------|-----------------|
| A1 | Streaming Agent Loop | P03 | T1 | 10.1 |
| A2 | Context Compaction | P03 | T2 | 10.4 |
| A3 | Tool Schemas | P03 | T3 | 10.2 |
| A4 | Intent Classification | P03 | T4 | 10.6 |
| A5 | Stall Detection | P03 | T5 | 10.7 |
| A6 | Completion Verification | P03 | T6 | 10.8 |
| A7 | Detached Agent Runs | P03 | T7 | 10.9 |
| A8 | Per-Turn Tool Policy | P03 | T8 | 10.3 |
| A9 | Tool Registration & Discovery | P05 | T1 | 10.2 |
| A10 | RAG-based Tool Selection | P05 | T2 | 10.2 |
| A11 | Tool Domain Mapping | P05 | T3 | — |
| A12 | Tool Execution Sandbox | P05 | T5 | 10.2 |

### MCP Domain (5 capabilities)

| # | Capability | Phase | Task |
|---|-----------|-------|------|
| M1 | MCP Server Discovery | P04 | T1 |
| M2 | MCP Tool Wrapping | P04 | T2 |
| M3 | MCP Transport Layers | P04 | T3 |
| M4 | MCP Configuration | P04 | T4 |
| M5 | MCP Tool Search | P04 | T5 |

### Architecture Domain (8 capabilities)

| # | Capability | Phase | Task |
|---|-----------|-------|------|
| R1 | API Domain Organization | P01 | T1-T5 |
| R2 | Service Boundary Enforcement | P02 | T1-T2 |
| R3 | Event Bus | P02 | T3-T5 |
| R4 | Database Migrations | P06 | T1-T3 |
| R5 | Prompt Security Guards | P05 | T4 |
| R6 | Token Counting | P07 | T1 |
| R7 | Structured Logging | P07 | T5 |
| R8 | Performance Baseline | P07 | T6 |

---

## Risk Matrix

| Risk | Severity | Probability | Impact | Mitigation | Phase |
|------|----------|-------------|--------|------------|-------|
| Agent loop rewrite introduces regressions | **Critical** | High | Agent subsystem non-functional | TDD for every component. Preserve backward-compatible API. Feature flag for new vs old loop. | P03 |
| Compaction loses critical context | **High** | Medium | User loses work context | Structured summary format preserves all task state. A/B testing with manual review. | P03 |
| MCP transport failures cascade | **High** | Medium | External tools unavailable | Circuit breaker pattern. Health monitoring every 30s. Graceful degradation to built-in tools only. | P04 |
| Prompt injection via retrieved content | **High** | Low | Agent executes malicious instructions | UNTRUSTED_SOURCE_DATA wrapping. Content sanitization. Injection detection patterns. | P05 |
| Event bus becomes bottleneck | **Medium** | Low | Inter-domain communication delayed | In-process async by default. External Redis bus only for cross-process. Backpressure handling. | P02 |
| Schema migration breaks existing data | **High** | Low | Data loss | Rollback scripts for every migration. Staged rollout. Backup before migrate. | P06 |
| Performance regression from new agent components | **Medium** | Medium | Slower user experience | Baseline metrics before. Performance gates in CI. Continuous benchmarking. | P07 |
| Tool selection accuracy degrades with tool count | **Medium** | Medium | Wrong tools selected, wasted tokens | Embedding quality testing. Fallback to keyword search. Top-K tuning. | P05 |
| Detached run state corruption | **High** | Low | Agent state lost on restart | Write-ahead log. Atomic state updates. Crash recovery tests. | P03 |
| Per-turn tool policy bypass | **Critical** | Low | Unauthorized tool execution | Security tests for every policy path. Audit logging. No bypass exceptions. | P03 |
| Circular imports after reorganization | **Medium** | High | Import errors at startup | Import validation in CI. Dependency direction enforcement. | P01, P02 |

---

## Performance Targets

| Metric | Target | Measurement Point | Phase |
|--------|--------|-------------------|-------|
| Agent loop first token latency | < 200ms (local), < 500ms (remote) | Time from user message to first SSE event | P03 |
| Agent loop streaming throughput | ≥ 30 tokens/sec | TPS measured at SSE endpoint | P07 |
| Context compaction time | < 3s for 100K token context | End-to-end compaction call duration | P03 |
| Tool execution p95 latency | < 500ms | Per-tool execution time (excluding LLM) | P07 |
| MCP server connection time | < 1s for local stdio | Time from discovery to ready state | P04 |
| MCP tool call round-trip | < 2s local, < 5s remote | Tool call initiation to response received | P04 |
| API response time p95 | < 100ms for non-agent endpoints | HTTP response time at load balancer | P01 |
| Event bus delivery latency | < 10ms for in-process | Event publish to handler execution | P02 |
| Tool selection accuracy | ≥ 85% relevant tools in top-5 | Human evaluation of tool relevance | P05 |
| Memory overhead for agent subsystem | < 200MB | RSS delta after agent initialization | P07 |
| Prompt injection detection rate | ≥ 95% | Test suite of 100 injection payloads | P05 |

---

## Estimated Duration

**25-35 days** (revised from 17-25 days in original plan)

| Phase | Days | Notes |
|-------|------|-------|
| P01 | 3-4 | API domain reorganization. Mechanical but requires careful validation. |
| P02 | 4-5 | Service boundaries + event bus. Foundation for all subsequent phases. |
| P03 | 7-10 | **Agent system hardening.** Largest, highest risk. 8 tasks covering all reference architecture features. |
| P04 | 3-4 | MCP integration. Can run parallel with P05. |
| P05 | 4-5 | Tool infrastructure. Can run parallel with P04. |
| P06 | 2-3 | Database schema updates. Can run parallel with P02-P05. |
| P07 | 3-4 | Observability. Depends on P03 for agent metrics. |
| P08 | 4-5 | Integration testing. Depends on all other phases. |

**Critical path duration:** 28 days (P01 + P02 + P03 + P07 + P08)
**With parallelism:** 25 days minimum (P04 ∥ P05, P06 ∥ P02)

---

## Definition of Done

### Functional Requirements

- [ ] All API endpoints respond correctly from domain-organized routers
- [ ] Event bus delivers typed events to registered handlers with zero message loss
- [ ] Agent loop streams responses via SSE with tool call parsing and response accumulation
- [ ] Context compaction triggers at 85% context utilization and produces valid Goal/Done/State/Pending summaries
- [ ] All tools have OpenAI-compatible JSON Schema definitions with full parameter specs
- [ ] Intent classifier correctly routes casual/admin/agent/continuation messages with ≥ 90% accuracy
- [ ] Stall detection identifies repeated identical tool calls within 3 iterations
- [ ] Completion verifier produces confidence score ≥ 0.8 for completed tasks
- [ ] Detached runs survive daemon restart with full replay capability
- [ ] Per-turn tool policy enforces allow/deny/ask correctly for all tool categories
- [ ] MCP servers are discovered, connected, and their tools are accessible through Cortex
- [ ] External content is wrapped in UNTRUSTED_SOURCE_DATA markers before entering any prompt
- [ ] Tool execution enforces resource limits (timeout, output size) and handles errors gracefully
- [ ] All database migrations apply cleanly and roll back cleanly
- [ ] Token counting, TPS tracking, and context usage metrics are accurate within 5%

### Quality Requirements

- [ ] All existing v1.01 tests pass (zero regression)
- [ ] New test coverage ≥ 90% for P03 (agent system) — the critical phase
- [ ] New test coverage ≥ 80% for all other phases
- [ ] Lint clean: `make lint` passes with zero warnings
- [ ] Type checking clean: `make typecheck` passes
- [ ] No circular imports between domains (validated by import check script)
- [ ] Import paths validated across all reorganized modules
- [ ] All code follows existing patterns: constructor injection, `get_db()` generator, `response_model=` on routes

### Security Requirements

- [ ] Prompt injection detection catches ≥ 95% of test payloads (100+ test cases)
- [ ] UNTRUSTED_SOURCE_DATA wrapping verified for all 7 external content paths (retrieval, files, search, MCP output, web fetch, user uploads, graph results)
- [ ] Tool policy bypass attempts are logged and blocked (10+ attack vectors tested)
- [ ] MCP tool calls subject to same security checks as built-in tools
- [ ] No SSRF, path traversal, or command injection vectors in tool execution
- [ ] Audit log captures all security-relevant events with structured format

### Performance Requirements

- [ ] Agent loop first token latency within target (< 200ms local)
- [ ] Streaming throughput ≥ 30 TPS sustained
- [ ] Context compaction completes within target (< 3s for 100K tokens)
- [ ] No memory leak in long-running agent sessions (tested with 100-turn conversation)
- [ ] Event bus handles 1000 events/second without backlog
- [ ] API response time p95 < 100ms for non-agent endpoints

### Integration Requirements

- [ ] Cross-domain integration tests pass (agent ↔ memory, agent ↔ tools, agent ↔ MCP, tools ↔ MCP)
- [ ] Agent loop end-to-end test covers: user message → intent classification → tool calls → compaction → response
- [ ] MCP integration test covers: server discovery → connect → tool call → response → disconnect
- [ ] Performance benchmark test establishes baseline metrics for all key operations
- [ ] Regression test suite covers all v1.02 features (target: 200+ test cases)
- [ ] Security scan passes with zero critical/high findings

---

## References

| Document | Location | Purpose |
|----------|----------|---------|
| Constitution | `.agents/plans/guide.md` | Architecture principles (Sections 4.6, 10.x for agent) |
| Implementation Guide | `.agents/plans/implementation_steps.md` | Execution order and constraints |
| FinalCompatibilities | `.agents/plans/FinalCompatibilities.md` | Cross-version capability mapping |
| Backend Snapshot | `.agents/plans/artifacts/backend_snapshot.md` | Current agent system inventory (60 files, 5,637 lines) |
| Migration Map | `.agents/plans/artifacts/migration_map.md` | File movement targets |
| Gap Analysis | `.agents/plans/artifacts/gap_analysis.md` | Missing capabilities (97 of 120) |
| Capability Model | `.agents/plans/artifacts/capability_model.md` | 120-capability taxonomy |
| Feature Inventory | `.agents/plans/artifacts/feature_inventory.md` | Current feature status |
| reference architecture Audit | `.agents/plans/artifacts/final_recommendations.md` | Red team findings driving this restructure |
