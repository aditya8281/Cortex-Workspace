# Capability Domains — CORTEX

**Document:** Capability Domain Organization
**Authority:** Stage 3 — Future Capability Exploration
**Date:** 2026-06-27

---

## Purpose

This document organizes the 110 discovered capabilities into 10 logical domains. The organization is temporary and exists to support Stage 4 planning. Each domain represents a coherent area of Cortex's intelligence.

---

## Domain Relationships

The domains are not independent. They form a layered architecture:

```
┌─────────────────────────────────────────────────────────┐
│  Interaction (how Cortex communicates)                  │
├─────────────────────────────────────────────────────────┤
│  Utility (daily life)  │  Developer Experience (craft)  │
├─────────────────────────────────────────────────────────┤
│  Cognition (thinking)  │  Execution (acting)            │
├─────────────────────────────────────────────────────────┤
│  Learning (adaptation) │  Integration (connections)     │
├─────────────────────────────────────────────────────────┤
│  Awareness (senses)    │  Memory (brain)                │
├─────────────────────────────────────────────────────────┤
│  Privacy & Security (shield)                            │
└─────────────────────────────────────────────────────────┘
```

**Foundation:** Privacy & Security — everything depends on trust.
**Perception:** Awareness + Memory — how Cortex perceives and remembers.
**Processing:** Cognition + Learning + Integration — how Cortex thinks, adapts, and connects.
**Action:** Execution — how Cortex acts on the world.
**Service:** Utility + Developer Experience — what Cortex provides to the user.
**Communication:** Interaction — how Cortex communicates with the user.

---

## Domain 1: Memory (13 capabilities)

**Purpose:** The persistent brain. Cortex's ability to remember, connect, and retrieve knowledge over years.

**Core Question:** How does Cortex remember everything it needs to serve the user?

**Key Insight:** Memory is not storage — it is understanding. Cortex does not just store facts. It understands relationships, context, confidence, and temporal relevance.

**Capabilities:** M1-M13 (Episodic, Semantic, Procedural, Working, Consolidation, Graph, Forgetting, Evolution, Context Retrieval, Search, Confidence-Weighted, Temporal, Cross-Domain)

---

## Domain 2: Awareness (16 capabilities)

**Purpose:** The senses. Cortex's ability to perceive the user's digital environment.

**Core Question:** How does Cortex understand what is happening around it?

**Key Insight:** Awareness is not surveillance — it is context. Cortex perceives to understand, not to monitor. Every awareness type serves the goal of better understanding the user's current situation.

**Capabilities:** A1-A16 (Filesystem, Repository, Project, Desktop, Terminal, Browser, Clipboard, Running Apps, Device, Notification, Calendar, Email, Workspace, Environment, System Health, Temporal)

---

## Domain 3: Cognition (14 capabilities)

**Purpose:** The thinking. Cortex's ability to process information and generate insights.

**Core Question:** How does Cortex think about what it knows?

**Key Insight:** Cognition is not computation — it is understanding. Cortex does not just process data. It reasons, hypothesizes, reflects, and evaluates. Cognition is what makes Cortex a brain, not a database.

**Capabilities:** C1-C14 (Planning, Task Decomposition, Reflection, Reasoning, Hypothesis, Confidence, Decision Support, Goal Management, Problem Solving, Error Analysis, Strategy, Self-Evaluation, Analogy, Causal Reasoning)

---

## Domain 4: Execution (12 capabilities)

**Purpose:** The hands. Cortex's ability to act on the world through tools and automation.

**Core Question:** How does Cortex translate understanding into action?

**Key Insight:** Execution is not automation — it is capability. Cortex does not just run scripts. It plans, executes, verifies, recovers, and learns from its actions. Execution is what makes Cortex useful, not just knowledgeable.

**Capabilities:** E1-E12 (Tool Execution, Automation, Workflow Orchestration, Scheduling, Permission Management, Recovery, Parallel Execution, Background Tasks, Action Verification, Execution History, Rollback, Batch Operations)

---

## Domain 5: Learning (10 capabilities)

**Purpose:** The adaptation. Cortex's ability to improve over time through experience.

**Core Question:** How does Cortex get better at serving the user?

**Key Insight:** Learning is not training — it is adaptation. Cortex does not retrain its models on user data. It learns patterns, preferences, and habits through observation and feedback. Learning makes Cortex more useful without compromising privacy.

**Capabilities:** L1-L10 (Preference, Workflow, Habit, Behavior Adaptation, Feedback, Personalization, Knowledge Refinement, Continuous Improvement, Pattern Recognition, Anomaly Detection)

---

## Domain 6: Interaction (12 capabilities)

**Purpose:** The voice. Cortex's ability to communicate with the user through multiple modalities.

**Core Question:** How does Cortex communicate its understanding to the user?

**Key Insight:** Interaction is not interface — it is communication. Cortex does not just display information. It converses, suggests, notifies, and adapts its communication style to the context. Good interaction is invisible — the user focuses on their work, not on Cortex.

**Capabilities:** I1-I12 (Conversational, Voice, Command Palette, GUI, CLI, API, Notifications, Proactive Assistance, Contextual Suggestions, Multi-Modal, Ambient Intelligence, Summarization)

---

## Domain 7: Developer Experience (15 capabilities)

**Purpose:** The craft. Cortex's ability to serve developers with specialized intelligence.

**Core Question:** How does Cortex help developers build better software?

**Key Insight:** Developer experience is not code generation — it is understanding. Cortex does not just write code. It understands architecture, reviews quality, assists with debugging, and guides design decisions. Developer experience is Cortex applied to the craft of software development.

**Capabilities:** D1-D15 (Code Understanding, Repository Intelligence, Code Review, Documentation Generation, Test Generation, Refactoring, Debugging, Architecture Guidance, Dependency Analysis, Performance Analysis, Security Analysis, Migration, Code Generation, Git Intelligence, CI/CD)

---

## Domain 8: Utility (12 capabilities)

**Purpose:** Daily life. Cortex's ability to assist with everyday digital tasks beyond coding.

**Core Question:** How does Cortex serve the user's complete digital life?

**Key Insight:** Utility is not features — it is assistance. Cortex does not build a calendar app or an email client. It understands the user's calendar and email and uses that understanding to provide better assistance. Utility is Cortex applied to the breadth of digital life.

**Capabilities:** U1-U12 (Calendar, Email, Tasks, Notes/Knowledge, Documents, Contacts, Workspace Management, Dashboard, Daily Briefing, Weekly Review, Habit Tracking, Focus Management)

---

## Domain 9: Integration (6 capabilities)

**Purpose:** The connections. Cortex's ability to connect with external tools and services.

**Core Question:** How does Cortex connect with the user's existing digital ecosystem?

**Key Insight:** Integration is not connectivity — it is understanding. Cortex does not just connect to services. It understands what those services do, how they relate to the user's work, and how to use them in service of the user's goals. Integration extends Cortex's awareness and capability without replacing existing tools.

**Capabilities:** X1-X6 (Tool Integration, Service Integration, Protocol Support, Extension System, Data Import/Export, Cross-Device Sync)

---

## Domain 10: Privacy & Security (10 capabilities)

**Purpose:** The shield. Cortex's ability to protect the user's data and maintain trust.

**Core Question:** How does Cortex earn and maintain the user's trust?

**Key Insight:** Privacy is not policy — it is architecture. Cortex's privacy guarantees are enforced by its design, not by promises. Every capability in this domain is structural, not procedural. Trust is Cortex's most valuable asset, and these capabilities protect it.

**Capabilities:** P1-P10 (Local Processing, Encryption at Rest, Encryption in Transit, Access Control, Audit Logging, Data Sovereignty, Transparency, Consent Management, Differential Privacy, Secure Enclaves)

---

## Cross-Domain Dependencies

| Domain | Depends On | Enables |
|--------|-----------|---------|
| Memory | — | All other domains |
| Awareness | — | Memory, Cognition, Learning |
| Cognition | Memory, Awareness | Execution, Interaction |
| Execution | Cognition, Memory | Utility, Developer Experience |
| Learning | Memory, Cognition | All domains (improves over time) |
| Interaction | Cognition, Execution | Utility, Developer Experience |
| Developer Experience | Memory, Cognition, Execution | — |
| Utility | Memory, Cognition, Execution | — |
| Integration | Memory, Execution | Awareness, Utility |
| Privacy & Security | — | All domains (foundation) |

---

## Domain Maturity Model

Each domain evolves through three maturity levels:

**Level 1: Foundation**
- Basic capability exists
- Works for simple cases
- Requires user guidance

**Level 2: Competent**
- Handles most cases reliably
- Works with minimal guidance
- Learns from interaction

**Level 3: Intelligent**
- Handles complex cases
- Anticipates needs
- Improves continuously

| Domain | Level 1 | Level 2 | Level 3 |
|--------|---------|---------|---------|
| Memory | Store and retrieve | Connect and relate | Understand and predict |
| Awareness | Detect changes | Understand context | Anticipate needs |
| Cognition | Answer questions | Analyze situations | Generate insights |
| Execution | Run commands | Automate workflows | Orchestrate complex tasks |
| Learning | Record feedback | Adapt behavior | Improve continuously |
| Interaction | Respond to queries | Suggest proactively | Communicate naturally |
| Developer Experience | Basic code analysis | Intelligent assistance | Deep understanding |
| Utility | Basic task tracking | Integrated management | Predictive assistance |
| Integration | Connect to tools | Understand data | Orchestrate across tools |
| Privacy & Security | Encrypt data | Enforce policies | Architectural guarantees |

---

## Detailed Capability Catalog

The following structured catalog provides detailed dependency and value information for each of the 110 capabilities across all 10 domains.

### Domain 1: Memory

| # | Name | Description | Value | Depends On | Strengthens |
|---|------|-------------|-------|------------|-------------|
| M1 | Episodic Memory | Remembers events with temporal context | High | — | Persistent Intelligence |
| M2 | Semantic Memory | Remembers structured knowledge | High | — | Persistent Intelligence |
| M3 | Procedural Memory | Remembers how the user performs tasks | High | Workflow Learning | Understand Before Acting |
| M4 | Working Memory | Short-term context buffer for current session | High | — | Assist Instead of Replace |
| M5 | Memory Consolidation | Periodic review, strengthening, fading | Medium | M1, M2, M3 | Long-Term Maintainability |
| M6 | Memory Graph | Memories form connected graph structure | High | M1, M2, M3 | Persistent Intelligence |
| M7 | Forgetting | Controlled fading of less-relevant memories | Medium | M5 | Long-Term Maintainability |
| M8 | Knowledge Evolution | Tracks how understanding changes over time | High | M2, M6 | Persistent Intelligence |
| M9 | Context Retrieval | Retrieves full context, not just facts | High | M6, M9 | Understand Before Acting |
| M10 | Memory Search | Unified search across all memory types | High | M6 | Assist Instead of Replace |
| M11 | Confidence-Weighted Memory | Every memory has reliability score | High | M1, M2, M8 | Human Control Always Exists |
| M12 | Temporal Memory | Time-aware relevance weighting | Medium | M1, M6 | Persistent Intelligence |
| M13 | Cross-Domain Memory | Memories span coding, projects, communications | High | M6, A13 | Understand Before Acting |

### Domain 2: Awareness

| # | Name | Description | Value | Depends On | Strengthens |
|---|------|-------------|-------|------------|-------------|
| A1 | Filesystem Awareness | Understands file relationships and patterns | High | — | Understand Before Acting |
| A2 | Repository Awareness | Understands code repos, structure, history | High | — | Understand Before Acting |
| A3 | Project Awareness | Tracks project lifecycle and goals | High | M1, M6 | Understand Before Acting |
| A4 | Desktop Awareness | Knows running apps and user focus | Medium | — | Assist Instead of Replace |
| A5 | Terminal Awareness | Understands terminal sessions and commands | Medium | — | Understand Before Acting |
| A6 | Browser Awareness | Knows web browsing context | Medium | — | Understand Before Acting |
| A7 | Clipboard Awareness | Understands clipboard content and intent | Low | — | Assist Instead of Replace |
| A8 | Running Applications | Knows what apps are active and why | Medium | A4 | Understand Before Acting |
| A9 | Device Awareness | Knows hardware capabilities and constraints | Medium | — | Local-First by Default |
| A10 | Notification Awareness | Filters signal from noise in notifications | Medium | — | Assist Instead of Replace |
| A11 | Calendar Awareness | Understands schedule and time context | High | — | Understand Before Acting |
| A12 | Email Awareness | Understands communications and action items | High | — | Understand Before Acting |
| A13 | Workspace Awareness | Synthesizes all awareness into coherent picture | High | A1-A12 | Understand Before Acting |
| A14 | Environment Awareness | Knows OS, tools, configuration | Medium | — | Local-First by Default |
| A15 | System Health Awareness | Monitors system resources and errors | Medium | — | Long-Term Maintainability |
| A16 | Temporal Awareness | Time-of-day, day-of-week context | Low | — | Assist Instead of Replace |

### Domain 3: Cognition

| # | Name | Description | Value | Depends On | Strengthens |
|---|------|-------------|-------|------------|-------------|
| C1 | Planning | Creates structured plans with dependencies | High | M2, M3 | Understand Before Acting |
| C2 | Task Decomposition | Breaks complex tasks into subtasks | High | C1 | Assist Instead of Replace |
| C3 | Reflection | Thinks about own thinking after tasks | High | M1, M8 | Scalable Evolution |
| C4 | Reasoning | Draws conclusions from evidence | High | M2, M6 | Understand Before Acting |
| C5 | Hypothesis Generation | Generates multiple hypotheses for problems | Medium | C4 | Understand Before Acting |
| C6 | Confidence Estimation | Knows how confident it is in conclusions | High | M11 | Human Control Always Exists |
| C7 | Decision Support | Presents options and analyzes tradeoffs | High | C4, C6 | Assist Instead of Replace |
| C8 | Goal Management | Tracks short/medium/long-term goals | Medium | M1, M6 | Assist Instead of Replace |
| C9 | Problem Solving | Systematic approach to user challenges | High | C4, C5 | Assist Instead of Replace |
| C10 | Error Analysis | Understands what went wrong and why | High | M1, A15 | Long-Term Maintainability |
| C11 | Strategy Generation | Suggests strategic approaches for complex tasks | Medium | C1, C4 | Assist Instead of Replace |
| C12 | Self-Evaluation | Assesses own performance and accuracy | Medium | C6, M11 | Scalable Evolution |
| C13 | Analogy Recognition | Patterns across domains | Medium | M13, M6 | Understand Before Acting |
| C14 | Causal Reasoning | Understands cause and effect chains | High | C4, M6 | Understand Before Acting |

### Domain 4: Execution

| # | Name | Description | Value | Depends On | Strengthens |
|---|------|-------------|-------|------------|-------------|
| E1 | Tool Execution | Uses tools to act on the world | High | — | Assist Instead of Replace |
| E2 | Automation | Automates routine tasks | High | E1, M3 | Assist Instead of Replace |
| E3 | Workflow Orchestration | Sequences complex multi-step workflows | High | E1, E2, C1 | Assist Instead of Replace |
| E4 | Scheduling | Manages recurring tasks and deadlines | Medium | E1, A11 | Assist Instead of Replace |
| E5 | Permission Management | Controls which actions are allowed | High | — | Human Control Always Exists |
| E6 | Recovery | Recovers from automation failures | High | E5 | Long-Term Maintainability |
| E7 | Parallel Execution | Runs independent tasks simultaneously | Medium | E1 | Scalable Evolution |
| E8 | Background Tasks | Manages long-running processes | Medium | E1, A9 | Assist Instead of Replace |
| E9 | Action Verification | Confirms actions achieved intended result | High | E1, C4 | Long-Term Maintainability |
| E10 | Execution History | Records all actions for learning | High | E1 | Scalable Evolution |
| E11 | Rollback | Undoes actions when results are unexpected | High | E6, E10 | Human Control Always Exists |
| E12 | Batch Operations | Handles bulk operations efficiently | Medium | E1 | Assist Instead of Replace |

### Domain 5: Learning

| # | Name | Description | Value | Depends On | Strengthens |
|---|------|-------------|-------|------------|-------------|
| L1 | Preference Learning | Learns user's preferences and choices | High | M2, M8 | Personalization |
| L2 | Workflow Learning | Learns how the user performs tasks | High | M3, M6 | Understand Before Acting |
| L3 | Habit Learning | Recognizes daily and weekly patterns | Medium | M1, A16 | Understand Before Acting |
| L4 | Behavior Adaptation | Adapts own behavior based on learning | High | L1, L2 | Scalable Evolution |
| L5 | Feedback Learning | Learns from explicit user feedback | High | M1, M8 | Scalable Evolution |
| L6 | Personalization | Tailors to individual user personality | Medium | L1, L4 | Assist Instead of Replace |
| L7 | Knowledge Refinement | Makes understanding more precise over time | High | M8, C4 | Persistent Intelligence |
| L8 | Continuous Improvement | Improves through accumulated small changes | High | C3, L5 | Scalable Evolution |
| L9 | Pattern Recognition | Recognizes patterns across time and domains | High | M6, M13 | Understand Before Acting |
| L10 | Anomaly Detection | Notices unusual changes and behaviors | Medium | M6, A15 | Assist Instead of Replace |

### Domain 6: Interaction

| # | Name | Description | Value | Depends On | Strengthens |
|---|------|-------------|-------|------------|-------------|
| I1 | Conversational Interface | Natural ongoing dialogue | High | — | Assist Instead of Replace |
| I2 | Voice Interface | Speaks and listens | Medium | I1 | Assist Instead of Replace |
| I3 | Command Palette | Quick-access search-and-execute | High | E1 | Assist Instead of Replace |
| I4 | GUI | Visual interfaces for visual tasks | Medium | — | Assist Instead of Replace |
| I5 | CLI | Command-line interface for scripting | High | E1 | Local-First by Default |
| I6 | API | Programmatic interface for integration | High | E1 | Scalable Evolution |
| I7 | Notifications | Rare, significant alerts only | Medium | A10 | Assist Instead of Replace |
| I8 | Proactive Assistance | Helps without being asked | High | A13, C5, L4 | Understand Before Acting |
| I9 | Contextual Suggestions | Suggests in context of current work | High | A13, L1 | Assist Instead of Replace |
| I10 | Multi-Modal Interaction | Text, voice, visual, haptic | Low | I1, I2, I4 | Assist Instead of Replace |
| I11 | Ambient Intelligence | Present without being intrusive | High | A13, I8 | Assist Instead of Replace |
| I12 | Summarization | Condenses information to key points | High | M2, C4 | Assist Instead of Replace |

### Domain 7: Developer Experience

| # | Name | Description | Value | Depends On | Strengthens |
|---|------|-------------|-------|------------|-------------|
| D1 | Code Understanding | Deep understanding of code semantics | High | M2, M6 | Understand Before Acting |
| D2 | Repository Intelligence | Understands repos as coherent systems | High | D1, A2 | Understand Before Acting |
| D3 | Code Review | Reviews code with depth of senior dev | High | D1, C4 | Long-Term Maintainability |
| D4 | Documentation Generation | Generates accurate documentation from code | Medium | D1 | Assist Instead of Replace |
| D5 | Test Generation | Generates meaningful test suites | High | D1 | Long-Term Maintainability |
| D6 | Refactoring Assistance | Suggests code improvements | Medium | D1, D3 | Long-Term Maintainability |
| D7 | Debugging Support | Assists with error diagnosis and resolution | High | D1, C9, C10 | Assist Instead of Replace |
| D8 | Architecture Guidance | Provides design decision support | High | D2, C7 | Architecture Before Implementation |
| D9 | Dependency Analysis | Maps dependencies and change impact | High | D1, D2 | Long-Term Maintainability |
| D10 | Performance Analysis | Identifies bottlenecks and optimization opportunities | Medium | D1, A15 | Long-Term Maintainability |
| D11 | Security Analysis | Identifies vulnerabilities | High | D1 | Privacy Before Convenience |
| D12 | Migration Assistance | Helps with framework/dependency upgrades | Medium | D1, D9 | Scalable Evolution |
| D13 | Code Generation | Generates code matching user style | High | D1, L1 | Assist Instead of Replace |
| D14 | Git Intelligence | Deep understanding of version control | High | D1, A2 | Understand Before Acting |
| D15 | CI/CD Understanding | Understands build/deploy pipelines | Medium | D14 | Long-Term Maintainability |

### Domain 8: Utility

| # | Name | Description | Value | Depends On | Strengthens |
|---|------|-------------|-------|------------|-------------|
| U1 | Calendar Management | Schedules, finds free time, prepares for events | High | A11 | Assist Instead of Replace |
| U2 | Email Management | Drafts, filters, surfaces, extracts actions | High | A12 | Assist Instead of Replace |
| U3 | Task Management | Creates, prioritizes, tracks tasks | High | C1, C2 | Assist Instead of Replace |
| U4 | Notes & Knowledge Management | Organizes, connects, surfaces knowledge | High | M2, M6 | Persistent Intelligence |
| U5 | Document Management | Organizes, searches, summarizes documents | High | M2, A1 | Assist Instead of Replace |
| U6 | Contact Management | Remembers people and relationships | Medium | M2, A12 | Persistent Intelligence |
| U7 | Digital Workspace Management | Organizes files, reduces clutter | Medium | A1 | Assist Instead of Replace |
| U8 | Personal Dashboard | Status, projects, deadlines, metrics | High | A13, M6 | Assist Instead of Replace |
| U9 | Daily Briefing | What happened, what's planned, what matters | High | A13, M1 | Assist Instead of Replace |
| U10 | Weekly Review | Accomplishments, patterns, improvements | Medium | C3, L8 | Scalable Evolution |
| U11 | Habit Tracking | Work patterns, productivity cycles | Medium | L3, A16 | Understand Before Acting |
| U12 | Focus Management | Filters distractions, protects deep work | Medium | A13, I8 | Assist Instead of Replace |

### Domain 9: Integration

| # | Name | Description | Value | Depends On | Strengthens |
|---|------|-------------|-------|------------|-------------|
| X1 | Tool Integration | Connects with IDEs, terminals, browsers | High | — | Local-First by Default |
| X2 | Service Integration | Connects with cloud services | Medium | — | Assist Instead of Replace |
| X3 | Protocol Support | MCP, REST, WebSocket, SSH | High | — | Scalable Evolution |
| X4 | Extension System | Third-party plugins and extensions | Medium | X3 | Scalable Evolution |
| X5 | Data Import/Export | Standard format data portability | High | — | Data Sovereignty |
| X6 | Cross-Device Synchronization | Consistent understanding across devices | Medium | X5 | Persistent Intelligence |

### Domain 10: Privacy & Security

| # | Name | Description | Value | Depends On | Strengthens |
|---|------|-------------|-------|------------|-------------|
| P1 | Local Processing | All intelligence on user's device | High | — | Local-First by Default |
| P2 | Encryption at Rest | Data encrypted when stored | High | — | Privacy Before Convenience |
| P3 | Encryption in Transit | Data encrypted when transmitted | High | — | Privacy Before Convenience |
| P4 | Access Control | Multi-factor, role-based, session mgmt | High | — | Human Control Always Exists |
| P5 | Audit Logging | Records all significant actions | High | — | Human Control Always Exists |
| P6 | Data Sovereignty | User owns all data, can export/delete | High | — | Privacy Before Convenience |
| P7 | Transparency | Explains actions, cites sources | High | — | Human Control Always Exists |
| P8 | Consent Management | Explicit consent for all data access | High | — | Privacy Before Convenience |
| P9 | Differential Privacy | Learning without compromising individuals | Medium | — | Privacy Before Convenience |
| P10 | Secure Enclaves | Sensitive ops in OS-protected memory | Medium | — | Privacy Before Convenience |

### Summary Statistics

| Domain | Capabilities | High Value | Medium Value | Low Value |
|--------|-------------|------------|--------------|-----------|
| Memory | 13 | 9 | 4 | 0 |
| Awareness | 16 | 5 | 8 | 3 |
| Cognition | 14 | 8 | 5 | 1 |
| Execution | 12 | 6 | 5 | 1 |
| Learning | 10 | 6 | 3 | 1 |
| Interaction | 12 | 6 | 4 | 2 |
| Developer Experience | 15 | 9 | 5 | 1 |
| Utility | 12 | 6 | 5 | 1 |
| Integration | 6 | 3 | 2 | 1 |
| Privacy & Security | 10 | 8 | 2 | 0 |
| **Total** | **110** | **66** | **43** | **11** |

**High-value capabilities (66):** These are the capabilities that most directly strengthen Cortex's vision. They should be prioritized in future planning.

**Low-value capabilities (11):** These are capabilities that are nice to have but not essential. They should be considered only after high and medium value capabilities are addressed.
