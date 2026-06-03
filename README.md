# Cortex Workspace: Hybrid Repo AI Agent

[![Python Version](https://img.shields.io/badge/python-3.14-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-19.0-61dafb.svg)](https://reactjs.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

A prototype repository-aware AI orchestration system designed for codebase understanding, semantic retrieval, graph-based context expansion, repository-level reasoning, and multi-file code editing.

---

## 🎯 The Core Problem & Architectural Shift

As local coding models scale, handling repository-level tasks directly inside model context windows becomes extremely slow, resource-heavy, and prone to hallucinations or retrieval failures.

Instead of solving this solely by scaling local parameter counts, the **Cortex Workspace** implements a hybrid, index-assisted orchestration layer:

```
                  ┌───────────────────────────────┐
                  │       User Chat Query         │
                  └──────────────┬────────────────┘
                                 │
                      ┌──────────▼──────────┐
                      │  Intent Classifier  │ (CHAT, TOOL, RAG, SYSTEM)
                      └──────────┬──────────┘
                                 │
                       ┌─────────▼─────────┐
                       │  Execution Graph  │ (Weighted Step Dependency)
                       │      Planner      │
                       └─────────┬─────────┘
                                 │
            ┌────────────────────┼────────────────────┐
            │                    │                    │
 ┌──────────▼──────────┐ ┌───────▼───────┐ ┌──────────▼──────────┐
 │    Memory Recall    │ │  Repo Search  │ │   System Actions    │
 │ (SQLite Hist / KMS) │ │ (RAG/FAISS)   │ │  (Read/Write/Exec)  │
 └──────────┬──────────┘ └───────┬───────┘ └──────────┬──────────┘
            │                    │                    │
            └────────────────────┼────────────────────┘
                                 │
                      ┌──────────▼──────────┐
                      │ Context Compiler /  │
                      │  Keyword Reranker   │
                      └──────────┬──────────┘
                                 │
                     ┌───────────▼───────────┐
                     │      LLM Router       │ (Local Ollama / Cloud API)
                     └───────────┬───────────┘
                                 │
                  ┌──────────────▼────────────────┐
                  │ Structured Response / Patches │
                  └───────────────────────────────┘
```

---

## ✨ Features

- **Hybrid Local + Cloud Orchestration**: Dynamic routing between offline local inference (via Ollama) and external hosted endpoints (OpenAI/Claude API).
- **Semantic Codebase Retrieval**: Extracts logical components using structure-aware AST parsing, generates vector embeddings, and searches via FAISS.
- **RAG Reranking**: Combines FAISS cosine similarity with substring and exact-word boundary keyword boosts to surface high-relevance code chunks.
- **Weighted Graph Traversal**: Structures execution steps using a dependency graph (`ExecutionGraph`), logging performance to influence future step biases.
- **DFS-Based Context Expansion**: Walks folder trees recursively using Depth-First-Search (DFS) to build logical context windows while respecting pruning limits.
- **Persistent Repository Memory**: Retains architectural profiles, package dependencies, tech stack details, and user interaction histories in a local SQLite database.
- **Incremental Indexing**: Uses file modification timestamps to update the vector database in milliseconds, bypassing unchanged files.
- **Autonomy Gates**: Strict permissions engine enforcing Observation Mode (read-only), Approval Mode (mutation approvals), and Automated Mode (safe categories).
- **Traces & Replay**: Detailed logging of step performance, context variables, and LLM payloads to allow easy step-by-step debugging.

---

## 🛠️ Technology Stack

- **Backend**: Python 3.14, FastAPI, SQLAlchemy 2.0, Alembic, Uvicorn, Pytest
- **AI/RAG**: FAISS (Vector store), SentenceTransformers (BAAI/bge-small-en-v1.5 embeddings), Ollama, httpx
- **Frontend**: React 19, Vite, TypeScript, Tailwind CSS, Framer Motion, Axios, Zustand
- **Environment**: Docker, Docker Compose, uv (Fast python package sync)

---

## 📂 Directory Layout

```
├── backend/                  # Python FastAPI codebase
│   └── app/
│       ├── agent/            # System scanning & file searching agents
│       ├── ai/               # LLM wrappers, providers, exceptions, memory repositories
│       ├── api/              # HTTP routers & controllers (V1 API surface)
│       ├── core/             # Configuration settings, logging, security, middleware
│       ├── db/               # Database connection and session lifecycle
│       ├── executor/         # Execution graph definitions, planners, response builders
│       ├── intelligence/     # Filesystem discovery, exclusions, sync services
│       ├── models/           # SQLAlchemy database schemas
│       ├── rag/              # Vector database layers, chunkers, retrievers
│       └── services/         # Core business logic layer
├── frontend/                 # React UI app
│   ├── src/                  # React components, routing, states, and styles
│   └── vite.config.ts        # Vite configuration (Proxying to backend:8000)
├── scripts/                  # Maintenance and index rebuilding scripts
├── tests/                    # Pytest suite
├── Development guide/        # Detailed project context and developer references
├── Makefile                  # Helper tasks shortcut
└── start.sh                  # One-step startup pipeline script
```

---

## 🚀 Setup & Startup Pipeline

The quickest way to boot up the entire development ecosystem is to use the automated `start.sh` script:

### Quickstart (Linux / MacOS)

```bash
# 1. Clone the repository
git clone https://github.com/aditya8281/Cortex-Workspace.git
cd Cortex-Workspace

# 2. Run the startup pipeline
./start.sh
```

**What `start.sh` does automatically:**
1. Verifies/copies `.env.example` to `.env` and generates a secure random `SECRET_KEY`.
2. Checks python environments and synchronizes dependencies using `uv sync`.
3. Runs database migrations (`uv run alembic upgrade head`).
4. Rebuilds the semantic vector store and local repository memory (`.cortex`).
5. Verifies frontend node packages and runs `npm install` if missing.
6. Starts the backend FastAPI API (`localhost:8000`) and React dev server (`localhost:5173`) concurrently.

---

### Fallback Manual Setup

If you prefer to set up the individual phases manually, execute:

```bash
# 1. Environment Config
cp .env.example .env
# Edit .env with your LLM configuration (AI_MODE, AI_API_KEY, OLLAMA_URL)

# 2. Install dependencies & run migrations
uv sync
uv run alembic upgrade head

# 3. Build repository search index
uv run python scripts/rebuild_index.py

# 4. Start backend development server
make dev

# 5. In another terminal shell: Install & Run Frontend
cd frontend
npm install
npm run dev
```

### Docker Setup

To run the application using Docker:

```bash
# Start all containers in the background (Ollama, Backend API, Frontend Web server)
docker compose up -d

# Show real-time container log logs
docker compose logs -f
```

---

## 🛠️ Makefile Reference

The workspace includes a `Makefile` in the root directory for standard operations:

| Command | Action |
|:---|:---|
| `make install` | Performs python dependency synchronization |
| `make dev` | Launches FastAPI server under hot reload (`port 8000`) |
| `make migrate` | Applies database migrations using Alembic |
| `make migration m="msg"` | Generates a new database migration file |
| `make db-reset` | Wipes the dev SQLite DB and rebuilds schemas |
| `make format` | Formats code layout using black & ruff |
| `make lint` | Runs syntax checks and typing checks (mypy + ruff) |
| `make test` | Executes pytest coverage suite |
| `make docker-up` | Boots docker-compose containers |
| `make docker-down` | Terminates docker-compose container services |

---

## 🔗 Key API Endpoints

### Health Check
- `GET /` - Root status message
- `GET /api/v1/health/live` - Backend status check
- `GET /api/v1/health/ready` - Database/Ollama responsiveness check

### Authentication & Users
- `POST /api/v1/users` - Register a new account
- `POST /api/v1/login` - Authenticate and fetch JWT token
- `GET /api/v1/users/me` - Get current session details

### AI & Reasoning
- `POST /api/v1/ai/ask` - Execute immediate reasoning
- `POST /api/v1/ai/chat` - Post query into conversation thread
- `GET /api/v1/execution/{id}/replay` - View event execution trace metadata

### Workspace Intelligence
- `GET /api/v1/workspace/intelligence` - Retrieve repository profile summary, graphs, dependencies, and autonomy policy details
- `POST /api/v1/workspace/sync` - Manually trigger index and repository profile sync runs

---

## 🤝 Contribution & Governance Guidelines

We welcome contributions to Cortex Workspace! To maintain codebase quality, low latency, and robustness, please follow these standardized processes.

### 🐛 Issue Reporting Process

If you encounter bugs, performance regressions, or security issues, please open an issue using the template below:

1. **Check Existing Issues**: Search the issue tracker to ensure it hasn't been reported.
2. **File a New Issue**: Use a clear, descriptive title prefixing with `[Bug]`, `[Feature]`, or `[Performance]`.
3. **Provide Details**:
   - **Environment**: OS (Linux/macOS/Windows), Python version, Node.js version.
   - **Steps to Reproduce**: Detailed list of steps to trigger the bug.
   - **Expected Behavior**: What the system should have done.
   - **Actual Behavior**: Logs, screenshots, traceback, or performance metrics.
   - **Context**: Workspace size, number of repositories indexed, whether local or cloud LLM mode was active.

---

### 🔀 Pull Request (PR) Process

All modifications to the codebase must go through the Pull Request pipeline:

#### 1. Branching Strategy
- Standard features: `feat/short-description`
- Bug fixes: `fix/short-description`
- Documentation: `docs/short-description`
- Performance tuning: `perf/short-description`

#### 2. Pre-Flight Checklist (Local Verification)
Before submitting a PR, ensure the following commands run without failure:
```bash
make format    # Auto-formats Python files via black/ruff
make lint      # Verifies typing (mypy) and coding standards
make test      # Executes the test suite and checks assertions
```
All tests must pass. No PR with failing tests will be merged.

#### 3. PR Template Guidelines
When submitting the PR, complete the standard template:
- **Summary**: Concise description of the changes (the "why" and "what").
- **Related Issue**: Reference issues resolved (e.g. `Closes #12`).
- **Verification Details**: Specify how you tested the change. If you modified RAG crawling or observer polling, provide latency metrics before and after the change.
- **Screenshots / Recordings**: If there are UI changes, embed visual diffs demonstrating the state progression.

#### 4. Review & Merge
- At least one core maintainer must review and approve the PR.
- Merges are handled using squash-and-merge to keep the main branch history clean.

---

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

