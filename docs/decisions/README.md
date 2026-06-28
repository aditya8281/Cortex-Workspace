Last updated: 2026-06-28

# Architecture Decision Records (ADRs)

Cortex tracks architectural decisions in this directory. Each ADR follows the standard format: Context, Decision, Consequences, Alternatives.

## Status Legend

- **Accepted** — Decision is in effect
- **Proposed** — Decision is planned for a future version
- **Deprecated** — Decision has been superseded

## ADR Index

### Confirmed (Accepted)

| # | Decision | Status | Supersedes |
|---|----------|--------|------------|
| 001 | [Agentic Development Ecosystem](001-agentic-ecosystem.md) | Accepted | — |
| 002 | [PostgreSQL as Primary Database](002-postgresql-primary-database.md) | Accepted | — |
| 003 | [Two-Password Auth Model](003-auth-model.md) | Accepted | — |
| 004 | [Fernet Encryption for Vault](004-fernet-vault-encryption.md) | Accepted | — |
| 005 | [Hybrid Retrieval Architecture](005-hybrid-retrieval.md) | Accepted | — |
| 006 | [Next.js 15 + React 19 Frontend](006-nextjs-react-frontend.md) | Accepted | — |
| 007 | [Three-Tier Embedding Fallback](007-embedding-fallback.md) | Revisiting | — |
| 008 | [Arq for Background Tasks](008-arq-background-tasks.md) | Revisiting | — |
| 009 | [Docker Compose Infrastructure](009-docker-compose-infrastructure.md) | Accepted | — |
| 010 | [TDD with SQLite Tests](010-tdd-sqlite-tests.md) | Accepted | — |
| 011 | [Multi-Agent Governance Ecosystem](011-multi-agent-governance.md) | Accepted | — |
| 012 | ["Warm Neural Dark" Design System](012-warm-neural-dark.md) | Accepted | — |
| 013 | [Code-Aware Knowledge Graph](013-code-aware-knowledge-graph.md) | Accepted | — |

### Revisiting (Proposed Replacements)

| # | Decision | Status | Replaces | Phase |
|---|----------|--------|----------|-------|
| 015 | [Pluggable Embedding Provider](015-pluggable-embedding-provider.md) | Proposed | 007 | V2 |
| 022 | [Event-Driven Runner](022-event-driven-runner.md) | Proposed | 008 | V3 |

### New (Proposed)

| # | Decision | Status | Phase |
|---|----------|--------|-------|
| 017 | [MCP Integration](017-mcp-integration.md) | Proposed | V3 |
| 018 | [Plugin Architecture](018-plugin-architecture.md) | Proposed | V2-V3 |
| 019 | [Desktop Mode Strategy](019-desktop-mode-strategy.md) | Proposed | V3-V5 |
| 020 | [Token Estimation](020-token-estimation.md) | Proposed | V2 |
| 021 | [Daily Productivity Tools](021-daily-productivity-tools.md) | Proposed | V4-V5 |

## Creating New ADRs

1. Copy an existing ADR as template
2. Number sequentially (next: 022)
3. Set Status to "Proposed"
4. Fill in: Context, Decision, Consequences, Alternatives, Related
5. Update this index

## Decision Debt

These decisions are aging and should be revisited:

| Decision | Age | Impact | Priority |
|----------|-----|--------|----------|
| Agent system (Planner→Executor) | Since initial commit | Core functionality degraded | Critical |
| Tool registry (no schemas) | Since initial commit | LLM function-calling degraded | Critical |
| Embedding (hardcoded tiers) | Since initial commit | Can't extend providers | High |
| Vector store (Qdrant-only) | Since initial commit | Can't do desktop mode | High |
| Background tasks (asyncio) | Since initial commit | Can't do daemon mode | High |
| Context (no compaction) | Since initial commit | Long conversations lose context | High |
| Middleware location | Since initial commit | Documentation drift | Low |
| Token estimation | Since initial commit | Inaccurate token counting | Medium |
