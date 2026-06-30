# v1.09: The Knowledge — CORTEX

**Document:** Version 1.09 Overview
**Authority:** Stage 6 — Master Versioned Implementation Roadmap
**Date:** 2026-06-30
**Type:** Capability Delivery

---

## Objective

Build the complete knowledge and learning system: directory-based knowledge ingestion, automatic file watching, content chunking and embedding, semantic search, knowledge graph of file relationships, chat integration with per-conversation memory toggle, AND user behavior learning — preference learning, workflow detection, habit recognition, feedback learning, personalization, pattern recognition, anomaly detection, and continuous improvement. Create a system where Cortex both understands the user's files at a content level AND learns from the user's behavior to personalize every interaction. This is the foundation for Cortex becoming a true knowledge companion that knows both what the user knows and how the user works.

---

## Question

"Can Cortex understand and remember what's in my files — and learn how I work?"

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
- **Learn user preferences** — Observes and records preferences for response style, UI layout, notification frequency, tool choices. Preferences strengthen with repeated observation, weaken when contradicted.
- **Understand workflows** — Detects multi-step workflows users repeat (e.g., "open editor → run tests → commit → push"). Records step sequences, frequency, and context for next-step suggestion.
- **Detect habits** — Identifies habitual behaviors (daily morning coding, afternoon email checking). Tracks trigger → action → frequency. Habit classification requires ≥5 occurrences.
- **Learn from feedback** — Records explicit feedback (corrections, affirmations) and implicit feedback (acceptance/rejection). Calculates learning rates to measure improvement.
- **Personalize responses** — Builds per-user profiles covering response style, preferred topics, active hours, expertise level. Adapts content length and suggestion density.
- **Recognize patterns** — Detects temporal, behavioral, and preference patterns. Patterns strengthen with occurrences.
- **Detect anomalies** — Identifies unusual behavior (activity at 3 AM, 10× normal command frequency). Flags anomalies for review; never auto-acts. Adaptive baselines.
- **Continuously improve** — Tracks improvement metrics: accuracy, response quality, suggestion acceptance rates.

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
| L1 | Preference Learning | Learning | Core | 1.6 (Evidence Over Opinion) — observations ground all preferences |
| L2 | Workflow Learning | Learning | Core | 4.7 (Workflow Architecture) — workflow as first-class pattern |
| L3 | Habit Detection | Learning | Core | 1.6 (Evidence Over Opinion) — ≥5 occurrences for classification |
| L4 | Behavior Adaptation | Learning | Core | 1.4 (Separation of Concerns) — adaptation service boundary |
| L5 | Feedback Learning | Learning | Core | 1.7 (Incremental Safety) — bounded delta per event |
| L6 | Personalization | Learning | Core | 1.1 (Local-First) — all profiles local |
| L7 | Knowledge Refinement | Learning | Core | 4.3 (Memory Architecture) — confidence adjusts with outcomes |
| L8 | Pattern Recognition | Learning | Core | 1.6 (Evidence Over Opinion) — minimum evidence threshold |
| L9 | Continuous Improvement | Learning | Core | 3.7 (Incremental Safety) — bounded improvement rates |
| L10 | Anomaly Detection | Learning | Core | 1.7 (Incremental Safety) — never auto-acts on anomalies |

**Total: 20 capabilities**

---

## Version Dependency Chain

```
v1.03 ──> v1.09 (embeddings, vector store, RAG pipeline)
v1.04 ──> v1.09 (file scanning, parsers, skip logic)
v1.07 ──> v1.09 (chat streaming, conversation model)
v1.09 Learning phases also benefit from:
  └── v1.06 ──> v1.09 (cognition for feedback learning, pattern recognition)
```

All four dependencies are ✅ complete.

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
| P07 | Learning Models & Schema | UserPreference, WorkflowPattern, Habit, LearningEvent, Pattern models + schemas + Alembic migration | 6 |
| P08 | Preference & Workflow Learning | PreferenceLearningService, WorkflowLearningService — core observation layer | 6 |
| P09 | Habits & Adaptation | HabitDetectionService, BehaviorAdaptationService, FeedbackLearningService | 6 |
| P10 | Personalization & Refinement | PersonalizationService, KnowledgeRefinementService, PatternRecognitionService, AnomalyDetectionService, ContinuousImprovementService | 7 |
| P11 | Learning API & Integration | REST API endpoints for all learning capabilities, frontend API client, learning dashboard, integration tests | 6 |
| **Total** | | | **72** |

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

## Learning Database Models

### UserPreference
```python
class UserPreference(Base):
    __tablename__ = "user_preferences"
    id: int (PK)
    user_id: int (FK -> users.id)
    category: str
    key: str
    value: dict (JSON)
    confidence: float (default=0.5, clamped 0.0–1.0)
    source: str  # explicit | observed | inferred
    observation_count: int
    last_observed: datetime
    created_at: datetime
    updated_at: datetime
    UniqueConstraint: (user_id, category, key)
```

### WorkflowPattern
```python
class WorkflowPattern(Base):
    __tablename__ = "workflow_patterns"
    id: int (PK)
    user_id: int (FK -> users.id)
    pattern_name: str
    description: str | None
    steps: list[str] (JSON)
    context: str | None
    frequency: int (default=1)
    confidence: float (default=0.3)
    last_observed: datetime
    created_at: datetime
    updated_at: datetime
```

### Habit
```python
class Habit(Base):
    __tablename__ = "habits"
    id: int (PK)
    user_id: int (FK -> users.id)
    habit_name: str
    description: str | None
    trigger: str | None
    action: str
    frequency: str  # daily | weekly | hourly | irregular
    occurrences: int (default=1)
    first_observed: datetime
    last_observed: datetime
    created_at: datetime
```

### LearningEvent
```python
class LearningEvent(Base):
    __tablename__ = "learning_events"
    id: int (PK)
    user_id: int (FK -> users.id)
    event_type: str  # affirmation | correction | feedback | implicit
    context: dict | None (JSON)
    input_data: dict | None (JSON)
    output_data: dict | None (JSON)
    delta: float (default=0.0, clamped ±0.1)
    applied: bool (default=False)
    created_at: datetime
```

### Pattern (Learned)
```python
class Pattern(Base):
    __tablename__ = "patterns"
    id: int (PK)
    user_id: int (FK -> users.id)
    pattern_type: str  # temporal | behavioral | preference
    description: str
    evidence: list (JSON)
    confidence: float (default=0.3)
    first_seen: datetime
    last_seen: datetime
    occurrences: int (default=1)
```

---

## File Inventory — New Files

### Backend Knowledge Models
- `backend/app/models/knowledge/__init__.py`
- `backend/app/models/knowledge/knowledge_source.py`
- `backend/app/models/knowledge/knowledge_file.py`
- `backend/app/models/knowledge/knowledge_chunk.py`
- `backend/app/models/knowledge/knowledge_graph_edge.py`

### Backend Learning Models
- `backend/app/models/learning/__init__.py`
- `backend/app/models/learning/user_preference.py`
- `backend/app/models/learning/workflow_pattern.py`
- `backend/app/models/learning/habit.py`
- `backend/app/models/learning/learning_event.py`
- `backend/app/models/learning/pattern.py`

### Backend Knowledge Schemas
- `backend/app/schemas/knowledge/__init__.py`
- `backend/app/schemas/knowledge/knowledge_source.py`
- `backend/app/schemas/knowledge/knowledge_file.py`
- `backend/app/schemas/knowledge/knowledge_chunk.py`
- `backend/app/schemas/knowledge/knowledge_graph.py`
- `backend/app/schemas/knowledge/search.py`

### Backend Learning Schemas
- `backend/app/schemas/learning/__init__.py`
- `backend/app/schemas/learning/preference.py`
- `backend/app/schemas/learning/workflow.py`
- `backend/app/schemas/learning/habit.py`
- `backend/app/schemas/learning/event.py`
- `backend/app/schemas/learning/pattern.py`

### Backend API Routes (Knowledge)
- `backend/app/api/v1/knowledge/__init__.py`
- `backend/app/api/v1/knowledge/router.py`
- `backend/app/api/v1/knowledge/sources.py`
- `backend/app/api/v1/knowledge/search.py`
- `backend/app/api/v1/knowledge/graph.py`
- `backend/app/api/v1/knowledge/sync.py`

### Backend API Routes (Learning)
- `backend/app/api/v1/learning/__init__.py`
- `backend/app/api/v1/learning/router.py`
- `backend/app/api/v1/learning/preferences.py`
- `backend/app/api/v1/learning/workflows.py`
- `backend/app/api/v1/learning/habits.py`
- `backend/app/api/v1/learning/feedback.py`
- `backend/app/api/v1/learning/patterns.py`
- `backend/app/api/v1/learning/personalization.py`
- `backend/app/api/v1/learning/anomalies.py`
- `backend/app/api/v1/learning/improvement.py`

### Backend Knowledge Services
- `backend/app/services/knowledge/__init__.py`
- `backend/app/services/knowledge/sync_service.py`
- `backend/app/services/knowledge/indexer.py`
- `backend/app/services/knowledge/graph_builder.py`
- `backend/app/services/knowledge/search_service.py`
- `backend/app/services/knowledge/watcher_service.py`

### Backend Learning Services
- `backend/app/services/learning/__init__.py`
- `backend/app/services/learning/preference_service.py`
- `backend/app/services/learning/workflow_service.py`
- `backend/app/services/learning/habit_service.py`
- `backend/app/services/learning/feedback_service.py`
- `backend/app/services/learning/adaptation_service.py`
- `backend/app/services/learning/personalization_service.py`
- `backend/app/services/learning/refinement_service.py`
- `backend/app/services/learning/pattern_service.py`
- `backend/app/services/learning/anomaly_service.py`
- `backend/app/services/learning/improvement_service.py`

### Backend Core Changes
- Modify: `backend/app/core/websocket.py` — WS progress channel for sync
- Modify: `backend/app/services/awareness/file_watcher.py` — multi-callback support
- Modify: `backend/app/models/interaction/conversation.py` — add memory_enabled
- Modify: `backend/app/api/v1/interaction/conversations.py` — memory toggle endpoint
- Modify: `backend/app/api/v1/interaction/ws_chat.py` — RAG injection

### Alembic Migrations
- `migrations/versions/c00000000006_add_knowledge_models.py`
- `migrations/versions/c00000000007_add_learning_models.py`

### Tests
- `tests/knowledge/` (new directory, 15+ files)
- `tests/learning/` (new directory, 15+ files)

### Frontend Knowledge Module
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

### Frontend Learning Module
- `frontend/src/features/learning/` (new feature module)
  - `components/PreferencePanel.tsx`
  - `components/WorkflowTimeline.tsx`
  - `components/HabitCard.tsx`
  - `components/FeedbackButton.tsx`
  - `components/LearningDashboard.tsx`
  - `components/AdaptationProfile.tsx`
  - `components/PatternDisplay.tsx`
  - `components/AnomalyAlert.tsx`
  - `page.tsx`, `api.ts`
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
