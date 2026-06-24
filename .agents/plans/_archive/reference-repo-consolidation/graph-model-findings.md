# Graph Model Findings

## Mem0 — Entity Store (Vector-Based Pseudo-Graph)

Mem0 does NOT use a graph database. It implements entity linking via a second vector store collection.

**How it works:**
1. LLM extracts entities from memory text (spaCy NER or regex)
2. Entities stored in a separate vector collection (`{provider}_{name}_entities`)
3. Each entity has `linked_memory_ids` pointing to memories mentioning it
4. During search, entities in the query boost matching memories

**Entity upsert logic:**
- Embed entity text → search entity store (similarity >= 0.95 = same entity)
- If match: append `memory_id` to `linked_memory_ids`
- If no match: create new entity record

**Entity boosting during search:**
```python
ENTITY_BOOST_WEIGHT = 0.5
boost = similarity × 0.5 × (1 / (1 + 0.001 × (num_linked - 1)²))
```
- More linked memories → lower individual boost (prevents hub bias)
- Boosts aggregated: memory_id → max(boost) across all query entities

**Limitation:** One-hop only. No multi-entity relationship traversal. No path queries.

---

## Graphiti — True Temporal Knowledge Graph

**Graph DB:** Neo4j (primary), FalkorDB, Kuzu, Neptune (via driver abstraction)

**Node types:**
| Type | Purpose | Key Properties |
|------|---------|----------------|
| EntityNode | Real-world entities | uuid, name, name_embedding, group_id, labels, summary, attributes |
| EpisodeNode | Raw input episodes | uuid, content, source, source_description, valid_at, entity_edges |
| CommunityNode | Cluster summaries | uuid, name, name_embedding, summary, group_id |
| SagaNode | Episode sequences | uuid, name, summary, first/last_episode_uuid, summarization watermarks |

**Edge types:**
| Type | Relationship | Source → Target |
|------|-------------|-----------------|
| EntityEdge | RELATES_TO | Entity → Entity |
| EpisodicEdge | MENTIONS | Episode → Entity |
| CommunityEdge | HAS_MEMBER | Community → Entity |
| HasEpisodeEdge | HAS_EPISODE | Saga → Episode |
| NextEpisodeEdge | NEXT_EPISODE | Episode → Episode |

**Bi-temporal properties on EntityEdge:**
- `valid_at` / `invalid_at` — real-world time bounds
- `created_at` / `expired_at` — system time bounds
- `reference_time` — timestamp from producing episode

**Index strategy:**
- Range indices: uuid, group_id, created_at, temporal fields
- Fulltext indices: entity names, edge facts, community summaries, episode content

**Cypher patterns:**
```cypher
-- Entity save (MERGE pattern)
MERGE (n:Entity {uuid: $uuid})
SET n += $entity_data

-- Edge save
MERGE (source:Entity {uuid: $source_uuid})
MERGE (target:Entity {uuid: $target_uuid})
MERGE (source)-[e:RELATES_TO {uuid: $edge_uuid}]->(target)
SET e += $edge_data
```

**Community detection:** Label propagation algorithm → CommunityNode with LLM summary → HAS_MEMBER edges to entities.

---

## Cortex Current — PostgreSQL Code Graph

**Graph DB:** PostgreSQL (SQLAlchemy ORM)

**Node model (`graph_nodes`):**
| Field | Type | Notes |
|-------|------|-------|
| chunk_id | FK → code_chunks | Links to code chunk |
| repo_id | FK → repo_indexes | Scoped to repo |
| node_type | String(50) | function, class, struct, enum, trait |
| name | String(500) | Symbol name |
| qualified_name | String(1000) | Fully qualified name |
| file_path | String(2048) | Source file |
| language | String(50) | Programming language |
| embedding_id | String(128) | Qdrant vector reference |
| start_line / end_line | Integer | Source location |

**Edge model (`graph_edges`):**
| Field | Type | Notes |
|-------|------|-------|
| source_id | FK → graph_nodes | Source node |
| target_id | FK → graph_nodes | Target node |
| edge_type | String(50) | calls, imports, inherits, contains |
| weight | Integer | Relationship strength |
| first_seen / last_seen | DateTime | Temporal tracking |

**Graph builder:** Regex-based extraction (imports, function calls, inheritance). Full rebuild per repo (clear + recreate).

**Cross-file search:** Embed query → Qdrant search → lookup GraphNodes → traverse edges for relationship context.

**Limitation:** Code-structure graph only. No semantic/conversational entities. No temporal knowledge beyond first_seen/last_seen.

---

## Comparative Graph Model

| Dimension | Mem0 | Graphiti | Cortex |
|-----------|------|----------|--------|
| **Graph DB** | None (vector store) | Neo4j / FalkorDB / Kuzu / Neptune | PostgreSQL (SQL) |
| **Node types** | 1 (entity, implicit) | 4 (Entity, Episode, Community, Saga) | 1 (GraphNode = code symbol) |
| **Edge types** | 1 (entity → memory_ids) | 5 (RELATES_TO, MENTIONS, HAS_MEMBER, HAS_EPISODE, NEXT_EPISODE) | 4 (calls, imports, inherits, contains) |
| **Temporal model** | None | Bi-temporal (valid/invalid + created/expired) | first_seen/last_seen only |
| **Contradiction handling** | None | Automatic invalidation | None |
| **Community detection** | None | Label propagation + LLM summaries | None |
| **Traversal** | One-hop (entity → memories) | Multi-hop via Cypher | SQL JOINs (limited) |
| **Entity extraction** | spaCy NER + regex | LLM-based NER + dedup | Regex only |
| **Multi-tenancy** | user_id/agent_id/run_id filters | group_id partitioning | repo_id scoping |
| **Semantic search** | Entity embeddings + boost | Entity name_embedding + fact_embedding | Node embedding_id (Qdrant) |
