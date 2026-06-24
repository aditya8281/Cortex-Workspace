# V2 Phase 1: Service Abstraction + Event Bus

**Duration estimate:** 5-8 days
**Dependencies:** V1 complete
**Risk:** Medium — interface design requires foresight

---

## Goals

Define Protocol interfaces for all 5 core services. Move existing implementations behind interfaces. Build in-process event bus. Decouple services through typed events. Zero behavior change — same functionality, clean boundaries.

## Deliverables

1. 5 Protocol interfaces (LLM, Embedding, VectorStore, Cache, Database)
2. Existing implementations wrapped behind interfaces
3. In-process event bus with typed events
4. Event log table in PostgreSQL
5. Event tracing with metadata
6. Services decoupled via events

## Architectural Changes

```
BEFORE:
  Agent → import → MemoryService (direct coupling)
  Agent → import → GraphService (direct coupling)
  EmbeddingService → if/elif chain for providers

AFTER:
  Agent → EventBus → MemoryService (decoupled)
  Agent → EventBus → GraphService (decoupled)
  EmbeddingService → Protocol[EmbeddingProvider] → registry
```

## Backend Changes

### New Files

| File | Purpose |
|------|---------|
| `backend/app/core/providers/__init__.py` | Provider package init |
| `backend/app/core/providers/llm.py` | `Protocol[LLMProvider]` definition |
| `backend/app/core/providers/embedding.py` | `Protocol[EmbeddingProvider]` definition |
| `backend/app/core/providers/vector_store.py` | `Protocol[VectorStore]` definition |
| `backend/app/core/providers/cache.py` | `Protocol[CacheProvider]` definition |
| `backend/app/core/providers/database.py` | `Protocol[DatabaseProvider]` definition |
| `backend/app/core/providers/registry.py` | Provider registry: `@register_provider("llm", "ollama")` |
| `backend/app/core/events/__init__.py` | Event bus package init |
| `backend/app/core/events/bus.py` | In-process event bus: publish, subscribe, trace |
| `backend/app/core/events/types.py` | Typed event definitions |
| `backend/app/core/events/tracing.py` | Event tracing + metadata |
| `backend/app/models/event_log.py` | EventLog SQLAlchemy model |
| `migrations/versions/d00000000001_event_log.py` | Event log table migration |

### Protocol Definitions

**LLMProvider:**
```python
class LLMProvider(Protocol):
    async def chat(self, messages: list[dict], model: str, **kwargs) -> str: ...
    async def stream_chat(self, messages: list[dict], model: str, **kwargs) -> AsyncGenerator: ...
    async def embed(self, text: str) -> list[float]: ...
    def list_models(self) -> list[ModelInfo]: ...
    async def health(self) -> bool: ...
```

**EmbeddingProvider:**
```python
class EmbeddingProvider(Protocol):
    async def embed(self, text: str) -> list[float]: ...
    async def embed_batch(self, texts: list[str]) -> list[list[float]]: ...
    @property
    def dimensions(self) -> int: ...
    async def health(self) -> bool: ...
```

**VectorStore:**
```python
class VectorStore(Protocol):
    async def upsert(self, collection: str, vectors: list[Vector]) -> None: ...
    async def search(self, collection: str, query: list[float], top_k: int) -> list[SearchResult]: ...
    async def delete(self, collection: str, ids: list[str]) -> None: ...
    async def list_collections(self) -> list[str]: ...
    async def health(self) -> bool: ...
```

**CacheProvider:**
```python
class CacheProvider(Protocol):
    async def get(self, key: str) -> str | None: ...
    async def set(self, key: str, value: str, ttl: int | None = None) -> None: ...
    async def delete(self, key: str) -> None: ...
    async def health(self) -> bool: ...
```

**Event Types:**
```python
@dataclass
class FileChanged: path: str; change_type: str; timestamp: float
@dataclass
class MemoryDecayed: count: int; timestamp: float
@dataclass
class IndexComplete: repo_id: int; files_indexed: int; timestamp: float
@dataclass
class EntityDiscovered: entity_id: str; entity_type: str; timestamp: float
@dataclass
class ConversationArchived: conversation_id: int; timestamp: float
@dataclass
class AgentRunComplete: run_id: int; status: str; timestamp: float
@dataclass
class JobStarted: job_id: str; job_type: str; timestamp: float
@dataclass
class JobCompleted: job_id: str; duration_ms: float; timestamp: float
@dataclass
class JobFailed: job_id: str; error: str; timestamp: float
```

### Modified Files

| File | Change |
|------|--------|
| `backend/app/services/llm/manager.py` | Implement `LLMProvider` protocol. Register via decorator. |
| `backend/app/services/embedding_service.py` | Implement `EmbeddingProvider` protocol. Register via decorator. |
| `backend/app/core/vector_db.py` | Implement `VectorStore` protocol. Register via decorator. |
| `backend/app/core/redis.py` | Implement `CacheProvider` protocol. Register via decorator. |
| `backend/app/main.py` | Initialize event bus on startup. Register providers. |

## Frontend Changes

**Minimal.** New settings page section for "Providers" showing registered LLM/embedding/vector store providers. Status indicators (green/yellow/red) for each.

## Memory Changes

Memory service subscribes to `AgentRunComplete` event. On completion, extracts facts from conversation. This is the first step toward V2 memory consolidation.

## Retrieval Changes

No changes yet. Context providers are Phase 3.

## Agent Changes

Agent loop now consumes `Protocol[LLMProvider]` instead of importing `llm_manager` directly. No behavior change — same interface, clean boundary.

## Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Protocol interface instability | Medium | High | Lock interfaces early. Version the API. |
| Event bus subtle bugs | Medium | High | Idempotent subscribers. Event tracing. Integration tests. |
| Provider registry complexity | Low | Medium | Start with decorator pattern. Keep it simple. |

## Exit Criteria

- [ ] 5 Protocol interfaces defined and documented
- [ ] Existing implementations wrapped behind interfaces
- [ ] New provider can be registered without modifying core code
- [ ] Event bus operational with typed events
- [ ] Event log table created
- [ ] Event tracing shows metadata for every event
- [ ] Services communicate via events (no new direct imports)
- [ ] All V1 tests pass
- [ ] New tests for providers, events, registry
- [ ] `make lint` + `make format` clean
