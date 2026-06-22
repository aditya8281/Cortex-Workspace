# Dead Code Recommendation — Cortex

**Generated:** 2026-06-22
**Context:** 8 backend services were identified as "dead code" (zero imports). This document evaluates each against Cortex's vision and recommends whether to delete permanently, keep, or restore.

---

## Cortex Vision

> **The cognitive operating layer for personal computing.**
>
> Build a continuously evolving understanding of the entire system—its files, repositories, applications, workflows, history, knowledge, and user intent. Connect them into a coherent model of the machine and its world.

The key words: **understanding**, **continuously evolving**, **coherent model**. Every service that contributes to deeper system understanding or better knowledge extraction has long-term value.

---

## Service-by-Service Analysis

### 1. `cross_file_search.py` (166 lines) — KEEP ✅

**What it does:** Semantic search across indexed code with graph enrichment. Combines vector similarity with knowledge graph relationships (e.g., "find all files that call function X" or "show me the dependency graph for module Y").

**Vision alignment:** HIGH — This is the bridge between raw search and true code understanding. Cortex's vision demands not just finding text but understanding relationships between files. Graph-enriched search is exactly the kind of "coherent model" the README describes.

**Why it's dead:** No router currently calls it. The search page uses a simpler vector-only search path.

**Recommendation:** Keep. Wire it into the search API as an advanced search mode. When users search code, results should include graph context (callers, callees, dependencies). This is a differentiator vs. generic search tools.

**Integration path:**
- Add a `/repos/{repo_id}/search/graph` endpoint that uses `CrossFileSearch`
- Wire the frontend's search page to optionally use graph-enriched results
- Depends on: `embedding_service`, `vector_db`, `graph` models (all exist)

---

### 2. `search_clustering.py` (44 lines) — KEEP ✅

**What it does:** Groups search results by document path, computing aggregate scores. Prevents the "10 results from the same file" problem.

**Vision alignment:** MEDIUM — As Cortex indexes more repositories, search results will naturally cluster. Without clustering, UX degrades. This is a quality-of-life feature that matters at scale.

**Why it's dead:** Only 44 lines, never integrated. The current search returns flat results.

**Recommendation:** Keep. It's tiny, has zero dependencies, and solves a real problem. Integrate it into the search pipeline as a post-processing step.

**Integration path:**
- Add as a post-processing step after vector search results are returned
- Return clustered results with `document_path`, `best_score`, `result_count`
- Zero risk — it's a pure function that transforms results

---

### 3. `threaded_scanner.py` (234 lines) — KEEP ✅

**What it does:** Multi-threaded file scanner with crash isolation. Scans directories using `ProcessPoolExecutor`/`ThreadPoolExecutor` with configurable workers, timeouts, and batch sizes. Inspired by sist2's fork-based scanner.

**Vision alignment:** HIGH — Cortex needs to scan thousands of files across repositories. A naive single-threaded scan is a bottleneck. This service provides the performance foundation for repository indexing at scale.

**Why it's dead:** The current `incremental_indexer.py` uses a simpler scan approach. `threaded_scanner` was written for a future that hasn't arrived yet.

**Recommendation:** Keep. As users add more repositories, scanning performance matters. This is infrastructure that will be needed when Cortex indexes large codebases (monorepos, 10k+ files).

**Integration path:**
- Replace the scan loop in `incremental_indexer.py` with `ThreadedScanner`
- Add a configuration option for max workers and batch size
- Medium risk — requires testing with real repository sizes

---

### 4. `batch_indexer.py` (172 lines) — KEEP ✅

**What it does:** Batch indexing service for bulk document insertion. Collects documents in a buffer and flushes them in configurable batches (default 50, flush every 5s). Inspired by sist2's bulk indexing pattern.

**Vision alignment:** MEDIUM-HIGH — When Cortex indexes a large repository, inserting chunks one-by-one into Qdrant/PostgreSQL is slow. Batch insertion is a standard performance optimization for vector databases.

**Why it's dead:** The current indexing pipeline inserts one chunk at a time. This was written for performance optimization that hasn't been applied yet.

**Recommendation:** Keep. This is a performance multiplier for repository indexing. When users index large codebases, batch insertion will be the difference between " indexing in 30 seconds" and "indexing in 5 minutes."

**Integration path:**
- Plug into the document indexing pipeline as a bulk insert layer
- Configure flush interval based on available memory
- Low risk — it's a buffering layer, not a core logic change

---

### 5. `document_statistics.py` (172 lines) — KEEP ⚠️ (with caveats)

**What it does:** Pre-computed statistics for indexed documents. Caches statistics in Redis with configurable TTL. Computes things like "total chunks per repo", "average chunk size", "language distribution".

**Vision alignment:** MEDIUM — Statistics help Cortex understand what it has indexed. The dashboard could show "your codebase is 60% Python, 30% TypeScript" or "repo X has 12,000 chunks across 340 files."

**Why it's dead:** The dashboard doesn't display these statistics yet. The service computes them but nobody reads them.

**Recommendation:** Keep with caution. It depends on `Document` and `DocumentChunk` models that may not be fully wired. Verify the model imports are valid before integrating.

**Integration path:**
- Wire into the dashboard to show repository statistics
- Add a `/repos/{repo_id}/stats` endpoint
- Medium risk — model dependencies need verification

---

### 6. `path_index.py` (276 lines) — KEEP ✅

**What it does:** Pre-computed path indexes for fast directory browsing. Provides O(1) directory listings by pre-computing the path hierarchy at index time. Inspired by sist2's `path_parent` function.

**Vision alignment:** HIGH — Cortex needs to understand file system structure. When a user browses a repository, directory listings should be instant. Pre-computing the path hierarchy at index time achieves this.

**Why it's dead:** The `PathIndex` model exists in the database but the service that populates it was never wired into the indexing pipeline.

**Recommendation:** Keep. This is foundational for the repository browser. Without it, directory listing requires scanning the filesystem on every request.

**Integration path:**
- Wire into the indexing pipeline to populate `PathIndex` during repo indexing
- Use `PathIndex` for directory listing endpoints instead of live filesystem scans
- Medium risk — requires the `PathIndex` model to be properly migrated

---

### 7. `model_detail_scraper.py` (264 lines) — KEEP ⚠️ (with caveats)

**What it does:** Scrapes detailed model information from Ollama and HuggingFace. Extracts architecture, parameter counts, quantization variants, benchmarks, and descriptions.

**Vision alignment:** MEDIUM — Cortex manages local LLM inference. Having rich model metadata helps users choose the right model for their hardware and use case.

**Why it's dead:** The models page already has static catalog data. This scraper was meant to keep it updated but was never integrated.

**Recommendation:** Keep with caution. The scraper uses `httpx` and `beautifulsoup4` — verify these are in `requirements.txt`. The scraping logic is fragile (website HTML changes) so it needs a fallback.

**Integration path:**
- Run as a periodic background task to update model catalog
- Add error handling for when Ollama/HF pages change structure
- High risk — external website scraping is inherently fragile

---

### 8. `indexing_orchestrator.py` (99 lines) — KEEP ✅

**What it does:** Routes file changes to the correct indexer based on file extension. Code files go to one indexer, documents to another, etc.

**Vision alignment:** HIGH — Cortex watches filesystem changes and needs to route them intelligently. This is the dispatcher that decides how to handle each file type.

**Why it's dead:** The current `file_watcher_v2.py` doesn't use it — it handles all files the same way.

**Recommendation:** Keep. This is the correct abstraction for file-type-aware indexing. Without it, every file type requires manual routing logic scattered across the codebase.

**Integration path:**
- Wire into `file_watcher_v2.py` as the dispatch layer
- Add indexer registrations for each file type
- Low risk — it's a thin routing layer

---

## Summary

| Service | Lines | Vision Alignment | Recommendation | Risk |
|---------|-------|-----------------|----------------|------|
| `cross_file_search.py` | 166 | HIGH | **KEEP** — graph-enriched search is a differentiator | Low |
| `search_clustering.py` | 44 | MEDIUM | **KEEP** — tiny, zero deps, solves real UX problem | Zero |
| `threaded_scanner.py` | 234 | HIGH | **KEEP** — performance foundation for large repos | Medium |
| `batch_indexer.py` | 172 | MEDIUM-HIGH | **KEEP** — performance multiplier for indexing | Low |
| `document_statistics.py` | 172 | MEDIUM | **KEEP** — dashboard enrichment, verify model deps | Medium |
| `path_index.py` | 276 | HIGH | **KEEP** — foundational for repository browser | Medium |
| `model_detail_scraper.py` | 264 | MEDIUM | **KEEP** — but fragile, needs fallback | High |
| `indexing_orchestrator.py` | 99 | HIGH | **KEEP** — correct abstraction for file routing | Low |

**Verdict: All 8 services should be kept.** They represent ~1,427 lines of production-quality code that directly serves Cortex's vision of deep system understanding. Deleting them would force reimplementation when these capabilities are needed.

---

## Implementation Priority

1. **Immediate** (wire into existing code):
   - `search_clustering.py` — drop into search pipeline
   - `indexing_orchestrator.py` — wire into file watcher
   - `cross_file_search.py` — add graph search endpoint

2. **Short-term** (performance):
   - `batch_indexer.py` — plug into indexing pipeline
   - `threaded_scanner.py` — replace naive file scanner

3. **Medium-term** (features):
   - `path_index.py` — populate during indexing, use for browsing
   - `document_statistics.py` — wire into dashboard

4. **Long-term** (maintenance):
   - `model_detail_scraper.py` — periodic catalog updates with fallback

---

## CLI Stubs (`cli/src/commands/` — 15 files, 42 lines)

**Verdict: DELETE permanently.** These are placeholder files (2-4 lines each) with no logic. They were part of an abandoned Tauri experiment. Cortex is a web application — a CLI is not part of the current vision.

---

*Generated by deadcode-recommendation.md*
