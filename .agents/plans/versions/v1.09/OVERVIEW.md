# v1.09: Learning Foundation — CORTEX

**Document:** Version 1.09 Overview
**Authority:** Stage 6 — Master Versioned Implementation Roadmap
**Date:** 2026-06-27
**Type:** Capability Delivery

---

## Objective

Build the learning system: preference learning, workflow learning, habit detection, behavior adaptation, feedback learning, personalization, knowledge refinement, pattern recognition, continuous improvement, and anomaly detection. Create a system where Cortex observes, records, and learns from every user interaction — building a personalized model of each user's preferences, habits, workflows, and behavioral patterns. This is the foundation for Cortex becoming a truly personalized AI assistant rather than a generic tool.

---

## Question

"Can Cortex learn and improve?"

---

## What This Version Delivers

After completing v1.09, Cortex can:

- **Learn user preferences** — Observe and record what users prefer: response style (concise vs. detailed), UI layout, notification frequency, tool choices. Preferences strengthen with repeated observation, weaken when contradicted. Source tracking: explicit (user said "I prefer X"), observed (user chose X three times), inferred (user's behavior suggests X).
- **Understand workflows** — Detect multi-step workflows users repeat: "open editor → run tests → commit → push." Record step sequences, frequency, and context. Surface common workflows for automation opportunities.
- **Detect habits** — Identify habitual behaviors: daily morning coding sessions, afternoon email checking, Friday afternoon commits. Track trigger → action → frequency. Distinguish habits (≥5 occurrences) from one-off actions.
- **Adapt behavior** — Modify Cortex responses based on learned preferences. If user prefers concise answers, trim verbose responses. If user ignores certain suggestions, reduce those suggestions. Per-user adaptation profiles.
- **Learn from feedback** — Record explicit feedback (corrections, affirmations) and implicit feedback (acceptance, rejection of suggestions). Calculate learning rates. Feedback events update preference confidence scores.
- **Personalize responses** — Build per-user profiles with response style, preferred topics, active hours, expertise level. Use profiles to personalize all Cortex interactions.
- **Refine knowledge** — Adjust memory confidence based on outcomes. If a memory led to correct behavior → boost confidence. If it led to error → reduce confidence. Correction feedback creates refined knowledge entries.
- **Recognize patterns** — Detect temporal patterns (codes in mornings), behavioral patterns (prefers vim over nano), preference patterns (always uses dark mode). Patterns strengthen with occurrences.
- **Continuously improve** — Track improvement metrics over time. Measure accuracy, response quality, suggestion acceptance rates. Drive systematic improvement.
- **Detect anomalies** — Identify unusual behavior: activity at 3 AM, 10x normal command frequency, unexpected application usage. Flag for user attention. Adapt baselines over time.

---

## Capabilities Delivered

| ID | Name | Domain | Priority | Architecture Principle |
|----|------|--------|----------|----------------------|
| L1 | Preference Learning | Learning | Core | 1.6 (Evidence Over Opinion) — preferences grounded in observations |
| L2 | Workflow Learning | Learning | Core | 4.7 (Workflow Architecture) — workflow detection as event processing |
| L3 | Habit Detection | Learning | Core | 1.6 (Evidence Over Opinion) — habits require ≥5 occurrences |
| L4 | Behavior Adaptation | Learning | Core | 1.4 (Separation of Concerns) — adaptation service boundary |
| L5 | Feedback Learning | Learning | Core | 1.7 (Incremental Safety) — learning rates prevent over-fitting |
| L6 | Personalization | Learning | Core | 1.1 (Local-First) — all profiles stored locally |
| L7 | Knowledge Refinement | Learning | Core | 4.3 (Memory Architecture) — confidence adjustment on outcomes |
| L8 | Pattern Recognition | Learning | Core | 1.6 (Evidence Over Opinion) — patterns require evidence |
| L9 | Continuous Improvement | Learning | Core | 3.7 (Incremental Safety) — measurable improvement metrics |
| L10 | Anomaly Detection | Learning | Core | 1.7 (Incremental Safety) — anomaly flags for safety review |

**Total: 10 capabilities**

---

## reference architecture Feature Traceability

| reference architecture Feature | Cortex Mapping | v1.09 Coverage |
|-----------------|----------------|----------------|
| User preference learning | L1 (Preference Learning) | Full — explicit/observed/inferred, confidence tracking |
| Workflow pattern detection | L2 (Workflow Learning) | Full — step sequences, frequency, context |
| Habit detection and tracking | L3 (Habit Detection) | Full — trigger-action-frequency, ≥5 threshold |
| Feedback-driven adaptation | L5 (Feedback Learning) | Full — correction/affirmation events, learning rates |
| Personalized responses | L6 (Personalization) | Full — per-user profiles, style adjustment |
| Knowledge confidence refinement | L7 (Knowledge Refinement) | Full — outcome-based confidence adjustment |
| Anomaly detection | L10 (Anomaly Detection) | Full — frequency, time, volume anomaly checks |

**reference architecture coverage for this version: 7 features, all fully covered.**

---

## Capability Mapping

```
v1.09 Learning Foundation
├── P01: Learning Models & Schema (foundation)
│   ├── UserPreference model (category/key/value/confidence/source)
│   ├── WorkflowPattern model (steps/frequency/confidence)
│   ├── Habit model (trigger/action/frequency/occurrences)
│   ├── LearningEvent model (event_type/delta/applied)
│   ├── Pattern model (type/evidence/confidence/occurrences)
│   ├── Pydantic schemas for all models
│   └── Alembic migration (5 tables)
├── P02: Preference & Workflow Learning (L1, L2)
│   ├── PreferenceLearningService (record, retrieve, strengthen)
│   ├── WorkflowLearningService (observe, detect, rank)
│   └── Confidence-based preference management
├── P03: Habits & Adaptation (L3, L4, L5)
│   ├── HabitDetectionService (observe, detect, frequency analysis)
│   ├── BehaviorAdaptationService (adapt responses, suggestions)
│   └── FeedbackLearningService (record feedback, learning rates)
├── P04: Personalization & Refinement (L6, L7, L8, L9, L10)
│   ├── PersonalizationService (user profiles, content adjustment)
│   ├── KnowledgeRefinementService (outcome-based confidence)
│   ├── PatternRecognitionService (detect, record, query patterns)
│   ├── AnomalyDetectionService (frequency/time/volume anomalies)
│   └── ContinuousImprovementService (metrics, tracking, scoring)
└── P05: API & Integration (all)
    ├── Learning API endpoints (preferences, habits, patterns, workflows, anomalies)
    ├── Learning dashboard frontend
    ├── Preference management UI
    ├── Comprehensive test suite (12 test files)
    └── Frontend API client
```

---

## Strengthened Definition of Done

- [ ] All 10 learning capabilities implemented and tested
- [ ] 5 database models with proper indexes (user_id, category, event_type, pattern_type)
- [ ] Alembic migration applies cleanly on fresh DB and on existing DB
- [ ] Migration rollback tested: downgrade removes learning tables, upgrade restores them
- [ ] `PreferenceLearningService` records explicit/observed/inferred preferences with confidence
- [ ] `WorkflowLearningService` detects multi-step patterns and ranks by frequency
- [ ] `HabitDetectionService` requires ≥5 occurrences to classify as habit
- [ ] `BehaviorAdaptationService` adjusts responses based on learned preferences
- [ ] `FeedbackLearningService` calculates learning rates from feedback history
- [ ] `PersonalizationService` builds per-user profiles from preference + pattern data
- [ ] `KnowledgeRefinementService` adjusts memory confidence based on outcomes
- [ ] `PatternRecognitionService` detects temporal, behavioral, and preference patterns
- [ ] `AnomalyDetectionService` flags frequency, time, and volume anomalies
- [ ] `ContinuousImprovementService` tracks improvement metrics over time
- [ ] All API endpoints have `response_model=` decorators per Architecture Principle 1.10
- [ ] Ownership checks: `resource.user_id == current_user.id` on ALL user-scoped endpoints
- [ ] Route order: specific routes before parameterized (e.g., `/patterns/type/{type}` after `/patterns`)
- [ ] Frontend API client typed with TypeScript interfaces matching Pydantic schemas
- [ ] All existing tests pass (zero regression)
- [ ] New test coverage ≥ 80% for all new services
- [ ] `make lint` + `make format` clean
- [ ] `make hooks-merge` passes

---

## Expanded Risk Matrix

| Risk | Likelihood | Impact | Mitigation | Phase |
|------|-----------|--------|------------|-------|
| Preference over-fitting to early observations | Medium | High | Learning rate dampening (confidence +0.1 max per observation); minimum 5 observations before high confidence | P02 |
| Habit detection false positives from repeated one-off actions | Medium | Medium | Require ≥5 occurrences AND temporal consistency; exclude burst patterns | P03 |
| Behavior adaptation makes wrong assumptions about user | Medium | High | Adaptation always conservative (trim only, never add); user override via explicit preference; confidence threshold for adaptation | P03 |
| Learning events table grows unbounded | Medium | Medium | Periodic cleanup of events older than 90 days; archive to cold storage; event aggregation into summaries | P03 |
| Anomaly detection generates too many false positives | High | Medium | Adaptive baselines that update weekly; configurable sensitivity; user can dismiss anomalies | P04 |
| Personalization profiles become stale | Low | Medium | Profile refresh on every interaction; confidence decay for unused preferences; automatic re-observation | P04 |
| Feedback recording adds latency to user interactions | Low | Medium | Async feedback recording via event bus; don't block response delivery | P03 |
| Pattern detection on small datasets produces noise | Medium | Low | Minimum evidence threshold (3 occurrences); confidence gating (only surface patterns with confidence > 0.5) | P04 |
| Learning system learns wrong things from adversarial input | Low | High | Source tracking (explicit > observed > inferred); explicit preferences override observed; user can reset learning data | P02 |

---

## Architecture Principle Cross-References

| Principle | How v1.09 Adheres |
|-----------|-------------------|
| **1.1 Local-First** | All learning data stored in PostgreSQL. No cloud ML services. Pattern detection is algorithmic (frequency analysis, statistical baselines). No external model training. |
| **1.2 Graceful Degradation** | If learning tables don't exist, services return defaults (confidence=0.5, standard style). No learning data → generic behavior. Learning enhances but never breaks. |
| **1.3 Daemon-First** | Learning event recording runs asynchronously via event bus. Background pattern detection via arq jobs. No blocking on user interaction. |
| **1.4 Separation of Concerns** | Each learning domain is its own service: preference ≠ workflow ≠ habit ≠ feedback ≠ personalization. Clean interfaces. No cross-service coupling within the learning layer. |
| **1.5 Plugin Boundaries** | Learning services expose clean protocols. Future ML model plugins (scikit-learn, ONNX) can replace algorithmic pattern detection without changing service interfaces. |
| **1.6 Evidence Over Opinion** | All learning grounded in evidence. Preferences require observations. Habits require ≥5 occurrences. Patterns require evidence lists. Anomalies require baseline comparison. No speculation. |
| **1.7 Incremental Safety** | Learning rates bounded (max ±0.1 per event). Confidence capped at 1.0, floored at 0.1. Anomaly detection flags for review, doesn't auto-act. User can reset all learning data. |

---

## Downstream Dependency Impact

### Directly Blocked Versions

| Version | What It Needs from v1.09 | Impact if Delayed |
|---------|-------------------------|-------------------|
| **v1.10 (Planning & Orchestration)** | User preferences for adaptive planning. Workflow patterns for plan templates. Habit data for scheduling. | Cannot build adaptive planning without user preference data |

### Indirect Dependencies

| Version | Why v1.09 Matters | Workaround |
|---------|-------------------|------------|
| **v1.11 (Interaction)** | Personalization profiles for natural interaction. Behavior adaptation for response tuning. | Generic responses only |
| **v1.12 (Developer Tools)** | Workflow patterns for dev workflow automation. Pattern recognition for code patterns. | Manual workflow configuration |
| **v1.13 (Autonomous Agents)** | User preferences guide agent behavior. Anomaly detection prevents rogue agents. | Agents use default behavior only |
| **v1.14 (Advanced Intelligence)** | Learning data feeds into cross-domain reasoning. Knowledge refinement improves memory quality. | Static knowledge base |

### Integration Points with Other Versions

- **v1.02 (Backend Architecture)** — Services use constructor injection pattern. Learning events use event bus for async recording. All learning data in PostgreSQL.
- **v1.03 (Memory Foundation)** — Knowledge refinement adjusts memory confidence scores. Learning events reference memory IDs. Memory and learning share the same PostgreSQL instance.
- **v1.04 (Awareness Foundation)** — Awareness events feed into preference learning (which apps user uses, when they work). Terminal awareness feeds workflow learning.
- **v1.07 (Memory Evolution)** — Learning patterns become graph nodes. Preference-learning edges connect user actions to outcomes. Memory evolution confidence adjustments feed into knowledge refinement.
- **v1.08 (Awareness Expansion)** — Desktop/terminal/browser awareness events become learning observations. Workspace awareness feeds workflow detection. Calendar awareness feeds habit detection.

---

## Phases

| Phase | Name | Focus | Complexity | Duration | Capabilities |
|-------|------|-------|------------|----------|-------------|
| P01 | Learning Models & Schema | Database models, Pydantic schemas, migration, rollback | Medium | 3-4 hours | Foundation |
| P02 | Preference & Workflow | Preference learning, workflow detection, confidence management | High | 5-6 hours | L1, L2 |
| P03 | Habits & Adaptation | Habit detection, behavior adaptation, feedback learning | High | 5-6 hours | L3, L4, L5 |
| P04 | Personalization & Refinement | Personalization, knowledge refinement, patterns, anomaly detection | High | 6-7 hours | L6, L7, L8, L9, L10 |
| P05 | API & Integration | Endpoints, frontend dashboard, preference management, tests | Medium | 4-5 hours | All |

**Total estimated: 23-28 hours (3-4 days focused development)**

---

## Dependencies

**Depends on:** v1.02 (Backend Architecture) — service patterns, event bus, PostgreSQL
**Blocks:** v1.10 (Planning & Orchestration — needs learning for adaptive planning)

**External dependencies:**
- PostgreSQL 14+ (JSONB support for learning metadata)
- SQLAlchemy 2.0 (async session support)
- Alembic (migration management)
- Redis (job queue for background pattern detection)
- Python `statistics` module (for anomaly detection baselines)

**Internal dependencies:**
- `backend/app/models/` — will extend with learning models
- `backend/app/db/session.py` — `get_db()` generator
- `backend/app/core/config.py` — configuration for learning rates, thresholds
- `backend/app/auth/dependencies.py` — `get_current_user` for ownership
- Event bus from v1.02 for async learning event recording

---

## Estimated Duration

7-8 days (23-28 hours focused development).

---

## Implementation Notes

### Database Schema Additions

```sql
-- P01 migration output
CREATE TABLE user_preferences (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    category VARCHAR(100) NOT NULL,   -- 'response_style', 'ui_layout', 'notification'
    key VARCHAR(200) NOT NULL,        -- 'length', 'sidebar', 'frequency'
    value TEXT,                        -- JSON: preference value
    confidence FLOAT DEFAULT 0.5,     -- 0.0 to 1.0
    source VARCHAR(50),               -- 'explicit', 'observed', 'inferred'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP,
    UNIQUE(user_id, category, key)
);

CREATE TABLE workflow_patterns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    pattern_name VARCHAR(200) NOT NULL,
    description TEXT,
    steps TEXT,                        -- JSON: list of workflow steps
    frequency INTEGER DEFAULT 1,
    last_observed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    confidence FLOAT DEFAULT 0.5,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE habits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    habit_name VARCHAR(200) NOT NULL,
    description TEXT,
    trigger VARCHAR(200),
    action VARCHAR(200),
    frequency VARCHAR(50),            -- 'daily', 'weekly', 'hourly', 'irregular'
    occurrences INTEGER DEFAULT 0,
    last_observed TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE learning_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    event_type VARCHAR(50) NOT NULL,  -- 'feedback', 'correction', 'affirmation'
    context TEXT,                      -- JSON: what was happening
    input_data TEXT,                   -- JSON: what Cortex did
    output_data TEXT,                  -- JSON: what user did in response
    delta FLOAT,                       -- Learning adjustment magnitude
    applied INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE patterns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    pattern_type VARCHAR(50),          -- 'temporal', 'behavioral', 'preference'
    description TEXT,
    evidence TEXT,                     -- JSON: list of evidence items
    confidence FLOAT DEFAULT 0.5,
    first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_seen TIMESTAMP,
    occurrences INTEGER DEFAULT 1
);

CREATE INDEX idx_user_preferences_user ON user_preferences(user_id);
CREATE INDEX idx_user_preferences_cat ON user_preferences(user_id, category);
CREATE INDEX idx_workflow_patterns_user ON workflow_patterns(user_id);
CREATE INDEX idx_habits_user ON habits(user_id);
CREATE INDEX idx_habits_action ON habits(user_id, action);
CREATE INDEX idx_learning_events_user ON learning_events(user_id);
CREATE INDEX idx_learning_events_type ON learning_events(user_id, event_type);
CREATE INDEX idx_patterns_user ON patterns(user_id);
CREATE INDEX idx_patterns_type ON patterns(user_id, pattern_type);
```

### Learning Rate Safety

All learning adjustments are bounded:

```python
MAX_CONFIDENCE = 1.0
MIN_CONFIDENCE = 0.1
MAX_DELTA_PER_EVENT = 0.1
MIN_OCCURRENCES_FOR_HABIT = 5
MIN_OCCURRENCES_FOR_PATTERN = 3
MIN_CONFIDENCE_FOR_ADAPTATION = 0.6
```

### Feedback Loop Architecture

```
User Interaction → Learning Event (async via event bus)
    → PreferenceLearningService (updates confidence)
    → HabitDetectionService (increments occurrences)
    → PatternRecognitionService (detects patterns)
    → BehaviorAdaptationService (adjusts next response)
    → KnowledgeRefinementService (adjusts memory confidence)
```

---

## Definition of Done

- [ ] All 10 learning capabilities implemented
- [ ] Learning services in `services/learning/`
- [ ] 5 database models with proper indexes
- [ ] Alembic migration applies and rolls back cleanly
- [ ] Preference learning with confidence tracking
- [ ] Workflow pattern detection with frequency ranking
- [ ] Habit detection with occurrence threshold
- [ ] Behavior adaptation with conservative defaults
- [ ] Feedback learning with learning rate calculation
- [ ] Personalization with per-user profiles
- [ ] Knowledge refinement with outcome-based confidence
- [ ] Pattern recognition with evidence requirements
- [ ] Anomaly detection with adaptive baselines
- [ ] Continuous improvement with metric tracking
- [ ] API endpoints with ownership checks
- [ ] Frontend API client typed with TypeScript
- [ ] All tests passing (existing + new)
- [ ] `make lint` + `make format` clean
- [ ] `make hooks-merge` passes

---

## Readiness for Next Version

v1.09 is complete when Cortex can learn and personalize. The following versions can proceed:

- **v1.10 (Planning & Orchestration)** can use learning data for adaptive planning
- **v1.11 (Interaction)** can personalize interactions using preference profiles
- **v1.12 (Developer Tools)** can automate workflows using detected patterns
- **v1.13 (Autonomous Agents)** can behave in user-aligned ways using adaptation profiles
- **v1.14 (Advanced Intelligence)** can reason across learned knowledge for deeper insights
