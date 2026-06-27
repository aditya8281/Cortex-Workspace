# v1.05: Privacy & Trust — CORTEX

**Document:** Version 1.05 Overview
**Authority:** Stage 6 — Master Versioned Implementation Roadmap
**Date:** 2026-06-27
**Type:** Capability Delivery

---

## Objective

Build the privacy and trust foundation: local processing guarantee, encryption at rest and in transit, role-based access control with policy engine, comprehensive audit logging, data sovereignty with full export, transparency with explainable decisions, consent management with granular scopes, and data protection with masking and key rotation.

---

## Question

"Can Cortex be trusted?"

---

## What This Version Delivers

After completing v1.05, Cortex has:

- **Local Processing Guarantee (P1):** All intelligence runs on the user's device. No data leaves the machine unless the user explicitly exports it. A `LocalProcessingService` enforces this invariant and can be verified at any time.
- **Encryption at Rest (P2):** Fernet-encrypted vaults with per-user keys, automatic key rotation every 90 days, encrypted backup support. All sensitive DB columns use application-layer encryption via `EncryptedType`.
- **Encryption in Transit (P3):** HTTPS enforcement on all API routes, TLS 1.3 minimum, HSTS headers, certificate pinning for outbound requests. Middleware enforces transport security.
- **Access Control (P4):** Full RBAC system with roles (admin, user, viewer), permissions matrix, policy engine supporting ABAC rules, resource-level ownership checks, session management with automatic expiry.
- **Audit Logging (P5):** Every significant action (CRUD, auth, consent changes, data export, access checks) is logged with user ID, action, resource type/id, IP, user agent, timestamps, success/failure, and error details. Logs are immutable and queryable.
- **Data Sovereignty (P6):** User owns all data. No server-side retention beyond explicit user action. Complete data lifecycle: create → access → modify → export → delete. Cryptographic proof of deletion.
- **Transparency (P7):** Every automated decision includes explainable reasoning: what factors were considered, what alternatives existed, confidence level, and audit trail. Users can query "why did Cortex do X?" at any time.
- **Consent Management (P8):** Granular consent records per data category, scope, and time period. Consent can be granted, revoked, and queried. All data access checks consent before proceeding.
- **Data Import/Export (X5):** Full data portability in standard formats (JSON, CSV). Users can export all their data, import from external sources, and verify export completeness.

---

## reference architecture Feature Traceability

This version maps to the following reference architecture features from the original specification:

| reference architecture Feature | Cortex Capability | Implementation |
|-----------------|-------------------|----------------|
| Data Encryption | P2, P3 | Fernet vault + TLS enforcement |
| Access Control | P4 | RBAC + ABAC policy engine |
| Audit Trail | P5 | Immutable audit log with full context |
| User Consent | P8 | Granular consent management with expiry |
| Data Export | X5 | JSON/CSV export with verification |
| Local-First | P1 | Local processing enforcement |
| Explainable AI | P7 | Decision explanation service |
| Data Deletion | P6 | Cryptographic deletion proof |

---

## Capability Mapping

| ID | Name | Domain | Priority | Description |
|----|------|--------|----------|-------------|
| P1 | Local Processing | Privacy | Foundation | All intelligence on user's device. No cloud dependency. |
| P2 | Encryption at Rest | Privacy | Foundation | Fernet-encrypted vaults, per-user keys, key rotation, encrypted DB columns. |
| P3 | Encryption in Transit | Privacy | Foundation | HTTPS enforcement, TLS 1.3, HSTS headers, certificate validation. |
| P4 | Access Control | Privacy | Foundation | RBAC roles, ABAC policies, permission matrix, session management. |
| P5 | Audit Logging | Privacy | Foundation | Immutable audit trail for all significant actions with full context. |
| P6 | Data Sovereignty | Privacy | Foundation | User owns all data, deletion proofs, no server-side retention. |
| P7 | Transparency | Privacy | Foundation | Explainable decisions, factor analysis, alternative tracking. |
| P8 | Consent Management | Privacy | Core | Granular consent per data category with expiry and revocation. |
| X5 | Data Import/Export | Integration | Foundation | Standard format portability: JSON, CSV, with completeness verification. |

**Total: 9 capabilities**

---

## Phases

| Phase | Name | Focus | Complexity | Duration |
|-------|------|-------|------------|----------|
| P01 | Privacy Models & Schema | Database models, Pydantic schemas, encryption models, consent tracking, access control schema | Medium | 1.0 day |
| P02 | Encryption & Access Control | Vault encryption service, RBAC implementation, policy engine, permission checking, local processing | High | 1.5 days |
| P03 | Audit & Consent Services | Audit logging, transparency explanations, data export, data masking, key rotation | Medium | 1.0 day |
| P04 | API & Integration | REST endpoints, frontend API client, privacy dashboard, security testing, Swagger docs | Medium | 1.0 days |

**Total estimated: 4-5 days**

---

## Architecture Principle Cross-References

This version engages the following architecture principles from `.agents/plans/guide.md`:

| Principle | Section | Relevance to v1.05 |
|-----------|---------|---------------------|
| Daemon Architecture | 4.1 | Privacy services run as daemon-internal singletons; audit logging integrates with daemon lifecycle |
| Memory Architecture | 4.3 | Encryption wraps memory storage; access control gates memory retrieval; consent controls memory creation |
| Graph Architecture | 4.4 | Knowledge graph queries respect access control; graph data encrypted at rest |
| Retrieval Architecture | 4.5 | RAG pipeline checks consent before retrieval; search results filtered by permission |
| Agent Architecture | 4.6 | Agent actions logged to audit trail; agent access controlled by RBAC; agent decisions explained by transparency service |
| Workflow Architecture | 4.7 | Workflow steps check permissions; workflow actions logged; workflow data exportable |
| Plugin Architecture | 4.8 | Plugins must declare data requirements; consent gates plugin data access; plugin actions audited |
| CLI Architecture | 4.9 | CLI commands check auth; CLI output respects access control; CLI operations logged |

---

## Downstream Dependency Impact

### Directly Blocked by v1.05

| Version | What It Needs | How v1.05 Provides It |
|---------|--------------|----------------------|
| v1.06 (Cognition & Execution) | Trust foundation for autonomous actions | RBAC controls what cognition can do; audit trail records all reasoning; transparency explains decisions |
| v1.10 (Planning & Orchestration) | Permission-gated workflows | Policy engine enforces workflow permissions; consent controls data flow in plans |
| v1.14 (Advanced Intelligence) | Explainable reasoning chain | Transparency service extends to reasoning traces; confidence scores audited |

### Indirect Dependencies

| Version | Dependency Chain |
|---------|-----------------|
| v1.07 (Memory Evolution) | v1.05 → v1.06 → v1.07 (memory evolution needs cognition, which needs trust) |
| v1.11 (Graph Intelligence) | v1.05 → graph queries respect RBAC and consent |
| v1.13 (Autonomous Agents) | v1.05 → agent autonomy requires audit + permission boundaries |

---

## Risk Matrix

| Risk | Likelihood | Impact | Mitigation | Phase |
|------|-----------|--------|------------|-------|
| Key rotation breaks existing encrypted data | Medium | High | Implement key ring with rotation; test decrypt with old keys after rotation; rollback migration | P02 |
| RBAC policy engine too slow for real-time checks | Low | Medium | Cache permission checks in Redis with 5-min TTL; invalidate on role change | P02 |
| Audit log table grows unbounded | Medium | Medium | Implement log retention policy (90-day default); partition by month; archival to cold storage | P03 |
| Consent state inconsistency across services | Low | High | Single consent service as source of truth; all access checks go through it; event-driven invalidation | P02 |
| Data export includes encrypted fields without decrypting | Medium | Medium | Export pipeline decrypts all fields before serialization; verify in integration tests | P03 |
| TLS middleware conflicts with existing CORS | Low | Medium | Test HTTPS redirect with CORS in combination; add exception for localhost development | P04 |
| Frontend consent UI doesn't reflect backend state | Medium | Low | SSE/WebSocket for real-time consent state sync; optimistic updates with rollback | P04 |
| Audit log query performance degrades with scale | Medium | Medium | Add composite indexes on (user_id, timestamp) and (resource_type, resource_id); paginate all queries | P03 |
| Plugin data access bypasses consent | Low | High | Plugin manager enforces consent check before any data access; tested in integration suite | P02 |

---

## Strengthened Definition of Done

### Per-Phase DoD

Each phase must satisfy:

- [ ] All task-level tests written and passing (unit + integration)
- [ ] Security scan: no hardcoded secrets, no SQL injection vectors, no unencrypted sensitive data
- [ ] Performance gate: all DB queries under 50ms at expected scale; API endpoints under 200ms p99
- [ ] Integration tests: cross-service flows verified (e.g., consent → access → audit → export)
- [ ] Documentation updated: API docs, architecture docs, ADR if new pattern introduced
- [ ] Code review: at least one approval, no unresolved comments
- [ ] Migration tested: applies cleanly, rolls back cleanly, no data loss

### Version-Level DoD

- [ ] All 9 privacy capabilities implemented and tested
- [ ] Privacy services in `services/privacy/` (encryption, access_control, audit, transparency, export, local_processing, data_masking, consent_manager)
- [ ] Privacy models in `models/privacy/` (audit_log, consent, data_export, access_policy, role, permission)
- [ ] Privacy API endpoints in `api/v1/privacy/` (audit, consent, export, transparency, access_control)
- [ ] Frontend privacy hooks in `features/privacy/api.ts`
- [ ] All unit tests passing (`make test`)
- [ ] All lint checks passing (`make lint`)
- [ ] Frontend tests passing (`cd frontend && npm test`)
- [ ] Integration test suite: consent → access → audit → export flow verified
- [ ] Security scan: bandit + safety check clean
- [ ] Performance: API endpoints p99 < 200ms
- [ ] ADR created for RBAC + ABAC hybrid decision

---

## Estimated Duration

4-5 days.

---

## Readiness for Next Version

v1.05 is complete when all privacy capabilities are implemented, tested, security-scanned, and performance-verified. v1.06 (Cognition & Execution Core) can begin immediately — it needs the trust foundation to safely execute autonomous reasoning and tool calls.
