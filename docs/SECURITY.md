# Cortex Security Patterns

---

## Authentication

### Two-Password Model

| Password | Purpose | Storage | Lifetime |
|----------|---------|---------|----------|
| Login password | Account authentication | Argon2 hash in `users.hashed_password` | Permanent |
| Vault password | Encrypt/decrypt vault files | Argon2 hash + Fernet key derivation in-memory | Cached after unlock, wiped on lock |

**Rationale**: A compromised login password does not expose encrypted vault files. The vault password never leaves the server in plaintext after unlock (cached as `SecurePasswordCache` with bytearray wipe).

### Cookie-Based Auth

- **Access tokens**: httpOnly cookies (`cortex_access`), 30-minute expiry, auto-refreshed
- **Refresh tokens**: httpOnly cookies (`cortex_refresh`), 7-day expiry, rotation on each use
- **CSRF**: Double-submit cookie pattern (`cortex_csrf` cookie + `X-CSRF-Token` header)
- **No localStorage**: All tokens in httpOnly cookies (XSS-resistant)

### Auto-Refresh Flow

1. API request returns 401 (token expired)
2. Frontend calls `POST /api/auth/refresh` with refresh token cookie
3. Backend rotates refresh token (issues new access + refresh, revokes old)
4. Original request retried with new access token
5. Transparent to user — no interruption

---

## Ownership Checks

**Rule**: Every user-scoped endpoint MUST verify `resource.user_id == current_user.id` before returning or mutating data.

- Use `Depends(get_current_user)` to resolve the authenticated user
- Query resources with `user_id` filter, not just resource ID
- Never trust client-provided user IDs

---

## Path Traversal Protection

Vault and file operations MUST sanitize paths:
- Reject any path containing `..`
- Reject absolute paths outside the allowed root
- Validate against the vault root before any file operation

---

## Rate Limiting

- Auth endpoints have stricter rate limits
- General endpoints use global IP-based rate limiting via Redis sliding window
- CSRF exemptions for authenticated API endpoints (vault, profile photo)

---

## API Security Patterns

- **Route ordering**: Specific routes before parameterized routes (e.g., `/models/installed` before `/models/{model_id}`)
- **Response models**: Always use `response_model=` on decorators
- **Dependency injection**: `Depends(get_db)` for sessions, `Depends(get_current_user)` for auth
- **Error handling**: `HTTPException` with appropriate codes (404 not found, 403 forbidden, 409 conflict)
- **Pydantic schemas**: Explicit field types in `backend/app/schemas/`. Never use `dict` for structured responses.

---

## Security Audit History

P0/P1 fixes applied:
- Memory API requires authentication
- Vault path traversal blocked
- Token expiry reduced to 30 minutes
- CSRF, CORS, WebSocket security tightened
- Foreign key constraints added to repo models
- CSRF exemptions for authenticated API endpoints
- IDOR vulnerabilities patched (ownership checks on all user-scoped resources)

---

## Frontend Security

- **Auth flow**: `AuthProvider` bootstraps via `GET /me`. Login sets httpOnly cookies. Logout locks vault, clears session. Auto token refresh on 401.
- **API proxy**: Client-side fetch → Next.js API route → FastAPI. Same-origin, no CORS issues.
- **No secrets in client code**: Backend URL exposed via `/api/env` only. No API keys in frontend bundles.

---

## Infrastructure Security

- **Docker**: PostgreSQL, Redis, Qdrant on localhost-only ports
- **CORS**: Restricted to explicit origins
- **CSP headers**: Content Security Policy enabled
- **TLS**: Configure at reverse proxy level (Caddy recommended for auto Let's Encrypt)
- **Secrets**: `detect-secrets` pre-commit hook with baseline
