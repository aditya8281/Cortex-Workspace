# Backend Quality Fixes — Task C Report

## What Was Implemented

All 14 backend quality fixes from `remaining-fix.md` Quality section:

### 1. Empty LLMHealthResponse/LLMMetricsResponse stubs
- Populated `LLMHealthResponse` with `status`, `latency_ms`, `error` fields
- Populated `LLMMetricsResponse` with `total_requests`, `total_tokens`, `avg_latency` fields

### 2. 7 endpoints return raw dicts, no typed responses
- Added `response_model=` to health, metrics, hardware, inference config endpoints
- Created `InferenceConfigResponse` and `HardwareInfoResponse` schemas

### 3. models.py is 927 lines — Split into sub-routers
- `catalog.py` — Model catalog browsing (list, search, compare, detail, inference config)
- `downloads.py` — Download management (installed, queue, history, download, cancel, delete)
- `settings.py` — Settings, storage, sync, updates
- `llm_health.py` — LLM health and metrics
- `models.py` — Main router that includes all sub-routers

### 4. DateTime tz-aware/naive inconsistency
- Standardized all models to `DateTime(timezone=True)` across 14 model files
- Affected: user.py, conversation.py, agent.py, notification.py, auth_event.py, document.py, embedding_cache.py, file_index.py, repo_index.py, graph.py, storage_registry.py, indexing_config.py, path_index.py

### 5. Default value mechanism inconsistency
- Changed `auth_event.py` from `default=lambda: datetime.now(timezone.utc)` to `server_default=func.now()` for consistency

### 6. parameter_count type mismatch (str vs float)
- Aligned all `parameter_count` fields to `float | None` in 6 schema classes:
  - `ModelCatalogEntry`, `ModelRecommendation`, `InstalledVariant`, `InstalledModel`, `ModelSearchResult`, `ModelVariantInfo`, `ModelDetailResponse`
- Updated `_guess_param_count` helper to return float

### 7. LLMManager.chat() creates raw SessionLocal()
- Added optional `db` parameter to `chat()` and `chat_stream()` methods
- Falls back to `SessionLocal()` only when no session is provided

### 8. Lazy singletons without thread safety
- Added `threading.Lock()` double-checked locking to `get_embedding_service()`
- Added `threading.Lock()` double-checked locking to `get_file_watcher_v2()`

### 9. Missing circuit breaker for external services
- Created `circuit_breaker.py` with `CircuitBreaker` class (CLOSED → OPEN → HALF_OPEN)
- Integrated into `embedding_service.py` for Ollama calls
- Integrated into `hybrid_retrieval.py` for Qdrant calls

### 10. Deep health check only checks DB
- Added Redis, Ollama, and Qdrant health checks to `HealthService`
- Updated `/health/deep` endpoint to run all checks and return structured status

### 11. SECRET_KEY defaults to empty string
- Added auto-generation in `model_post_init` using `secrets.token_hex(32)` when no key is provided

### 12. AgentFeedbackCreateResponse.feedback typed as dict
- Changed `feedback: dict` to `feedback: AgentFeedbackInfo` (typed schema)

### 13. Hardcoded English GIN index config
- Created migration `c00000000003_use_simple_gin_config.py` to replace `'english'` with `'simple'` config

### 14. IndexedFile.is_stale() uses os.stat() in model
- Removed `is_stale()` method from `IndexedFile` model
- Created `file_staleness.py` service with `is_indexed_file_stale()` function

## Files Changed

**New files:**
- `backend/app/api/v1/catalog.py`
- `backend/app/api/v1/downloads.py`
- `backend/app/api/v1/settings.py`
- `backend/app/api/v1/llm_health.py`
- `backend/app/services/circuit_breaker.py`
- `backend/app/services/file_staleness.py`
- `migrations/versions/c00000000003_use_simple_gin_config.py`

**Modified files:**
- `backend/app/schemas/model.py` — response schemas, parameter_count types
- `backend/app/schemas/agent.py` — AgentFeedbackCreateResponse
- `backend/app/api/v1/models.py` — reduced to router include aggregator
- `backend/app/api/v1/health.py` — deep health checks
- `backend/app/services/llm/manager.py` — session parameter
- `backend/app/services/embedding_service.py` — circuit breaker, thread safety
- `backend/app/services/file_watcher_v2.py` — thread safety
- `backend/app/services/health_service.py` — Redis/Ollama/Qdrant checks
- `backend/app/services/hybrid_retrieval.py` — circuit breaker
- `backend/app/core/config.py` — SECRET_KEY auto-generation
- `backend/app/models/user.py` — DateTime(timezone=True)
- `backend/app/models/agent.py` — DateTime(timezone=True)
- `backend/app/models/conversation.py` — DateTime(timezone=True)
- `backend/app/models/notification.py` — DateTime(timezone=True)
- `backend/app/models/auth_event.py` — DateTime(timezone=True), server_default
- `backend/app/models/document.py` — DateTime(timezone=True)
- `backend/app/models/embedding_cache.py` — DateTime(timezone=True)
- `backend/app/models/file_index.py` — DateTime(timezone=True), removed is_stale
- `backend/app/models/repo_index.py` — DateTime(timezone=True)
- `backend/app/models/graph.py` — DateTime(timezone=True)
- `backend/app/models/storage_registry.py` — DateTime(timezone=True)
- `backend/app/models/indexing_config.py` — DateTime(timezone=True)
- `backend/app/models/path_index.py` — DateTime(timezone=True)

## Test Results

- **248/248 tests passing** (pytest -x -q --tb=short)
- Lint: All checks passed on changed files
- No regressions detected

## Self-Review Findings

- All 14 items from the quality audit are implemented
- Sub-router split maintains identical API contract (same paths, same response shapes)
- Circuit breaker has configurable thresholds (3 failures, 15s recovery)
- Thread-safe singletons use double-checked locking pattern
- DateTime standardization is backward-compatible (PostgreSQL stores timestamps identically)

## Concerns

- The migration `c00000000003` changes GIN index config from 'english' to 'simple'. This is a breaking change for existing full-text search queries that rely on English stemming. Existing data will need reindexing.
- The `downloads.py` sub-router creates ad-hoc DB sessions via `next(get_db())` for endpoints that don't use FastAPI's dependency injection cleanly. This is a pattern inconsistency but was necessary to maintain the existing endpoint signatures.
