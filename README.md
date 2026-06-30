Last updated: 2026-06-30

# CORTEX

## Vision

**A local-first machine intelligence layer that gives your computer its own persistent understanding, memory, reasoning, and agency.**

CORTEX is a long-term effort to build a real AI companion — like Jarvis, or the AI in Rick's garage. Not a chatbot. Not a repository assistant. Not a RAG platform. Not a model wrapper.

CORTEX is an entire local AI brain ecosystem that lives on your machine and grows with you. It knows your files, your code, your conversations, your projects, your habits. It understands context — not just the current message, but everything that came before. It remembers, reasons, learns, and acts.

The goal is to transform a computer from a tool you operate into a companion that understands you.

### What CORTEX Is Not

- **Not a chatbot** — it doesn't just respond to prompts. It maintains persistent understanding across sessions.
- **Not a repo assistant** — it doesn't just index code. It understands your entire digital world as a connected system.
- **Not a RAG platform** — retrieval is a feature, not the product. CORTEX uses RAG to serve a deeper goal: genuine machine intelligence.
- **Not a model wrapper** — it isn't a thin UI over an API. It's an entire cognition layer with memory, reasoning, and agency.

### What CORTEX Is

- **A living knowledge graph** — files, conversations, memories, and relationships connected into a coherent model of your digital life.
- **A persistent memory** — memories that accumulate, decay, and strengthen based on use. CORTEX remembers what matters.
- **An agentic intelligence** — autonomous agents that can plan, reason, search, write, and execute with your approval.
- **A system-aware brain** — understands your filesystem, repositories, services, models, and workflows as interconnected systems.
- **A model-free companion** — runs any model (Ollama, llama.cpp, OpenAI, Anthropic) or degrades gracefully. You choose the brain, CORTEX provides the mind.

---

## Current Status

| Area | State |
|------|-------|
| Backend API | 200+ REST + 4 WebSocket endpoints across 10 domain routers |
| Auth + Vault | Production-quality — JWT + Argon2, Fernet encryption, secure password cache, CSRF double-submit |
| Agent System | Agent loop, run manager, stall detection, verifier, compactor, policy engine |
| Memory System | Episodic, semantic, working memory with graph relationships and search |
| Intelligence | Model catalog, providers, variants, benchmarks, recommendation engine |
| LLM Integration | llama.cpp + Ollama with provider abstraction |
| Awareness | Device detection, file tracking, project detection, repo analysis, health monitoring, context & attention |
| Privacy | Consent management, audit logging, access control, RBAC/ABAC |
| Frontend | 20 real pages + 10 Coming Soon, 72 feature components, 12 shared UI components |
| Tests | 2,077 passing (backend pytest) |
| Linting | ruff + mypy — clean |
| Database | 13 active Alembic migrations |

### Codebase Metrics

| Metric | Value |
|--------|-------|
| Backend Python files | 425 |
| Backend LoC | 46,733 |
| Frontend TSX/TS files | 149 |
| Frontend LoC | 17,348 |
| Test files | 194 |
| Test LoC | 21,784 |
| Documentation files | 32 |
| Git commits | 738 |

---

## Quick Start

**Prerequisites:** Python 3.12+, [uv](https://github.com/astral-sh/uv), Node.js 24+, Docker (optional).

```bash
git clone <repo-url> Cortex-Workspace
cd Cortex-Workspace

# Infrastructure (PostgreSQL + Redis)
docker compose up -d

# Environment
cp .env.example .env
# Edit .env — generate SECRET_KEY: openssl rand -hex 32

# Dependencies + migrations
make install
make migrate
```

**Port note:** Docker exposes PostgreSQL on **5432**. `.env.example` defaults to **5435** for use with `./start.sh` (embedded PostgreSQL).

### Running

| Option | Command | What it does |
|--------|---------|--------------|
| **A (recommended)** | `make dev-full` | Backend :8000 + Frontend :3000 |
| **B** | `./start.sh` | Embedded PG + migrations + both servers |
| **C** | `make dev` / `make dev-frontend` | Separate terminals |

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| API docs | http://localhost:8000/docs |

---

## Architecture

CORTEX combines a FastAPI backend, Next.js frontend, Rust-based code intelligence, and a Python CLI into a single workspace. The architecture is designed around encrypted vaults, knowledge graphs, vector search, LLM integration, and autonomous agents.

```
┌────────────────────────────────────────────────┐
│  Frontend (Next.js 15)  http://localhost:3000  │
└──────────────────────┬─────────────────────────┘
                       │
┌──────────────────────▼─────────────────────────┐
│  Backend (FastAPI)    http://localhost:8000    │
└──────┬───────────────────────────┬─────────────┘
       │                           │
  ┌────▼────┐  ┌──────────┐  ┌────▼─────┐
  │PostgreSQL│  │  Qdrant  │  │  Redis   │
  └──────────┘  └──────────┘  └──────────┘
```

**For detailed architecture, see [docs/architecture/overview.md](docs/architecture/overview.md).**

---

## Frontend Pages

| Page | Status | Description |
|------|--------|-------------|
| `/` | Real | System overview — CPU, RAM, GPU, disk metrics |
| `/chat` | Real | Conversations, streaming, model selection, code blocks |
| `/agents` | Real | Agent management, chat, run history |
| `/models` | Real | Browse, download, compare, installed models |
| `/awareness` | Real | Device, environment, health, project cards |
| `/awareness/repos` | Real | Repository management, add/list/remove |
| `/awareness/indexing` | Real | Indexing configuration, graph view |
| `/awareness/context` | Real | Context and attention system |
| `/memory` | Real | Knowledge graph, search, memory management |
| `/search` | Real | Unified search across all domains |
| `/vault` | Real | Encrypted document locker |
| `/privacy` | Real | Overview dashboard with consent, audit, storage |
| `/privacy/audit` | Real | Audit log viewer with filters, pagination |
| `/privacy/consent` | Real | Consent management with toggles |
| `/system` | Real | System health monitoring |
| `/settings` | Real | User settings, profile, preferences |
| `/cognition` | Real | Cognition dashboard |
| `/execution` | Real | Execution monitoring |
| `/auth` | Real | Login |
| `/auth/register` | Real | Registration |
| `/compare` | Coming Soon | Model comparison |
| `/marketplace` | Coming Soon | Model marketplace |
| `/notes` | Coming Soon | Notes system |
| `/scheduler` | Coming Soon | Task scheduling |
| `/tasks` | Coming Soon | Task management |
| `/apps` | Coming Soon | Application integrations |
| `/knowledge` | Coming Soon | Knowledge graph explorer |
| `/intelligence` | Coming Soon | Intelligence dashboard |
| `/developer` | Coming Soon | Developer tools & API |
| `/docs` | Coming Soon | Documentation viewer |

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 15, React 19, TypeScript, Tailwind CSS |
| Backend | FastAPI, Python 3.12+ |
| Database | PostgreSQL 16 (SQLite in tests only) |
| ORM | SQLAlchemy 2.0 + Alembic |
| Cache | Redis 7 (optional, graceful fallback) |
| Auth | JWT + Argon2 (cookie-based) |
| Encryption | Fernet + PBKDF2 (vault) |
| Vector DB | Qdrant (embedded) |
| Embeddings | ONNX Runtime (BGE-M3) |
| LLM | llama.cpp, Ollama (provider abstraction) |
| Task Queue | arq (Redis-based) |

---

## Development

```bash
make install       # uv sync + npm install
make migrate       # alembic upgrade head
make test          # 2,077 tests (backend pytest)
make lint          # ruff + mypy
make format        # ruff format
make check         # lint + test
make design        # Rebuild frontend via /project:design
```

### Make Targets

| Target | Purpose |
|--------|---------|
| `make dev` | Backend hot reload |
| `make dev-frontend` | Frontend dev server |
| `make dev-full` | Both |
| `make design` | Rebuild frontend via `/project:design` |
| `make db-shell` | psql |
| `make db-reset` | Drop schema + remigrate |
| `make db-backup` | pg_dump |
| `make build-frontend` | Production frontend build |
| `make docker-build` | Build production image |
| `make worker` | Start arq worker |

---

## Documentation

| Document | Audience | Contents |
|----------|----------|----------|
| [README.md](./README.md) | Everyone | Overview, quick start, features |
| [CLAUDE.md](./CLAUDE.md) | AI Agents | Development guidance, commands, patterns |
| [AGENTS.md](./AGENTS.md) | AI Agents | Behavior rules, security, API patterns |
| [DESIGN.md](./DESIGN.md) | Designers | Design system, tokens, components |
| [PRODUCT.md](./PRODUCT.md) | Designers | Product definition, brand, principles |
| [docs/architecture/overview.md](docs/architecture/overview.md) | Engineers | System architecture, tech decisions |
| [docs/reference/api.md](docs/reference/api.md) | Engineers | API reference, endpoints, auth |
| [docs/reference/database.md](docs/reference/database.md) | Engineers | DB schema, migrations, conventions |
| [docs/guides/governance.md](docs/guides/governance.md) | Everyone | Rules of engagement, security patterns |
| [docs/domains/memory.md](docs/domains/memory.md) | Engineers | Memory domain documentation |
| [docs/decisions/](docs/decisions/) | Engineers | Architecture Decision Records (ADRs) |

---

## License

MIT
