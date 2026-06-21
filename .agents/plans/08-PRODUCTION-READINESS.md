# Cortex Production Readiness Checklist

> Living document — last updated: 2026-06-22
>
> Checkboxes reflect current state. Items marked `[x]` are implemented.
> Items marked `[ ]` are identified gaps that need work before production.

---

## 1. Security

### Authentication & Authorization

- [x] JWT access tokens with configurable expiry (`ACCESS_TOKEN_EXPIRE_MINUTES`)
- [x] Refresh token rotation (new token on every refresh, old token revoked)
- [x] httpOnly cookies for token storage (XSS-resistant)
- [x] Argon2 password hashing (via passlib with bcrypt fallback)
- [x] CSRF double-submit cookie pattern (`cortex_csrf` + `X-CSRF-Token` header)
- [x] Rate limiting on auth endpoints (Redis sliding window)
- [x] Bearer token bypass for CSRF (API clients not affected)
- [x] Ownership checks on all user-scoped endpoints (`resource.user_id == current_user.id`)
- [ ] Account lockout after 5 consecutive failed login attempts
- [ ] API key authentication for programmatic access (separate from session auth)
- [ ] Session invalidation on password change

### Input Validation & Sanitization

- [x] Pydantic models for request validation on most endpoints
- [x] Password strength validation (min 8 chars, alpha + digit)
- [ ] Full input sanitization audit (XSS, SQL injection, path traversal)
- [ ] File upload content-type validation (not just extension)
- [ ] Request body size limits on all upload endpoints

### Vault Security

- [x] Per-file Fernet encryption with PBKDF2 key derivation (600K iterations)
- [x] Vault password hash stored separately from login password
- [x] In-memory password cache with bytearray secure wipe on lock
- [x] Path traversal protection on all vault file operations (`..` and absolute path rejection)
- [x] Vault file extension whitelist (40+ allowed types)
- [x] Max file size limit (50 MB)
- [x] Password rotation re-encrypts all files atomically
- [ ] Vault access audit logging

### Transport Security

- [x] HTTPS redirect middleware (configurable, off by default for dev)
- [x] HSTS header (`max-age=31536000; includeSubDomains`)
- [x] Secure cookie flags in production (`secure=True`, `samesite=lax`)

### Security Headers

- [x] `X-Content-Type-Options: nosniff`
- [x] `X-Frame-Options: DENY`
- [x] `X-XSS-Protection: 1; mode=block`
- [x] `Referrer-Policy: strict-origin-when-cross-origin`
- [x] `Content-Security-Policy` (dev and prod variants)
- [x] `Strict-Transport-Security`

---

## 2. Reliability

### Health Checks

- [x] Liveness probe (`GET /api/v1/health/live`)
- [x] Readiness probe (`GET /api/v1/health/ready`)
- [x] Deep health check (database, Redis, Qdrant, LLM status)
- [x] Health check task in arq worker (every 30 minutes)

### Resilience

- [x] Database connection pooling (SQLAlchemy engine)
- [x] Graceful Redis fallback (all Redis operations wrapped in try/except)
- [x] Graceful LLM fallback (llama.cpp → Ollama → error with clear message)
- [x] Graceful embedding fallback (ONNX → Ollama → mock)
- [x] Orphaned agent run cleanup on startup
- [x] Sync state recovery on startup
- [ ] Circuit breaker for external services (Ollama, Qdrant)
- [ ] Retry logic with exponential backoff for database operations
- [ ] Graceful degradation chain (feature flags for degraded mode)
- [ ] Request timeout on all external calls

### Logging & Observability

- [x] Structured logging with request IDs (`RequestIdFilter`)
- [x] Request/response logging middleware with duration tracking
- [x] Per-request metrics recording (`record_request`)
- [ ] Log levels configurable per-module
- [ ] Error aggregation and alerting
- [ ] Distributed tracing (OpenTelemetry)

---

## 3. Performance

### Backend

- [x] GZip compression (min 500 bytes)
- [x] Async FastAPI handlers
- [x] Database connection pooling
- [x] Redis caching for rate limiting and token storage
- [ ] Query optimization (N+1 detection, prefetch related objects)
- [ ] Redis caching for frequent queries (model catalog, user settings)
- [ ] Response caching headers for static/immutable data
- [ ] Pagination with cursors for large result sets
- [ ] Background task processing for heavy operations (arq)

### Frontend

- [x] Next.js App Router (server components by default)
- [x] Code splitting (route-based)
- [ ] Bundle size analysis and optimization
- [ ] Image optimization (next/image)
- [ ] Font optimization (next/font)
- [ ] Prefetching for navigation paths
- [ ] Service worker for offline support

### Infrastructure

- [x] PostgreSQL with connection pooling
- [x] Redis for caching and task queue
- [x] Qdrant for vector search (in-memory or persistent)
- [ ] Resource limits in Docker Compose (CPU, memory)
- [ ] Horizontal scaling plan for API servers

---

## 4. Testing

### Backend

- [x] Test framework: pytest
- [x] Test fixtures: conftest.py with database setup
- [x] API tests: 20+ test files covering auth, vault, models, agents, etc.
- [ ] 80%+ code coverage (current: estimated 40-50%)
- [ ] Service layer unit tests (embedding, hybrid retrieval, RAG pipeline)
- [ ] Integration tests for agent system
- [ ] Database migration tests (upgrade + downgrade)
- [ ] Load tests (locust or k6)

### Frontend

- [x] Test framework: vitest
- [x] Test utilities: test-utils.tsx with render helpers
- [x] Component tests: Button.test.tsx
- [ ] 60%+ code coverage
- [ ] Hook tests (useFolderPicker, useSystemWebSocket)
- [ ] API client tests (client.ts, domain modules)
- [ ] E2E tests (Playwright): auth flow, vault, chat, search

### CI/CD

- [x] `make check` (lint + test)
- [x] `make prod-check` (clean + lint + test)
- [x] Ruff linting
- [x] MyPy type checking
- [ ] Pre-commit hooks enforcement
- [ ] Coverage threshold enforcement in CI
- [ ] Visual regression tests

---

## 5. Operations

### Deployment

- [x] Docker Compose for local development
- [x] Dockerfile for production builds
- [x] Alembic migrations (25 sequential migrations)
- [x] `make migrate` for applying migrations
- [x] `make db-reset` for clean slate
- [ ] Production deployment guide
- [ ] Environment variable reference document
- [ ] Blue-green deployment support
- [ ] Rolling update strategy

### Backup & Recovery

- [x] `make db-backup` (pg_dump)
- [ ] Automated backup schedule (cron or systemd timer)
- [ ] Backup verification tests
- [ ] Point-in-time recovery documentation
- [ ] Vault backup/restore procedure
- [ ] Disaster recovery runbook

### Monitoring

- [x] `/metrics` Prometheus endpoint
- [x] Request duration and status code tracking
- [x] LLM usage tracking (tokens, requests, errors)
- [ ] Dashboard (Grafana or similar)
- [ ] Alerting rules (error rate, latency, disk usage)
- [ ] Log aggregation (Loki, ELK, or cloud equivalent)
- [ ] Uptime monitoring

### Maintenance

- [x] `make clean` (remove caches)
- [x] `make lock` (update dependencies)
- [ ] Dependency vulnerability scanning
- [ ] Automated dependency updates (Renovate/Dependabot)
- [ ] Database vacuum and maintenance schedule
- [ ] Log rotation configuration

---

## 6. Documentation

### Developer Documentation

- [x] README.md with setup instructions
- [x] API documentation (OpenAPI/Swagger at `/docs`)
- [x] API documentation (ReDoc at `/redoc`)
- [x] Design system documentation (`DESIGN.md`)
- [x] Architecture document (`07-ARCHITECTURE.md`)
- [x] Production readiness checklist (this document)
- [ ] Contributing guide
- [ ] Code style guide
- [ ] Git workflow documentation

### User Documentation

- [ ] User guide (getting started, features)
- [ ] Vault usage guide
- [ ] Agent system guide
- [ ] Model management guide
- [ ] Troubleshooting guide

### Operations Documentation

- [ ] Deployment guide
- [ ] Runbook (common operations and their commands)
- [ ] Incident response procedures
- [ ] Capacity planning guide
- [ ] Security audit procedures

---

## 7. Compliance & Privacy

- [x] No external telemetry or analytics
- [x] No cloud sync without explicit user action
- [x] Local-first architecture (all processing on user machine)
- [x] User data deletion support (`deleted_at` soft delete)
- [ ] GDPR/data retention policy documentation
- [ ] Privacy policy
- [ ] Terms of service
- [ ] Data export functionality

---

## 8. Scalability Considerations

### Current Limits

| Resource | Limit | Mitigation |
|----------|-------|------------|
| Database | Single PostgreSQL instance | Connection pooling, query optimization |
| Vector DB | Single Qdrant instance | Collection-per-tenant filtering |
| LLM | Single provider at a time | Provider failover chain |
| File uploads | 50 MB per vault file | Enforced at application level |
| Embeddings | 768-dim vectors | Configurable via `EMBEDDING_DIM` |

### Scaling Path

1. **Single machine** (current): Docker Compose with all services on one host
2. **Vertical scaling**: Increase resources for PostgreSQL, Qdrant, Redis
3. **Horizontal scaling**: Multiple API server instances behind load balancer
4. **Distributed**: Separate services into microservices (agent, indexing, LLM)

---

## Priority Order

### Critical (Must-have for any deployment)

1. Account lockout after failed attempts
2. Input sanitization audit
3. 80%+ backend test coverage
4. Automated backups
5. Production deployment guide

### High (Should-have for production)

1. Circuit breaker for external services
2. Redis caching for frequent queries
3. API key authentication
4. Monitoring dashboard
5. E2E tests

### Medium (Nice-to-have)

1. Frontend bundle optimization
2. Distributed tracing
3. Blue-green deployment
4. Load tests
5. Visual regression tests

### Low (Future improvements)

1. Offline support (service worker)
2. Microservices decomposition
3. Multi-tenant isolation
4. GDPR compliance documentation
5. Capacity planning tools
