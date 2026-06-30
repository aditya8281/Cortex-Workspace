Last updated: 2026-06-30

# CORTEX Governance Rules

This document defines the rules of engagement for all participants (human and agent) in the Cortex development process.

---

## Single Source of Truth

| Topic | Source of Truth | Location |
|-------|----------------|----------|
| Agent behavior | CLAUDE.md | `/CLAUDE.md` |
| Security patterns | AGENTS.md | `/AGENTS.md` |
| System architecture | docs/architecture/overview.md | `/docs/architecture/overview.md` |
| Development roadmap | .agents/plans/IMPLEMENTATION_STEPS.md | `/`.agents/plans/IMPLEMENTATION_STEPS.md` |
| API reference | docs/reference/api.md | `/docs/reference/api.md` |
| Database schema | docs/reference/database.md | `/docs/reference/database.md` |
| Governance | docs/guides/governance.md | `/docs/guides/governance.md` (this file) |
| Design system | DESIGN.md | `/DESIGN.md` |
| Product definition | PRODUCT.md | `/PRODUCT.md` |
| Architectural decisions | docs/decisions/ | `/docs/decisions/` |
| Audit history | docs/audits/ | `/docs/audits/` |
| Hook system | .claude/hooks/ | `/.claude/hooks/` |
| Frontend design | .claude/skills/design/SKILL.md | `/.claude/skills/design/SKILL.md` |

**Rule:** If a topic appears in multiple files, the source of truth wins. Other files must reference it, not duplicate it.

---

## Agent Permission Model

| Level | Capabilities | Human Approval Required |
|-------|-------------|------------------------|
| **Read-only** | Explore code, search, analyze | No |
| **Contributor** | Create branches, commit code | For merge |
| **Reviewer** | Review PRs, approve changes | For final merge |
| **Architect** | Create ADRs, modify governance | Always |

**Default:** Agents start at **Read-only**. Permission upgrades require human approval.

**Violation:** If an agent exceeds its permission level, the action must be reverted and the agent must request upgrade.

---

## Clarification Rules

### Agent MUST Ask Human

| Situation | Reason |
|-----------|--------|
| Irreversible decisions | Schema migrations, breaking API changes, security policy changes |
| Multiple valid paths | Architecture choices with trade-offs, design alternatives |
| Scope ambiguity | Unclear requirements, missing specifications |
| Resource constraints | Time/token budget decisions, priority conflicts |
| Security implications | New auth patterns, data handling changes |
| Breaking changes | API modifications, schema changes, dependency upgrades |
| Cross-domain impact | Changes affecting >2 subsystems |
| New patterns | Introducing new technologies or approaches not in current stack |

### Agent MAY Proceed Without Asking

| Situation | Reason |
|-----------|--------|
| Clear specifications | Task is well-defined with explicit acceptance criteria |
| Existing patterns | Following established codebase patterns |
| Mechanical changes | Typo fixes, formatting, import organization |
| Test updates | Updating tests for existing functionality |
| Documentation fixes | Correcting errors, updating examples |
| Dependency updates | Minor version bumps without breaking changes |

---

## Skill Governance

### Skill-First Rule

Before performing any significant task, agents must determine whether an existing skill can improve the process.

**Workflow:** Context → Find Skill → Use Skill → Brainstorm → Plan → Implement → Test → Validate → Review → Complete

**NOT:** Context → Implement Immediately

### Mandatory Skill Discovery

At the beginning of every major task:

1. Identify the task domain
2. Search for relevant skills
3. Evaluate available skills
4. Select the best skill or skill combination
5. Apply those skills before continuing

### Skill Gap Detection

During execution, agents must continuously evaluate:

- Is this process repetitive?
- Is this process likely to happen again?
- Is this process Cortex-specific?
- Is this process difficult enough to benefit from standardization?
- Is this process valuable enough to reuse?

If yes: Create a Skill Improvement Candidate.

### Skill Creation Workflow

Whenever a reusable workflow is identified:

1. Extract the process
2. Document the process
3. Create a dedicated skill
4. Add examples
5. Add validation steps
6. Integrate it into existing workflows

Creating skills should become a normal part of Cortex development.

### Cortex-Specific Skills

Actively build a library of Cortex-specific skills:

- Cortex Architecture Audit
- Cortex Repository Health Review
- Cortex Planning Consistency Audit
- Cortex Documentation Consistency Audit
- Cortex Memory Review
- Cortex Retrieval Review
- Cortex Model Marketplace Review
- Cortex Agent Review
- Cortex Desktop Readiness Audit
- Cortex Release Readiness Audit
- Cortex Frontend/Backend Contract Audit
- cortex-integrity — Repository integrity analysis (structural, semantic, evolution scans)

Whenever a Cortex-specific workflow becomes mature and reusable, convert it into a dedicated skill.

### Skill Evolution

Skills must not remain static. When a skill is used:

- Review effectiveness
- Review output quality
- Review missing steps
- Review friction points
- Improve the skill

Skills should evolve alongside Cortex.

### Long-Term Objective

The Cortex repository should gradually evolve into a skill-driven engineering system. Over time, more work should move from ad-hoc manual execution to reusable, documented, validated skills.

Success means future agents spend less time reinventing workflows and more time executing proven processes. Whenever a better workflow is discovered, the agent should improve the ecosystem itself rather than only completing the immediate task.

---

## Branching Rules

### Mandatory Branch-Then-Merge

Every significant change must go through a feature branch. Never commit directly to `main`.

**Rule:** `main` branch must always be in a working state. All changes go through: `main` → feature branch → work → verify → merge back to `main`.

**Branch naming:**
- `feat/<topic>` — new features
- `fix/<topic>` — bug fixes
- `docs/<topic>` — documentation changes
- `refactor/<topic>` — code refactoring

**Branch lifecycle:**
1. Create branch from `main`
2. Make changes, commit with descriptive messages
3. Run relevant hooks and tests on the branch
4. When ready, run full verification (`make hooks-merge`, `make test`, `make lint`)
5. Merge to `main` with `--no-ff` (merge commit, not fast-forward)
6. Delete the feature branch after merge

**Parallel branch limit:** Minimize parallel branches. Finish one before starting the next. Maximum 2-3 active branches at any time to reduce merge conflicts.

**Main branch protection:**
- All hooks must pass before merge
- All tests must pass
- No direct commits to `main`
- No merge if main is broken

---

## Code Quality Standards

### Mandatory Before Every Commit

1. `make lint` passes (ruff + mypy)
2. `make format` applied (ruff format)
3. No secrets in code (detect-secrets)
4. No large files added (>500KB)

### Mandatory Before Every PR

1. All tests pass (`make test` + `cd frontend && npm test`)
2. Frontend builds (`cd frontend && npm run build`)
3. No regressions (existing tests still pass)
4. Documentation updated (if applicable)
5. ADR created (if architectural decision made)
6. Run `/project:review` for code quality analysis

### Mandatory Before Merge

1. CI passes (GitHub Actions)
2. Human review approved
3. No unresolved conflicts
4. No revert of previous reverts (circular)

---

## Documentation Standards

### When to Update Documentation

| Change Type | Docs to Update |
|-------------|---------------|
| New API endpoint | docs/API.md |
| New database table | docs/DATABASE.md |
| New security pattern | docs/GOVERNANCE.md (Security section) |
| Architecture change | docs/ARCHITECTURE.md |
| New decision | docs/decisions/NNN-name.md |
| Bug found | docs/audits/YYYY-MM-DD-report.md |
| Governance change | docs/GOVERNANCE.md |

### Documentation Format

- Use Markdown with consistent heading levels
- Include "Last updated" date at top of each doc
- Use tables for structured data
- Use code blocks for commands and examples
- Cross-reference related docs with relative links

---

## Decision Tracking Rules

### When to Create an ADR

- New technology choice
- Architecture pattern change
- Security policy change
- API design decision
- Database schema philosophy change
- Testing strategy change
- Deployment approach change

### ADR Format

```markdown
# ADR-NNN: Title

**Status:** Proposed | Accepted | Deprecated | Superseded by ADR-XXX
**Date:** YYYY-MM-DD
**Deciders:** List of people/agents involved

## Context

What is the issue we're facing?

## Decision

What did we decide?

## Consequences

What are the implications?

## Alternatives Considered

What else did we evaluate?
```

### ADR Rules

1. ADRs are immutable once accepted
2. ADRs can be superseded, not modified
3. ADRs must reference related ADRs
4. ADRs must include alternatives considered
5. ADRs must be created before implementation

---

## Audit Rules

### When to Run Audits

| Trigger | Frequency |
|---------|-----------|
| Scheduled | Weekly (automated) |
| Before release | Manual |
| After major changes | Manual |
| On request | Manual |

### Audit Scope

- Architecture drift detection
- Documentation drift detection
- Technical debt identification
- Dead code detection
- Duplicate code detection
- Incomplete feature detection
- Placeholder detection (TBD, TODO, FIXME)
- Security vulnerability scanning
- Test coverage analysis

### Audit Reporting

Findings are reported in `docs/audits/YYYY-MM-DD-report.md` with:
- Summary (counts by severity)
- Individual findings with file/line references
- Recommended fixes
- Status tracking (Open → In Progress → Fixed)

---

## Security

### Authentication

#### Two-Password Model

| Password | Purpose | Storage | Lifetime |
|----------|---------|---------|----------|
| Login password | Account authentication | Argon2 hash in `users.hashed_password` | Permanent |
| Vault password | Encrypt/decrypt vault files | Argon2 hash + Fernet key derivation in-memory | Cached after unlock, wiped on lock |

**Rationale**: A compromised login password does not expose encrypted vault files. The vault password never leaves the server in plaintext after unlock (cached as `SecurePasswordCache` with bytearray wipe).

#### Cookie-Based Auth

- **Access tokens**: httpOnly cookies (`cortex_access`), 30-minute expiry, auto-refreshed
- **Refresh tokens**: httpOnly cookies (`cortex_refresh`), 7-day expiry, rotation on each use
- **CSRF**: Double-submit cookie pattern (`cortex_csrf` cookie + `X-CSRF-Token` header)
- **No localStorage**: All tokens in httpOnly cookies (XSS-resistant)

#### Auto-Refresh Flow

1. API request returns 401 (token expired)
2. Frontend calls `POST /api/auth/refresh` with refresh token cookie
3. Backend rotates refresh token (issues new access + refresh, revokes old)
4. Original request retried with new access token
5. Transparent to user — no interruption

---

### Ownership Checks

**Rule**: Every user-scoped endpoint MUST verify `resource.user_id == current_user.id` before returning or mutating data.

- Use `Depends(get_current_user)` to resolve the authenticated user
- Query resources with `user_id` filter, not just resource ID
- Never trust client-provided user IDs

---

### Path Traversal Protection

Vault and file operations MUST sanitize paths:
- Reject any path containing `..`
- Reject absolute paths outside the allowed root
- Validate against the vault root before any file operation

---

### Rate Limiting

- Auth endpoints have stricter rate limits
- General endpoints use global IP-based rate limiting via Redis sliding window
- CSRF exemptions for authenticated API endpoints (vault, profile photo)

---

### API Security Patterns

- **Route ordering**: Specific routes before parameterized routes (e.g., `/models/installed` before `/models/{model_id}`)
- **Response models**: Always use `response_model=` on decorators
- **Dependency injection**: `Depends(get_db)` for sessions, `Depends(get_current_user)` for auth
- **Error handling**: `HTTPException` with appropriate codes (404 not found, 403 forbidden, 409 conflict)
- **Pydantic schemas**: Explicit field types in `backend/app/schemas/`. Never use `dict` for structured responses.

---

### Security Audit History

P0/P1 fixes applied:
- Memory API requires authentication
- Vault path traversal blocked
- Token expiry reduced to 30 minutes
- CSRF, CORS, WebSocket security tightened
- Foreign key constraints added to repo models
- CSRF exemptions for authenticated API endpoints
- IDOR vulnerabilities patched (ownership checks on all user-scoped resources)

---

### Frontend Security

- **Auth flow**: `AuthProvider` bootstraps via `GET /me`. Login sets httpOnly cookies. Logout locks vault, clears session. Auto token refresh on 401.
- **API proxy**: Client-side fetch → Next.js API route → FastAPI. Same-origin, no CORS issues.
- **No secrets in client code**: Backend URL exposed via `/api/env` only. No API keys in frontend bundles.

---

### Infrastructure Security

- **Docker**: PostgreSQL, Redis, Qdrant on localhost-only ports
- **CORS**: Restricted to explicit origins
- **CSP headers**: Content Security Policy enabled
- **TLS**: Configure at reverse proxy level (Caddy recommended for auto Let's Encrypt)
- **Secrets**: `detect-secrets` pre-commit hook with baseline
