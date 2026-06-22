# Cortex Security & Reliability Audit Report (v2)

Generated: 2026-06-22  
Updated: 2026-06-22 (P0/P1 fixes applied)  
Auditor: Automated Security Analysis  
Scope: Full codebase — `backend/`, infrastructure, configuration  
Previous audit: `.agents/audit/security-audit-report.md`

---

## Fixed Issues (2026-06-22)

| ID | Issue | Fix |
|----|-------|-----|
| C1 | Agent self-approval bypass | Added explicit block: `approve_tool` cannot be called via LLM tool-calling |
| H1 | Auth rate limiter key mismatch (`/api/auth` vs `/api/v1/auth`) | Fixed prefix to `/api/v1/auth` in `rate_limit.py:33` |
| H2 | Refresh token reuse clears ALL users' tokens | Scoped `clear_pattern` to `refresh:user:{user_id}:*` |
| H4 | Vault brute-force unprotected | Added 5 attempts/minute rate limit with in-memory fallback |
| M1 | `_list_files_tool` has no path restriction | Added `_ensure_within_workspace()` call |
| Q1 | Token revocation silently ignored on logout | Added logging |
| Q2 | Security token store/revoke at warning level | Upgraded to error level |

## Fixed Issues — Session 3 (2026-06-22)

| ID | Issue | Fix |
|----|-------|-----|
| H-S5 | GitHub token encryption weak key derivation | Replaced SHA-256 with HKDF |
| H-S8 | HuggingFace token stored in plaintext | Added Fernet encryption with HKDF |
| H-S10 | Rate limiting fails open on Redis outage | Added in-memory fallback |
| M-S1 | CSRF vault exemption unnecessary | Removed from exempt list |
| M-S5 | WebSocket no per-user limits | Added per-user connection tracking |
| M-S6 | CORS hardcoded to localhost | Added CORS_ORIGINS env var |
| M-S8 | validate_storage_path not called | Added validation call |
| M-C4 | Agent tools type mismatch | Added field_validator |
| M-CL3 | Redundant auth/security.py | Deleted |
| M-CL5 | Unused UI components (3 files) | Deleted |

---

## Executive Summary

| Severity | Count | Description |
|----------|-------|-------------|
| CRITICAL | 1 | Immediate exploitation risk |
| HIGH | 7 | Significant security gap |
| MEDIUM | 15 | Defense-in-depth weakness |
| LOW | 12 | Hardening opportunity |
| **Total** | **35** | |

### Changes from v1 Audit

| Status | Count | Notes |
|--------|-------|-------|
| **Fixed** | 11 | Resolved since v1 audit |
| **Remaining** | 10 | Carried over, partially addressed |
| **New** | 14 | Discovered in this audit |
| **Downgraded** | 4 | Severity reduced due to mitigations |

---

## Summary of Fixed Issues (from v1)

| v1 ID | Title | Status | Notes |
|-------|-------|--------|-------|
| C2 | Agent reads arbitrary files | **FIXED** | `executor.py:216-228` now uses `_ensure_within_workspace()` |
| C3 | Agent writes arbitrary files | **FIXED** | `executor.py:234-246` now uses `_ensure_within_workspace()` |
| C4 | web_fetch SSRF | **MITIGATED** | `tools.py:189-206` now blocks private IPs and non-HTTP schemes |
| C5 | Unauthenticated /ws/demo | **FIXED** | `ws.py:19-33` now requires JWT token in query params |
| H6 | DB password logged at startup | **FIXED** | `main.py:102` logs "System database initialized" without URL |
| H7 | Vault rename path traversal | **FIXED** | `vault_service.py:472-478` validates name and resolved path |
| M3 | Login clears blocks across IPs | **MITIGATED** | `rate_limit.py:30-34` only clears user block, IP block preserved |
| M5 | Request size bypass via chunked encoding | **FIXED** | `main.py:44-62` adds `RequestSizeLimitMiddleware` |
| M12 | HSTS header over HTTP | **FIXED** | `middleware.py:62-63` only sends HSTS over HTTPS |
| M14 | git_diff flag injection | **FIXED** | `tools.py:167-168` rejects paths starting with `-` |
| H5 | create_run no agent ownership check | **FIXED** | `agents.py:83` calls `get_agent(agent_id, user_id=current_user.id)` |

---

## Part 1: Critical Vulnerabilities

### C1: Agent self-approval mechanism is bypassable

**File:** `agents/executor.py:52-58`  
**CWE:** CWE-862 (Missing Authorization)

The approval mechanism uses an in-memory set (`_approved_tools`). The LLM can call `approve_tool('exec_command')` as part of its tool-call output, effectively self-approving dangerous operations.

```python
def approve_tool(self, tool_name: str) -> None:
    self._approved_tools.add(tool_name)
```

**Attack scenario:** A prompt injection in user-provided content instructs the agent to call `approve_tool` before `exec_command`. The agent generates both tool calls in sequence, bypassing the human-approval gate.

**Impact:** Full system compromise via arbitrary command execution.

**Mitigation (partial):** The workspace restriction (`AGENT_WORKSPACE`) limits file I/O scope, but `exec_command` runs with the backend process's full privileges.

---

## Part 2: High-Severity Issues

### H1: Auth rate limiter key mismatch — auth endpoints not actually rate-limited

**File:** `core/rate_limit.py:33`  
**CWE:** CWE-770 (Allocation of Resources Without Limits)

```python
is_auth_endpoint = request.url.path.startswith("/api/auth")
```

Auth endpoints are registered under `/api/v1/auth/` (see `auth/router.py`), but the check looks for `/api/auth`. This means auth endpoints receive the full 100 req/min global limit instead of the intended 10 req/min auth limit.

**Impact:** Brute-force attempts on login are not properly rate-limited.

---

### H2: Refresh token reuse detection clears ALL users' tokens

**File:** `auth/service.py:190`  
**CWE:** CWE-287 (Improper Authentication)

```python
await redis_cache.clear_pattern("refresh:*")
```

When reuse is detected, the code clears ALL refresh tokens matching `refresh:*` — not just the affected user's tokens. This is a denial-of-service vector: any reuse attempt (intentional or accidental) logs out every user.

**Impact:** All authenticated users are logged out simultaneously.

---

### H3: WebSocket tokens in URL query string

**Files:** `api/ws.py:21`, `api/v1/ws_system.py:61`  
**CWE:** CWE-598 (Use of GET Request Token in URL)

Tokens appear in:
- Server access logs
- Browser history and address bar
- HTTP Referer headers
- Proxy/load-balancer logs
- URL bar during screen sharing

No revocation check is performed on WebSocket auth tokens (they decode JWT but don't check the revocation list in Redis).

**Impact:** Token leakage through logs; no session revocation for WebSocket connections.

---

### H4: No rate limiting on vault password attempts

**File:** `api/v1/vault.py:88-98`, `services/vault_service.py:216-239`  
**CWE:** CWE-307 (Improper Restriction of Excessive Authentication Attempts)

The vault unlock endpoint has no rate limiting. An attacker can brute-force the vault password without any lockout or delay mechanism. Unlike the login endpoint (which has `auth/rate_limit.py`), vault password verification has no protection.

**Impact:** Vault encryption bypassed via brute-force.

---

### H5: GitHub token encryption uses deterministic key from SECRET_KEY

**File:** `api/v1/github.py:69-78`  
**CWE:** CWE-321 (Use of Hard-coded Cryptographic Key)

```python
key = hashlib.sha256(settings.SECRET_KEY.encode()).digest()
fernet_key = Fernet(base64.urlsafe_b64encode(key))
encrypted = fernet_key.encrypt(body.token.encode()).decode()
```

The GitHub PAT is encrypted with a Fernet key derived directly from the app's SECRET_KEY. Anyone with access to the SECRET_KEY (e.g., from `.env` on disk) can decrypt all stored GitHub tokens. There is no per-user key derivation.

**Impact:** Compromise of SECRET_KEY exposes all GitHub PATs.

---

### H6: `/metrics` endpoint unauthenticated and rate-limit exempt

**Files:** `api/metrics.py:32-69`, `core/rate_limit.py:30`  
**CWE:** CWE-200 (Exposure of Sensitive Information)

The `/metrics` endpoint exposes:
- Application uptime
- Memory usage (RSS)
- Request counts and error rates
- Request latency percentiles

It is explicitly exempt from rate limiting and has no authentication. Useful for attack reconnaissance.

**Impact:** Information disclosure aiding targeted attacks.

---

### H7: `get_current_user` double-decode accepts revoked tokens during Redis outage

**File:** `core/db.py:44-64`  
**CWE:** CWE-287 (Improper Authentication)

The `get_current_user` function decodes the token twice: once via `verify_access_token` and once via `jwt.decode` for revocation check. If Redis is down, `is_access_token_revoked` returns `True` (fail-closed — good), but `verify_access_token` already accepted the token. The `except JWTError` on line 60 only catches decode errors from the second decode, not revocation failures.

Actually, reviewing more carefully: `is_access_token_revoked` now returns `True` on Redis failure (line 83-84 of `security.py`), which correctly rejects the request. This is **fail-closed** behavior — the v1 audit's concern is addressed.

**Status:** FIXED since v1 audit (security.py:77-84 now returns `True` on Redis failure).

---

### H8: Repository registration has no path restrictions

**File:** `api/v1/repository.py:85-104`  
**CWE:** CWE-22 (Improper Limitation of a Pathname to a Restricted Directory)

```python
path = Path(payload.path).expanduser().resolve()
if not path.is_dir():
    raise HTTPException(status_code=400, detail=f"Path is not a directory: {payload.path}")
```

Users can register any directory on the filesystem as a repository. This allows:
- Indexing `/etc`, `/root`, `/proc`
- Reading sensitive configuration files via the indexing pipeline
- Exhausting disk/CPU by indexing massive directories

**Impact:** Arbitrary filesystem reading via indexing; resource exhaustion.

---

## Part 3: Medium-Severity Issues

### M1: `_list_files_tool` has no path restriction

**File:** `agents/executor.py:248-264`  
**CWE:** CWE-22 (Path Traversal)

Unlike `_read_file_tool` and `_write_file_tool` (which use `_ensure_within_workspace`), `_list_files_tool` accepts any path and lists its contents:

```python
async def _list_files_tool(self, path: str = ".") -> str:
    dir_path = Path(path)
    if not dir_path.is_dir():
        return f"Not a directory: {path}"
    entries = sorted(dir_path.iterdir(), ...)
```

An agent can list `/etc`, `/root`, or any directory on the system.

**Impact:** Directory traversal information disclosure.

---

### M2: CSRF exemption for vault endpoints is incorrect

**File:** `core/csrf.py:26`  
**CWE:** CWE-352 (Cross-Site Request Forgery)

```python
EXEMPT_PREFIXES = ("/api/v1/auth/", "/api/v1/health/", "/metrics", "/ws", "/api/v1/me/vault/")
```

Vault endpoints are exempted from CSRF because they require `get_current_user`. However, if auth cookies are the primary credential, a CSRF attack could submit requests with the user's cookies. The double-submit cookie pattern should apply to vault operations too, unless Bearer tokens are always used.

**Impact:** Potential CSRF on vault file operations if cookies are the auth mechanism.

---

### M3: Password validation is weak

**File:** `core/security.py:30-35`  
**CWE:** CWE-521 (Weak Password Requirements)

```python
def validate_password_strength(password: str) -> bool:
    if not password or len(password) < 8:
        return False
    has_alpha = any(c.isalpha() for c in password)
    has_digit = any(c.isdigit() for c in password)
    return has_alpha and has_digit
```

Passwords as weak as `password1` pass validation. No requirements for:
- Uppercase letters
- Special characters
- Maximum consecutive characters
- Common password dictionary check

**Impact:** Accounts vulnerable to dictionary and brute-force attacks.

---

### M4: Vault password re-encryption is not atomic

**File:** `services/vault_service.py:560-625`  
**CWE:** CWE-755 (Improper Handling of Exceptional Conditions)

All vault files are decrypted into memory, then re-encrypted in a loop. If the process crashes after decryption but before all files are re-encrypted:
- Some files encrypted with new key
- Others still encrypted with old key
- User cannot decrypt all files with either password

No backup or rollback mechanism exists.

**Impact:** Potential data loss during password rotation.

---

### M5: `run.error` stores internal exception messages

**File:** `agents/run_manager.py:168`  
**CWE:** CWE-209 (Generation of Error Message Containing Sensitive Information)

```python
run.error = "Agent execution failed"
```

This is now a static string — **improved from v1**. However, `step.observation` on line 136 still stores `f"Error: {e}"`, which could contain file paths, SQL errors, or stack traces that are returned via the API.

**Impact:** Internal path and error disclosure through step observations.

---

### M6: Rate limiting fails open on Redis outage

**File:** `core/rate_limit.py:47-49`  
**CWE:** CWE-693 (Protection Mechanism Failure)

```python
except Exception as e:
    logger.warning("Rate limiter Redis failure for %s %s: %s", request.method, request.url.path, e)
    return await call_next(request)
```

When Redis is unavailable, all rate limiting is disabled. Combined with the auth rate limiter also failing open, brute-force protection is completely absent during Redis outages.

**Impact:** DoS protection disabled during infrastructure failures.

---

### M7: Vault password cached in plaintext in memory

**File:** `services/vault_service.py:40-87, 236-237`  
**CWE:** CWE-316 (Plaintext Storage of Password)

The `SecurePasswordCache` stores passwords as `bytearray` objects and attempts to wipe them on `pop()`. However:
- `get()` and `__getitem__` return `str` objects (immutable, GC may retain copies)
- Python strings are immutable; intermediate `str` copies are not zeroed
- The password is held in memory for the entire session duration

**Impact:** Memory dump / cold-boot attack can extract vault passwords.

---

### M8: HuggingFace token stored in plaintext

**File:** `api/v1/models.py:511-559`  
**CWE:** CWE-312 (Cleartext Storage of Sensitive Information)

User model settings store `huggingface_token` directly in the database without encryption:

```python
settings_row.huggingface_token = value  # line ~549
```

**Impact:** Database compromise exposes HuggingFace API tokens.

---

### M9: `/api/v1/auth/me` and `/api/v1/auth/me PUT` don't use `get_current_user` dependency

**File:** `auth/router.py:157-168, 171-202`  
**CWE:** CWE-306 (Missing Authentication for Critical Function)

The `/api/v1/auth/me` endpoints manually extract and verify tokens instead of using the `get_current_user` dependency. This means they don't benefit from the dependency injection pattern's consistency (e.g., future auth improvements won't automatically apply).

While functionally equivalent, this is a maintenance risk and inconsistency.

---

### M10: WebSocket connections have no per-user limits

**File:** `core/websocket.py`  
**CWE:** CWE-770 (Allocation of Resources Without Limits)

The `ConnectionManager` limits connections per channel (100), but not per user. A single user can open unlimited connections, exhausting server memory and file descriptors.

**Impact:** Resource exhaustion by a single authenticated user.

---

### M11: CORS has no production origins configured

**File:** `core/config.py:30-37`  
**CWE:** CWE-942 (Permissive Cross-domain Policy)

Default origins are localhost only. Production deployment requires manual configuration. If a developer accidentally deploys with default settings and uses a reverse proxy that adds CORS headers, the application's CORS policy may be bypassed.

---

### M12: Vault password change doesn't re-derive key from new password

**File:** `services/vault_service.py:560-625`  
**CWE:** CWE-325 (Missing Required Cryptographic Step)

During password rotation, files are decrypted with the old password and re-encrypted with the new password. However, the new encryption uses `encrypt_bytes(content, new_pw)` which derives a new Fernet key. This is correct but the intermediate state (all files decrypted in memory) is a window of vulnerability.

---

### M13: Error messages in conversation streaming leak internal details

**File:** `api/v1/conversations.py:166-170`  
**CWE:** CWE-209 (Information Exposure)

```python
except Exception as e:
    error_msg = f"Error: {str(e)[:200]}"
    full_response = error_msg
    yield f"data: {json.dumps({'type': 'chunk', 'content': error_msg, ...})}\n\n"
```

Exception messages (truncated to 200 chars) are streamed directly to the client. These may contain file paths, SQL errors, or library internals.

**Impact:** Information disclosure through error messages.

---

### M14: `validate_storage_path()` not called during storage registration updates

**File:** `services/storage_registry.py:17-37`  
**CWE:** CWE-20 (Improper Input Validation)

The `register_user_storage` function stores the path without calling `validate_storage_path()`. Validation is only done during registration in `auth/service.py`. If a code path updates the registry directly, the path is not validated.

---

## Part 4: Low-Severity Issues

### L1: No `SECRET_KEY` rotation mechanism

**Files:** `core/config.py`, `.env`  
**CWE:** CWE-324 (Use of a Key Past its Expiration Date)

The same SECRET_KEY is used for all JWT signing. No mechanism exists for key rotation without invalidating all sessions.

### L2: Redis has no password in docker-compose

**File:** `docker-compose.yml:20-30`  
**CWE:** CWE-287 (Improper Authentication)

Redis runs without authentication. Any process on the host can connect and read/write token data.

### L3: Repositories with `user_id=NULL` visible to all users

**File:** `api/v1/repository.py:67-69`  
**CWE:** CWE-863 (Incorrect Authorization)

```python
.filter((RepoIndex.user_id == current_user.id) | (RepoIndex.user_id.is_(None)))
```

Repos with NULL user_id are returned to every authenticated user.

### L4: `SecurePasswordCache.get()` returns immutable strings

**File:** `services/vault_service.py:51-59`  
**CWE:** CWE-316 (Cleartext Storage in Memory)

Python's immutable `str` objects cannot be zeroed. GC may retain copies indefinitely.

### L5: CSP dev mode allows `ws://localhost:*` connections

**File:** `core/middleware.py:11-18`  
**CWE:** CWE-1021 (Improper Restriction of Rendered UI Layers)

Development CSP allows WebSocket connections to any localhost port.

### L6: No `Cache-Control: no-store` on authenticated responses

**File:** `core/middleware.py`  
**CWE:** CWE-525 (Use of Web Browser Cache Containing Sensitive Information)

Authenticated API responses may be cached by browsers or proxies.

### L7: No `Permissions-Policy` header

**File:** `core/middleware.py`  
**CWE:** CWE-693 (Protection Mechanism Failure)

Missing header that restricts browser features (camera, microphone, geolocation).

### L8: `x-xss-protection` header is deprecated

**File:** `core/middleware.py:33`  
**CWE:** N/A (Misconfiguration)

CSP is the proper defense; the legacy header can enable XSS in older browsers.

### L9: Hardcoded DB credentials as defaults in source code

**File:** `core/config.py:14`  
**CWE:** CWE-798 (Use of Hard-coded Credentials)

```python
DATABASE_URL: str = "postgresql://cortex:cortex@localhost:5432/cortex"
```

### L10: Vault extension allowlist includes `.env`, `.key`, `.pem`

**File:** `services/vault_service.py:89-137`  
**CWE:** N/A (Security Design)

Allowing `.env`, `.key`, `.pem`, and `.crt` files in the vault means users may store secrets there. These files are encrypted, but the vault password may be weaker than the secrets they contain.

### L11: `git_log` has no path restriction

**File:** `agents/tools.py:141-161`  
**CWE:** CWE-22 (Path Traversal)

`git_log` accepts any `repo_path` and runs `git log` in that directory. While the output is limited, it confirms the existence of git repositories and their commit history.

### L12: Thread-safety of in-memory refresh token stores

**File:** `core/security.py:96-98`  
**CWE:** CWE-362 (Concurrent Execution Using Shared Resource)

The `_memory_active` and `_memory_revoked` dicts use a `threading.Lock`, but in an async context with uvicorn's event loop, multiple coroutines may interleave between lock acquisitions. This is a minor correctness issue under high concurrency.

---

## Part 5: Failure Mode Analysis

### Redis Outage

| System | Behavior | Risk | Status |
|--------|----------|------|--------|
| Token revocation (access) | **Fail-closed** — rejects request | LOW | ✅ Fixed |
| Token revocation (refresh) | Falls back to memory cache | MEDIUM | ⚠️ Single-worker only |
| Rate limiting | **Fail-open** — requests allowed | HIGH | ❌ Unchanged |
| Brute-force blocking | **Fail-open** — no checks | HIGH | ❌ Unchanged |
| Refresh token storage | Falls back to memory | MEDIUM | ⚠️ Single-worker only |

### Database Outage

| System | Behavior | Risk |
|--------|----------|------|
| Auth | 500 errors on all requests | MEDIUM |
| Health check | Fails readiness probe | LOW |
| Agent execution | Fails with generic error | LOW |

### LLM Provider Outage

| System | Behavior | Risk |
|--------|----------|------|
| Chat | Returns fallback message | LOW |
| Agent execution | Falls back to keyword routing | LOW |
| Title generation | Falls back to content truncation | LOW |

### Process Crash During Vault Password Rotation

| State | Impact |
|-------|--------|
| Pre-decryption | No data loss |
| Post-decryption, pre-encryption | **DATA LOSS** |
| Mid-encryption | **PARTIAL DATA LOSS** |

---

## Part 6: Remediation Priority

### Phase 1: Critical (Fix immediately)

1. **Fix agent self-approval** — Require human confirmation via a separate, cryptographically signed mechanism (not LLM-generated tool calls)
2. **Fix `_list_files_tool`** — Add `_ensure_within_workspace()` call
3. **Add vault brute-force protection** — Implement rate limiting on vault unlock endpoint

### Phase 2: High (Fix soon)

4. **Fix auth rate limiter key** — Change `/api/auth` to `/api/v1/auth` in `rate_limit.py:33`
5. **Fix refresh token reuse** — Scope `clear_pattern` to the affected user's tokens only
6. **Move WebSocket tokens out of URL** — Use secure cookie or WebSocket handshake header
7. **Restrict repository paths** — Validate that repo paths are within allowed directories
8. **Authenticate `/metrics`** — Require auth or restrict to admin users
9. **Encrypt HuggingFace tokens** — Use Fernet encryption with per-user key derivation
10. **Scope GitHub token encryption** — Derive encryption key from user-specific secret, not just app SECRET_KEY

### Phase 3: Medium (Fix when touching these areas)

11. **Strengthen password validation** — Require uppercase, special char, and common-password check
12. **Add atomicity to vault rotation** — Backup old files before re-encryption
13. **Sanitize step observation errors** — Don't store raw exception messages
14. **Add per-user WebSocket limits** — Prevent resource exhaustion
15. **Fix CSRF vault exemption** — Apply CSRF to vault POST/PUT/DELETE endpoints
16. **Add `Cache-Control: no-store`** to authenticated responses
17. **Validate storage paths on registration updates**
18. **Add `Permissions-Policy` header**

### Phase 4: Low (Harden opportunistically)

19. Implement `SECRET_KEY` rotation support
20. Add Redis password to docker-compose
21. Remove deprecated `x-xss-protection` header
22. Remove hardcoded DB credentials from defaults
23. Add git command path restrictions
24. Restrict repository visibility for NULL user_id entries

---

## Appendix A: Endpoints Auth Status

All API endpoints under `/api/v1/` require authentication via `Depends(get_current_user)` unless noted otherwise.

| Endpoint | Auth | Owner Check | Rate Limited |
|----------|------|-------------|--------------|
| `POST /api/v1/auth/register` | ❌ Public | N/A | ⚠️ Wrong prefix |
| `POST /api/v1/auth/login` | ❌ Public | N/A | ⚠️ Wrong prefix |
| `POST /api/v1/auth/refresh` | ❌ Public | N/A | ⚠️ Wrong prefix |
| `POST /api/v1/auth/logout` | ❌ Public | N/A | ⚠️ Wrong prefix |
| `GET /api/v1/auth/me` | ✅ Manual | ✅ | ⚠️ Wrong prefix |
| `PUT /api/v1/auth/me` | ✅ Manual | ✅ | ⚠️ Wrong prefix |
| `DELETE /api/v1/auth/me` | ✅ Manual | ✅ | ⚠️ Wrong prefix |
| `POST /api/v1/auth/restore` | ✅ Manual | ✅ | ⚠️ Wrong prefix |
| `GET /api/v1/health/*` | ❌ Public | N/A | Exempt |
| `GET /metrics` | ❌ Public | N/A | Exempt |
| `GET /api/v1/repos` | ✅ | ✅ | ✅ |
| `POST /api/v1/repos` | ✅ | ✅ | ✅ |
| `POST /api/v1/repos/{id}/index` | ✅ | ✅ | ✅ |
| `POST /api/v1/agents/runs` | ✅ | ✅ | ✅ |
| `GET /api/v1/agents/runs/{id}` | ✅ | ✅ | ✅ |
| `POST /api/v1/me/vault/unlock` | ✅ | N/A | ❌ No limit |
| `POST /api/v1/me/vault/files/upload` | ✅ | ✅ | ✅ |
| `POST /api/v1/me/vault/files/export` | ✅ | ✅ | ✅ |
| `POST /api/v1/me/vault/change-password` | ✅ | ✅ | ✅ |
| `WS /ws/demo` | ✅ JWT | N/A | ❌ No limit |
| `WS /ws/system` | ✅ JWT | N/A | ❌ No limit |
| All other `/api/v1/*` | ✅ | ✅ | ✅ |

---

## Appendix B: Secrets Exposure Map

| Secret | Location | Encrypted | Accessible Via |
|--------|----------|-----------|----------------|
| JWT SECRET_KEY | `.env:8` | ❌ Plaintext on disk | Filesystem access |
| DATABASE_URL (with password) | `.env:13` | ❌ Plaintext on disk | Filesystem access |
| Redis URL | `.env:16` | ❌ Plaintext on disk | Filesystem access |
| GitHub PAT | DB `user.github_token_encrypted` | ✅ Fernet | Anyone with SECRET_KEY |
| Vault password hash | DB `user.vault_password_hash` | ✅ Argon2 | N/A |
| HuggingFace token | DB `user_settings.huggingface_token` | ❌ Plaintext | Database access |
| Vault password (cached) | In-memory `_vault_passwords` | ❌ Plaintext in RAM | Memory dump |
| User passwords | DB `user.hashed_password` | ✅ Argon2 | N/A |
