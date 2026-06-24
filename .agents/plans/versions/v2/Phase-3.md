# V2 Phase 3: Memory Consolidation + Context Providers + Config

**Duration estimate:** 7-10 days
**Dependencies:** V2 Phase 1 (event bus), V2 Phase 2 (MCP)
**Risk:** High — memory consolidation quality directly affects reliability

---

## Goals

Build the memory consolidation pipeline (LLM extraction, 3-level dedup, contradiction detection, bi-temporal tracking). Replace monolithic hybrid_retrieval.py with composable context providers. Add PersistentConfig, model routing, retrieval enhancements.

## Deliverables

1. Memory consolidation pipeline (extract → dedup → contradict → merge)
2. LLM-based entity extraction (replaces regex)
3. Bi-temporal knowledge tracking (valid_at/invalid_at)
4. Context provider architecture (composable, token-budgeted)
5. PersistentConfig (env → DB → user hierarchy)
6. Model routing (right model for right task)
7. Retrieval enhancements (adaptive normalization, entity boosting)

## Architectural Changes

```
BEFORE:
  Memory = manual CRUD + confidence decay
  Retrieval = monolithic hybrid_retrieval.py

AFTER:
  Memory = automated pipeline: extract → dedup → contradict → merge → decay
  Retrieval = composable context providers, each token-budgeted
```

## Backend Changes

### New Files

| File | Purpose |
|------|---------|
| `backend/app/services/memory/__init__.py` | Memory pipeline package |
| `backend/app/services/memory/consolidator.py` | Main pipeline orchestrator |
| `backend/app/services/memory/extractor.py` | LLM-based fact extraction |
| `backend/app/services/memory/deduplicator.py` | 3-level dedup (batch, vector, hash) |
| `backend/app/services/memory/contradictor.py` | Contradiction detection + invalidation |
| `backend/app/services/memory/bitemporal.py` | Bi-temporal tracking (valid_at/invalid_at) |
| `backend/app/services/context/__init__.py` | Context provider package |
| `backend/app/services/context/provider.py` | `Protocol[ContextProvider]` |
| `backend/app/services/context/manager.py` | Budget allocation + composition |
| `backend/app/services/context/memory_provider.py` | Memory → context |
| `backend/app/services/context/graph_provider.py` | Graph → context |
| `backend/app/services/context/search_provider.py` | Search → context |
| `backend/app/services/context/vault_provider.py` | Vault files → context |
| `backend/app/services/context/conversation_provider.py` | Conversation history → context |
| `backend/app/services/config/persistent.py` | PersistentConfig: env → DB → user |
| `backend/app/services/routing/model_router.py` | Model routing rules |
| `backend/app/models/user_config.py` | UserConfig + SystemConfig models |
| `backend/app/models/event_log.py` | Already created in Phase 1 |
| `migrations/versions/d00000000003_memory_pipeline.py` | Memory pipeline schema changes |
| `migrations/versions/d00000000004_config_tables.py` | Config tables |
| `migrations/versions/d00000000005_routing_rules.py` | Model routing rules table |

### Memory Consolidation Pipeline

```
Content indexed / Conversation archived
  │
  ▼
Event Bus: index_complete / conversation_archived
  │
  ▼
Extractor (LLM) → new facts[]
  │
  ▼
Deduplicator (3-level)
  ├─ Batch-level: within extraction, embedding similarity
  ├─ Existing: vs stored memories, vector similarity
  └─ Exact: hash-based match
  │
  ▼
Contradictor → compare new facts vs existing
  ├─ No contradiction → proceed
  └─ Contradiction found → invalidate old (set invalid_at)
  │
  ▼
Merger → consolidate duplicates, keep highest confidence
  │
  ▼
Confidence assigner → initial confidence + decay formula
  │
  ▼
Store in long_term_memory (with valid_at/invalid_at)
```

### Context Provider Protocol

```python
class ContextProvider(Protocol):
    name: str
    priority: int  # Higher = more important for budget allocation

    async def gather(
        self, query: str, token_budget: int
    ) -> list[ContextChunk]: ...

    def token_count(self, chunks: list[ContextChunk]) -> int: ...
```

### PersistentConfig Hierarchy

```
Environment Variables (highest priority)
  ↓ override
Database SystemConfig (admin settings)
  ↓ override
Database UserConfig (per-user preferences)
  ↓ override
Code Defaults (lowest priority)
```

### Model Routing

| Task Type | Model Selection |
|-----------|----------------|
| Agent conversation | User's preferred model |
| Memory extraction | Cheaper/faster model (configurable) |
| Context compaction | Cheaper/faster model |
| Embedding | ONNX/Ollama (existing) |
| Entity extraction | Cheaper/faster model |
| Completion verification | Same as agent model |

## Frontend Changes

| Page | Change |
|------|--------|
| Settings | New "Providers" section with model routing rules |
| Settings | New "Preferences" section with PersistentConfig UI |
| Memory | Show consolidation status (last run, facts extracted, duplicates removed) |
| Memory | Show bi-temporal: valid_from / valid_until on memories |

## Memory Changes

**This IS the memory phase.** Summary:
- LLM extraction replaces regex
- 3-level deduplication
- Contradiction detection + invalidation
- Bi-temporal tracking
- Automated pipeline via event bus

## Retrieval Changes

Monolithic hybrid_retrieval.py → composable context providers. Each provider is independent, token-budgeted, composable. Agent loop consumes providers, not a single pipeline.

## Agent Changes

Agent loop now uses ContextManager (composable providers) instead of hardcoded retrieval. Model routing selects appropriate model per task.

## Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| LLM extraction quality | Medium | High | Use proven prompts. Validate against real conversations. |
| Dedup false positives | Medium | High | Conservative thresholds. Allow manual review. |
| Context provider regression | Medium | High | Feature flag for old vs new retrieval. A/B test. |
| Config hierarchy complexity | Low | Medium | Simple override chain. Well-documented. |

## Exit Criteria

- [ ] Memory consolidation pipeline runs on event triggers
- [ ] LLM extraction produces quality facts
- [ ] 3-level dedup prevents duplicates
- [ ] Contradiction detection invalidates old facts
- [ ] Bi-temporal tracking works (valid_at/invalid_at)
- [ ] Context providers are composable and token-budgeted
- [ ] PersistentConfig hierarchy works (env → DB → user)
- [ ] Model routing selects appropriate models
- [ ] Retrieval enhancements improve search quality
- [ ] All V1 + V2 Phase 1-2 tests pass
- [ ] New memory pipeline + context provider tests
- [ ] `make lint` + `make format` clean
