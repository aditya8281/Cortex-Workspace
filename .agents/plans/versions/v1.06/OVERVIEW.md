# v1.06: Cognition & Execution Core — CORTEX

**Document:** Version 1.06 Overview
**Authority:** Stage 6 — Master Versioned Implementation Roadmap
**Date:** 2026-06-27
**Type:** Capability Delivery

---

## Objective

Build the cognitive processing core and execution foundation: task planning with DAG-based decomposition, error analysis with pattern matching and root cause determination, hypothesis generation with Bayesian confidence updating, tool execution with sandboxed validation and confirmation gates, workflow orchestration with dependency resolution, and action verification with safety rules.

---

## Question

"Can Cortex think and act?"

---

## What This Version Delivers

After completing v1.06, Cortex can:

- **Plan Tasks (C4):** Decompose complex goals into ordered step DAGs with dependencies, parallel tracks, and confidence estimation. Plans are persisted, trackable, and interruptible.
- **Analyze Errors (C10):** Classify errors by type, determine root causes via pattern matching against historical data, suggest resolutions, and learn prevention strategies. Error patterns are aggregated for systematic improvement.
- **Generate Hypotheses (C9):** Form hypotheses from evidence, track supporting and contradicting evidence, update confidence scores using Bayesian reasoning, and resolve hypotheses as confirmed or rejected. Hypotheses inform planning decisions.
- **Estimate Confidence (C6):** Score confidence in any reasoning output based on task type, historical success rates, novelty, data quality, and evidence balance. Confidence drives whether to proceed autonomously or request user confirmation.
- **Execute Tools (E2):** Register tools with typed parameter schemas, validate inputs, execute in isolated context, record results and timing, handle failures gracefully. Dangerous operations require explicit confirmation.
- **Orchestrate Workflows (E6):** Chain tool executions into multi-step workflows with dependency graphs, conditional branching, error recovery, and parallel execution. Workflows are resumable and cancellable.
- **Verify Actions (E10):** Pre-flight safety checks on every action: dangerous pattern detection, resource limits, permission validation, side-effect analysis. Actions blocked if verification fails.
- **Automate Routines (E5):** Schedule and trigger workflow execution based on events or time, with retry logic and exponential backoff on failure.

---

## reference architecture Feature Traceability

| reference architecture Feature | Cortex Capability | Implementation |
|-----------------|-------------------|----------------|
| Task Planning | C4 | DAG-based TaskPlanningService with dependency resolution |
| Error Recovery | C10, E6 | ErrorAnalysisService + WorkflowOrchestrator retry logic |
| Confidence Scoring | C6 | Bayesian ConfidenceEstimationService |
| Hypothesis Testing | C9 | HypothesisService with evidence tracking |
| Tool Use | E2, E10 | ExecutionEngine with ToolRegistry + ActionVerifier |
| Workflow Automation | E5, E6 | WorkflowOrchestrator with conditional branching |
| Safety Guards | E10 | ActionVerifier with dangerous pattern detection |
| Learning from Mistakes | C10 | ErrorAnalysisService pattern aggregation feeds back to planning |

---

## Capability Mapping

| ID | Name | Domain | Priority | Description |
|----|------|--------|----------|-------------|
| C4 | Reasoning | Cognition | Foundation | Draws conclusions from evidence; DAG-based task decomposition; step-by-step plan execution. |
| C6 | Confidence Estimation | Cognition | Foundation | Scores confidence 0-100 on any reasoning output; explains factors; drives autonomous vs. user-confirm decisions. |
| C9 | Problem Solving | Cognition | Core | Systematic hypothesis generation; evidence tracking; Bayesian confidence updating; resolution lifecycle. |
| C10 | Error Analysis | Cognition | Core | Classifies errors; pattern matching against history; root cause determination; resolution and prevention suggestions. |
| E2 | Automation | Execution | Core | Automates routine tasks; tool registration with typed schemas; sandboxed execution; result recording. |
| E5 | Permission Management | Foundation | Foundation | Controls which actions are allowed; pre-flight checks; resource limits; dangerous operation blocking. |
| E6 | Recovery | Execution | Core | Recovers from automation failures; retry with backoff; checkpoint/resume in workflows; partial result preservation. |
| E10 | Execution History | Execution | Core | Records all actions with timing, results, errors; queryable history for learning and debugging. |

**Total: 8 capabilities**

---

## Phases

| Phase | Name | Focus | Complexity | Duration |
|-------|------|-------|------------|----------|
| P01 | Cognition Models & Schema | Reasoning models, hypothesis models, confidence scoring schema, tool execution models, workflow models | Medium | 1.0 day |
| P02 | Planning & Error Analysis | DAG-based TaskPlanningService, ErrorAnalysisService with pattern matching, plan decomposition engine | High | 1.5 days |
| P03 | Hypothesis & Confidence | HypothesisService with Bayesian updating, ConfidenceEstimationService with multi-factor scoring | High | 1.0 day |
| P04 | Tool Execution | ToolRegistry with validation, ExecutionEngine with sandbox, ActionVerifier, WorkflowOrchestrator with DAG | High | 1.5 days |
| P05 | API & Integration | REST endpoints for all cognition/execution services, frontend API clients, real-time tool execution view | Medium | 1.0 day |

**Total estimated: 6-7 days**

---

## Architecture Principle Cross-References

This version engages the following architecture principles from `.agents/plans/guide.md`:

| Principle | Section | Relevance to v1.06 |
|-----------|---------|---------------------|
| Daemon Architecture | 4.1 | Cognition services run as daemon-internal singletons; execution engine integrates with daemon lifecycle |
| Memory Architecture | 4.3 | Planning accesses memory for context; error analysis learns from memory patterns; hypotheses query memory for evidence |
| Graph Architecture | 4.4 | Task DAGs mirror graph structures; hypothesis evidence forms a belief graph; error patterns form a failure graph |
| Retrieval Architecture | 4.5 | Planning uses RAG to gather context; confidence estimation uses retrieval quality as a factor |
| Agent Architecture | 4.6 | Agent loop uses planning for decomposition; agent uses tools via execution engine; agent confidence gates autonomy level |
| Workflow Architecture | 4.7 | WorkflowOrchestrator extends the workflow system; plan execution IS a workflow; error recovery integrates with workflow retry |
| Plugin Architecture | 4.8 | Tools are a specialized plugin type; plugin registry shares infrastructure with tool registry; plugin actions go through ActionVerifier |

---

## Downstream Dependency Impact

### Directly Blocked by v1.06

| Version | What It Needs | How v1.06 Provides It |
|---------|--------------|----------------------|
| v1.10 (Planning & Orchestration) | Task planning + workflow orchestration | TaskPlanningService and WorkflowOrchestrator are the foundation |
| v1.14 (Advanced Intelligence) | Confidence + hypothesis + reasoning | ConfidenceEstimationService and HypothesisService enable sophisticated reasoning |
| v1.13 (Autonomous Agents) | Tool execution + action verification | ExecutionEngine and ActionVerifier are required for safe autonomous action |

### Indirect Dependencies

| Version | Dependency Chain |
|---------|-----------------|
| v1.07 (Memory Evolution) | v1.06 → memory evolution uses planning to organize memory consolidation |
| v1.08 (Awareness Expansion) | v1.06 → awareness uses error analysis to improve monitoring accuracy |
| v1.11 (Graph Intelligence) | v1.06 → graph reasoning uses hypothesis generation for link prediction |
| v1.12 (System Integration) | v1.06 → system integration uses workflows for cross-service orchestration |

---

## Risk Matrix

| Risk | Likelihood | Impact | Mitigation | Phase |
|------|-----------|--------|------------|-------|
| DAG cycle detection misses edge cases | Medium | High | Implement Tarjan's SCC algorithm; test with known cyclic graphs; add cycle detection in decomposition | P02 |
| Bayesian confidence update diverges | Low | High | Clamp probabilities to [0.01, 0.99]; implement prior strength parameter; test with known distributions | P03 |
| Tool execution sandbox escape | Low | Critical | Restrict tool execution to whitelisted async functions; no subprocess, no filesystem write outside sandbox; security test suite | P04 |
| Workflow partial failure loses state | Medium | High | Checkpoint after every step; implement resume from checkpoint; test with injected failures | P04 |
| Error pattern matching too slow at scale | Medium | Medium | Index error_type in DB; cache pattern counts in Redis; aggregate nightly, query from cache | P02 |
| Confidence estimation produces stale scores | Low | Medium | Recompute confidence on each evidence change; cache with short TTL; invalidate on related data change | P03 |
| Tool registry memory leak from dynamic registration | Low | Medium | Weak references for tool functions; periodic cleanup of unregistered tools; max tools per user | P04 |
| API response time degrades with plan complexity | Medium | Medium | Paginate plan lists; lazy-load step details; index on user_id + status | P05 |
| ActionVerifier false positives block legitimate actions | Medium | Medium | Tunable sensitivity levels; whitelisted patterns per tool; user override with audit trail | P04 |

---

## Strengthened Definition of DoD

### Per-Phase DoD

Each phase must satisfy:

- [ ] All task-level tests written and passing (unit + integration)
- [ ] Security scan: no SQL injection, no unsafe eval/exec, no unvalidated tool parameters
- [ ] Performance gate: plan decomposition < 500ms; tool execution recording < 100ms; confidence computation < 50ms
- [ ] Integration tests: cross-service flows verified (e.g., plan → execute → record → analyze error → update hypothesis)
- [ ] Documentation updated: API docs, service architecture docs, ADR if new pattern introduced
- [ ] Code review: at least one approval, no unresolved comments
- [ ] Migration tested: applies cleanly, rolls back cleanly, no data loss

### Version-Level DoD

- [ ] All 8 cognition/execution capabilities implemented and tested
- [ ] Cognition services in `services/cognition/` (planning, error_analysis, hypothesis, confidence)
- [ ] Execution services in `services/execution/` (tool_registry, engine, action_verifier, workflow)
- [ ] Cognition/execution API endpoints in `api/v1/cognition/` and `api/v1/execution/`
- [ ] Frontend API clients in `features/cognition/api.ts` and `features/execution/api.ts`
- [ ] All unit tests passing (`make test`)
- [ ] All lint checks passing (`make lint`)
- [ ] Frontend tests passing (`cd frontend && npm test`)
- [ ] Integration test suite: plan → execute → record → error → hypothesis → confidence flow verified
- [ ] Security scan: tool execution sandbox verified, no escape vectors
- [ ] Performance: plan decomposition p99 < 500ms; tool execution p99 < 200ms; confidence compute p99 < 50ms
- [ ] ADR created for DAG-based planning and Bayesian confidence updating

---

## Estimated Duration

6-7 days.

---

## Readiness for Next Version

v1.06 is complete when all cognition and execution capabilities are implemented, tested, security-scanned, and performance-verified. v1.10 (Planning & Orchestration) can begin immediately — it extends the planning and workflow systems built here. v1.07 (Memory Evolution) and v1.08 (Awareness Expansion) can proceed independently in parallel.
