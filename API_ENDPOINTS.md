# Backend API Endpoints — Authoritative Reference

Last updated: 2026-06-18

This reference reflects the **active, verified routes** in the current codebase:
- App entry: [main.py](backend/app/main.py)
- Versioned router: [api/router.py](backend/app/api/router.py)
- Auth router: [auth/router.py](backend/app/auth/router.py)
- Version prefix: `/api/v1`

Conventions:
- Authentication: HTTP Bearer JWT. Dependency: `get_current_user` ([api/deps.py](backend/app/api/deps.py))
- Admin endpoints: additionally require `require_admin` ([auth/dependencies.py](backend/app/auth/dependencies.py))
- All endpoints below have been tested and verified working.

---

## Top-Level Endpoints

### Root

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/` | None | Health check — returns `{message: "Cortex Workspace is running 🚀"}` |

### Auth

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/auth/register` | None | Create user, returns JWT tokens + user |
| POST | `/api/auth/login` | None | Login, returns JWT tokens + user |
| POST | `/api/auth/refresh` | None | Exchange refresh token for new access + refresh tokens |
| POST | `/api/auth/logout` | None | Invalidate refresh token |
| GET | `/api/auth/me` | Required | Get current user profile |
| PUT | `/api/auth/me` | Required | Update own account fields (vault_password with current_password) |
| POST | `/api/auth/check-username` | None | Real-time username availability check |

### Memory (Central Memory System)

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/memory` | Optional | List knowledge entries (user-scoped if authenticated) |
| POST | `/api/memory` | Optional | Store a memory entry (associated to user if authenticated) |

**GET /api/memory** — Query params: `limit` (1–100, default 24)
- Response: `{timestamp, count, categories, entries[]}`
- Entries have: `id, user_id, category, title, content, source_path, created_at, updated_at`

**POST /api/memory** — Body: `{title, content, category?, source_path?}`
- Response: `{status: "stored", entry: {...}}`

---

## Versioned API (/api/v1)

### Health

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/v1/health/live` | None | Liveness probe — returns `{status: "alive"}` |
| GET | `/api/v1/health/ready` | None | Readiness probe (DB check) — returns `{status, database}` |
| GET | `/api/v1/health/deep` | None | Deep health (DB check) — returns `{status, checks: {database}}` |

### Users (Admin Only)

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/v1/users` | Admin | List all users |
| GET | `/api/v1/users/{user_id}` | Admin | Get user by ID |
| PUT | `/api/v1/users/{user_id}` | Admin | Update user (username, full_name; role changes blocked) |
| DELETE | `/api/v1/users/{user_id}` | Admin | Delete user |
| POST | `/api/v1/users/{user_id}/promote` | Admin | Promote to admin |
| POST | `/api/v1/users/{user_id}/demote` | Admin | Demote (self-protection: cannot demote yourself) |

### Profile

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/v1/me/profile` | Required | Get current user profile |
| PUT | `/api/v1/me/profile` | Required | Update profile fields (full_name, nickname, bio, description) |
| POST | `/api/v1/me/profile/photo` | Required | Upload profile photo (JPEG/PNG/WebP, max 2 MB) — auto-resized to 256×256 avatar + 64×64 thumbnail |
| GET | `/api/v1/me/profile/photo` | Required | Serve current user's own profile photo |
| GET | `/api/v1/me/profile/photo/{user_id}` | None | Serve a user's profile photo (public — for `<img>` tags) |
| DELETE | `/api/v1/me/profile/photo` | Required | Remove current user's profile photo |

### GitHub

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/v1/me/github` | Required | Check GitHub connection status |
| POST | `/api/v1/me/github` | Required | Connect GitHub account (username + encrypted personal access token) |
| DELETE | `/api/v1/me/github` | Required | Disconnect GitHub account |

---

## Schemas

### UserRegisterPayload
```
username: str (1–128 chars, required)
password: str (min 8 chars, required)
confirm_password: str (min 8 chars, required)
full_name: str (min 1 char, required)
nickname: str (min 1 char, required)
vault_password: str (min 8 chars, required)
storage_root?: str
# Deprecated aliases (backward compat):
data_path?: str
personal_storage_path?: str
bio?: str
description?: str
handles?: dict
preferences?: dict
```

### UserResponse
```
id: int
username: str | None
full_name: str
role: str ("user" | "admin")
nickname: str
bio?: str | None
description?: str | None
profile_photo?: str | None
handles?: dict
storage_root?: str | None
github_username?: str | None
data_path?: str | None       # deprecated, mirrors storage_root
personal_storage_path?: str | None  # deprecated, mirrors storage_root
preferences?: dict
```

### TokenResponse
```
access_token: str
token_type: "bearer"
refresh_token?: str
user?: UserResponse
```

### MemoryCreatePayload
```
title: str (1–512 chars)
content: str (min 1 char)
category: str (default "note", 1–64 chars)
source_path?: str (max 1024 chars)
```

### UserUpdate (Admin)
```
username?: str
full_name?: str
role?: str   # blocked — returns 400 if different from current
```

### MeUpdate (Auth)
```
username?: str
full_name?: str
nickname?: str
bio?: str
description?: str
profile_photo?: str
handles?: dict
preferences?: dict
password?: str
current_password?: str  # required for vault_password update
vault_password?: str
```

### ProfileUpdate (/api/v1/me/profile)
```
full_name?: str
nickname?: str
bio?: str
description?: str
```

### UsernameCheckRequest (/api/auth/check-username)
```
username: str
```

### UsernameCheckResponse
```
available: bool
message: str
```

### GitHubConnectRequest (/api/v1/me/github POST)
```
username: str
token: str
```

### GitHubResponse (/api/v1/me/github)
```
connected: bool
github_username: str | None
```

---

## Notes

- First registered user is automatically assigned the `admin` role
- Refresh tokens are JWT-based with configurable expiry (default 7 days)
- Refresh tokens are server-revocable when Redis is available; JWT-only fallback when Redis is down
- Rate limiting on login attempts is Redis-backed with graceful fallback (fail-open)
- The memory system is user-scoped: authenticated users see only their entries plus global entries
- Profile photos are processed server-side: resized to 256×256 WebP avatar + 64×64 thumbnail
- GitHub tokens are encrypted with Fernet (derived from SECRET_KEY) before storage
- Username availability can be checked in real-time via /api/auth/check-username
- Registration uses a multi-step wizard: Account → Profile → GitHub → Vault
