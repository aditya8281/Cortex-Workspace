# Knowledge Management — Spec

> **Version:** v1.09 "The Knowledge"
> **Date:** 2026-06-30
> **Status:** Draft

## Problem

Cortex has file awareness (v1.04 knows *which* files exist) and memory (v1.03 can store/retrieve vector embeddings), but it cannot *understand* file contents. When a user asks "find the file about CNNs" or "what did I write about transformers?", Cortex has no answer — it has never parsed, chunked, or embedded the user's documents.

## Solution

A complete knowledge management system where users add directories as "Knowledge Sources." Cortex walks each directory, parses every file it can understand, chunks the content, creates vector embeddings, and stores everything for semantic retrieval. A filesystem watcher auto-tracks changes. Chat sessions can optionally query this knowledge base via RAG. A knowledge graph connects related files.

## Personas

- **Researcher** — has a folder of papers, notes, and code. Wants to search across them and ask questions.
- **Developer** — has a project with docs, source code, and configs. Wants Cortex to understand the project structure.
- **Writer** — has a directory of drafts and research. Wants to find related content.

## Functional Requirements

### Knowledge Source Management
- FR1: User can add a directory path as a Knowledge Source
- FR2: User can name and describe each source
- FR3: User can select embedding model per source (mock/onnx/ollama)
- FR4: User can configure chunk strategy and size per source
- FR5: User can delete a source (removes all indexed data)
- FR6: User can toggle auto-watch per source

### Sync Pipeline
- FR7: System walks all files in a source directory recursively
- FR8: System skips .git, node_modules, __pycache__, hidden dirs
- FR9: System computes SHA-256 hash — skips unchanged files
- FR10: System parses 13+ file types via existing parsers
- FR11: System chunks parsed content (semantic, fixed, or paragraph)
- FR12: System generates embeddings and stores in Qdrant
- FR13: System batches Qdrant upserts (100/batch)
- FR14: System tracks progress (files indexed, total, chunks)
- FR15: User can trigger force re-sync (clear + re-index)

### Auto-Watch
- FR16: After sync, file watcher monitors the source path
- FR17: File created → parse + chunk + embed + store
- FR18: File modified → re-hash → re-chunk → re-embed → update
- FR19: File deleted → remove chunks from Qdrant + DB
- FR20: File renamed → delete old path, create new path
- FR21: Events debounced (2s) to prevent thrashing

### Chat Memory
- FR22: Each conversation has a memory_enabled toggle
- FR23: When on, every user message triggers Qdrant search
- FR24: Top 5 chunks injected as context into LLM prompt
- FR25: Context truncated at 4000 chars to avoid overflow
- FR26: Toggle state persists across sessions

### Knowledge Graph
- FR27: System builds edges between related files
- FR28: Edge types: shared_extension, cross_reference, embedding_proximity, co_occurrence
- FR29: Edge strength weighted (0.0–1.0)
- FR30: User can view graph with force-directed visualization
- FR31: User can rebuild graph on demand

### Search
- FR32: Dedicated search page with text input
- FR33: Hybrid retrieval (vector + fulltext + graph via RRF)
- FR34: Filter by source, file type
- FR35: Results show content snippets + file paths + scores
- FR36: Empty states for no results

## Data Model

### KnowledgeSource
```
id, user_id, name, path, description, watch_enabled, auto_sync,
embedding_model, chunk_strategy, chunk_size, chunk_overlap,
status, progress, error_message, total_files, indexed_files,
total_chunks, last_synced_at, created_at, updated_at
```

### KnowledgeFile
```
id, source_id, user_id, file_path, content_hash, file_size,
mime_type, file_extension, chunk_count, status, error_message,
last_indexed_at, created_at
```

### KnowledgeChunk
```
id, file_id, source_id, chunk_index, content, content_hash,
token_count, embedding_id, created_at
```

### KnowledgeGraphEdge
```
id, source_id, file_id_a, file_id_b, relationship_type,
strength, metadata, created_at
```

## Non-Functional Requirements

- NFR1: Incremental sync only — unchanged files skipped (hash-based)
- NFR2: Batch upsert 100 chunks at a time to Qdrant
- NFR3: Debounce watcher at 2s
- NFR4: Max file size 50MB
- NFR5: RAG context capped at 4000 chars
- NFR6: Max 1000 edges per graph query response
- NFR7: WebSocket progress events during sync

## Future Considerations

- Multi-user: knowledge is per-user, not global
- Per-source embedding model allows migration without rebuilding all sources
- Graph visualization supports Obsidian-like exploration patterns
- Sync progress via WebSocket enables real-time UI updates
