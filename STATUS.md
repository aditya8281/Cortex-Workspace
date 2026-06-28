# CORTEX — Project Status

**Last Updated:** 2026-06-28
**Branch:** `frontend-design`
**Total Commits:** 636

---

## Codebase Metrics

| Metric | Value |
|--------|-------|
| Backend Python files | 379 |
| Backend LoC | 40,947 |
| Backend services | 106 |
| Backend models | 44 |
| Backend schemas | 45 |
| Agent system files | 67 |
| Frontend TSX/TS files | 107 |
| Frontend LoC | 9,933 |
| Frontend feature components | 38 |
| Frontend shared UI components | 12 |
| Test files (total) | 201 (169 root + 32 backend) |
| Test LoC | 18,041 |
| Tests passing | 1,743 |
| Test warnings | 5 (third-party: passlib, starlette) |
| Database migrations | 37 |
| Documentation files | 57 |
| ADRs | 22 |
| API endpoints | 186 (177 domain + 9 auth) |
| Frontend pages | 17 real + 4 Coming Soon = 24 total |
| Git commits | 636 |

---

## Backend Architecture

### 10 Domain Routers (177 endpoints)

| Domain | Endpoints | Services | Description |
|--------|-----------|----------|-------------|
| Memory | 44 | memory/*, knowledge_graph | Episodic/semantic/working memory, graph relationships, search, decay |
| Privacy | 39 | privacy/* | Consent management, audit logging, RBAC/ABAC, data export, vault encryption |
| Awareness | 23 | awareness/* | Device detection, file tracking, project detection, repo analysis, health monitoring |
| Interaction | 23 | chat/*, conversations | Chat conversations, streaming SSE, model selection, notifications |
| Integration | 15 | sync/*, file_watcher | GitHub sync, file system watching, service connectors |
| Cognition | 14 | agents/* | Agent loop, run manager, stall detection, verifier, compactor, policy engine |
| Developer | 11 | intelligence/* | Model catalog, providers, variants, benchmarks, recommendation engine |
| System | 8 | system/* | Health checks (live/ready/deep), system metrics, process monitoring |

### Auth Router (9 endpoints)

| Endpoint | Method | Description |
|----------|--------|-------------|
| /auth/register | POST | User registration |
| /auth/login | POST | JWT login |
| /auth/logout | POST | Token invalidation |
| /auth/refresh | POST | Token refresh |
| /auth/me | GET | Current user |
| /auth/csrf | GET | CSRF token |
| /auth/rate-limit | GET | Rate limit info |
| /auth/audit | GET | Audit log |
| /auth/password | PUT | Change password |

### Agent System

| Component | File | Lines | Description |
|-----------|------|-------|-------------|
| Loop | loop.py | 481 | Main agent execution loop |
| Run Manager | run_manager.py | 415 | Run lifecycle management |
| Tool Defs | tool_defs.py | 542 | Tool definitions and schemas |
| Verifier | verifier.py | 321 | Output verification |
| Executor | executor.py | 321 | Tool execution |
| Security | security.py | — | Security policy engine |

### Services (106 files, 40,947 LoC)

| Largest Files | Lines | Purpose |
|---------------|-------|---------|
| vault.py | 810 | Encrypted vault operations |
| ollama_catalog.py | 687 | Ollama model catalog |
| tool_defs.py | 542 | Agent tool definitions |
| recommendation.py | 525 | Model recommendation engine |
| downloader.py | 522 | Model download manager |

---

## Frontend Architecture

### 24 Pages (17 real + 4 Coming Soon)

| Page | Lines | Description |
|------|-------|-------------|
| / (Dashboard) | 56B | System metrics — CPU, RAM, GPU, disk |
| /chat | 325 | Conversations, streaming, code blocks, sources |
| /agents | 232 | Agent management, chat, run history |
| /models | 315 | Browse, download, compare, installed |
| /awareness | 39 | Overview cards |
| /awareness/repos | 140 | Repository management |
| /awareness/indexing | 30 | Indexing config |
| /memory | 281 | Knowledge graph, search |
| /search | 135 | Unified search |
| /vault | 194 | Encrypted document locker |
| /privacy | 33 | Overview dashboard |
| /privacy/audit | 189 | Audit log viewer |
| /privacy/consent | 163 | Consent management |
| /system | 95 | System health |
| /settings | 162 | User settings |
| /auth | 89 | Login |
| /auth/register | 104 | Registration |
| /marketplace | — | Coming Soon |
| /notes | — | Coming Soon |
| /scheduler | — | Coming Soon |
| /tasks | — | Coming Soon |

### 12 Shared UI Components

| Component | Location | Description |
|-----------|----------|-------------|
| Badge | shared/ui/Badge.tsx | Status badges (default/success/warning/danger) |
| Button | shared/ui/Button.tsx | Action buttons (primary/ghost/danger, sm/md/lg) |
| Card | shared/ui/Card.tsx | Content containers |
| ComingSoon | shared/ui/ComingSoon.tsx | Placeholder for future features |
| EmptyState | shared/ui/EmptyState.tsx | Empty state illustrations |
| Input | shared/ui/Input.tsx | Form inputs |
| Modal | shared/ui/Modal.tsx | Dialog with focus trap |
| Skeleton | shared/ui/Skeleton.tsx | Loading shimmer |
| StatusDot | shared/ui/StatusDot.tsx | Status indicators |
| Toast | shared/ui/Toast.tsx | Notifications |
| Tooltip | shared/ui/Tooltip.tsx | Hover tooltips |
| Tabs | shared/ui/Tabs.tsx | Tab navigation |

### Design System (DESIGN.md Tokens)

| Token | Hex | Usage |
|-------|-----|-------|
| void | #0a0a0f | Background |
| bg-elevated | #111118 | Elevated surfaces |
| bg-surface | #16161f | Cards, inputs |
| bg-hover | #1c1c28 | Hover states |
| accent | #0ea5c9 | Primary accent |
| text-primary | #e8e8ed | Primary text |
| text-secondary | #9a9aaa | Secondary text |
| text-muted | #7a7a8a | Muted text |
| border-subtle | #1e1e2a | Borders |
| danger | #ef4444 | Destructive |
| success | #22c55e | Success |
| warning | #eab308 | Warning |

### Quality Gates

| Check | Status |
|-------|--------|
| Forbidden patterns (transition-all, h-screen, scale(0), gradient-text) | 0 violations |
| ARIA annotations | 53 across codebase |
| Focus-visible rings | All interactive elements |
| Reduced motion | Global in globals.css |
| Touch targets | min-h-[44px] on buttons, h-11 on inputs |
| Contrast ratios | All pass WCAG AA (4.5:1) |

### Animation Budgets (Emil Kowalski Standard)

| Element | Duration | Easing |
|---------|----------|--------|
| Hover | 150ms | ease-out |
| Press | 75-80ms | ease-out |
| Modal/Toast | 250ms | ease-out-quart |
| Sidebar nav | 200ms | ease-out |
| Progress bars | 300-500ms | ease-out |

---

## Test Suite (1,743 passing)

| Category | Tests | Coverage |
|----------|-------|----------|
| Agents | ~300 | Loop, compactor, events, intent, stall, token counter, tools, policy, verifier |
| API | ~250 | Auth, conversations, security, indexing, knowledge, memory, agents, GitHub |
| Awareness | ~150 | Device, environment, health, filesystem, project, repository, API |
| Intelligence | ~200 | Catalogue, download, hardware, models, Ollama, providers, recommendation, scanning, seed, sync |
| Memory | ~200 | API, search, decay, working memory, graph, document indexer |
| Privacy | ~150 | Access control, API, audit, deletion, encryption, export, models, transparency |
| Services | ~200 | Memory services, notification, settings, system |
| Infrastructure | ~100 | Config, DB bootstrap, middleware, Redis cache, vault |

---

## Git History (Last 15 Commits)

```
1277da8 fix: resolve Pyright warnings and line-length violations
86bd92b fix: resolve type errors and remaining datetime deprecation warnings
55866a4 fix: replace datetime.utcnow() with datetime.now(timezone.utc) to resolve deprecation warnings
704f0c5 docs: update README, CLAUDE.md, STATUS.md with verified metrics (1743 tests, 186 endpoints, 24 pages)
41e4e78 refactor: migrate inline animate-pulse to shared Skeleton component
05a82e1 feat(chat): wire ConversationItem, MessageBubble, SourcesPanel into chat page
b4d896d feat(privacy): add overview dashboard, audit log viewer, and consent management pages
f3a2314 feat(chat): add ConversationItem and SourcesPanel components
32cb0bb feat(awareness): add IndexingConfigForm and indexing configuration page
2c3f443 feat(awareness): add RepoListItem, AddRepoModal, IndexProgress, GraphView
8b8f7e2 feat(awareness): add DeviceCard, EnvironmentCard, HealthCard, ProjectCard
d6e7f3a feat(awareness): add overview dashboard, repos page, and API client
c4a2b1d feat(models): add ModelCard, BrowseView, InstalledView, DownloadsView
e5f9a3b feat(dashboard): replace hardcoded SystemOverview with real metrics
f3c2b1d feat(chat): add CodeBlock and MessageBubble components
```

---

## What Was Built This Session

| Plan | Files Created | Files Modified | Status |
|------|--------------|----------------|--------|
| Docs + Metrics | 2 (.env.example, STATUS.md) | 3 (README, CLAUDE.md, architecture/overview.md) | COMPLETE |
| Skeleton Migration | 7 files updated | — | COMPLETE |
| Datetime Deprecation Fix | — | 10 files | COMPLETE |
| Type Errors + Lint Fix | — | 4 files | COMPLETE |
| Awareness Dashboard | 15 | 1 (Sidebar) | COMPLETE |
| Dashboard Integration | 0 | 3 (api.ts, SystemOverview, MetricsRow) | COMPLETE |
| Privacy & Trust | 12 | 1 (Sidebar) | COMPLETE |
| Chat Improvements | 4 | 1 (chat/page.tsx) | COMPLETE |
| Dashboard Integration | 0 | 3 (api.ts, SystemOverview, MetricsRow) | COMPLETE |
| Privacy & Trust | 12 | 1 (Sidebar) | COMPLETE |
| Chat Improvements | 4 | 1 (chat/page.tsx) | COMPLETE |
| Skeleton Migration | 7 files updated | — | COMPLETE |
| Documentation Update | 3 (README, CLAUDE.md, STATUS.md) | — | COMPLETE |

---

## Known Technical Debt

| Issue | Severity | File | Impact |
|-------|----------|------|--------|
| .cortex_bootstrap/ existed in working tree | CRITICAL | root | Security — now removed |
| SecurePasswordCache stores passwords in memory | CRITICAL | vault.py | Accepted risk for single-server; needs HSM for multi-server |
| 5 test warnings (passlib/starlette, not ours) | MINOR | deps | Third-party; no action |
| No .env.example in repo | MODERATE | root | Onboarding friction |
| backend/tests/ and tests/ both exist | MODERATE | both | Confusing test organization |
| 810-line vault.py (god module) | MODERATE | vault.py | Maintainability |
| 687-line ollama_catalog.py | MODERATE | services/ | Maintainability |
| Inline skeleton in StreamingIndicator/IndexProgress | MINOR | 2 files | Intentional — different animation patterns |
| No sr-only text on icon-only buttons | MINOR | Sidebar.tsx | Accessibility for older screen readers |
| Test count stale in docs/audits/ | MINOR | docs/ | Already fixed in this session |

---

## Infrastructure

| Component | Technology | Port |
|-----------|-----------|------|
| Backend | FastAPI + Python 3.12 | 8000 |
| Frontend | Next.js 15 + React 19 | 3000 |
| Database | PostgreSQL 16 | 5435 (start.sh) / 5432 (Docker) |
| Cache | Redis 7 (optional) | 6379 |
| Vector DB | Qdrant (embedded) | 6333 |
| Task Queue | arq + Redis | — |
| Auth | JWT + Argon2 + CSRF | — |
| Encryption | Fernet + PBKDF2 | — |

---

## Frontend Pages Coverage

| Page | Status | Backend |
|------|--------|---------|
| Dashboard | REAL | /system/metrics, /models/health |
| Chat | REAL | /chat/* |
| Agents | REAL | /agents/* |
| Models | REAL | /intelligence/*, /developer/catalog |
| Awareness | REAL | /awareness/* |
| Memory | REAL | /memory/* |
| Search | REAL | /memory/search |
| Vault | REAL | /privacy/vault/* |
| Privacy | REAL | /privacy/* |
| System | REAL | /system/health/* |
| Settings | REAL | /auth/me |
| Auth | REAL | /auth/* |
| Marketplace | COMING SOON | — |
| Notes | COMING SOON | — |
| Scheduler | COMING SOON | — |
| Tasks | COMING SOON | — |

---

## How to Run

```bash
# Backend
make install && make migrate && make dev

# Frontend
cd frontend && npm install && npm run dev

# Both
make dev-full

# Tests
make test                    # 1,743 tests
cd frontend && npm run build # 24 pages, 0 errors
```

---

## Future Plans

- v1.0-v1.14: Complete remaining 4 Coming Soon pages (Marketplace, Notes, Scheduler, Tasks) when backends are ready
- v1.5-v1.8: Integration, cognition, intelligence, developer tools expansion
- v1.9-v1.14: Desktop shell, scheduler, marketplace, cross-encoder, polish
- Security: Vault password tokenization for production multi-server deployments
- Performance: Database indexing for critical query paths
- Monitoring: Structured logging, error tracking, usage analytics
- Documentation: Onboarding guide, API examples, architecture diagrams

---

## Quick Links

| Resource | Location |
|----------|----------|
| Architecture | docs/architecture/overview.md |
| API Reference | docs/reference/api.md |
| Database Schema | docs/reference/database.md |
| Design System | DESIGN.md |
| Product Definition | PRODUCT.md |
| ADRs | docs/decisions/ |
| Domain Docs | docs/domains/ |
| Governance | docs/guides/governance.md |
| Implementation Plans | docs/superpowers/plans/ |
| Design Specs | docs/superpowers/specs/ |
