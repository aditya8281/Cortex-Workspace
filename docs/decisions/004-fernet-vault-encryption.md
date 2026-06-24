# ADR-004: Fernet Encryption for Vault

**Status:** Accepted
**Date:** 2026-06-24
**Deciders:** Adi + Claude Code

## Context

Users need encrypted file storage (vault) that protects files at rest. Files are encrypted per-user with keys derived from the vault password.

## Decision

Use Fernet symmetric encryption with:
- Per-user vault password
- Per-file salt derivation
- SecurePasswordCache that wipes passwords from memory

## Consequences

### Positive
- Battle-tested encryption (Fernet is well-audited)
- Per-user isolation
- Password wiped from memory after use

### Negative
- Fernet is symmetric — single key for all files per user
- No file-level access control (all-or-nothing vault access)

## Alternatives Considered

None — Fernet is the right choice for local-first file encryption.

## Related

- `backend/app/services/vault_service.py` — Implementation (806 lines)
