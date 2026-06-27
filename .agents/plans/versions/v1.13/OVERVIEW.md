# v1.13: Utility & Integration — CORTEX

**Document:** Version 1.13 Overview
**Authority:** Stage 6 — Master Versioned Implementation Roadmap
**Date:** 2026-06-27
**Type:** Capability Delivery
**Complexity:** High

---

## Objective

Build comprehensive utility services (calendar, email, tasks, notes, documents, contacts, workspace, dashboard) and a full integration layer (tool integration, service integration, protocol support, extensions, import/export, cross-device sync). This version transforms CORTEX from an intelligence system into a complete daily-life operating system.

---

## Question

"Can Cortex help with daily life and connect to the world?"

---

## What This Version Delivers

After completing v1.13, Cortex can:

- Manage calendar events with recurrence rules, CalDAV support, and conflict detection
- Process, categorize, and summarize emails with AI-powered triage
- Track tasks with priorities, due dates, subtasks, and recurring schedules
- Store, organize, search, and version Markdown notes with wiki-links and frontmatter
- Handle multi-format documents with smart chunking, version history, and full-text search
- Manage contacts with CardDAV support and automatic entity-linking
- Organize workspaces as logical groupings of projects, notes, and resources
- Provide unified dashboards with cross-domain aggregation and real-time metrics
- Integrate with external tools via registered adapters with health monitoring
- Connect to services via MCP, REST, and WebSocket protocols
- Install, enable, disable, and remove extensions via a plugin registry
- Import and export data across all domains with format conversion
- Sync data across devices with conflict resolution and differential sync
- Deliver daily briefings and weekly reviews
- Track habits and manage focus sessions

---

## reference architecture Feature Traceability

This version implements **reference architecture Tier 4 (Full AI Assistant)** and extends it with comprehensive integration capabilities:

| reference architecture Item | Cortex Delivery | Version Plan Mapping |
|---------------|-----------------|---------------------|
| Email system (IMAP/SMTP, triage, AI reply) | EmailProcessingService — categorization, summarization, action detection | P03 |
| Calendar system (CRUD, ICS, CalDAV, RRULE) | CalendarService — full CRUD, recurrence, CalDAV sync, conflict detection | P02 |
| Task system (CRUD, priorities, reminders) | TaskService — priorities, subtasks, recurring tasks, reminders | P02 |
| Notes system (markdown, wiki-links, frontmatter) | NotesService — Markdown-native, tags, folders, full-text search | P02 |
| Documents system (multi-format, smart chunking) | DocumentHandlingService — multi-format, version history, chunking | P03 |
| Contacts system (CardDAV, resolution) | ContactService — CRUD, CardDAV, entity-linking | P03 |
| Workspace dashboard | DashboardService — cross-domain aggregation, metrics, widgets | P05 |
| Tool integration | ToolIntegrationService — adapter registry, health checks, execution | P04 |
| Protocol support (MCP, REST, WebSocket) | ProtocolSupportService — unified protocol handler | P04 |
| Extension system | ExtensionService — install, toggle, uninstall, config | P05 |
| Cross-device sync | CrossDeviceSyncService — differential sync, conflict resolution | P05 |
| Data portability (import/export) | DataPortabilityService — multi-format import/export | P04 |

**Coverage:** All reference architecture Tier 4 items addressed. Three new capabilities beyond reference architecture: Daily Briefing (U9), Weekly Review (U10), Habit Tracking (U11), Focus Management (U12).

---

## Capabilities Delivered

| ID | Name | Domain | Priority | Phase |
|----|------|--------|----------|-------|
| U1 | Calendar Management | Utility | Core | P02 |
| U2 | Email Processing | Utility | Core | P03 |
| U3 | Task Management | Utility | Core | P02 |
| U4 | Notes Management | Utility | Core | P02 |
| U5 | Document Handling | Utility | Core | P03 |
| U6 | Contact Management | Utility | Core | P03 |
| U7 | Workspace Organization | Utility | Core | P05 |
| U8 | Dashboard | Utility | Core | P05 |
| U9 | Daily Briefing | Utility | Core | P05 |
| U10 | Weekly Review | Utility | Core | P05 |
| U11 | Habit Tracking | Utility | Core | P02 |
| U12 | Focus Management | Utility | Core | P02 |
| X1 | Tool Integration | Integration | Core | P04 |
| X2 | Service Integration | Integration | Core | P04 |
| X3 | Protocol Support | Integration | Core | P04 |
| X4 | Extension System | Integration | Core | P05 |
| X5 | Data Portability | Integration | Core | P04 |
| X6 | Cross-Device Sync | Integration | Core | P05 |
| P9 | Data Portability | Privacy | Core | P04 |
| P10 | Right to be Forgotten | Privacy | Core | P04 |

**Total: 20 capabilities** (19 from original + X5 Data Portability split from P9)

---

## Capability Mapping

### Utility Capabilities by Domain Integration

| Utility Domain | Cross-Domain Dependencies | Intelligence Integration |
|----------------|---------------------------|--------------------------|
| Calendar | Tasks (due dates link to events), Contacts (meeting attendees), Notes (meeting notes) | CalendarService feeds DailyBriefingService for morning summary |
| Tasks | Calendar (deadline events), Notes (task notes), Documents (attached files) | TaskService feeds FocusManager for prioritized work sessions |
| Notes | Documents (embedded docs), Tasks (action items from notes), Contacts (mentioned people) | NotesService feeds KnowledgeGraph for entity extraction |
| Documents | Notes (linked notes), Tasks (action items), Calendar (document deadlines) | DocumentHandlingService feeds HybridRetrievalV2 for full-text + semantic search |
| Contacts | Calendar (attendees), Tasks (assigned contacts), Email (sender/recipient) | ContactService feeds EntityLinker for automatic cross-domain linking |
| Email | Calendar (meeting invites), Tasks (action items), Contacts (sender resolution) | EmailProcessingService feeds AI categorization and priority scoring |
| Dashboard | All domains — aggregates metrics, surfaces insights | DashboardService orchestrates cross-domain query composition |
| Workspace | All domains — logical grouping container | WorkspaceService provides namespace isolation for multi-project users |

### Integration Capabilities by Protocol

| Protocol | Supported Operations | Security Considerations |
|----------|---------------------|------------------------|
| MCP | Tool discovery, tool invocation, resource listing | Token-based auth, rate limiting, input validation |
| REST | CRUD operations, webhooks, service proxying | JWT auth, CORS, request size limits |
| WebSocket | Real-time updates, live sync, streaming | Connection auth, heartbeat, reconnection |

---

## Phases

| Phase | Name | Focus | Complexity | Duration | Risk |
|-------|------|-------|------------|----------|------|
| P01 | Utility Models & Schema | Database models, Pydantic schemas, migrations | Medium | 3-4h | Low |
| P02 | Calendar & Tasks | Calendar, task, notes, habit, focus services | High | 6-8h | Medium |
| P03 | Email & Documents | Email processing, document handling, contacts | High | 5-7h | Medium |
| P04 | Integration Layer | Tool/service/protocol integration, data portability | High | 5-6h | High |
| P05 | Extensions & Sync | Extensions, cross-device sync, workspace, dashboard | High | 6-8h | High |
| P06 | API & Integration | All endpoints, frontend components, tests, webhooks | Medium | 5-6h | Medium |

**Total estimated: 30-39 hours (10-12 working days)**

---

## Dependencies

### Upstream Dependencies

| Version | Component Needed | How v1.13 Uses It |
|---------|------------------|-------------------|
| v1.05 | Privacy models, encryption, vault | Document storage encryption, data export/import encryption, contact privacy |
| v1.08 | Awareness models, context providers | Calendar/task context for awareness engine, dashboard awareness metrics |
| v1.01 | Domain-driven structure | Utility/integration services follow established domain patterns |
| v1.02 | Event bus, service registry | Utility services publish events, register with service registry |
| v1.03 | Auth infrastructure | All endpoints require JWT auth, ownership checks |
| v1.04 | Frontend architecture | Dashboard/workspace components follow feature module patterns |

### Downstream Impact

v1.13 feeds into v1.14 (Advanced Intelligence) by providing:
- **Utility data** for advanced reasoning (calendar patterns, task history, note content)
- **Integration layer** for connecting advanced cognition to external services
- **Workspace context** for consciousness simulation
- **Dashboard metrics** for meta-cognition performance tracking

---

## Architecture Principle Cross-References

| Principle | How v1.13 Satisfies It |
|-----------|----------------------|
| **3.1 Local-First** | All utility data stored in local PostgreSQL. No external service calls without explicit user action. CalDAV/CardDAV are opt-in sync, not required. |
| **3.2 Graceful Degradation** | Every integration service has a fallback: ToolIntegration returns stub for unavailable tools, ProtocolSupport degrades to mock responses, SyncService queues changes when offline. |
| **3.3 Daemon-First, Surface-Second** | All utility capabilities accessible via API (P06). Dashboard works via CLI. Workspace management works without frontend. |
| **3.4 Separation of Concerns** | Calendar ≠ Tasks ≠ Notes ≠ Documents ≠ Contacts — each is an independent service boundary. Integration layer is separate from utility layer. |
| **3.5 Plugin Boundaries Early** | Extension system (P05) provides Protocol interfaces for all extension points. ToolIntegration uses adapter pattern. |
| **3.6 Evidence Over Opinion** | All model schemas derived from reference architecture Tier 4 requirements and real-world usage patterns. |
| **3.7 Incremental Safety** | P01 creates all models with migration rollback. Each phase builds on the previous. Tests at every boundary. |

---

## Expanded Risk Matrix

| Risk | Probability | Impact | Severity | Mitigation | Phase |
|------|------------|--------|----------|------------|-------|
| CalDAV/CardDAV integration complexity | High | Medium | High | Start with local-only, add CalDAV as opt-in adapter behind Protocol interface | P02, P03 |
| Cross-device sync conflict resolution | Medium | High | High | Implement last-write-wins first, add operational transform later | P05 |
| Extension system security (arbitrary code execution) | Medium | High | High | Sandboxed execution, permission model, code signing verification | P05 |
| Email protocol complexity (IMAP/SMTP/OAuth) | High | Medium | High | Abstract behind EmailProvider Protocol, implement mock first, real later | P03 |
| Dashboard performance with many domains | Medium | Medium | Medium | Pagination, caching, lazy loading of domain widgets | P05 |
| Document format parsing failures | Medium | Low | Medium | Graceful fallback to raw text extraction, format detection | P03 |
| Migration rollback for complex schema | Low | High | Medium | Write rollback migration alongside forward migration, test both | P01 |
| Task recursive dependencies (subtasks) | Low | Medium | Low | Limit nesting depth to 5, validate no cycles at creation | P02 |
| Rate limiting on integration endpoints | Low | Medium | Low | Configurable rate limits per extension, global fallback | P06 |
| Frontend component bundle size | Medium | Low | Low | Lazy loading per feature module, code splitting | P06 |

---

## Performance Considerations

| Area | Target | Strategy |
|------|--------|----------|
| Calendar queries | <50ms for 1 year of events | Indexed on (user_id, start_time), partition by month |
| Task list queries | <30ms for 1000 tasks | Indexed on (user_id, status, due_date) |
| Note full-text search | <100ms for 5000 notes | PostgreSQL full-text search with GIN index on content |
| Document search | <200ms for 10K documents | Hybrid: full-text for metadata, vector for content similarity |
| Dashboard aggregation | <500ms for all domains | Materialized views, cached queries, background refresh |
| Extension loading | <100ms per extension | Lazy import, cached module references |
| Sync conflict resolution | <200ms per conflict | Hash-based detection, vector clock ordering |
| Email categorization | <500ms per email | Keyword-based fast path, LLM-based for ambiguous |

---

## Security Considerations

| Area | Threat | Mitigation |
|------|--------|------------|
| Document storage | Sensitive file content exposure | Fernet encryption at rest (existing vault pattern) |
| Email processing | Credential leakage in IMAP/SMTP | OAuth 2.0 tokens, never store plaintext passwords |
| Extension system | Malicious extension code execution | Permission model, sandboxed execution, user approval required |
| Cross-device sync | Man-in-the-middle data interception | TLS for all sync traffic, HMAC verification |
| Data export | Sensitive data in export files | Encrypted exports with user password, audit logging |
| Calendar sharing | Event data exposure | Per-event visibility settings, user-scoped queries only |
| Contact data | PII exposure | Encryption at rest, access logging, right-to-be-forgotten support |
| Webhook endpoints | SSRF via webhook URLs | URL validation, allowlist for outbound connections |
| Tool integration | Command injection via tool parameters | Input sanitization, parameterized queries, allowlist-based execution |

---

## Database Schema Summary

### New Tables (P01)

| Table | Key Columns | Indexes | Purpose |
|-------|-------------|---------|---------|
| `calendar_events` | user_id, title, start_time, end_time, recurrence, rrule | (user_id, start_time), (user_id, end_time) | Calendar events with recurrence |
| `tasks` | user_id, title, priority, status, due_date, parent_id | (user_id, status), (user_id, due_date), (parent_id) | Task management with subtasks |
| `notes` | user_id, title, content, tags, folder, pinned | (user_id, folder), GIN on content (full-text) | Markdown notes |
| `documents` | user_id, title, file_path, file_type, version | (user_id, file_type), GIN on summary | Document metadata |
| `document_versions` | document_id, version, content, created_by | (document_id, version) | Version history |
| `contacts` | user_id, name, email, phone, organization | (user_id, email), (user_id, name) | Contact management |
| `email_messages` | user_id, subject, body, category, sender, received_at | (user_id, category), (user_id, received_at) | Email cache |
| `habits` | user_id, name, frequency, target_count, current_streak | (user_id, name) | Habit tracking |
| `focus_sessions` | user_id, start_time, end_time, task_id, productivity_score | (user_id, start_time) | Focus management |
| `extensions` | user_id, name, version, enabled, config | (user_id, name) | Extension registry |
| `sync_metadata` | device_id, data_type, version_hash, last_synced | (device_id, data_type) | Cross-device sync |
| `workspaces` | user_id, name, description, settings | (user_id, name) | Workspace organization |
| `webhooks` | user_id, url, secret, events, enabled | (user_id, enabled) | Webhook system |

### Migration Strategy

- Forward migration: Creates all tables with proper indexes
- Rollback migration: Drops all tables, preserves data in backup
- Data integrity: Foreign keys enforced, CHECK constraints on enums
- Performance: Partial indexes for common queries, GIN indexes for full-text

---

## Validation Commands

```bash
# After P01 (Models)
make migration m="add utility and integration models"  # Migration applies
alembic upgrade head && alembic downgrade -1 && alembic upgrade head  # Rollback test
make test  # All tests pass

# After P02 (Calendar & Tasks)
pytest tests/test_utility_calendar.py -v
pytest tests/test_utility_tasks.py -v
pytest tests/test_utility_notes.py -v
make lint

# After P03 (Email & Documents)
pytest tests/test_utility_email.py -v
pytest tests/test_utility_documents.py -v
pytest tests/test_utility_contacts.py -v

# After P04 (Integration)
pytest tests/test_integration_tools.py -v
pytest tests/test_integration_protocols.py -v
pytest tests/test_integration_portability.py -v

# After P05 (Extensions & Sync)
pytest tests/test_integration_extensions.py -v
pytest tests/test_integration_sync.py -v
pytest tests/test_utility_workspace.py -v
pytest tests/test_utility_dashboard.py -v

# After P06 (API)
pytest tests/ -v  # Full suite
make check  # lint + test
make hooks-merge  # Pre-merge validation

# Performance
python -m pytest tests/performance/test_utility_queries.py -v
```

---

## Definition of Done

### All Criteria Must Be Met

- [ ] All 20 utility/integration capabilities implemented and tested
- [ ] Utility services in `backend/app/services/utility/`
- [ ] Integration services in `backend/app/services/integration/`
- [ ] All database models created with proper indexes and constraints
- [ ] All Pydantic schemas with validation rules
- [ ] All API endpoints with `response_model=` decorators
- [ ] All endpoints require JWT auth with ownership checks
- [ ] Frontend API client with TypeScript types
- [ ] Frontend dashboard and workspace components
- [ ] Webhook system with HMAC verification
- [ ] Extension system with permission model
- [ ] Cross-device sync with conflict resolution
- [ ] Data import/export with format conversion
- [ ] All tests passing (`make test` + `cd frontend && npm test`)
- [ ] Lint clean (`make lint` + `make format`)
- [ ] Build succeeds (`make check`)
- [ ] Documentation updated
- [ ] Migration applies cleanly with rollback verified
- [ ] Performance targets met for all query patterns
- [ ] Security review complete for extension system and sync

---

## Estimated Duration

**10-12 working days** (30-39 hours of implementation)

Phase breakdown:
- P01: 3-4 hours (models & schema)
- P02: 6-8 hours (calendar, tasks, notes, habits, focus)
- P03: 5-7 hours (email, documents, contacts)
- P04: 5-6 hours (integration layer, protocols, portability)
- P05: 6-8 hours (extensions, sync, workspace, dashboard)
- P06: 5-6 hours (API, frontend, tests, webhooks)
