# Cortex

Cortex is a portable, local-first AI workspace for chat, repository understanding, memory persistence, model routing, and safe system interaction.

It is designed to run the same way on Windows, Linux, and macOS, either:

- with Docker as the primary deployment path
- with a manual Python + Node setup as a secondary path

## What Cortex Does

- Chat with local or cloud models
- Search and reason over repository files
- Persist conversation and workspace memory
- Route requests across model providers
- Expose a safety layer for file and system actions
- Keep the memory vault portable across machines

## Architecture

### Runtime Abstraction Layer

Cortex avoids direct OS-specific assumptions by routing filesystem and system operations through the runtime and path layers in `backend/app/core/runtime.py`, `backend/app/core/paths.py`, and `backend/app/core/system_paths.py`.

That layer is responsible for:

- normalizing paths
- blocking protected system directories
- keeping file access OS-agnostic
- resolving workspace-relative storage locations

### Memory System

Cortex stores durable state in a memory vault managed by `backend/app/services/memory_manager.py`.

The vault is split into categories such as:

- `embeddings`
- `vector_db`
- `metadata_db`
- `graph`
- `sync_state`
- `activity_logs`
- `cache`
- `user_profiles`
- `repos`
- `temp`

In Docker, the vault is mounted at `/cortex_memory` and persisted in a named Docker volume, so memory survives:

- container restarts
- image updates
- host changes
- machine migration when the volume is copied or exported

### Model Routing System

Cortex separates model selection from request execution through the routing stack in `backend/app/ai/llm_router.py`, `backend/app/ai/providers/registry.py`, and the model registry/database layer.

Routing is driven by:

- `DEFAULT_MODEL`
- `MODEL_API_KEYS`
- `CLOUD_PROVIDER_CONFIGS`
- user-selected model settings
- local vs cloud provider metadata

This lets Cortex switch between local Ollama models and cloud providers without hardcoding provider credentials into the codebase.

## Repository Layout

- `backend/` FastAPI backend, memory, routing, sync, and tool orchestration
- `frontend/` Vite + React UI
- `scripts/` helper scripts for Docker and vault initialization
- `infra/nginx/` production frontend reverse-proxy config
- `docker-compose.yml` production stack
- `docker-compose.dev.yml` development stack

## Setup

## Docker Setup, Primary Path

### 1. Configure Environment

Create your runtime file once:

```bash
cp .env.docker .env
```

If you want to customize the stack, edit:

- `MEMORY_PATH`
- `DEFAULT_MODEL`
- `MODEL_API_KEYS`
- `CLOUD_PROVIDER_CONFIGS`
- `OLLAMA_URL`
- `REDIS_URL`

### 2. Start Cortex

One command:

```bash
./scripts/docker-run.sh
```

Or equivalently:

```bash
docker compose up -d --build
```

### 3. Open the App

- Frontend: `http://localhost`
- Backend API: `http://localhost:8000`
- Ollama: `http://localhost:11434`

### Docker Lifecycle Commands

- Build: `./scripts/docker-build.sh`
- Run: `./scripts/docker-run.sh`
- Restart: `./scripts/docker-restart.sh`
- Clean reset: `./scripts/docker-clean-reset.sh`

Clean reset removes the named volumes, including the persistent Cortex memory volume.

### Production Docker Topology

- `backend` container runs the FastAPI app and database migrations
- `frontend` container serves the built React app through Nginx
- `ollama` container provides local model inference
- `redis` container provides cache support
- `cortex_memory` volume stores the memory vault

## Manual Setup, Secondary Path

Manual installation is for local development or environments where you want to control each layer yourself.

### Prerequisites

- Python 3.14+
- Node.js 22+
- `uv`
- npm
- Optional: Ollama for local models
- Optional: Redis for cache support

### Backend

#### 1. Create environment file

```bash
cp .env.example .env
```

Set these values at minimum:

- `MEMORY_PATH`
- `DEFAULT_MODEL`
- `MODEL_API_KEYS`
- `CLOUD_PROVIDER_CONFIGS`

#### 2. Install dependencies

```bash
uv sync
```

#### 3. Initialize the Cortex brain vault

```bash
uv run python scripts/init_memory.py
```

This creates the persistent vault directory structure at the configured memory path.

#### 4. Run database migrations

```bash
uv run alembic upgrade head
```

#### 5. Start the backend

```bash
uv run uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
```

### Frontend

#### 1. Install dependencies

```bash
cd frontend
npm install
```

#### 2. Development mode

```bash
npm run dev
```

The Vite dev server proxies `/api` requests to the backend.

#### 3. Production build

```bash
npm run build
```

To verify the build locally, run:

```bash
npm run preview -- --host 0.0.0.0
```

In a real production deployment, serve `frontend/dist` with Nginx or the provided Docker frontend image.

## Environment Variables

### Core

- `APP_NAME`
- `DEBUG`
- `API_V1_PREFIX`
- `SECRET_KEY`
- `DATABASE_URL`
- `REDIS_URL`
- `ENV`

### AI and Routing

- `DEFAULT_MODEL`
- `MODEL_API_KEYS`
- `CLOUD_PROVIDER_CONFIGS`
- `AI_MODE`
- `AI_MODEL`
- `AI_API_KEY`
- `AI_API_URL`
- `LOCAL_MODEL`
- `OLLAMA_URL`

### Memory

- `MEMORY_PATH`

### Frontend

- `VITE_API_URL`

### Example JSON values

```bash
MODEL_API_KEYS={"openai":"sk-...","anthropic":"..."}
CLOUD_PROVIDER_CONFIGS={"openai":{"api_url":"https://api.openai.com/v1"}}
```

## Usage Guide

### Chat

- Use the chat interface in the frontend.
- Cortex routes the request through the intent and model routing stack.
- Conversation memory is saved automatically when the authenticated chat path is used.

### File System

- Use the repository and workspace views to inspect files and context.
- Cortex resolves file operations through its runtime abstraction layer instead of assuming host-specific paths.
- Safe path checks prevent the memory system from escaping the vault or touching protected directories.

### Switching Models

- Set the default model with `DEFAULT_MODEL`.
- Provide provider keys through `MODEL_API_KEYS`.
- Provide provider endpoints through `CLOUD_PROVIDER_CONFIGS`.
- Select a different model in the UI when the route supports it.

### Memory Behavior

- The brain vault is the durable storage layer for Cortex.
- `MEMORY_PATH` controls where the vault lives.
- In Docker, that path is `/cortex_memory`.
- In manual installs, pick a stable host path and keep it consistent.

## Safety Model

- No root is required for normal operation
- Docker containers run as a non-root user
- Path access is restricted by the runtime abstraction and memory manager
- Protected system directories are blocked
- Cortex is designed to be OS-agnostic rather than shelling out to OS-specific paths
- Dangerous file or vault operations are isolated behind explicit service layers

## Portability

Cortex is intended to behave consistently across Windows, Linux, and macOS by:

- avoiding hardcoded host-specific paths
- resolving storage through `MEMORY_PATH`
- keeping the vault in a portable directory or Docker volume
- using frontend API calls that work through the same relative `/api/v1` path in every environment

## Troubleshooting

### Docker does not start

- Confirm Docker Desktop or the Docker Engine is running
- Check that ports `80`, `8000`, `11434`, and `6379` are free
- Run `docker compose logs -f` to inspect container output

### Backend cannot reach the model provider

- Verify `DEFAULT_MODEL`, `AI_MODE`, and `OLLAMA_URL`
- If using cloud providers, confirm `MODEL_API_KEYS` and `CLOUD_PROVIDER_CONFIGS`
- Make sure the provider is enabled in the database-backed model registry

### Memory does not persist

- Confirm the backend container mounts the `cortex_memory` volume
- Confirm `MEMORY_PATH=/cortex_memory` in Docker
- Use `docker compose down -v` only when you want to intentionally erase the vault

### Frontend cannot reach the API

- In Docker, the frontend is served through Nginx and proxies `/api` to the backend
- In manual mode, make sure the backend is running on `http://localhost:8000`
- In Vite dev mode, verify the proxy target is pointing to the backend service

### Manual backend fails on startup

- Re-run `uv sync`
- Re-run `uv run python scripts/init_memory.py`
- Re-run `uv run alembic upgrade head`

## Suggested Workflow

1. Copy `.env.docker` to `.env`
2. Run `./scripts/docker-run.sh`
3. Open `http://localhost`
4. Use `./scripts/docker-clean-reset.sh` only when you want a full reset

## License

MIT
