Last updated: 2026-06-28

# ADR-003: Two-Password Authentication Model

**Status:** Accepted
**Date:** 2026-06-24
**Deciders:** Adi + Claude Code

## Context

Cortex needs authentication for API access and encryption for user files (vault). A single password for both creates a single point of failure — if the session is compromised, the attacker gets everything.

## Decision

Implement a two-password model:
1. **Login password** — JWT access token (30min) + refresh token (7-day) in httpOnly cookies
2. **Vault password** — Separate password for Fernet encryption of user files

JWT access + refresh tokens. CSRF double-submit cookie pattern.

## Consequences

### Positive
- Vault isolation: compromised session cannot access files without vault password
- Defense in depth: two independent authentication layers
- httpOnly cookies prevent XSS attacks on tokens

### Negative
- Users must manage two passwords
- More complex UX (vault unlock screen)

## Alternatives Considered

1. **Single password** — Rejected. Weaker security, no isolation between session and vault.
2. **Bearer tokens** — Rejected. Less secure than httpOnly cookies.

## Related

- `backend/app/core/security.py` — JWT + CSRF implementation
- `backend/app/api/v1/auth.py` — Auth routes
