# V6 Phase 2: Graph Intelligence + Cross-Encoder Reranking

**Duration estimate:** 10-14 days
**Dependencies:** V6 Phase 1 (marketplace, workflows)
**Risk:** HIGH — graph intelligence is research-heavy, cross-encoder adds inference cost

---

## Goals

Elevate the knowledge graph from passive storage to active intelligence. Add graph reasoning (inference, community detection, importance scoring). Add cross-encoder reranking for dramatically better search quality. Make Cortex's retrieval world-class.

## Deliverables

1. Graph intelligence engine (reasoning, inference, community detection)
2. Cross-encoder reranking (2-stage retrieval: recall → rerank)
3. Graph-aware context selection (agent uses graph for context)
4. Entity importance scoring (PageRank-like for knowledge graph)
5. Community detection (cluster related entities)
6. Graph reasoning (infer new relationships from existing ones)
7. Reranking UI (show why results ranked as they are)
8. Search quality metrics dashboard

## Architectural Changes

```
BEFORE:
  Graph = storage + basic traversal
  Retrieval = vector similarity → RRF merge → MMR diversity

AFTER:
  Graph = intelligence (reasoning, inference, communities, importance)
  Retrieval = vector recall → cross-encoder rerank → graph-aware selection
  Search quality = measurable, optimizable, visible to user
```

## Backend Changes

### New Files

| File | Purpose |
|------|---------|
| `backend/app/services/graph/intelligence/__init__.py` | Graph intelligence package |
| `backend/app/services/graph/intelligence/reasoner.py` | Graph reasoning engine |
| `backend/app/services/graph/intelligence/community.py` | Community detection (Louvain/Leiden) |
| `backend/app/services/graph/intelligence/importance.py` | Entity importance (PageRank) |
| `backend/app/services/graph/intelligence/inferencer.py` | Relationship inference |
| `backend/app/services/graph/intelligence/explainer.py` | Explain entity connections |
| `backend/app/services/retrieval/__init__.py` | Retrieval package (replaces hybrid_retrieval.py) |
| `backend/app/services/retrieval/recall.py` | Stage 1: multi-source recall |
| `backend/app/services/retrieval/reranker.py` | Stage 2: cross-encoder reranking |
| `backend/app/services/retrieval/graph_selector.py` | Stage 3: graph-aware selection |
| `backend/app/services/retrieval/quality.py` | Search quality metrics |
| `backend/app/services/retrieval/models.py` | Retrieval data models |
| `backend/app/services/models/reranker.py` | Cross-encoder model management |
| `backend/app/api/v1/graph_intelligence.py` | Graph intelligence API |
| `backend/app/api/v1/search_v2.py` | Enhanced search API with reranking |
| `migrations/versions/d00000000013_graph_intelligence.py` | Graph intelligence tables |

### Graph Intelligence Engine

```python
class GraphIntelligence:
    """Active intelligence layer on top of knowledge graph."""

    async def reason(self, query: str) -> list[Inference]:
        """Infer new relationships from existing graph structure."""
        # Pattern: if A works_at B, and B located_in C, then A located_in C
        # Pattern: if A emailed B frequently, and B works_at C, then A knows about C
        ...

    async def detect_communities(self) -> list[Community]:
        """Detect clusters of related entities."""
        # Leiden algorithm for community detection
        # Each community = group of closely related entities
        ...

    async def score_importance(self) -> dict[str, float]:
        """Score entity importance (PageRank-like)."""
        # Entities with many connections = more important
        # Entities connected to important entities = more important
        # Temporal decay: recently active = more important
        ...

    async def explain_connection(self, entity_a: str, entity_b: str) -> Explanation:
        """Explain how two entities are connected."""
        # Find shortest path
        # Explain each edge in the path
        # Show strength of connection
        ...

    async def infer_relationships(self, entity: str) -> list[InferredRelationship]:
        """Infer new relationships for an entity."""
        # Based on patterns in graph
        # Based on co-occurrence in documents
        # Based on communication patterns
        ...
```

### Cross-Encoder Reranking

```python
class CrossEncoderReranker:
    """Two-stage retrieval: recall → rerank with cross-encoder."""

    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        self.model = CrossEncoder(model_name)

    async def rerank(
        self,
        query: str,
        candidates: list[SearchResult],
        top_k: int = 10,
    ) -> list[RankedResult]:
        """Rerank candidates using cross-encoder."""
        # 1. Score each (query, document) pair
        pairs = [(query, c.content) for c in candidates]
        scores = self.model.predict(pairs)

        # 2. Sort by score
        ranked = sorted(
            zip(candidates, scores),
            key=lambda x: x[1],
            reverse=True
        )

        # 3. Return top_k with scores
        return [
            RankedResult(
                content=c.content,
                score=float(s),
                original_score=c.score,
                rerank_delta=float(s) - c.score,
                source=c.source,
            )
            for c, s in ranked[:top_k]
        ]
```

### Enhanced Retrieval Pipeline

```
User Query
  │
  ▼
Stage 1: Recall (multi-source)
  ├─ Vector search (top 50)
  ├─ Fulltext search (top 50)
  ├─ Graph traversal (related entities, top 20)
  ├─ Memory search (top 20)
  └─ Document search (top 20)
  │
  ▼
Merge + dedup (RRF) → ~100 candidates
  │
  ▼
Stage 2: Cross-Encoder Rerank
  └─ Score each (query, candidate) pair → top 20
  │
  ▼
Stage 3: Graph-Aware Selection
  ├─ Boost entities with high importance score
  ├─ Boost entities in active communities
  ├─ Apply recency bias
  └─ Ensure diversity (no single entity dominates)
  │
  ▼
Final Results (top 10) + Explainability
```

### Search Quality Metrics

```python
class SearchQualityMetrics:
    """Track and expose search quality metrics."""

    async def record_search(
        self,
        query: str,
        results: list[RankedResult],
        clicked: list[int] | None = None,  # Which results user clicked
        dwell_time: dict[int, float] | None = None,  # Time spent on each
    ) -> None:
        """Record search event for quality tracking."""
        ...

    async def get_metrics(self, period: str = "7d") -> QualityReport:
        """Get quality metrics for a time period."""
        return QualityReport(
            total_searches=self._count_searches(period),
            avg_click_position=self._avg_click_position(period),
            zero_result_rate=self._zero_result_rate(period),
            avg_results_clicked=self._avg_clicks(period),
            improvement_over_baseline=self._compare_baseline(period),
        )
```

## Frontend Changes

| Page | Change |
|------|--------|
| Search | Cross-encoder reranking (dramatically better results) |
| Search | Explainability panel (why each result was ranked) |
| Graph | Community visualization (colored clusters) |
| Graph | Entity importance (size = importance) |
| Graph | Reasoning results (inferred relationships) |
| Settings | Reranker model selection |
| New: /search/quality | Search quality dashboard |

### Search — Explainability Panel

```
┌─────────────────────────────────────────────────┐
│ 🔍 "memory consolidation pipeline"              │
├─────────────────────────────────────────────────┤
│                                                 │
│ 1. Memory Consolidation Pipeline — design.md    │
│    Score: 0.95 (reranked from #3)              │
│    Why: Exact title match + graph connection    │
│    to 12 related entities                       │
│    [Show path] [Why ranked here?]               │
│                                                 │
│ 2. Phase 3: Memory Consolidation — Phase-3.md   │
│    Score: 0.92 (reranked from #1)              │
│    Why: Direct content match + high importance  │
│    entity (you authored this)                   │
│    [Show path] [Why ranked here?]               │
│                                                 │
│ 3. Memory Deduplication — deduplicator.py       │
│    Score: 0.88 (reranked from #5)              │
│    Why: Related via graph edge "part_of" to #1  │
│    [Show path] [Why ranked here?]               │
│                                                 │
│ Quality: 95% relevance | Source: 4 documents   │
│ Time: 120ms (recall: 80ms, rerank: 40ms)       │
└─────────────────────────────────────────────────┘
```

### Graph — Community Visualization

```
┌─────────────────────────────────────────────────┐
│ 🔗 Knowledge Graph                              │
├─────────────────────────────────────────────────┤
│ View: [Entities] [Communities] [Reasoning]       │
│                                                 │
│     ┌─────────────────────────────┐             │
│     │    🔵 Memory Cluster       │             │
│     │   ┌───┐ ┌───┐ ┌───┐       │             │
│     │   │mem│──│ded│──│ext│       │             │
│     │   └─┬─┘ └───┘ └─┬─┘       │             │
│     │     │            │         │             │
│     │   ┌─┴─┐      ┌──┴──┐      │             │
│     │   │con│      │bi-  │      │             │
│     │   │tra│      │temp │      │             │
│     │   └───┘      └─────┘      │             │
│     └─────────────────────────────┘             │
│                                                 │
│  Communities: Memory (5), Agent (8), Graph (4)  │
│  Inferred: 3 new relationships found            │
│  [Show Inferred] [Reason About...]              │
└─────────────────────────────────────────────────┘
```

### Search Quality Dashboard

```
┌─────────────────────────────────────────────────┐
│ 📊 Search Quality                               │
├─────────────────────────────────────────────────┤
│ Period: [Last 7 days ▼]                         │
│                                                 │
│ Total searches: 234                             │
│ Avg results clicked: 2.3                        │
│ Avg click position: 1.8                         │
│ Zero-result rate: 3%                            │
│                                                 │
│ Relevance trend:                                │
│ ████████████████████░░  92% (↑5% from baseline) │
│                                                 │
│ Top queries:                                    │
│ 1. "memory consolidation" — 100% relevance      │
│ 2. "agent loop" — 95% relevance                 │
│ 3. "embeddings" — 90% relevance                 │
│                                                 │
│ Cross-encoder impact:                           │
│ Without rerank: 78% relevance                   │
│ With rerank: 92% relevance (+18%)              │
└─────────────────────────────────────────────────┘
```

## Memory Changes

Graph intelligence feeds back into memory. Inferred relationships stored as new graph edges with confidence scores. Community detection used for memory organization.

## Retrieval Changes

This IS the retrieval phase. Monolithic hybrid_retrieval.py replaced with:
1. Recall stage (multi-source)
2. Cross-encoder reranking
3. Graph-aware selection
4. Quality measurement

## Agent Changes

Agent uses enhanced retrieval for context building. Graph reasoning provides additional context. Explainability helps agent understand why it has certain information.

## Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Cross-encoder latency | High | Medium | Use small model (MiniLM). Batch inference. Cache scores. |
| Graph inference errors | Medium | Medium | Confidence thresholds. Human review for low-confidence inferences. |
| Community detection quality | Medium | Low | Leiden algorithm is well-tested. Visual verification. |
| Search quality regression | Medium | High | A/B testing. Quality metrics. Rollback capability. |
| Model download size | Medium | Low | Bundle cross-encoder with app. Lazy loading. |

## Exit Criteria

- [ ] Cross-encoder reranking improves search quality
- [ ] Graph communities detected and visualized
- [ ] Entity importance scoring works
- [ ] Graph reasoning infers new relationships
- [ ] Explainability panel shows ranking reasons
- [ ] Search quality dashboard shows metrics
- [ ] Reranker configurable (model selection)
- [ ] All V1-V6 Phase 1 tests pass
- [ ] New graph intelligence + reranking tests
- [ ] `make lint` + `make format` clean
- [ ] Search quality baseline established and documented
