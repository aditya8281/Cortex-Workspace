# Batch 2 — Indexing, Retrieval & Search Architecture Findings

**Date:** 2026-06-25
**Repos:** LlamaIndex, sist2, turbovec
**Focus:** Indexing architecture, retrieval pipelines, chunking strategies, search systems, ranking, metadata, incremental indexing, vector storage, embedding strategies, context assembly

---

## LlamaIndex — The Composable RAG Framework

### Architecture Summary

LlamaIndex is a **composable RAG framework** with ~27 integration categories. The core is intentionally lean (~30 direct deps). Everything vendor-specific lives in `llama-index-integrations/` as separate pip packages.

```
Document → [NodeParser] → [TextNode]
QueryBundle → [Retriever] → [NodeWithScore]
[NodeWithScore] → [Postprocessor] → [NodeWithScore]
[NodeWithScore] → [Synthesizer] → Response
```

**Key insight:** LlamaIndex's power is in the composition — every stage is swappable via ABCs, and the pipeline is assembled from independent components.

### Chunking Strategies (13 implementations)

| Strategy | Approach | Best For |
|----------|----------|----------|
| **TokenSplitter** | tiktoken token count with overlap | General text |
| **SentenceSplitter** | NLTK sentence tokenizer + token-aware splitting | Natural language |
| **SentenceWindowNodeParser** | Individual sentences with surrounding window | Precise retrieval |
| **SemanticSplitterNodeParser** | Splits at embedding-distance boundaries | Topic-segmented content |
| **SemanticDoubleMergingSplitter** | Two-pass: merge within sections, then across | Hierarchical docs |
| **CodeSplitter** | Tree-sitter AST-aware splitting | Code files |
| **MarkdownNodeParser** | Markdown headers → hierarchical nodes | Documentation |
| **HTMLNodeParser** | HTML structure-aware parsing | Web content |
| **JSONNodeParser** | JSON structure → nodes | Structured data |
| **HierarchicalNodeParser** | Multi-level chunks with parent-child relationships | Large documents |
| **LangChainSplitterAdapter** | Wraps any LangChain text splitter | Compatibility |

**Key design decisions:**
- `TextNode` carries `NodeRelationship` metadata (PARENT, NEXT, PREV, SOURCE)
- HierarchicalNodeParser creates parent-child relationships enabling AutoMergingRetriever
- SentenceWindowNodeParser stores individual sentences but retrieves with surrounding context
- SemanticSplitter uses embedding distance to find natural break points

### Retrieval Architecture (6 retriever types)

| Retriever | Pattern | When to Use |
|-----------|---------|-------------|
| **VectorIndexRetriever** | Embed query → vector store query → NodeWithScore | Default single-source |
| **QueryFusionRetriever** | Fan-out to multiple retrievers + RRF/relative-score fusion | Hybrid multi-source |
| **RecursiveRetriever** | Follows node references (IndexNode → referenced objects) | Object/tool lookup |
| **AutoMergingRetriever** | Collapses child chunks to parent when enough children retrieved | Hierarchical chunking |
| **RouterRetriever** | LLM selects which sub-retriever to use | Multi-index routing |
| **TransformRetriever** | Pre-processes queries before retrieval | Query expansion |

### Hybrid Search (3 fusion modes)

```python
class FUSION_MODES(str, Enum):
    RECIPROCAL_RANK = "reciprocal_rerank"    # RRF (k=60)
    RELATIVE_SCORE = "relative_score"         # Relative score fusion
    DIST_BASED_SCORE = "dist_based_score"     # Distance-based fusion
```

**QueryFusionRetriever** also generates LLM-based query variants from the original, enabling multi-query fusion.

### Response Synthesis (7 modes)

| Mode | Approach | When to Use |
|------|----------|-------------|
| **CompactAndRefine** | Stuff nodes → iteratively refine answer | DEFAULT |
| **Refine** | Original iterative refinement | Detailed answers |
| **TreeSummarize** | Recursive summarization up a tree | Large context sets |
| **SimpleSummarize** | Single-pass summarization | Quick answers |
| **Accumulate** | Combine per-node answers | Multi-doc aggregation |
| **Generation** | No context, LLM only | Creative/factual |
| **Compact** | Stuff only, no refinement | Speed priority |

### Post-Processing (reranking strategies)

| Postprocessor | Type | Notes |
|---------------|------|-------|
| **SentenceTransformerRerank** | Neural | Local model reranking |
| **CohereRerank** | API | Cloud reranking |
| **JinaRerank** | API | Cloud reranking |
| **FlashRank** | Lightweight | Fast approximate reranking |
| **LLMRerank** | LLM-based | LLM judges relevance |
| **RankGPTRerank** | LLM-based | GPT-based reranking |
| **KeywordNodePostprocessor** | Metadata | Adds keyword metadata |
| **MetadataReplacementPostprocessor** | Metadata | Replaces node text with metadata |
| **TimeObjectivePostprocessor** | Recency | Boosts recent documents |
| **EmbeddingOptimizer** | Embedding | Optimizes embeddings for better retrieval |

### Ingestion Pipeline (Incremental Indexing)

```python
pipeline = IngestionPipeline(
    transformations=[SentenceSplitter(), KeywordExtractor()],
    docstore=docstore,
    cache=IngestionCache(),  # Hash-based transform caching
)
```

**DocstoreStrategy:**
- `UPSERT` — Insert new, update existing
- `UPSERT_DEDUPLICATES` — Insert new, skip duplicates
- `DELETE` — Delete removed, insert new
- `UPDATES` — Track and apply only changes

**IngestionCache:** Hash-based caching of transform results. Re-runs skip already-processed transforms when input hasn't changed.

### Storage Model

**StorageContext** orchestrates persistence:
- `docstore` — Node content + metadata (key → JSON)
- `index_store` — Index structure metadata
- `vector_stores` — Named vector stores (default + namespaced)
- `graph_store` — Knowledge graph triples
- `property_graph_store` — Labeled property graph

Default: in-memory `SimpleKVStore` (serialized as JSON). 70+ external backends via integrations.

### What Cortex Can Learn from LlamaIndex

1. **Composable pipeline architecture** — Every stage (chunking, retrieval, reranking, synthesis) is swappable via ABCs
2. **Hierarchical chunking with parent-child** — Enables AutoMergingRetriever to collapse to parent context
3. **SentenceWindow retrieval** — Store individual sentences, retrieve with surrounding context
4. **IngestionCache** — Hash-based transform caching avoids redundant computation
5. **Multi-query fusion** — LLM generates query variants, each retriever runs independently, results fused
6. **70+ vector store backends** — Proves the value of vector store abstraction

---

## sist2 — Self-Contained File Search Engine

### Architecture Summary

sist2 is a **C-first file indexer** with embedded SQLite FTS5 search. No external DB required. Scan → Index → Web three-phase architecture.

```
walk_directory → parse(file) → .sist2 SQLite DB → FTS5 search / ES bulk index
```

**Key design decisions:**
- C binary, no runtime dependencies (SQLite embedded)
- Two-phase: scan (parse + extract) separated from index (search engine ingestion)
- Virtual file abstraction (`vfile_t`) for transparent archive-inside-archive scanning
- Metadata as linked list during parsing, serialized to JSON at write time
- FTS5 as first-class search engine (no Elasticsearch needed for medium-scale)

### Indexing Pipeline

**Phase 1: Scan** (`sist2 scan`)
- `nftw()` recursive directory traversal with depth limit
- PCRE exclusion regex + .gitignore-style ignore list
- Thread pool for parallel parsing
- MIME detection: extension lookup → libmagic fallback
- Incremental: mtime-based change detection (if mtime unchanged → SKIP)

**Phase 2: Index** (`sist2 index` or `sist2 sqlite-index`)
- SQLite: Attaches scan DB to search DB, builds FTS5 virtual table
- Elasticsearch: Bulk indexes all documents via HTTP API

### File Type Support (15+ parsers)

| Category | Formats | Parser |
|----------|---------|--------|
| Text | .txt, .log, .csv, .ini | parse_text |
| Markup | .html, .xml, .xhtml, .svg | parse_markup |
| Ebooks | .pdf, .xps, .fb2, .epub | parse_ebook (MuPDF) |
| Office | .docx, .xlsx, .pptx | parse_ooxml |
| Office Legacy | .doc, .wpd | parse_msdoc, parse_wpd |
| Media | .mp4, .avi, .mkv, .mp3, .flac | parse_media (FFmpeg) |
| Raw Images | .cr2, .nef, .arw, .dng | parse_raw |
| Comics | .cbr, .cbz | parse_comic |
| MOBI | .mobi, .prc | parse_mobi |
| Fonts | .ttf, .otf, .woff | parse_font |
| Archives | .zip, .tar, .7z, .rar | parse_archive (libarchive, recursive) |
| JSON | .json, .ndjson | parse_json, parse_ndjson |
| OCR | Any image/ebook | Tesseract overlay |

### Search Pipeline (SQLite FTS5 Backend)

**FTS5 query:**
```sql
SELECT doc.*, rank
FROM document_view doc
WHERE search MATCH ?1
  AND index_id IN (...)
  AND path = @path OR path GLOB @path_glob
  AND size BETWEEN @size_min AND @size_max
  AND mtime BETWEEN @date_min AND @date_max
  AND mime IN (...)
ORDER BY rank DESC
```

**BM25 weights:** `bm25(8, 3, 8, 5)` — name=8, content=3, title=8, path=5

**Sort modes:** Score, Size, Mtime, Random, Name, ID, Embedding (brute-force cosine)

**Filter operators:** Path glob, size range, date range, MIME type, tags, index ID

**Keyset pagination** via `after_cursor` (sort_var, doc.ROWID)

### Metadata System

Captured per file as linked list of `meta_line_t` during parsing:
- **String:** content, title, author, modified_by, artist, album, genre, codecs, EXIF fields, font_name
- **Numeric:** width, height, duration, bitrate, pages
- **Structural:** name, path, extension, size, mtime, tags, checksum

### Embedding/Vector Support

- Embeddings stored as BLOB of float32 in `embedding` table
- Cosine similarity via OpenBLAS `cblas_sdot` + `cblas_snrm2`
- Registered as custom SQLite function
- SQLite backend: brute-force O(n) scan
- ES backend: HNSW approximate kNN (ES 8.x+)
- Generation via external user scripts (not built-in)

### Incremental Indexing

**mtime-based change detection:**
```
IF exists AND mtime matches → SKIP
IF exists AND mtime differs → UPDATE (re-parse)
IF not exists → INSERT (new)
```

After scan: unmarked documents → `delete_list` → removed during index

### What Cortex Can Learn from sist2

1. **Two-phase scan/index separation** — Decouple parsing from indexing for better incremental support
2. **Virtual file abstraction** — Transparent archive-inside-archive scanning via vfile_t
3. **FTS5 as first-class search** — SQLite FTS5 is viable for medium-scale without Elasticsearch
4. **mtime-based incremental** — Simpler and faster than hash-based for change detection
5. **Metadata as linked list** — Accumulate metadata during parsing, serialize once at write time
6. **User script extensibility** — Embedding generation via external scripts, not hardcoded providers
7. **15+ file parsers** — Comprehensive format support via libscan library

---

## turbovec — Scalar-Quantized Vector Search

### Architecture Summary

TurboVec is a **pure scalar-quantized vector search library** (Rust + Python bindings). It implements TurboQuant — 2/3/4-bit compression with SIMD-accelerated flat scan. The bet: aggressive quantization + fast SIMD scan beats approximate graph search.

```
FP32 vectors → Normalize → Random Rotate → TQ+ Calibrate → Lloyd-Max Quantize → Bit-Pack
Search: Query → LUT → SIMD nibble scan → Top-k heap
```

### Quantization Pipeline

1. **Normalize** — Unit vector + store norm
2. **Random Rotation** — Fixed orthogonal matrix (makes coordinates Beta-distributed)
3. **TQ+ Calibration** — Per-coordinate shift+scale (first add only, frozen after)
4. **Lloyd-Max Quantization** — 4/8/16 levels for 2/3/4-bit (analytically derived from Beta distribution — no training)
5. **Bit-Pack** — SIMD-blocked layout (x86: perm0-interleaved; ARM: sequential)
6. **Scale Store** — RaBitQ length-renormalization correction

### Performance Characteristics

| Bit Width | Compression (d=1536) | Recall vs FAISS PQ |
|-----------|---------------------|-------------------|
| 4-bit | ~8× (736 bytes/vector) | +0.2–1.9pp at R@1 |
| 2-bit | ~16× (370 bytes/vector) | Tied with FAISS |
| 3-bit | ~10× | Between 2 and 4 |

**No HNSW/IVF** — Flat sequential scan over compressed data. No training, no index construction time.

### SIMD Kernels

| Kernel | Architecture | Notes |
|--------|-------------|-------|
| AVX-512BW | x86 Sapphire Rapids+ | Pair-of-blocks processing |
| AVX2 | x86 Haswell+ | FAISS-style perm0 layout |
| NEON | AArch64 | Sequential layout |
| Scalar | Any | Pre-AVX2 fallback |

### Incremental Add

- `add(vectors)` — Encode + pack + append (no rebuild)
- TQ+ calibration frozen after first add
- Codebooks are analytical (Beta distribution) — no retraining
- `swap_remove(i)` — O(1) delete
- `IdMapIndex` — Stable external ID mapping

### Integration Points

Drop-in replacements for:
- LangChain `InMemoryVectorStore`
- LlamaIndex `SimpleVectorStore`
- Haystack `InMemoryDocumentStore`
- Agno `LanceDb`

### What Cortex Can Learn from turbovec

1. **Quantized vector storage** — 8-16× compression with comparable recall. Critical for desktop-first (limited disk/RAM).
2. **Flat scan over compressed data** — Simpler than HNSW, no training phase, no index construction time.
3. **Incremental add without rebuild** — New vectors appended, no graph restructuring.
4. **Platform-specific SIMD** — Runtime CPU detection for optimal kernel selection.
5. **No training dependency** — Codebooks derived analytically from Beta distribution.

---

## Cortex Current Systems (Precise Implementation Details)

### Indexing Pipeline

**Two-track system:**
1. **Batch (IncrementalIndexer):** SHA-256 hash + mtime/size pre-filter → full re-index if changed
2. **Real-time (FileWatcherV2):** watchdog library, 2-second debounce, routes to IndexingOrchestrator

**Change detection:**
```
Step 1: mtime + size pre-filter (cheap)
Step 2: SHA-256 hash check (expensive, only if step 1 passes)
Step 3: Full re-index (chunks + embed + upsert to Qdrant)
```

**File parsing:** 21 tracked extensions. Code files → symbol-level chunking. Documents → semantic chunker.

### Chunking

**Code chunker (`chunker.py`):**
- Regex symbol detection: `def`, `function`, `class`, `struct`, `enum`, `trait`, `fn`, `func`, `type`, `interface`
- Max tokens: 500 (default)
- Token estimation: `len(text) // 4`
- Context window: 200 chars before/after each chunk

**Semantic chunker (`semantic_chunker.py`):**
- Document-type-aware: Markdown (heading-based), Code (symbol-based), Notebook (cell-based), Text (paragraph-based)
- Max tokens: 800, overlap: 150 (declared but unused in accumulation)
- Context addition: 200 chars before/after

### Fulltext Search

- PostgreSQL `to_tsvector('english', ...)` + GIN index
- Custom suffix stemmer (19 rules, NOT Porter stemmer)
- BM25-style ranking via `ts_rank_cd(..., 32)` (cover density normalization)
- Field weights: content=1.0, symbol_name=0.8, file_path=0.3, language=0.2

### Hybrid Retrieval

- Three sources: vector (Qdrant), fulltext (PostgreSQL), graph (PostgreSQL)
- RRF merge: `score = Σ 1/(60 + rank_i + 1)`
- MMR diversity: `MMR = 0.3 * relevance - 0.7 * max_similarity_to_selected`
- Text similarity: Jaccard-like word overlap (intersection/max)
- Dedup: 50% overlap threshold
- Graph search: fixed score 0.4, max 3 query terms, ILIKE matching

### Embedding System

- Three-tier: ONNX (nomic-embed-text-v1) → Ollama → Mock (MD5→deterministic vector)
- Embedding dim: 768
- Max token length: 512
- Batch size: 32 (incremental), 50 (batch)
- Cache: PostgreSQL, 30-day TTL, SHA-256 content hash

### Vector Storage

- Qdrant, 768-dim cosine
- Two collections: `cortex_code` (code chunks), `cortex_memory` (documents)
- Auto-creates collection on first upsert
- Circuit breaker for Qdrant availability

### RAG Pipeline

- Max context tokens: 4000
- Max results: 8
- Content truncation: 500 chars per result
- Sources: vector + fulltext (graph excluded by default)
- Token budget: accumulate results until hitting limit
