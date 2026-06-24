# CORTEX API Reference

Base URL: `http://localhost:8000`

Interactive docs: `http://localhost:8000/docs`

---

## Authentication

| Route | Purpose | Auth |
|-------|---------|------|
| `/api/auth/register` | Create account | None |
| `/api/auth/login` | Login, set httpOnly cookies | None |
| `/api/auth/logout` | Revoke refresh token, lock vault | Required |
| `/api/auth/refresh` | Rotate access + refresh tokens | Cookie |
| `/api/auth/check-username` | Check username availability | None |

## Users (Admin)

| Route | Purpose | Auth |
|-------|---------|------|
| `/api/v1/users/` | List users | Admin |
| `/api/v1/users/{user_id}` | Get/update/delete user | Admin |
| `/api/v1/users/{user_id}/promote` | Promote to admin | Admin |
| `/api/v1/users/{user_id}/demote` | Demote from admin | Admin |

## Profile

| Route | Purpose | Auth |
|-------|---------|------|
| `/api/v1/me/profile` | GET/PUT profile | Required |
| `/api/v1/me/profile/photo` | Upload/delete avatar | Required |
| `/api/v1/me/github` | GET/POST/DELETE GitHub connection | Required |

## Vault

| Route | Purpose | Auth |
|-------|---------|------|
| `/api/v1/me/vault/lock` | Lock vault | Required |
| `/api/v1/me/vault/unlock` | Unlock vault (vault password) | Required |
| `/api/v1/me/vault/files` | List/create/upload files | Required |
| `/api/v1/me/vault/files/{path}` | Get/update/delete file | Required |
| `/api/v1/me/vault/search` | Search vault files | Required |

## Memory

| Route | Purpose | Auth |
|-------|---------|------|
| `/api/memory` | List/create knowledge entries | Required |
| `/api/memory/search` | Semantic search | Required |
| `/api/memory/scan-repo` | Trigger repository scanning | Required |
| `/api/memory/bulk-embed` | Bulk embedding generation | Required |

## Search

| Route | Purpose | Auth |
|-------|---------|------|
| `/api/v1/search` | Unified search across all data types | Required |

## Repositories

| Route | Purpose | Auth |
|-------|---------|------|
| `/api/v1/repos` | Repository CRUD + indexing triggers | Required |

## Agents

| Route | Purpose | Auth |
|-------|---------|------|
| `/api/v1/agents` | Agent CRUD | Required |
| `/api/v1/agents/{id}/runs` | Agent run management | Required |
| `/api/v1/agents/{id}/runs/{id}/steps` | Agent step tracking | Required |
| `/api/v1/agents/{id}/runs/{id}/feedback` | User feedback on runs | Required |

## Conversations

| Route | Purpose | Auth |
|-------|---------|------|
| `/api/v1/conversations` | Conversation CRUD + SSE streaming | Required |

## Models

| Route | Purpose | Auth |
|-------|---------|------|
| `/api/v1/models` | Model catalog listing | Required |
| `/api/v1/models/installed` | Installed models | Required |
| `/api/v1/models/{model_id}` | Model details | Required |
| `/api/v1/models/{model_id}/download` | Download model | Required |
| `/api/v1/models/{model_id}/compare` | Compare models | Required |
| `/api/v1/models/settings` | Per-user model settings | Required |

## Long-Term Memory

| Route | Purpose | Auth |
|-------|---------|------|
| `/api/v1/long-term-memory` | CRUD + decay management | Required |

## Knowledge

| Route | Purpose | Auth |
|-------|---------|------|
| `/api/v1/knowledge` | Knowledge system health + stats | Required |

## Indexing

| Route | Purpose | Auth |
|-------|---------|------|
| `/api/v1/indexing` | Indexing config CRUD + preview | Required |

## Sync

| Route | Purpose | Auth |
|-------|---------|------|
| `/api/v1/sync` | File watcher start/stop + validation | Required |

## Notifications

| Route | Purpose | Auth |
|-------|---------|------|
| `/api/v1/notifications` | List/read notifications | Required |

## System

| Route | Purpose | Auth |
|-------|---------|------|
| `/api/v1/health/live` | Liveness probe | None |
| `/api/v1/health/ready` | Readiness probe | None |
| `/api/v1/health/deep` | Deep health check | None |
| `/api/v1/system/status` | System status | Varies |
| `/api/v1/system/metrics` | System metrics | Varies |

## WebSocket

| Route | Purpose | Auth |
|-------|---------|------|
| `/ws` | Echo + demo + system metrics | None |
| `/ws/models` | Model download progress | None |
| `/ws/system` | System metrics stream | None |

---

## Auth Flow

1. **Register/Login** → backend sets httpOnly cookies (`cortex_access` + `cortex_refresh`)
2. **Requests** → frontend sends to `/api/*` → proxied to FastAPI by Next.js. Cookies forwarded.
3. **Refresh** → access token expires (30min) → frontend calls `POST /api/auth/refresh` → rotates tokens → retries original request. Transparent to user.
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
