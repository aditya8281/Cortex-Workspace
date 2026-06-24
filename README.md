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
| Tests | 486+ passing (backend pytest + frontend vitest) |
| Frontend build | Passes |
| Linting | ruff + ESLint + mypy — all clean |
| Auth + vault backend | Production-quality foundation |
| Vault UI | Full file browser with table/list/grid views |
| Neural Dark redesign | Complete (warm dark, Neural Network background) |
| CLI | Scaffolded (command stubs) |
| LLM Integration | llama.cpp + Ollama with provider abstraction |
| Model Catalog | Full catalogue with providers, variants, benchmarks |
| Agentic Ecosystem | Governance, workflows, hooks, automation — complete |

**Phases 1–3 complete. Phases 4–6 partially complete. See [Roadmap](docs/ROADMAP.md) for details.**

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

**For detailed architecture, see [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).**

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 15, React 19, TypeScript, Tailwind CSS |
| Frontend UI | framer-motion, Radix UI, cmdk, sonner, Three.js |
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
| CLI | TypeScript, Commander.js |

---

## Development

```bash
make install       # uv sync + npm install
make migrate       # alembic upgrade head
make test          # 486+ tests (backend pytest + frontend vitest)
make lint          # ruff + mypy
make format        # ruff format
make check         # lint + test
```

### Make Targets

| Target | Purpose |
|--------|---------|
| `make dev` | Backend hot reload |
| `make dev-frontend` | Frontend dev server |
| `make dev-full` | Both |
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
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Engineers | System architecture, tech decisions |
| [docs/ROADMAP.md](docs/ROADMAP.md) | Everyone | Development roadmap, phases, status |
| [docs/API.md](docs/API.md) | Engineers | API reference, endpoints, auth |
| [docs/DATABASE.md](docs/DATABASE.md) | Engineers | DB schema, migrations, conventions |
| [docs/SECURITY.md](docs/SECURITY.md) | Engineers | Security patterns, auth flow |
| [docs/DEVELOPER_GUIDE.md](docs/DEVELOPER_GUIDE.md) | Everyone | Ecosystem, workflows, hooks |
| [docs/GOVERNANCE.md](docs/GOVERNANCE.md) | Everyone | Rules of engagement |
| [docs/agents/](docs/agents/) | AI Agents | Domain context, triage, issue tracking |

---

## License

MIT
