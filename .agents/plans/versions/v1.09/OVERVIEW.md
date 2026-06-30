# v1.09: The Knowledge — CORTEX

**Document:** Version 1.09 Overview
**Authority:** Stage 6 — Master Versioned Implementation Roadmap
**Date:** 2026-06-30
**Type:** Capability Delivery

---

## Objective

Build the knowledge management system: directory-based knowledge ingestion, automatic file watching, content chunking and embedding, semantic search, knowledge graph of file relationships, and chat integration with per-conversation memory toggle. Create a system where Cortex understands the user's files at a content level — parsing, chunking, embedding, and indexing every file in watched directories, automatically tracking changes via filesystem watchers, and making that knowledge accessible through chat and search. This is the foundation for Cortex becoming a true knowledge companion that knows what the user knows.

---

## Question

"Can Cortex understand and remember what's in my files?"

---

## What This Version Delivers

After completing v1.09, Cortex can:

- **Ingest directories as knowledge sources** — Add any directory path as a "Knowledge Source" with one click. Cortex walks the entire tree, parses every file it can understand, chunks the content, and creates vector embeddings for semantic retrieval.
- **Auto-watch for changes** — Once a directory is added and synced, a filesystem watcher monitors it. File created → parsed and indexed. File modified → re-chunked and re-embedded. File deleted → chunks removed from vector store. All changes propagate within seconds.
- **Parse 13+ file types** — Plain text, Markdown, Python/JS/TS code, PDF, DOCX, XLSX, PPTX, EPUB, HTML, JSON, YAML, CSV, and more via existing parser infrastructure.
- **Semantic search across all knowledge** — Dedicated search endpoint with hybrid retrieval (vector + fulltext + graph via RRF). Filter by source, file type, date range. Results show content snippets, file paths, relevance scores.
- **Per-conversation memory toggle** — Each chat session has a memory on/off switch. When on, every message triggers RAG retrieval across knowledge sources. Ask "find the file about CNNs" or "what did I write about transformers?" — Cortex answers from its knowledge base.
- **Knowledge graph of file relationships** — Files connected by shared topics, cross-references, import relationships, and embedding proximity. Interactive graph visualization like Obsidian.
- **Choose embedding model per source** — Select which embedding model to use: ONNX BGE-M3 (default), Ollama nomic-embed, or lightweight mock mode. Per-source configuration.
- **Incremental sync only** — Content-hash based change detection. Unchanged files are skipped entirely. Batch operations for efficiency.

---

## Capabilities Delivered

| ID | Name | Domain | Priority | Architecture Principle |
|----|------|--------|----------|----------------------|
| K1 | Knowledge Source Management | Knowledge | Core | 1.1 (Local-First) — all knowledge stored locally |
| K2 | Content Parsing & Chunking | Knowledge | Core | 4.3 (Memory Architecture) — chunk-then-embed pattern |
| K3 | File Embedding & Vector Storage | Knowledge | Core | 4.3 (Vector + Fulltext + Graph) — hybrid retrieval |
| K4 | Watchdog Auto-Sync | Knowledge | Core | 1.4 (Separation of Concerns) — watcher service boundary |
| K5 | Incremental Re-Indexing | Knowledge | Core | 3.7 (Incremental Safety) — hash-based change detection |
| K6 | Chat Memory Integration | Knowledge | Core | 1.7 (Streaming-Native) — RAG context injection |
| K7 | Knowledge Graph Relationships | Knowledge | Core | 4.3 (Graph) — file-to-file and file-to-topic edges |
| K8 | Hybrid Semantic Search | Knowledge | Core | 4.3 (RRF + MMR) — vector + fulltext + graph |
| K9 | Per-Source Embedding Config | Knowledge | Core | 1.4 (Separation of Concerns) — per-source model choice |
| K10 | Knowledge Graph Visualization | Knowledge | Nice | — force-directed graph for UI |

**Total: 10 capabilities**

---

## Version Dependency Chain

```
v1.03 ──> v1.09 (embeddings, vector store, RAG pipeline)
v1.04 ──> v1.09 (file scanning, parsers, skip logic)
v1.07 ──> v1.09 (chat streaming, conversation model)
```

All three dependencies are ✅ complete.

---

## Phases

| Phase | Name | What It Delivers | Tasks |
|-------|------|-----------------|-------|
| P01 | Knowledge Models & Schema | KnowledgeSource, KnowledgeFile, KnowledgeChunk, KnowledgeGraphEdge models + schemas + Alembic migration | 6 |
| P02 | Sync & Indexing Engine | KnowledgeSyncService — walk, parse, chunk, embed, store pipeline with progress tracking | 8 |
| P03 | Watchdog & Auto-Sync | Connect file watcher to auto re-index on create/modify/delete with debounce | 6 |
| P04 | Chat Memory Integration | Per-conversation memory toggle, RAG injection into chat context | 6 |
| P05 | Knowledge Graph & Search | File relationship extraction, topic clustering, search API, knowledge graph endpoints | 7 |
| P06 | Frontend UI | Knowledge management page, search page, chat toggle, graph visualization, embedding config | 8 |
| **Total** | | | **41** |

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│                   Frontend                           │
│  Knowledge Page  │  Search Page  │  Chat Toggle     │
└────────┬──────────┴──────┬───────┴──────┬───────────┘
         │                 │              │
┌────────▼─────────────────▼──────────────▼───────────┐
│                 API Layer (FastAPI)                   │
│  /knowledge/sources  │  /knowledge/search            │
│  /knowledge/graph    │  PATCH /conversations/{id}/mem │
└────────┬───────────────────────────────┬─────────────┘
         │                               │
┌────────▼───────────────┐  ┌───────────▼─────────────┐
│  Sync Orchestrator     │  │  Chat Handler            │
│  walk → parse → chunk  │  │  RAG → LLM → stream     │
│  → embed → store       │  │  memory on/off           │
└────────┬───────────────┘  └─────────────────────────┘
         │
┌────────▼─────────────────────────────────────────────┐
│                 Services                              │
│  Parsers  │  Chunker  │  Embedding  │  Qdrant        │
│  (13)     │  (3 strats)│  Service   │  Vector DB     │
└──────────────────────────────────────────────────────┘
         │
┌────────▼─────────────────────────────────────────────┐
│  File Watcher (watchdog)  │  Knowledge Graph Builder │
│  create / modify / delete │  topic / import / ref    │
└──────────────────────────────────────────────────────┘
```

### Data Flow — Initial Sync

```
User adds path ──> KnowledgeSource (status=syncing)
                        │
                        ▼
                  Walk directory
                  (skip .git, node_modules, hidden, blocked)
                        │
                        ▼
                  For each file:
                  ┌─────────────────┐
                  │ 1. Check hash   │─── unchanged → skip
                  │ 2. Detect mime  │
                  │ 3. Parse content│
                  │ 4. Chunk text   │
                  │ 5. Generate emb │
                  │ 6. Store in     │
                  │    Qdrant + DB  │
                  │ 7. Extract rels │
                  └─────────────────┘
                        │
                        ▼
            KnowledgeSource (status=idle, last_synced=now)
            File watcher registered for path
```

### Data Flow — Auto-Sync (Watchdog)

```
File created ──> debounce (2s) ──> parse → chunk → embed → add to Qdrant → add DB record
File modified ─> debounce (2s) ──> re-hash → changed? → re-chunk → re-embed → update Qdrant
File deleted ──> debounce (2s) ──> remove Qdrant points → delete DB records
File renamed ──> debounce (2s) ──> delete old + create new
```

### Data Flow — Chat with Memory

```
User sends message ──> Chat handler checks memory_enabled=True
                            │
                            ▼
                   Embed user message
                            │
                            ▼
                   Search Qdrant across user's knowledge sources
                            │
                            ▼
                   Retrieve top-K chunks (default 5)
                            │
                            ▼
                   Inject as context into LLM prompt:
                   "Based on your knowledge base:
                    [file:path/to/file.py]
                    [content snippet]
                    ..."
                            │
                            ▼
                   LLM generates response with file context
```

---

## Database Models

### KnowledgeSource
```python
class KnowledgeSource(Base):
    __tablename__ = "knowledge_sources"
    id: int (PK)
    user_id: int (FK -> users.id)
    name: str
    path: str (absolute path)
    description: str | None
    watch_enabled: bool (default=True)
    auto_sync: bool (default=True)
    embedding_model: str (default="onnx-bge-m3")
    chunk_strategy: str (default="semantic")  # semantic | fixed | paragraph
    chunk_size: int (default=512)
    chunk_overlap: int (default=64)
    status: str  # idle | syncing | indexing | error
    progress: float (0.0 to 1.0)
    error_message: str | None
    total_files: int
    indexed_files: int
    total_chunks: int
    last_synced_at: datetime | None
    created_at: datetime
    updated_at: datetime
```

### KnowledgeFile
```python
class KnowledgeFile(Base):
    __tablename__ = "knowledge_files"
    id: int (PK)
    source_id: int (FK -> knowledge_sources.id, CASCADE)
    user_id: int (FK -> users.id)
    file_path: str (relative to source)
    content_hash: str (SHA-256)
    file_size: int
    mime_type: str | None
    file_extension: str | None
    chunk_count: int (default=0)
    status: str  # pending | indexed | failed
    error_message: str | None
    last_indexed_at: datetime | None
    created_at: datetime
```

### KnowledgeChunk
```python
class KnowledgeChunk(Base):
    __tablename__ = "knowledge_chunks"
    id: int (PK)
    file_id: int (FK -> knowledge_files.id, CASCADE)
    source_id: int (FK -> knowledge_sources.id, CASCADE)
    chunk_index: int
    content: str (text content, up to 100KB)
    content_hash: str
    token_count: int
    embedding_id: str | None (Qdrant point ID)
    created_at: datetime
```

### KnowledgeGraphEdge
```python
class KnowledgeGraphEdge(Base):
    __tablename__ = "knowledge_graph_edges"
    id: int (PK)
    source_id: int (FK -> knowledge_sources.id)
    file_id_a: int (FK -> knowledge_files.id)
    file_id_b: int (FK -> knowledge_files.id)
    relationship_type: str  # shared_topic | cross_reference | import | co_occurrence | embedding_proximity
    strength: float (0.0 to 1.0)
    metadata: dict | None (JSON)
    created_at: datetime
```

---

## File Inventory — New Files

### Backend Models
- `backend/app/models/knowledge/__init__.py`
- `backend/app/models/knowledge/knowledge_source.py`
- `backend/app/models/knowledge/knowledge_file.py`
- `backend/app/models/knowledge/knowledge_chunk.py`
- `backend/app/models/knowledge/knowledge_graph_edge.py`

### Backend Schemas
- `backend/app/schemas/knowledge/__init__.py`
- `backend/app/schemas/knowledge/knowledge_source.py`
- `backend/app/schemas/knowledge/knowledge_file.py`
- `backend/app/schemas/knowledge/knowledge_chunk.py`
- `backend/app/schemas/knowledge/knowledge_graph.py`
- `backend/app/schemas/knowledge/search.py`

### Backend API Routes
- `backend/app/api/v1/knowledge/__init__.py`
- `backend/app/api/v1/knowledge/router.py`
- `backend/app/api/v1/knowledge/sources.py`
- `backend/app/api/v1/knowledge/search.py`
- `backend/app/api/v1/knowledge/graph.py`
- `backend/app/api/v1/knowledge/sync.py`

### Backend Services
- `backend/app/services/knowledge/__init__.py`
- `backend/app/services/knowledge/sync_service.py`
- `backend/app/services/knowledge/indexer.py`
- `backend/app/services/knowledge/graph_builder.py`
- `backend/app/services/knowledge/search_service.py`
- `backend/app/services/knowledge/watcher_service.py`

### Backend Core Changes
- Modify: `backend/app/core/websocket.py` — WS progress channel for sync
- Modify: `backend/app/services/awareness/file_watcher.py` — multi-callback support
- Modify: `backend/app/models/interaction/conversation.py` — add memory_enabled
- Modify: `backend/app/api/v1/interaction/conversations.py` — memory toggle endpoint
- Modify: `backend/app/api/v1/interaction/ws_chat.py` — RAG injection

### Alembic Migration
- `migrations/versions/c00000000006_add_knowledge_models.py`

### Tests
- `tests/knowledge/` (new directory, 15+ files)

### Frontend
- `frontend/src/features/knowledge/` (new feature module)
  - `components/KnowledgeSourceList.tsx`
  - `components/KnowledgeSourceForm.tsx`
  - `components/SyncProgress.tsx`
  - `components/EmbeddingConfig.tsx`
  - `components/SearchResults.tsx`
  - `components/GraphVisualization.tsx`
  - `components/SearchFilter.tsx`
  - `page.tsx`, `api.ts`
- Modify: `frontend/src/features/chat/components/ChatSidebar.tsx` — memory toggle
- Modify: `frontend/src/shared/ws/useWebSocket.ts` — sync progress channel
