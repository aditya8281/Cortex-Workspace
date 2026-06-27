# v1.10: Planning & Orchestration — CORTEX

**Document:** Version 1.10 Overview
**Authority:** Stage 6 — Master Versioned Implementation Roadmap
**Date:** 2026-06-27
**Type:** Capability Delivery
**reference architecture Feature ID:** ODY-PLAN-100

---

## Objective

Build the planning and orchestration system: high-level planning, task decomposition, decision support with what-if analysis, goal management, problem solving, strategy selection, workflow orchestration engine, task scheduling with cron-like patterns, dependency resolution, recovery and rollback mechanisms, parallel execution, background tasks, execution history logging, and state snapshots.

---

## Question

"Can Cortex plan complex work and orchestrate execution?"

---

## What This Version Delivers

After completing v1.10, Cortex can:

- Plan complex multi-step operations with LLM-assisted decomposition
- Decompose goals into actionable task trees with dependencies and estimated durations
- Provide decision support with weighted trade-off analysis and what-if scenario modeling
- Manage long-term goals with hierarchical sub-goals, deadlines, and progress tracking
- Solve problems using structured decomposition, analogy, and iteration strategies
- Orchestrate complex workflows with sequential and parallel execution modes, dependency resolution, and step-level error handling
- Schedule operations for later execution with cron expressions, recurrence patterns, and timezone awareness
- Recover from failures automatically using recovery points and configurable recovery actions
- Execute independent tasks in parallel with configurable concurrency limits and semaphore-based backpressure
- Run background operations with lifecycle management, health checks, and graceful shutdown
- Maintain complete execution history with input/output capture, duration tracking, and audit trail
- Rollback completed operations with state restoration and dependency-aware inverse operations

---

## Capabilities Delivered

| ID | Name | Domain | Priority | Architecture Principle |
|----|------|--------|----------|----------------------|
| C1 | High-Level Planning | Cognition | Core | 3.4 Separation of Concerns |
| C2 | Task Decomposition | Cognition | Core | 3.6 Evidence Over Opinion |
| C3 | Decision Support | Cognition | Core | 3.6 Evidence Over Opinion |
| C5 | Goal Management | Cognition | Core | 3.1 Local-First |
| C7 | Problem Solving | Cognition | Core | 3.4 Separation of Concerns |
| C8 | Strategy Selection | Cognition | Core | 3.5 Plugin Boundaries Early |
| E3 | Workflow Orchestration | Execution | Core | 3.3 Daemon-First |
| E4 | Scheduling | Execution | Core | 3.3 Daemon-First |
| E7 | Recovery | Execution | Core | 3.2 Graceful Degradation |
| E8 | Parallel Execution | Execution | Core | 3.7 Incremental Safety |
| E9 | Background Tasks | Execution | Core | 3.3 Daemon-First |
| E11 | Execution History | Execution | Core | 3.6 Evidence Over Opinion |
| E12 | Rollback | Execution | Core | 3.2 Graceful Degradation |

**Total: 13 capabilities**

---

## reference architecture Feature Traceability

| reference architecture Feature | v1.10 Capability | Traceability |
|------------------|-----------------|--------------|
| ODY-PLAN-100 | Planning & Orchestration (all) | Primary delivery |
| ODY-COGN-200 | C1, C2, C3, C5, C7, C8 | Planning extends cognition core from v1.06 |
| ODY-EXEC-300 | E3, E4, E7, E8, E9, E11, E12 | Orchestration extends execution engine from v1.03 |
| ODY-MEM-400 | Execution history feeds memory | History events captured in knowledge graph |
| ODY-LEARN-500 | Decision outcomes improve strategy | Decision outcomes update learning models |

---

## Capability Mapping to Services

| Capability | Primary Service | Supporting Services | DB Tables |
|------------|----------------|---------------------|-----------|
| C1 High-Level Planning | `AdvancedPlanningService` | `ProblemSolvingService` | `plans`, `plan_steps` |
| C2 Task Decomposition | `AdvancedPlanningService` | — | `plan_steps`, `goal_sub_goals` |
| C3 Decision Support | `DecisionSupportService` | — | `decisions` |
| C5 Goal Management | `AdvancedPlanningService` | — | `goals` |
| C7 Problem Solving | `ProblemSolvingService` | `AdvancedPlanningService` | `problems` |
| C8 Strategy Selection | `ProblemSolvingService` | — | `strategies` |
| E3 Workflow Orchestration | `AdvancedWorkflowOrchestrator` | `ParallelExecutionService` | `workflow_runs`, `workflow_steps` |
| E4 Scheduling | `SchedulingService` | — | `scheduled_tasks` |
| E7 Recovery | `RecoveryService` | — | `recovery_points` |
| E8 Parallel Execution | `ParallelExecutionService` | — | `parallel_runs` |
| E9 Background Tasks | `BackgroundTaskService` | `SchedulingService` | `background_tasks` |
| E11 Execution History | `ExecutionHistoryService` | — | `execution_history` |
| E12 Rollback | `RollbackService` | `RecoveryService` | `rollback_operations` |

---

## Phases

| Phase | Name | Focus | Complexity | Duration | reference architecture Trace |
|-------|------|-------|------------|----------|---------------|
| P01 | Planning Models & Schema | Database models, Pydantic schemas, migration rollback | Medium | 3-4h | ODY-PLAN-100 |
| P02 | Planning & Decision Support | High-level planning, decision support with what-if analysis | High | 6-7h | ODY-COGN-200 |
| P03 | Orchestration & Scheduling | Workflow orchestration engine, task scheduling, dependency resolution | High | 6-7h | ODY-EXEC-300 |
| P04 | Recovery & History | Recovery, rollback, execution history with audit trail | High | 5-6h | ODY-EXEC-300 |
| P05 | API & Integration | REST endpoints, frontend dashboard, workflow visualization, tests | Medium | 4-5h | ODY-PLAN-100 |

---

## Dependencies

**Depends on:**
- v1.03 (Memory Foundation) — plans need memory for context, execution history feeds knowledge graph
- v1.04 (Awareness) — goal tracking integrates with awareness engine's activity monitoring
- v1.06 (Cognition Core) — planning extends reasoning chain, decision support builds on problem-solving primitives
- v1.09 (Learning) — strategy selection uses learned patterns, decision outcomes improve future planning

**Blocks:**
- v1.14 (Advanced Intelligence) — advanced reasoning requires planning + orchestration as primitives
- v1.13 (Utility & Integration) — scheduling infrastructure needed for utility automation

**Downstream Impact:**
- v1.14 can compose planning with multi-agent coordination
- v1.13 can use scheduling for automated utility tasks (email sync, calendar updates)
- Any future version needing automated workflows depends on E3/E4

---

## Risk Matrix

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Workflow engine race conditions in parallel execution | Medium | High | Semaphore-based concurrency limits, idempotent step execution, explicit state machine |
| Cron expression parsing edge cases (timezone, DST) | High | Medium | Use `croniter` library, fallback to simple interval scheduling |
| Recovery point state snapshots grow large | Medium | Medium | Compress snapshots, implement snapshot rotation policy, cap at 100 per execution |
| Rollback of side-effecting operations may be unsafe | High | High | Mark non-rollbackable operations, implement compensating transactions, log all side effects |
| Scheduling drift with long-running background tasks | Low | Medium | Heartbeat-based liveness detection, configurable timeout with auto-restart |
| Schema migration complexity (5 new tables) | Medium | Low | Test rollback migration, verify idempotent upgrade/downgrade |
| Decision support what-if analysis requires LLM calls | Medium | Medium | Cache common decision templates, implement offline fallback scoring |

---

## Architecture Principle Cross-References

| Principle | How v1.10 Satisfies It |
|-----------|----------------------|
| 3.1 Local-First | All planning data, execution history, and recovery points stored in local SQLite. No cloud dependency for any operation. |
| 3.2 Graceful Degradation | Recovery service works without Redis (in-memory fallback). Scheduling falls back to simple timers if cron engine unavailable. Parallel execution degrades to sequential. |
| 3.3 Daemon-First | All planning and orchestration operations accessible via CLI and API. Background task management runs in daemon process. |
| 3.4 Separation of Concerns | Planning service ≠ Decision support ≠ Orchestration ≠ Recovery. Each has distinct responsibilities, communicates via typed interfaces. |
| 3.5 Plugin Boundaries Early | Strategy selection uses `StrategyProtocol` interface. Recovery actions defined as pluggable `RecoveryActionProtocol`. |
| 3.6 Evidence Over Opinion | Decision outcomes tracked and scored. Execution history provides evidence for future planning. |
| 3.7 Incremental Safety | Recovery points enable safe rollback. Execution history enables audit. All operations idempotent where possible. |

---

## Cross-Domain Integration

| Integration Point | Target System | Integration Pattern |
|-------------------|---------------|-------------------|
| Execution history | Knowledge Graph (v1.03) | Events emitted on execution completion → graph entity creation |
| Decision outcomes | Learning Engine (v1.09) | Decision results → feedback loop → strategy improvement |
| Goal progress | Awareness Engine (v1.04) | Goal state changes → awareness events → proactive suggestions |
| Scheduled tasks | Scheduling Daemon (v1.03) | Cron jobs registered with daemon scheduler, heartbeat monitored |
| Workflow steps | Tool Execution Engine (v1.03) | Orchestrator invokes tools via existing tool execution interface |
| Recovery points | Memory System (v1.03) | State snapshots indexed for quick retrieval during recovery |

---

## Estimated Duration

7-8 days.

---

## Definition of Done

- [ ] All 13 planning/orchestration capabilities implemented and tested
- [ ] Services in `backend/app/services/cognition/` and `backend/app/services/execution/`
- [ ] Models in `backend/app/models/cognition/` and `backend/app/models/execution/`
- [ ] Schemas in `backend/app/schemas/cognition/` and `backend/app/schemas/execution/`
- [ ] All database migrations apply cleanly (upgrade + downgrade)
- [ ] Recovery and rollback mechanisms tested with failure scenarios
- [ ] Parallel execution tested with concurrency limits
- [ ] Scheduling tested with cron expressions and recurrence patterns
- [ ] Execution history captures full audit trail
- [ ] All unit tests passing (`make test`)
- [ ] Lint clean (`make lint`)
- [ ] All API endpoints documented with `response_model=`
- [ ] Frontend planning dashboard with workflow visualization

---

## Success Criteria

| Metric | Target |
|--------|--------|
| Planning latency (10-step plan) | < 2 seconds |
| Workflow orchestration throughput | 50 steps/second sequential |
| Parallel execution concurrency | Configurable 1-20, default 5 |
| Recovery point creation overhead | < 50ms |
| Rollback execution time | < 5 seconds per operation |
| Scheduling accuracy | < 100ms drift from scheduled time |
| Execution history query latency | < 100ms for 10K records |
| Test coverage | > 85% for planning and execution services |
