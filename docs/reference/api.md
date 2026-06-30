Last updated: 2026-06-30

# CORTEX API Reference

Base URL: `http://localhost:8000`

Interactive docs: `http://localhost:8000/docs`

---

## Authentication

Registered at `/api/v1/auth/*` (no domain prefix).

| Route | Method | Purpose | Auth |
|-------|--------|---------|------|
| `/api/v1/auth/register` | POST | Create account | None |
| `/api/v1/auth/login` | POST | Login, set httpOnly cookies | None |
| `/api/v1/auth/logout` | POST | Revoke refresh token, lock vault | Required |
| `/api/v1/auth/refresh` | POST | Rotate access + refresh tokens | Cookie |
| `/api/v1/auth/check-username` | POST | Check username availability | None |
| `/api/v1/auth/me` | GET/PUT/DELETE | Get/update/delete profile | Required |
| `/api/v1/auth/restore` | POST | Restore vault from backup | Required |

## Memory Domain

All routes under `/api/v1/memory/*`.

### Knowledge

| Route | Method | Purpose |
|-------|--------|---------|
| `/api/v1/memory/knowledge/health` | GET | Knowledge system health |
| `/api/v1/memory/knowledge/stats` | GET | Knowledge statistics |
| `/api/v1/memory/knowledge/retrieval-metrics` | GET | Retrieval performance metrics |

### Search

| Route | Method | Purpose |
|-------|--------|---------|
| `/api/v1/memory/search` | GET/POST | Unified search |
| `/api/v1/memory/search/answer` | POST | AI-powered answer generation |

### Long-Term Memory

| Route | Method | Purpose |
|-------|--------|---------|
| `/api/v1/memory/long-term-memory` | GET/POST | List/create memories |
| `/api/v1/memory/long-term-memory/stats` | GET | Statistics |
| `/api/v1/memory/long-term-memory/{id}/reinforce` | POST | Reinforce memory |
| `/api/v1/memory/long-term-memory/{id}` | DELETE | Delete memory |

### Episodic Memory

| Route | Method | Purpose |
|-------|--------|---------|
| `/api/v1/memory/episodic` | GET/POST | List/create episodic memories |
| `/api/v1/memory/episodic/{id}` | GET/PUT/DELETE | Get/update/delete |

### Semantic Memory

| Route | Method | Purpose |
|-------|--------|---------|
| `/api/v1/memory/semantic` | GET/POST | List/create semantic memories |

### Working Memory

| Route | Method | Purpose |
|-------|--------|---------|
| `/api/v1/memory/working` | GET/POST | List/create working memory items |
| `/api/v1/memory/working/{id}` | GET/PUT/DELETE | Get/update/delete |

### Memory Graph

| Route | Method | Purpose |
|-------|--------|---------|
| `/api/v1/memory/graph` | GET | List graph nodes/edges |
| `/api/v1/memory/graph/{id}` | GET | Get node with connections |

### Cortex Search & Forgetting

| Route | Method | Purpose |
|-------|--------|---------|
| `/api/v1/memory/cortex-search` | POST | Multi-signal search |
| `/api/v1/memory/forget` | POST | Apply forgetting decay |

## Awareness Domain

All routes under `/api/v1/awareness/*`.

| Route | Method | Purpose |
|-------|--------|---------|
| `/api/v1/awareness/device/info` | GET | Hardware and OS info |
| `/api/v1/awareness/environment` | GET | Safe environment variables |
| `/api/v1/awareness/environment/paths` | GET | System PATH entries |
| `/api/v1/awareness/files/scan` | POST | Scan directory |
| `/api/v1/awareness/files/changes` | GET | Recent file changes |
| `/api/v1/awareness/files/summary` | GET | File statistics |
| `/api/v1/awareness/health` | GET | System health status |
| `/api/v1/awareness/health/status` | GET | Health summary |
| `/api/v1/awareness/indexing/config` | GET/PUT | Indexing configuration |
| `/api/v1/awareness/indexing/preview` | POST | Preview indexing scope |
| `/api/v1/awareness/project/scan` | GET | Detect project type/frameworks |
| `/api/v1/awareness/repos` | GET/POST | List/create repositories |
| `/api/v1/awareness/repos/{id}` | GET/PUT/DELETE | Repository CRUD |
| `/api/v1/awareness/repos/{id}/index` | POST | Trigger repository indexing |
| `/api/v1/awareness/repos/{id}/graph` | GET | Repository code graph |
| `/api/v1/awareness/repos/{id}/graph/node/{nodeId}` | GET | Graph node details |

## Privacy Domain

All routes under `/api/v1/privacy/*`.

### Audit

| Route | Method | Purpose |
|-------|--------|---------|
| `/api/v1/privacy/audit/logs` | GET | Audit log entries |
| `/api/v1/privacy/audit/stats` | GET | Audit statistics |

### Consent

| Route | Method | Purpose |
|-------|--------|---------|
| `/api/v1/privacy/consent` | GET | List consent items |
| `/api/v1/privacy/consent/grant` | POST | Grant consent |
| `/api/v1/privacy/consent/revoke` | POST | Revoke consent |

### Export

| Route | Method | Purpose |
|-------|--------|---------|
| `/api/v1/privacy/export/create` | POST | Create data export |
| `/api/v1/privacy/export/status/{id}` | GET | Export status |
| `/api/v1/privacy/export/list` | GET | List exports |

### Transparency

| Route | Method | Purpose |
|-------|--------|---------|
| `/api/v1/privacy/transparency/summary` | GET | Data usage summary |
| `/api/v1/privacy/transparency/templates` | GET | Transparency report templates |

### Access Control

| Route | Method | Purpose |
|-------|--------|---------|
| `/api/v1/privacy/access-control/roles` | GET | List roles/permissions |

### Vault

| Route | Method | Purpose |
|-------|--------|---------|
| `/api/v1/privacy/vault/status` | GET | Vault lock status |
| `/api/v1/privacy/vault/files` | GET | List vault files |
| `/api/v1/privacy/vault/files/upload` | POST | Upload file |
| `/api/v1/privacy/vault/files/preview/{path}` | GET | Preview file content |
| `/api/v1/privacy/vault/files/download/{path}` | GET | Download file |
| `/api/v1/privacy/vault/files/{path}` | DELETE | Delete file |
| `/api/v1/privacy/vault/files/{path}/rename` | PUT | Rename file |
| `/api/v1/privacy/vault/files/{path}/metadata` | PUT | Update metadata |
| `/api/v1/privacy/vault/files/move` | POST | Move file |
| `/api/v1/privacy/vault/folders` | POST | Create folder |
| `/api/v1/privacy/vault/search` | POST | Search vault files |
| `/api/v1/privacy/vault/lock` | POST | Lock vault |
| `/api/v1/privacy/vault/unlock` | POST | Unlock vault |
| `/api/v1/privacy/vault/change-password` | POST | Change vault password |

### Model Settings (via privacy router)

| Route | Method | Purpose |
|-------|--------|---------|
| `/api/v1/privacy/models/usage/stats` | GET | Model usage statistics |
| `/api/v1/privacy/models/sync` | POST | Sync model catalog |
| `/api/v1/privacy/models/storage` | GET | Storage usage breakdown |
| `/api/v1/privacy/models/updates` | GET | Available model updates |
| `/api/v1/privacy/models/settings` | GET/PUT | Per-user model settings |
| `/api/v1/privacy/models/catalogue/refresh` | POST | Refresh model catalog |

## Cognition Domain

All routes under `/api/v1/` (cognition router has no prefix).

| Route | Method | Purpose |
|-------|--------|---------|
| `/api/v1/agents` | GET/POST | List/create agents |
| `/api/v1/agents/{id}` | GET/PUT/DELETE | Agent CRUD |
| `/api/v1/agents/runs` | GET/POST | List/create agent runs |
| `/api/v1/agents/runs/{runId}` | GET | Get run details |
| `/api/v1/agents/runs/{runId}/status` | GET | Run status |
| `/api/v1/agents/runs/{runId}/stream` | POST | Stream run execution |
| `/api/v1/agents/runs/{runId}/steps` | GET | Run steps |
| `/api/v1/agents/runs/{runId}/feedback` | GET/POST | Feedback on runs |
| `/api/v1/agents/metrics` | GET | Agent metrics |

## Interaction Domain

All routes under `/api/v1/` (interaction router has no prefix).

### Conversations

| Route | Method | Purpose |
|-------|--------|---------|
| `/api/v1/conversations` | GET/POST | List/create conversations |
| `/api/v1/conversations/{id}` | GET/DELETE | Get/delete conversation |
| `/api/v1/conversations/{id}/title` | PATCH | Update title |
| `/api/v1/conversations/{id}/messages` | POST | Send message (SSE) |

### Notifications

| Route | Method | Purpose |
|-------|--------|---------|
| `/api/v1/notifications` | GET | List notifications |
| `/api/v1/notifications/{id}/read` | POST | Mark read |
| `/api/v1/notifications/read-all` | POST | Mark all read |
| `/api/v1/notifications/{id}` | DELETE | Dismiss notification |

### Profile

| Route | Method | Purpose |
|-------|--------|---------|
| `/api/v1/me/profile` | GET/PUT | Get/update profile |
| `/api/v1/me/profile/photo` | POST/GET/DELETE | Upload/get/delete avatar |

## System Domain

All routes under `/api/v1/` (system router has no prefix).

| Route | Method | Purpose |
|-------|--------|---------|
| `/api/v1/system/metrics` | GET | CPU, RAM, disk, GPU metrics |
| `/api/v1/system/logs` | GET | Recent log entries |
| `/api/v1/health/live` | GET | Liveness probe |
| `/api/v1/health/ready` | GET | Readiness probe |
| `/api/v1/models/health` | GET | LLM provider health |
| `/api/v1/models/metrics` | GET | LLM request/token metrics |

## Developer Domain

All routes under `/api/v1/` (developer router has no prefix).

| Route | Method | Purpose |
|-------|--------|---------|
| `/api/v1/models` | GET | Model catalog listing |
| `/api/v1/models/refresh` | POST | Refresh model catalog |
| `/api/v1/models/recommended` | GET | Recommended models for hardware |
| `/api/v1/models/hardware` | GET | Hardware info for recommendations |
| `/api/v1/models/search` | GET | Search models |
| `/api/v1/models/autocomplete` | GET | Model name autocomplete |
| `/api/v1/models/compare` | POST | Compare models side-by-side |
| `/api/v1/models/{modelId}` | GET | Model details |
| `/api/v1/models/{modelId}/inference-config` | GET | Inference configuration for model |
| `/api/v1/me/github` | GET | GitHub connection info |
| `/api/v1/me/github` | POST | Connect GitHub account |
| `/api/v1/me/github` | DELETE | Disconnect GitHub account |

## Integration Domain

All routes under `/api/v1/` (integration router has no prefix).

### Downloads

| Route | Method | Purpose |
|-------|--------|---------|
| `/api/v1/models/installed` | GET | Installed models |
| `/api/v1/models/installed/sync` | POST | Sync installed models |
| `/api/v1/models/downloads/queue` | GET | Download queue |
| `/api/v1/models/downloads/history` | GET | Download history |
| `/api/v1/models/{name}/download` | POST | Start download |
| `/api/v1/models/{name}/progress` | GET | Download progress |
| `/api/v1/models/{name}/cancel` | POST | Cancel download |
| `/api/v1/models/{name}/local` | DELETE | Remove model from local storage |
| `/api/v1/models/downloads/{job_id}/pause` | POST | Pause download |
| `/api/v1/models/downloads/{job_id}/resume` | POST | Resume download |
| `/api/v1/models/downloads/reorder` | POST | Reorder download queue |
| `/api/v1/models/downloads/bulk-cancel` | POST | Cancel multiple downloads |
| `/api/v1/models/downloads/clear-completed` | POST | Clear completed downloads |

### Sync

| Route | Method | Purpose |
|-------|--------|---------|
| `/api/v1/sync/defaults` | GET | Sync defaults |
| `/api/v1/sync/start` | POST | Start sync job |
| `/api/v1/sync/validate-path` | POST | Validate sync path |
| `/api/v1/sync/stop` | POST | Stop sync job |
| `/api/v1/sync/status` | GET | Sync status |
| `/api/v1/sync/jobs` | GET | List sync jobs |
| `/api/v1/sync/jobs/{job_id}` | GET | Get sync job details |

## WebSocket

| Route | Purpose |
|-------|---------|
| `/ws` | Echo + demo + system metrics |
| `/ws/models` | Model download progress (1s updates) |
| `/ws/system` | System metrics (500ms) + logs (3s) + processes (5s) |
| `/ws/chat` | Chat streaming |

---

## Auth Flow

1. **Register/Login** → backend sets httpOnly cookies (`cortex_access` + `cortex_refresh`)
2. **Requests** → frontend sends to `/api/*` → proxied to FastAPI by Next.js. Cookies forwarded.
3. **Refresh** → access token expires (30min) → frontend calls `POST /api/v1/auth/refresh` → rotates tokens → retries original request. Transparent to user.
4. **Logout** → revoke refresh token, lock vault, clear cookies

**Token lifetimes:**
- Access token: 30 minutes (configurable via `ACCESS_TOKEN_EXPIRE_MINUTES`)
- Refresh token: 7 days

**Two password model:**
- Login password → account auth (Argon2)
- Vault password → file encryption (separate hash; cached in memory after unlock)
- First registered user is auto-promoted to `admin`.

---

## Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `SECRET_KEY` | (empty) | JWT + Fernet derivation |
| `DATABASE_URL` | `postgresql://cortex:cortex@localhost:5435/cortex` | App database |
| `REDIS_URL` | `redis://localhost:6379/0` | Token store / rate limit |
| `CORTEX_ROOT` | `ProjectRoot/CortexMemory` | System storage root |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | JWT access token lifetime |
| `LLM_PROVIDER` | `auto` | LLM provider: `auto`, `llama.cpp`, `ollama`, `none` |
| `LLM_MODEL_PATH` | — | Path to local GGUF model file |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama server URL |
| `LLM_CONTEXT_SIZE` | `4096` | LLM context window size |
| `LLM_GPU_LAYERS` | `0` | GPU layers for llama.cpp |
