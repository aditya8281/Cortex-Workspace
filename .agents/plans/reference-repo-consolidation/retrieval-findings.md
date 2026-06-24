# Retrieval Findings

## Mem0 — Triple-Signal Retrieval

**Pipeline (8 steps):**

1. **Preprocess:** Lemmatize query (BM25) + extract entities (NER)
2. **Embed:** Action-aware embedding (different vectors for add/search/update)
3. **Semantic search:** Over-fetch 4× or min 60 results
4. **Keyword search:** BM25 via vector store's `keyword_search()` (optional, backend-dependent)
5. **BM25 scoring:** Query-length-adaptive sigmoid normalization
   - ≤3 terms: midpoint=5.0, steepness=0.7
   - ≤6 terms: midpoint=7.0, steepness=0.6
   - ≤9 terms: midpoint=9.0, steepness=0.5
   - ≤15 terms: midpoint=10.0, steepness=0.5
   - >15 terms: midpoint=12.0, steepness=0.5
6. **Entity boost:** Query entities → entity store search → linked memory boost (max 0.5 weight)
7. **Score fusion:** `combined = (semantic + bm25 + entity_boost) / max_possible`
   - max_possible adapts: semantic only=1.0, +BM25=2.0, +entity=1.5, all three=2.5
8. **Optional reranking:** Cohere, SentenceTransformer, ZeroEntropy, LLM-based, HuggingFace

**Filter operators:** AND/OR/NOT, $gte/$lte/$gt/$lt/$eq/$neq, $in/$nin

**Key insight:** The score normalization adapts to which signals are available, not a fixed formula.

---

## Graphiti — Multi-Layer Search Architecture

**4 search layers, each independently configurable:**

| Layer | Search Methods | Rerankers |
|-------|---------------|-----------|
| EntityEdge | BM25, CosineSimilarity, BFS | RRF, NodeDistance, EpisodeMentions, MMR, CrossEncoder |
| EntityNode | BM25, CosineSimilarity, BFS | RRF, NodeDistance, EpisodeMentions, MMR, CrossEncoder |
| EpisodeNode | BM25 | RRF, CrossEncoder |
| CommunityNode | BM25, CosineSimilarity | RRF, MMR, CrossEncoder |

**Search methods:**
- **BM25:** Lucene fulltext on node names, edge facts, community summaries, episode content
- **Cosine Similarity:** Vector similarity on embeddings (entity name, edge fact)
- **BFS:** Breadth-first graph traversal from origin nodes (configurable max_depth)

**Rerankers:**
- **RRF:** Reciprocal Rank Fusion — merges rankings from multiple search methods
- **MMR:** Maximal Marginal Relevance — balances relevance with diversity (configurable lambda)
- **CrossEncoder:** Neural reranking for precision
- **NodeDistance:** Boosts edges/nodes closer to a center node
- **EpisodeMentions:** Boosts edges/nodes mentioned in more episodes

**Pre-built search recipes:**
```python
COMBINED_HYBRID_SEARCH_CROSS_ENCODER  # BM25 + cosine + BFS → cross_encoder rerank
EDGE_HYBRID_SEARCH_CROSS_ENCODER      # Edges only, same combo
EDGE_HYBRID_SEARCH_NODE_DISTANCE      # Edges, BM25 + cosine → node_distance rerank
COMMUNITY_HYBRID_SEARCH_MMR           # Communities, BM25 + cosine → MMR
```

**Search flow:**
1. Embed query → search_vector
2. For each layer: run search_methods in parallel → apply reranker → filter by min_score
3. Expand BFS from found nodes (if configured)
4. Merge results across layers
5. Return SearchResults(edges, nodes, episodes, communities) with scores

**Key insight:** Search is composable — pick methods + rerankers per layer. Not a single fixed pipeline.

---

## Cortex Current — Hybrid Retrieval V2

**Pipeline:**
1. **Vector search:** Embed query → Qdrant search with repo_id filter
2. **Fulltext search:** PostgreSQL ILIKE / trigram search on code content
3. **Graph search:** Find related nodes via graph traversal
4. **Merge + deduplicate:** Combine results, deduplicate by chunk_id
5. **Score normalization:** Normalize scores across sources
6. **Return:** RetrievalResult list with source attribution

**RAG Pipeline:**
1. `retrieve_context(query, repo_id, max_tokens=4000, max_results=8)`
2. Calls HybridRetrievalV2 with sources=["vector", "fulltext", "graph"]
3. Token budget management: accumulates until MAX_CONTEXT_TOKENS (4000)
4. Formats context with source attribution
5. Returns RAGContext (results + formatted_context + token_count + source_count)

**Fulltext search:**
- Custom suffix-stemmer for query expansion
- BM25-style scoring with configurable field weights
- Zero external dependencies

**Retrieval metrics:**
- In-memory circular buffer (max 1000 events)
- Tracks: query, result_count, sources_used, latency_ms, top_score

**What's missing:**
- No MMR diversity reranking
- No cross-encoder reranking
- No BFS graph expansion
- No entity-based boosting
- No action-aware embeddings
- No query-length-adaptive scoring
- Score normalization is basic (not adaptive to available signals)

---

## Comparative Retrieval

| Dimension | Mem0 | Graphiti | Cortex |
|-----------|------|----------|--------|
| **Search signals** | Semantic + BM25 + Entity boost | Semantic + BM25 + BFS (per layer) | Vector + Fulltext + Graph |
| **Reranking** | 5 optional rerankers | 5 rerankers (composable per layer) | None |
| **Diversity** | MMR (via reranker) | MMR (configurable lambda) | None |
| **Entity awareness** | Entity boost in scoring | BFS expansion + NodeDistance rerank | Graph traversal (basic) |
| **Score fusion** | Adaptive (depends on available signals) | RRF (reciprocal rank fusion) | Basic normalization |
| **Over-fetch** | 4× or min 60 | Configurable per layer | Not configurable |
| **Token budget** | None (returns top_k) | None (returns all above min_score) | 4000 tokens max |
| **Metrics** | None (explain mode optional) | None | In-memory circular buffer |
| **Composability** | Fixed pipeline (signals optional) | Fully composable (methods × rerankers × layers) | Fixed pipeline |
