# Memory Model Findings

## Mem0 — Distilled Facts Model

**What is a memory?** A self-contained factual statement (15-80 words), extracted from conversations by an LLM. NOT a raw message.

**MemoryItem schema:**
```python
class MemoryItem(BaseModel):
    id: str                    # UUID
    memory: str                # The distilled fact text
    hash: Optional[str]        # MD5 for deduplication
    metadata: Optional[Dict]   # Arbitrary key-value
    score: Optional[float]     # Similarity score [0,1]
    created_at: Optional[str]  # ISO timestamp
    updated_at: Optional[str]  # ISO timestamp
```

**Memory types (enum):**
- `SEMANTIC` — facts, preferences, knowledge
- `EPISODIC` — events, experiences, conversations
- `PROCEDURAL` — how-to knowledge, workflows

**Storage payload per vector:**
- `data` — the fact text
- `hash` — MD5 for dedup
- `created_at` / `updated_at`
- `user_id` / `agent_id` / `run_id` — scoping (exactly one required)
- `actor_id` / `role` — who said it
- `memory_type` — semantic/episodic/procedural
- `attributed_to` — "user" or "assistant"
- Custom metadata

**Consolidation pipeline (V3 Additive):**
1. Context gathering: session scope, last N messages, existing memories
2. LLM extraction: ADD-only (LLM only extracts new facts, never deletes)
3. LLM consolidation: compares new extractions against existing memories → ADD/UPDATE/DELETE/NONE
4. Persistence: embed → create/update/delete in vector store + history DB + entity linking

**Deduplication (3 levels):**
1. Recently extracted memories (within current batch)
2. Existing memories (LLM sees scope-filtered existing memories)
3. Hash-based (MD5 stored in payload)

**History/audit trail:**
```sql
CREATE TABLE history (
    id TEXT PRIMARY KEY,
    memory_id TEXT,
    old_memory TEXT,        -- Previous text
    new_memory TEXT,        -- Updated text
    event TEXT,             -- "ADD" | "UPDATE" | "DELETE"
    created_at DATETIME,
    updated_at DATETIME,
    is_deleted INTEGER,
    actor_id TEXT,
    role TEXT
)
```

**Key insight:** Every memory mutation is recorded. Full version history of every fact.

---

## Graphiti — Bi-Temporal Entity Edge Model

**What is a memory?** A bi-temporal fact between two entities, stored as a graph edge.

**EntityEdge schema:**
```python
class EntityEdge(Edge):
    name: str                    # Relation type (e.g., "WORKS_AT")
    fact: str                    # Natural language fact
    fact_embedding: list[float]  # Vector embedding of the fact
    episodes: list[str]          # Which episodes reference this fact
    created_at: datetime         # When recorded in graph
    expired_at: datetime | None  # When invalidated (soft delete)
    valid_at: datetime | None    # When fact became true (real world)
    invalid_at: datetime | None  # When fact stopped being true
    reference_time: datetime | None  # Timestamp from producing episode
    attributes: dict[str, Any]   # Relation-type-specific properties
```

**Bi-temporal model:**
- **Valid time** (`valid_at`/`invalid_at`): When the fact was true in reality
- **Transaction time** (`created_at`/`expired_at`): When the fact was recorded/invalidated in the system

**Episodic model:**
Every raw input (message, document) becomes an `EpisodicNode` with edges to mentioned entities and facts. Episodes chain into `SagaNode` (conversation sequences).

**Community model:**
Entity clusters → `CommunityNode` with LLM-generated summaries. Enables high-level reasoning without full graph traversal.

**Key insight:** Memories are edges in a graph, not standalone records. This enables relationship-aware retrieval.

---

## Cortex Current — Typed Memory Records

**What is a memory?** A `LongTermMemory` record with category, confidence, and decay.

**LongTermMemory schema:**
```sql
long_term_memories:
    id              INTEGER PRIMARY KEY
    user_id         INTEGER FK → users
    category        VARCHAR(50)   -- preference|pattern|correction|fact|context
    title           VARCHAR(200)  -- short label
    content         TEXT          -- full content
    confidence      FLOAT         -- 0.0-1.0, starts 0.5
    access_count    INTEGER       -- how often accessed
    last_accessed_at DATETIME     -- updated on access
    source          VARCHAR(100)  -- origin
    source_id       INTEGER       -- FK to source
    embedding_id    VARCHAR(100)  -- Qdrant vector reference
    tags            JSON          -- user labels
    is_active       BOOLEAN       -- soft delete
    decayed_at      DATETIME      -- last decay timestamp
```

**Confidence mechanics:**
- Starts at 0.5
- Reinforce: +0.1 per call (capped at 1.0), increments access_count
- Decay: active memories not accessed in 30+ days → confidence *= 0.95
- Search filter: min_confidence threshold

**Knowledge entries (separate table):**
`KnowledgeEntry` records with vector embedding, consolidated from conversations via `MemoryManager.consolidate_from_conversation()`.

**Key insight:** Cortex has confidence/decay mechanics (good), but no memory consolidation, no deduplication, no version history.

---

## Comparative Memory Model

| Dimension | Mem0 | Graphiti | Cortex |
|-----------|------|----------|--------|
| **Unit of memory** | Distilled fact (text) | Bi-temporal entity edge | Typed record (category + content) |
| **Schema fields** | 7 core fields + metadata | 11 fields including temporal bounds | 13 fields including confidence/decay |
| **Storage** | Vector store payload | Graph edge properties | PostgreSQL row + Qdrant vector |
| **Type system** | Semantic / Episodic / Procedural | Entity / Episode / Community / Saga | preference / pattern / correction / fact / context |
| **Versioning** | Full audit trail (SQLite history) | Bi-temporal (invalidated edges stay) | None (overwrite on update) |
| **Confidence** | None (implicit via search score) | None (implicit via temporal recency) | Explicit (0.0-1.0, decay over time) |
| **Decay** | None | None (facts invalidated, not decayed) | Time-based (30-day threshold, ×0.95) |
| **Deduplication** | LLM-based (3 levels) | LLM-based (entity + edge dedup) | None |
| **Consolidation** | ADD/UPDATE/DELETE pipeline | Invalidation + new version | None |
| **Access tracking** | None | Implicit (episode mentions) | Explicit (access_count, last_accessed_at) |
