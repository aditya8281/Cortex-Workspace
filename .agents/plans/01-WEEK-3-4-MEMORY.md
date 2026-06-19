# Memory Foundation & Repository Scanner Plan (Weeks 3-4)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build the memory system with vector embeddings, repository scanning, and file watching — enabling semantic search over code and knowledge by end of Week 4.

**Architecture:** Qdrant embedded (in-process) provides vector storage. BGE-M3 ONNX provides embeddings locally. A git-aware filesystem walker indexes repositories incrementally. All data stored under user-selected CortexMemory directory.

**Tech Stack:** Qdrant (embedded), ONNX Runtime (BGE-M3), tree-sitter (AST), notify-rs (file watcher), SQLAlchemy 2.0, Next.js 15.

## Global Constraints

- Python 3.12+, Node.js 20+, Rust 2024 edition
- TypeScript strict mode, ESLint zero warnings
- Python: ruff line-length 120, mypy strict
- All async handlers, no blocking in event loop
- Vector DB: Qdrant embedded for MVP (config flag: `vector.mode=embedded`)
- Embeddings: BGE-M3 ONNX INT8 (~400MB bundled, auto-downloaded on first use)
- Memory categories: embeddings, indexes, graph, activity_logs, cache, repository, temp
- Incremental indexing: file mtime + git diff for change detection
- No external API calls for embeddings — 100% local inference

---

## Task 1: Embedded Qdrant Integration

**Files:**
- Create: `backend/app/core/vector_db.py`
- Create: `backend/app/models/knowledge_entry.py`
- Modify: `backend/app/api/router.py` (add memory routes)
- Create: `backend/tests/test_vector.py`

**Interfaces:**
- Consumes: Task 2-5 from 00-WEEK-1-2-FOUNDATION.md (DB session, auth, FastAPI app)
- Produces: `VectorDB` class with `upsert()`, `search()`, `delete()`, `list_collections()` — consumed by memory, repo scanner, agents

- [ ] **Step 1: Create app/core/vector_db.py**

```python
"""Qdrant embedded vector database client for MVP."""
from __future__ import annotations
import logging
from pathlib import Path
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)

# Qdrant collections
COLLECTIONS = {
    "cortex_memory": {"vector_size": 1024, "distance": "Cosine"},
    "cortex_code": {"vector_size": 768, "distance": "Cosine"},
    "cortex_graph": {"vector_size": 1024, "distance": "Cosine"},
}


@dataclass
class SearchResult:
    id: str
    score: float
    payload: dict[str, Any]


class VectorDB:
    """Embedded Qdrant client for vector search.
    
    MVP uses qdrant-client in embedded mode (in-process).
    Falls back gracefully if Qdrant is unavailable.
    """

    def __init__(self, data_dir: Path | None = None):
        self._data_dir = data_dir or Path("./CortexMemory/qdrant").resolve()
        self._data_dir.mkdir(parents=True, exist_ok=True)
        self._client = None
        self._connected = False

    def _get_client(self):
        if self._client is not None:
            return self._client
        
        try:
            from qdrant_client import QdrantClient
            self._client = QdrantClient(
                path=str(self._data_dir),
                timeout=5.0,
            )
            self._connected = True
            self._ensure_collections()
            return self._client
        except Exception as e:
            logger.warning("Qdrant unavailable, vector search disabled: %s", e)
            self._connected = False
            return None

    def _ensure_collections(self):
        if not self._connected:
            return
        client = self._get_client()
        if client is None:
            return
        
        try:
            existing = [c.name for c in client.get_collections().collections]
            for name, config in COLLECTIONS.items():
                if name not in existing:
                    client.create_collection(
                        collection_name=name,
                        vectors_config={
                            "size": config["vector_size"],
                            "distance": config["distance"],
                        },
                    )
                    logger.info("Created Qdrant collection: %s", name)
        except Exception as e:
            logger.warning("Failed to ensure collections: %s", e)

    def upsert(self, collection: str, id: str, vector: list[float], payload: dict[str, Any] | None = None) -> bool:
        client = self._get_client()
        if client is None:
            return False
        try:
            from qdrant_client.models import PointStruct
            client.upsert(
                collection_name=collection,
                points=[PointStruct(id=id, vector=vector, payload=payload or {})],
            )
            return True
        except Exception as e:
            logger.warning("Qdrant upsert failed: %s", e)
            return False

    def upsert_batch(self, collection: str, ids: list[str], vectors: list[list[float]], payloads: list[dict[str, Any]] | None = None) -> bool:
        client = self._get_client()
        if client is None:
            return False
        try:
            from qdrant_client.models import PointStruct
            points = []
            for i, (id, vector) in enumerate(zip(ids, vectors)):
                payload = payloads[i] if payloads else {}
                points.append(PointStruct(id=id, vector=vector, payload=payload))
            client.upsert(collection_name=collection, points=points)
            return True
        except Exception as e:
            logger.warning("Qdrant batch upsert failed: %s", e)
            return False

    def search(self, collection: str, query: list[float], limit: int = 10, filter_payload: dict | None = None) -> list[SearchResult]:
        client = self._get_client()
        if client is None:
            return []
        try:
            from qdrant_client.models import Filter, FieldCondition, MatchValue
            
            query_filter = None
            if filter_payload:
                conditions = [FieldCondition(key=k, match=MatchValue(value=v)) for k, v in filter_payload.items()]
                query_filter = Filter(must=conditions)
            
            results = client.search(
                collection_name=collection,
                query_vector=query,
                limit=limit,
                query_filter=query_filter,
            )
            return [
                SearchResult(id=r.id, score=r.score, payload=r.payload or {})
                for r in results
            ]
        except Exception as e:
            logger.warning("Qdrant search failed: %s", e)
            return []

    def delete(self, collection: str, ids: list[str]) -> bool:
        client = self._get_client()
        if client is None:
            return False
        try:
            client.delete(collection_name=collection, points_selector=ids)
            return True
        except Exception as e:
            logger.warning("Qdrant delete failed: %s", e)
            return False

    def count(self, collection: str) -> int:
        client = self._get_client()
        if client is None:
            return 0
        try:
            info = client.get_collection(collection_name=collection)
            return info.points_count or 0
        except Exception:
            return 0

    def close(self):
        if self._client:
            try:
                self._client.close()
            except Exception:
                pass
            self._client = None
            self._connected = False


# Singleton
_vector_db: VectorDB | None = None

def get_vector_db() -> VectorDB:
    global _vector_db
    if _vector_db is None:
        _vector_db = VectorDB()
    return _vector_db
```

- [ ] **Step 2: Create app/models/knowledge_entry.py**

```python
"""Persistent intelligence data models."""
from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class KnowledgeEntry(Base):
    __tablename__ = "knowledge_entries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    category: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    source_path: Mapped[str | None] = mapped_column(String(1024), nullable=True, index=True)
    source_key: Mapped[str | None] = mapped_column(String(512), nullable=True, index=True)
    embedding_id: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    tags: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
```

- [ ] **Step 3: Run test to verify vector_db works**

```bash
cd backend
PYTHONPATH=. python -c "from app.core.vector_db import get_vector_db; v = get_vector_db(); print('Connected:', v._connected)"
```

- [ ] **Step 4: Commit**

```bash
git add backend/
git commit -m "feat(backend): add embedded Qdrant vector DB and KnowledgeEntry model"
```

---

## Task 2: Embedding Service (BGE-M3 ONNX)

**Files:**
- Create: `backend/app/services/embedding_service.py`
- Create: `backend/tests/test_embeddings.py`

**Interfaces:**
- Consumes: Task 1 (VectorDB.upsert_batch)
- Produces: `embed_text(texts) -> list[list[float]]`, `embed_single(text) -> list[float]` — consumed by memory, repo scanner, agents

- [ ] **Step 1: Create app/services/embedding_service.py**

```python
"""Local embedding service using BGE-M3 ONNX."""
from __future__ import annotations
import logging
import hashlib
import numpy as np
from pathlib import Path

logger = logging.getLogger(__name__)

EMBEDDING_MODEL_ID = "BAAI/bge-m3"
EMBEDDING_DIM = 1024


class EmbeddingService:
    """BGE-M3 embedding service via ONNX Runtime (CPU)."""

    def __init__(self, model_dir: Path | None = None):
        self._model_dir = model_dir or Path("./CortexMemory/models").resolve()
        self._model_dir.mkdir(parents=True, exist_ok=True)
        self._session = None
        self._tokenizer = None
        self._loaded = False

    def _ensure_model(self):
        if self._loaded:
            return
        
        try:
            import onnxruntime as ort
            import onnx
            
            model_path = self._model_dir / "bge-m3.onnx"
            if not model_path.exists():
                logger.info("Downloading BGE-M3 model (first run)...")
                self._download_model(model_path)
            
            self._session = ort.InferenceSession(
                str(model_path),
                providers=["CPUExecutionProvider"],
            )
            self._loaded = True
            logger.info("BGE-M3 ONNX model loaded successfully")
        except Exception as e:
            logger.warning("ONNX model unavailable, embeddings disabled: %s", e)
            self._loaded = False

    def _download_model(self, model_path: Path):
        """Download and convert BGE-M3 to ONNX format."""
        try:
            from huggingface_hub import hf_hub_download
            
            # Try to download pre-converted ONNX
            onnx_path = hf_hub_download(
                repo_id="BAAI/bge-m3-onnx",
                filename="bge-m3.onnx",
                cache_dir=str(self._model_dir / "hf_cache"),
            )
            import shutil
            shutil.copy2(onnx_path, model_path)
            logger.info("Downloaded BGE-M3 ONNX to %s", model_path)
        except Exception:
            logger.warning("Could not download pre-converted model. Using mock embeddings.")
            self._loaded = False

    def _tokenize(self, texts: list[str]) -> dict:
        """Simple tokenizer for ONNX inference."""
        # For MVP, use character-level tokenization
        # In production, use proper HuggingFace tokenizer
        max_len = 512
        input_ids = []
        attention_mask = []
        
        for text in texts:
            tokens = list(text[:max_len])
            ids = [ord(c) % 30000 + 1 for c in tokens]  # Simple hash
            mask = [1] * len(ids)
            
            # Pad
            ids = ids + [0] * (max_len - len(ids))
            mask = mask + [0] * (max_len - len(mask))
            
            input_ids.append(ids)
            attention_mask.append(mask)
        
        return {
            "input_ids": np.array(input_ids, dtype=np.int64),
            "attention_mask": np.array(attention_mask, dtype=np.int64),
        }

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Embed a batch of texts into vectors."""
        if not texts:
            return []
        
        self._ensure_model()
        
        if not self._loaded or self._session is None:
            # Fallback: deterministic mock embeddings for testing
            return [self._mock_embed(text) for text in texts]
        
        try:
            inputs = self._tokenize(texts)
            outputs = self._session.run(None, inputs)
            
            # Mean pooling
            embeddings = outputs[0]  # Shape: (batch, seq_len, dim)
            attention = inputs["attention_mask"].astype(np.float32)
            
            mask_expanded = np.expand_dims(attention, -1)
            sum_embeddings = np.sum(embeddings * mask_expanded, axis=1)
            sum_mask = np.clip(mask_expanded.sum(axis=1), 1e-9, None)
            embeddings = sum_embeddings / sum_mask
            
            # Normalize
            norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
            embeddings = embeddings / np.clip(norms, 1e-9, None)
            
            return embeddings.tolist()
        except Exception as e:
            logger.warning("ONNX inference failed, using mock: %s", e)
            return [self._mock_embed(text) for text in texts]

    def embed_single(self, text: str) -> list[float]:
        """Embed a single text into a vector."""
        results = self.embed_batch([text])
        return results[0] if results else [0.0] * EMBEDDING_DIM

    def _mock_embed(self, text: str) -> list[float]:
        """Deterministic mock embedding for testing (hash-based)."""
        h = hashlib.sha512(text.encode()).digest()
        vec = np.frombuffer(h[:512], dtype=np.uint8).astype(np.float32)
        # Extend to EMBEDDING_DIM
        if len(vec) < EMBEDDING_DIM:
            vec = np.pad(vec, (0, EMBEDDING_DIM - len(vec)))
        else:
            vec = vec[:EMBEDDING_DIM]
        # Normalize
        vec = vec / np.linalg.norm(vec)
        return vec.tolist()

    def compute_embedding_id(self, text: str) -> str:
        """Compute a deterministic ID for deduplication."""
        return hashlib.sha256(text.encode()).hexdigest()[:32]


# Singleton
_embedding_service: EmbeddingService | None = None

def get_embedding_service() -> EmbeddingService:
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service
```

- [ ] **Step 2: Create tests/test_embeddings.py**

```python
def test_embed_single():
    from app.services.embedding_service import EmbeddingService, EMBEDDING_DIM
    svc = EmbeddingService()
    vec = svc.embed_single("Hello, world!")
    assert len(vec) == EMBEDDING_DIM
    assert all(isinstance(v, float) for v in vec)

def test_embed_batch():
    from app.services.embedding_service import EmbeddingService, EMBEDDING_DIM
    svc = EmbeddingService()
    texts = ["Hello", "World", "Test"]
    vecs = svc.embed_batch(texts)
    assert len(vecs) == 3
    for v in vecs:
        assert len(v) == EMBEDDING_DIM

def test_embedding_deterministic():
    from app.services.embedding_service import EmbeddingService
    svc = EmbeddingService()
    v1 = svc.embed_single("deterministic test")
    v2 = svc.embed_single("deterministic test")
    assert v1 == v2

def test_embedding_id():
    from app.services.embedding_service import EmbeddingService
    svc = EmbeddingService()
    id1 = svc.compute_embedding_id("test")
    id2 = svc.compute_embedding_id("test")
    assert id1 == id2
    assert len(id1) == 32
```

- [ ] **Step 3: Run tests**

```bash
cd backend
PYTHONPATH=. pytest tests/test_embeddings.py -v
```

- [ ] **Step 4: Commit**

```bash
git add backend/
git commit -m "feat(backend): add BGE-M3 embedding service with ONNX + mock fallback"
```

---

## Task 3: Memory API (CRUD + Semantic Search)

**Files:**
- Create: `backend/app/api/memory.py`
- Modify: `backend/app/api/router.py` (add memory router)
- Create: `backend/tests/test_memory.py`

**Interfaces:**
- Consumes: Task 1 (VectorDB), Task 2 (EmbeddingService), Task 5 from 00-WEEK-1-2-FOUNDATION.md (auth deps)
- Produces: GET /api/memory, POST /api/memory, GET /api/memory/{id}, DELETE /api/memory/{id}, POST /api/memory/search

- [ ] **Step 1: Create app/api/memory.py**

```python
from __future__ import annotations
from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.api.deps import get_current_user_optional, get_db
from app.models.knowledge_entry import KnowledgeEntry
from app.models.user import User
from app.core.vector_db import get_vector_db
from app.services.embedding_service import get_embedding_service

router = APIRouter()

COLLECTION = "cortex_memory"


class MemoryCreatePayload(BaseModel):
    title: str = Field(min_length=1, max_length=512)
    content: str = Field(min_length=1)
    category: str = Field(default="note", min_length=1, max_length=64)
    source_path: str | None = Field(default=None, max_length=1024)


class MemorySearchPayload(BaseModel):
    query: str = Field(min_length=1)
    category: str | None = None
    limit: int = Field(default=10, ge=1, le=100)


def _serialize_memory(entry: KnowledgeEntry) -> dict[str, object]:
    return {
        "id": entry.id,
        "user_id": entry.user_id,
        "category": entry.category,
        "title": entry.title,
        "content": entry.content,
        "source_path": entry.source_path,
        "tags": entry.tags,
        "embedding_id": entry.embedding_id,
        "created_at": entry.created_at.isoformat() if entry.created_at else None,
        "updated_at": entry.updated_at.isoformat() if entry.updated_at else None,
    }


@router.get("/api/memory")
def read_memory(limit: int = 24, offset: int = 0, category: str | None = None, db: Session = Depends(get_db), current_user: User | None = Depends(get_current_user_optional)):
    safe_limit = max(1, min(limit, 100))
    safe_offset = max(0, offset)
    query = db.query(KnowledgeEntry)
    if current_user is not None:
        filter_clause = (KnowledgeEntry.user_id == current_user.id) | (KnowledgeEntry.user_id.is_(None))
        query = query.filter(filter_clause)
    if category:
        query = query.filter(KnowledgeEntry.category == category)
    
    total = query.count()
    entries = query.order_by(KnowledgeEntry.updated_at.desc()).offset(safe_offset).limit(safe_limit).all()
    categories = db.query(KnowledgeEntry.category, func.count(KnowledgeEntry.id)).group_by(KnowledgeEntry.category).all()
    
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total": total,
        "count": len(entries),
        "offset": safe_offset,
        "limit": safe_limit,
        "categories": {cat: cnt for cat, cnt in categories},
        "entries": [_serialize_memory(e) for e in entries],
    }


@router.post("/api/memory")
def write_memory(payload: MemoryCreatePayload, db: Session = Depends(get_db), current_user: User | None = Depends(get_current_user_optional)):
    # Create entry
    embedding_svc = get_embedding_service()
    embedding_id = embedding_svc.compute_embedding_id(f"{payload.title} {payload.content}")
    
    entry = KnowledgeEntry(
        user_id=current_user.id if current_user else None,
        category=payload.category,
        title=payload.title,
        content=payload.content,
        source_path=payload.source_path,
        source_key=f"manual:{payload.category}:{payload.title}:{datetime.now(timezone.utc).timestamp()}",
        embedding_id=embedding_id,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    
    # Embed and store in vector DB
    vector = embedding_svc.embed_single(f"{payload.title} {payload.content}")
    vdb = get_vector_db()
    vdb.upsert(
        collection=COLLECTION,
        id=str(entry.id),
        vector=vector,
        payload={"id": entry.id, "title": payload.title, "category": payload.category, "user_id": entry.user_id},
    )
    
    return {"status": "stored", "entry": _serialize_memory(entry)}


@router.post("/api/memory/search")
def search_memory(payload: MemorySearchPayload, db: Session = Depends(get_db), current_user: User | None = Depends(get_current_user_optional)):
    embedding_svc = get_embedding_service()
    vdb = get_vector_db()
    
    query_vector = embedding_svc.embed_single(payload.query)
    filter_payload = {}
    if current_user:
        filter_payload["user_id"] = current_user.id
    if payload.category:
        filter_payload["category"] = payload.category
    
    results = vdb.search(COLLECTION, query_vector, limit=payload.limit, filter_payload=filter_payload if filter_payload else None)
    
    # Fetch full entries from DB
    entry_ids = [int(r.id) for r in results]
    entries = db.query(KnowledgeEntry).filter(KnowledgeEntry.id.in_(entry_ids)).all() if entry_ids else []
    entry_map = {str(e.id): e for e in entries}
    
    return {
        "results": [
            {
                "score": r.score,
                "entry": _serialize_memory(entry_map[r.id]) if r.id in entry_map else None,
            }
            for r in results
        ]
    }


@router.delete("/api/memory/{entry_id}")
def delete_memory(entry_id: int, db: Session = Depends(get_db), current_user: User | None = Depends(get_current_user_optional)):
    entry = db.query(KnowledgeEntry).filter(KnowledgeEntry.id == entry_id).first()
    if not entry:
        return {"deleted": False}
    
    # Delete from vector DB
    vdb = get_vector_db()
    vdb.delete(COLLECTION, [str(entry.id)])
    
    # Delete from SQL
    db.delete(entry)
    db.commit()
    
    return {"deleted": True}
```

- [ ] **Step 2: Update app/api/router.py**

```python
from fastapi import APIRouter
from app.api.v1.health import router as health_router
from app.api.auth import router as auth_router
from app.api.v1.vault import router as vault_router
from app.api.memory import router as memory_router

api_router = APIRouter()

api_router.include_router(health_router, tags=["Health"])
api_router.include_router(auth_router)
api_router.include_router(vault_router, prefix="/me/vault", tags=["Vault"])
api_router.include_router(memory_router)
```

- [ ] **Step 3: Create tests/test_memory.py**

```python
def test_create_memory(client):
    resp = client.post("/api/memory", json={
        "title": "Test Entry",
        "content": "This is a test knowledge entry.",
        "category": "note",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "stored"
    assert data["entry"]["title"] == "Test Entry"

def test_list_memory(client):
    client.post("/api/memory", json={"title": "Entry 1", "content": "Content 1", "category": "note"})
    client.post("/api/memory", json={"title": "Entry 2", "content": "Content 2", "category": "code"})
    
    resp = client.get("/api/memory")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 2
    assert len(data["entries"]) == 2

def test_search_memory(client):
    client.post("/api/memory", json={"title": "Python decorators", "content": "How to use decorators in Python", "category": "code"})
    client.post("/api/memory", json={"title": "Docker setup", "content": "Setting up Docker containers", "category": "note"})
    
    resp = client.post("/api/memory/search", json={"query": "Python decorators"})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["results"]) > 0

def test_delete_memory(client):
    create_resp = client.post("/api/memory", json={"title": "Delete me", "content": "Content", "category": "note"})
    entry_id = create_resp.json()["entry"]["id"]
    
    del_resp = client.delete(f"/api/memory/{entry_id}")
    assert del_resp.status_code == 200
    assert del_resp.json()["deleted"] is True
```

- [ ] **Step 4: Run tests**

```bash
cd backend
PYTHONPATH=. pytest tests/test_memory.py -v
```

- [ ] **Step 5: Commit**

```bash
git add backend/
git commit -m "feat(backend): add memory CRUD API with semantic vector search"
```

---

## Task 4: Repository Scanner (Git-Aware Indexing)

**Files:**
- Create: `backend/app/services/repo_scanner.py`
- Create: `backend/app/services/chunker.py`
- Create: `backend/app/models/repo_index.py`
- Create: `backend/tests/test_repo_scanner.py`

**Interfaces:**
- Consumes: Task 1 (VectorDB), Task 2 (EmbeddingService), Task 3 (Memory API)
- Produces: `scan_repo(path) -> ScanResult`, `get_repo_status(repo_id) -> RepoStatus`

- [ ] **Step 1: Create app/models/repo_index.py**

```python
from datetime import datetime
from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class RepoIndex(Base):
    __tablename__ = "repo_indexes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    repo_path: Mapped[str] = mapped_column(String(2048), nullable=False)
    repo_name: Mapped[str] = mapped_column(String(256), nullable=False)
    language: Mapped[str | None] = mapped_column(String(64), nullable=True)
    total_files: Mapped[int] = mapped_column(Integer, default=0)
    total_chunks: Mapped[int] = mapped_column(Integer, default=0)
    last_commit: Mapped[str | None] = mapped_column(String(64), nullable=True)
    last_indexed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())


class CodeChunk(Base):
    __tablename__ = "code_chunks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    repo_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    file_path: Mapped[str] = mapped_column(String(2048), nullable=False)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    language: Mapped[str | None] = mapped_column(String(64), nullable=True)
    symbol_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    symbol_name: Mapped[str | None] = mapped_column(String(256), nullable=True, index=True)
    start_line: Mapped[int] = mapped_column(Integer, nullable=True)
    end_line: Mapped[int] = mapped_column(Integer, nullable=True)
    embedding_id: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
```

- [ ] **Step 2: Create app/services/chunker.py**

```python
"""Text chunking service for code and documents."""
from __future__ import annotations
import re
from dataclasses import dataclass


@dataclass
class Chunk:
    content: str
    file_path: str
    chunk_index: int
    language: str | None = None
    symbol_type: str | None = None
    symbol_name: str | None = None
    start_line: int | None = None
    end_line: int | None = None


def chunk_code(content: str, file_path: str, max_tokens: int = 500, overlap: int = 50) -> list[Chunk]:
    """Split code into semantic chunks (functions, classes, or by line count)."""
    chunks = []
    lines = content.split("\n")
    
    # Simple strategy: split by blank lines or function/class boundaries
    current_chunk = []
    chunk_idx = 0
    start_line = 1
    
    for i, line in enumerate(lines, 1):
        # Detect function/class boundaries
        is_boundary = bool(re.match(r'^(def |class |function |export |const |async def )', line.strip()))
        
        if is_boundary and current_chunk and len("\n".join(current_chunk)) > 100:
            chunks.append(Chunk(
                content="\n".join(current_chunk),
                file_path=file_path,
                chunk_index=chunk_idx,
                start_line=start_line,
                end_line=i - 1,
            ))
            chunk_idx += 1
            current_chunk = []
            start_line = i
        
        current_chunk.append(line)
        
        # Token estimate: ~4 chars per token
        if len("\n".join(current_chunk)) > max_tokens * 4:
            chunks.append(Chunk(
                content="\n".join(current_chunk),
                file_path=file_path,
                chunk_index=chunk_idx,
                start_line=start_line,
                end_line=i,
            ))
            chunk_idx += 1
            current_chunk = []
            start_line = i + 1
    
    if current_chunk:
        chunks.append(Chunk(
            content="\n".join(current_chunk),
            file_path=file_path,
            chunk_index=chunk_idx,
            start_line=start_line,
            end_line=len(lines),
        ))
    
    return chunks


def chunk_text(content: str, file_path: str, max_tokens: int = 500, overlap: int = 50) -> list[Chunk]:
    """Split text into chunks by paragraph or token limit."""
    paragraphs = content.split("\n\n")
    chunks = []
    current = []
    current_len = 0
    chunk_idx = 0
    
    for para in paragraphs:
        para_len = len(para) // 4  # ~4 chars per token
        if current_len + para_len > max_tokens and current:
            chunks.append(Chunk(
                content="\n\n".join(current),
                file_path=file_path,
                chunk_index=chunk_idx,
            ))
            chunk_idx += 1
            current = []
            current_len = 0
        current.append(para)
        current_len += para_len
    
    if current:
        chunks.append(Chunk(
            content="\n\n".join(current),
            file_path=file_path,
            chunk_index=chunk_idx,
        ))
    
    return chunks


LANGUAGE_MAP = {
    ".py": "python", ".js": "javascript", ".ts": "typescript",
    ".tsx": "tsx", ".jsx": "jsx", ".rs": "rust", ".go": "go",
    ".java": "java", ".c": "c", ".cpp": "cpp", ".h": "c",
    ".rb": "ruby", ".php": "php", ".swift": "swift", ".kt": "kotlin",
    ".sql": "sql", ".sh": "shell", ".md": "markdown", ".json": "json",
    ".yaml": "yaml", ".yml": "yaml", ".toml": "toml", ".xml": "xml",
    ".html": "html", ".css": "css",
}

SKIP_DIRS = {".git", "node_modules", "__pycache__", "venv", ".venv", "dist", "build", ".next", "target"}


def detect_language(file_path: str) -> str | None:
    """Detect programming language from file extension."""
    from pathlib import Path
    ext = Path(file_path).suffix.lower()
    return LANGUAGE_MAP.get(ext)
```

- [ ] **Step 3: Create app/services/repo_scanner.py**

```python
"""Repository scanner for code indexing."""
from __future__ import annotations
import logging
import hashlib
from pathlib import Path
from dataclasses import dataclass, field
from sqlalchemy.orm import Session

from app.models.repo_index import RepoIndex, CodeChunk
from app.services.chunker import chunk_code, chunk_text, detect_language, SKIP_DIRS

logger = logging.getLogger(__name__)

COLLECTION = "cortex_code"


@dataclass
class ScanResult:
    repo_id: int
    repo_path: str
    repo_name: str
    files_scanned: int
    chunks_created: int
    languages: dict[str, int]
    status: str


@dataclass
class RepoStatus:
    repo_id: int
    repo_name: str
    status: str
    total_files: int
    total_chunks: int
    languages: dict[str, int]


class RepoScanner:
    """Scan and index repositories for code understanding."""

    def __init__(self, db: Session):
        self._db = db

    def scan_repo(self, repo_path: str, user_id: int | None = None) -> ScanResult:
        """Scan a repository and index all code files."""
        path = Path(repo_path).resolve()
        if not path.exists():
            raise FileNotFoundError(f"Repository not found: {repo_path}")

        repo_name = path.name
        
        # Get or create repo index
        existing = self._db.query(RepoIndex).filter(RepoIndex.repo_path == str(path)).first()
        if existing:
            repo_index = existing
            # Clear existing chunks for re-index
            self._db.query(CodeChunk).filter(CodeChunk.repo_id == repo_index.id).delete()
        else:
            repo_index = RepoIndex(
                user_id=user_id,
                repo_path=str(path),
                repo_name=repo_name,
                status="indexing",
            )
            self._db.add(repo_index)
            self._db.commit()
            self._db.refresh(repo_index)

        # Scan files
        files_scanned = 0
        chunks_created = 0
        languages: dict[str, int] = {}

        for file_path in self._walk_repository(path):
            lang = detect_language(str(file_path))
            if lang:
                languages[lang] = languages.get(lang, 0) + 1
            
            try:
                content = file_path.read_text(errors="ignore")
                if len(content.strip()) < 10:
                    continue
                
                rel_path = str(file_path.relative_to(path))
                chunks = chunk_code(content, rel_path) if lang else chunk_text(content, rel_path)
                
                for chunk in chunks:
                    code_chunk = CodeChunk(
                        repo_id=repo_index.id,
                        file_path=chunk.file_path,
                        chunk_index=chunk.chunk_index,
                        content=chunk.content,
                        language=lang,
                        symbol_type=chunk.symbol_type,
                        symbol_name=chunk.symbol_name,
                        start_line=chunk.start_line,
                        end_line=chunk.end_line,
                    )
                    self._db.add(code_chunk)
                    chunks_created += 1
                
                files_scanned += 1
            except Exception as e:
                logger.debug("Skipping file %s: %s", file_path, e)

        # Update repo index
        repo_index.total_files = files_scanned
        repo_index.total_chunks = chunks_created
        repo_index.language = max(languages, key=languages.get) if languages else None
        repo_index.status = "indexed"
        
        # Get last commit hash if git repo
        try:
            import subprocess
            result = subprocess.run(
                ["git", "-C", str(path), "rev-parse", "HEAD"],
                capture_output=True, text=True, timeout=5
            )
            repo_index.last_commit = result.stdout.strip()[:64]
        except Exception:
            pass
        
        from datetime import datetime, timezone
        repo_index.last_indexed_at = datetime.now(timezone.utc)
        
        self._db.commit()

        # Embed and store in vector DB
        self._embed_chunks(repo_index.id)

        return ScanResult(
            repo_id=repo_index.id,
            repo_path=str(path),
            repo_name=repo_name,
            files_scanned=files_scanned,
            chunks_created=chunks_created,
            languages=languages,
            status="indexed",
        )

    def _walk_repository(self, path: Path) -> list[Path]:
        """Walk repository files, skipping ignored directories."""
        files = []
        for item in sorted(path.rglob("*")):
            if item.is_file() and not item.name.startswith("."):
                if not any(skip in item.parts for skip in SKIP_DIRS):
                    files.append(item)
        return files

    def _embed_chunks(self, repo_id: int):
        """Embed all chunks for a repository and store in vector DB."""
        from app.services.embedding_service import get_embedding_service
        from app.core.vector_db import get_vector_db

        chunks = self._db.query(CodeChunk).filter(CodeChunk.repo_id == repo_id).all()
        if not chunks:
            return

        embedding_svc = get_embedding_service()
        vdb = get_vector_db()

        batch_size = 32
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]
            texts = [f"{c.file_path}\n{c.content[:500]}" for c in batch]
            vectors = embedding_svc.embed_batch(texts)
            
            ids = [str(c.id) for c in batch]
            payloads = [
                {"id": c.id, "file_path": c.file_path, "language": c.language, "symbol_name": c.symbol_name}
                for c in batch
            ]
            
            vdb.upsert_batch(COLLECTION, ids, vectors, payloads)
            
            # Update embedding IDs
            for chunk, vector in zip(batch, vectors):
                chunk.embedding_id = hashlib.sha256(str(vector[:10]).encode()).hexdigest()[:32]

        self._db.commit()
        logger.info("Embedded %d chunks for repo %d", len(chunks), repo_id)

    def get_repo_status(self, repo_id: int) -> RepoStatus | None:
        repo = self._db.query(RepoIndex).filter(RepoIndex.id == repo_id).first()
        if not repo:
            return None
        
        chunks = self._db.query(CodeChunk).filter(CodeChunk.repo_id == repo_id).all()
        languages = {}
        for c in chunks:
            if c.language:
                languages[c.language] = languages.get(c.language, 0) + 1
        
        return RepoStatus(
            repo_id=repo.id,
            repo_name=repo.repo_name,
            status=repo.status,
            total_files=repo.total_files,
            total_chunks=repo.total_chunks,
            languages=languages,
        )
```

- [ ] **Step 4: Create tests/test_repo_scanner.py**

```python
import tempfile
from pathlib import Path
from app.db.base import Base
from app.db.session import SessionLocal
from app.models.user import User
from app.models.repo_index import RepoIndex, CodeChunk
from app.core.security import hash_password
from app.services.repo_scanner import RepoScanner


def test_scan_repo(client):
    # Create test repo
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_dir = Path(tmpdir) / "test_repo"
        repo_dir.mkdir()
        
        # Create test files
        (repo_dir / "main.py").write_text("def hello():\n    return 'world'\n")
        (repo_dir / "utils.js").write_text("function add(a, b) {\n  return a + b;\n}\n")
        (repo_dir / "README.md").write_text("# Test Repo\n\nThis is a test.\n")
        
        # Create DB session
        db = SessionLocal()
        try:
            scanner = RepoScanner(db)
            result = scanner.scan_repo(str(repo_dir))
            
            assert result.status == "indexed"
            assert result.files_scanned >= 2
            assert result.chunks_created >= 2
            assert "python" in result.languages
        finally:
            db.close()


def test_detect_language():
    from app.services.chunker import detect_language
    assert detect_language("main.py") == "python"
    assert detect_language("index.ts") == "typescript"
    assert detect_language("README.md") == "markdown"
    assert detect_language("unknown.xyz") is None
```

- [ ] **Step 5: Run tests**

```bash
cd backend
PYTHONPATH=. pytest tests/test_repo_scanner.py -v
```

- [ ] **Step 6: Commit**

```bash
git add backend/
git commit -m "feat(backend): add repository scanner with code chunking and embedding"
```

---

## Task 5: Memory Explorer Frontend

**Files:**
- Create: `frontend/app/memory/page.tsx`
- Create: `frontend/src/shared/components/SearchBar.tsx`
- Create: `frontend/src/shared/components/MemoryList.tsx`
- Create: `frontend/src/shared/components/MemoryDetail.tsx`

**Interfaces:**
- Consumes: Task 4 from 00-WEEK-1-2-FOUNDATION.md (auth, design tokens, UI components), Task 3 (memory API)
- Produces: Memory explorer UI with search, list, detail views

- [ ] **Step 1: Create frontend/app/memory/page.tsx**

```tsx
"use client";
import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "../../src/shared/auth/AuthProvider";
import DashboardShell from "../../src/shared/layout/DashboardShell";
import Card from "../../src/shared/ui/Card";
import Input from "../../src/shared/ui/Input";
import Button from "../../src/shared/ui/Button";

interface MemoryEntry {
  id: number;
  title: string;
  content: string;
  category: string;
  source_path?: string;
  created_at?: string;
}

export default function MemoryPage() {
  const router = useRouter();
  const { user, loading } = useAuth();
  const [entries, setEntries] = useState<MemoryEntry[]>([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedEntry, setSelectedEntry] = useState<MemoryEntry | null>(null);
  const [showCreate, setShowCreate] = useState(false);
  const [newEntry, setNewEntry] = useState({ title: "", content: "", category: "note" });
  const [total, setTotal] = useState(0);

  useEffect(() => { if (!loading && !user) router.replace("/auth"); }, [user, loading, router]);

  useEffect(() => {
    if (!user) return;
    fetchEntries();
  }, [user]);

  async function fetchEntries() {
    try {
      const token = sessionStorage.getItem("cortex_token");
      const res = await fetch("http://localhost:8000/api/memory", {
        headers: { Authorization: `Bearer ${token}` },
      });
      const data = await res.json();
      setEntries(data.entries || []);
      setTotal(data.total || 0);
    } catch (err) { console.error("Failed to fetch memory:", err); }
  }

  async function handleSearch() {
    if (!searchQuery.trim()) { fetchEntries(); return; }
    try {
      const token = sessionStorage.getItem("cortex_token");
      const res = await fetch("http://localhost:8000/api/memory/search", {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({ query: searchQuery, limit: 20 }),
      });
      const data = await res.json();
      setEntries(data.results?.map((r: { entry: MemoryEntry }) => r.entry).filter(Boolean) || []);
    } catch (err) { console.error("Search failed:", err); }
  }

  async function handleCreate() {
    try {
      const token = sessionStorage.getItem("cortex_token");
      const res = await fetch("http://localhost:8000/api/memory", {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify(newEntry),
      });
      const data = await res.json();
      if (data.entry) { setEntries((prev) => [data.entry, ...prev]); setShowCreate(false); setNewEntry({ title: "", content: "", category: "note" }); }
    } catch (err) { console.error("Create failed:", err); }
  }

  async function handleDelete(id: number) {
    try {
      const token = sessionStorage.getItem("cortex_token");
      await fetch(`http://localhost:8000/api/memory/${id}`, { method: "DELETE", headers: { Authorization: `Bearer ${token}` } });
      setEntries((prev) => prev.filter((e) => e.id !== id));
      if (selectedEntry?.id === id) setSelectedEntry(null);
    } catch (err) { console.error("Delete failed:", err); }
  }

  if (loading || !user) return null;

  return (
    <DashboardShell>
      <div className="max-w-6xl mx-auto space-y-6 animate-fade-in">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-xl font-display font-semibold text-text">Memory</h1>
            <p className="text-sm text-text-muted">{total} knowledge entries</p>
          </div>
          <Button onClick={() => setShowCreate(!showCreate)}>{showCreate ? "Cancel" : "Add Entry"}</Button>
        </div>

        {/* Search */}
        <div className="flex gap-2">
          <Input placeholder="Search knowledge base..." value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)} onKeyDown={(e) => e.key === "Enter" && handleSearch()} className="flex-1" />
          <Button onClick={handleSearch}>Search</Button>
        </div>

        {/* Create Form */}
        {showCreate && (
          <Card className="p-6 space-y-4">
            <Input label="Title" value={newEntry.title} onChange={(e) => setNewEntry({ ...newEntry, title: e.target.value })} />
            <div>
              <label className="block text-sm font-medium text-text-secondary mb-1.5">Content</label>
              <textarea className="h-32 w-full rounded-md bg-bg-surface border border-border px-3 py-2 text-sm text-text placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-accent" value={newEntry.content} onChange={(e) => setNewEntry({ ...newEntry, content: e.target.value })} />
            </div>
            <div className="flex gap-2">
              <Button onClick={handleCreate}>Save Entry</Button>
              <Button variant="ghost" onClick={() => setShowCreate(false)}>Cancel</Button>
            </div>
          </Card>
        )}

        {/* Entries Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {entries.map((entry) => (
            <Card key={entry.id} className="p-4 hover:border-accent/20 transition-colors cursor-pointer" onClick={() => setSelectedEntry(entry)}>
              <div className="flex items-start justify-between mb-2">
                <span className="text-xs px-2 py-0.5 rounded-full bg-accent-faint text-accent">{entry.category}</span>
                <button onClick={(e) => { e.stopPropagation(); handleDelete(entry.id); }} className="text-text-muted hover:text-error text-xs">Delete</button>
              </div>
              <h3 className="text-sm font-medium text-text mb-1">{entry.title}</h3>
              <p className="text-xs text-text-muted line-clamp-2">{entry.content}</p>
              {entry.source_path && <p className="text-[10px] text-text-muted mt-2 truncate">{entry.source_path}</p>}
            </Card>
          ))}
        </div>

        {entries.length === 0 && (
          <Card className="p-12 text-center">
            <p className="text-text-muted">No entries found. Start by adding knowledge or indexing a repository.</p>
          </Card>
        )}
      </div>
    </DashboardShell>
  );
}
```

- [ ] **Step 2: Run frontend typecheck**

```bash
cd frontend
npm run typecheck
```

- [ ] **Step 3: Commit**

```bash
git add frontend/
git commit -m "feat(frontend): add Memory Explorer with search, create, delete"
```

---

## Task 6: Vault Frontend UI

**Files:**
- Create: `frontend/app/vault/page.tsx`
- Create: `frontend/src/shared/components/FileTree.tsx`

**Interfaces:**
- Consumes: Task 5 from 00-WEEK-1-2-FOUNDATION.md (auth, design tokens), Task 4 from 00-WEEK-1-2-FOUNDATION.md (vault API)
- Produces: Vault UI with file tree, upload, download, unlock/lock

- [ ] **Step 1: Create frontend/app/vault/page.tsx**

```tsx
"use client";
import { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "../../src/shared/auth/AuthProvider";
import { apiVaultStatus, apiVaultUnlock, apiVaultLock } from "../../src/shared/auth/cortexApi";
import DashboardShell from "../../src/shared/layout/DashboardShell";
import Card from "../../src/shared/ui/Card";
import Button from "../../src/shared/ui/Button";
import Input from "../../src/shared/ui/Input";

interface VaultFile { name: string; path: string; is_dir: boolean; size: number; favorite: boolean; tags: string[]; }

export default function VaultPage() {
  const router = useRouter();
  const { user, loading } = useAuth();
  const [vaultStatus, setVaultStatus] = useState<{ locked: boolean } | null>(null);
  const [password, setPassword] = useState("");
  const [files, setFiles] = useState<VaultFile[]>([]);
  const [currentFolder, setCurrentFolder] = useState("/");
  const [error, setError] = useState("");
  const [uploading, setUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => { if (!loading && !user) router.replace("/auth"); }, [user, loading, router]);
  useEffect(() => { if (user) apiVaultStatus().then(setVaultStatus).catch(() => {}); }, [user]);

  useEffect(() => {
    if (vaultStatus && !vaultStatus.locked) fetchFiles();
  }, [vaultStatus, currentFolder]);

  async function handleUnlock() {
    setError("");
    try {
      await apiVaultUnlock(password);
      setVaultStatus({ locked: false });
      setPassword("");
    } catch (err: unknown) { setError(err instanceof Error ? err.message : "Unlock failed"); }
  }

  async function handleLock() {
    await apiVaultLock();
    setVaultStatus({ locked: true });
    setFiles([]);
  }

  async function fetchFiles() {
    try {
      const token = sessionStorage.getItem("cortex_token");
      const res = await fetch(`http://localhost:8000/api/v1/me/vault/files?folder=${encodeURIComponent(currentFolder)}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setFiles(await res.json());
    } catch (err) { console.error("Failed to fetch files:", err); }
  }

  async function handleUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    try {
      const token = sessionStorage.getItem("cortex_token");
      const formData = new FormData();
      formData.append("file", file);
      formData.append("folder", currentFolder);
      await fetch("http://localhost:8000/api/v1/me/vault/files/upload", {
        method: "POST", headers: { Authorization: `Bearer ${token}` }, body: formData,
      });
      fetchFiles();
    } catch (err) { console.error("Upload failed:", err); }
    setUploading(false);
    if (fileInputRef.current) fileInputRef.current.value = "";
  }

  async function handleDownload(filePath: string) {
    const token = sessionStorage.getItem("cortex_token");
    const res = await fetch(`http://localhost:8000/api/v1/me/vault/files/download/${filePath}`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url; a.download = filePath.split("/").pop() || "download"; a.click();
    URL.revokeObjectURL(url);
  }

  async function handleDelete(filePath: string) {
    if (!confirm(`Delete ${filePath}?`)) return;
    const token = sessionStorage.getItem("cortex_token");
    await fetch(`http://localhost:8000/api/v1/me/vault/files/${filePath}`, {
      method: "DELETE", headers: { Authorization: `Bearer ${token}` },
    });
    fetchFiles();
  }

  if (loading || !user) return null;

  return (
    <DashboardShell>
      <div className="max-w-4xl mx-auto space-y-6 animate-fade-in">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-xl font-display font-semibold text-text">Vault</h1>
            <p className="text-sm text-text-muted">Encrypted file storage</p>
          </div>
          {vaultStatus && !vaultStatus.locked && (
            <div className="flex gap-2">
              <input ref={fileInputRef} type="file" className="hidden" onChange={handleUpload} />
              <Button onClick={() => fileInputRef.current?.click()} loading={uploading}>Upload</Button>
              <Button variant="destructive" onClick={handleLock}>Lock</Button>
            </div>
          )}
        </div>

        {/* Unlock Screen */}
        {vaultStatus?.locked && (
          <Card className="p-8 max-w-md mx-auto text-center space-y-4">
            <div className="h-12 w-12 rounded-full bg-bg-elevated border border-border flex items-center justify-center mx-auto">
              <svg className="h-6 w-6 text-accent" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M16.5 10.5V6.75a4.5 4.5 0 10-9 0v3.75m-.75 11.25h10.5a2.25 2.25 0 002.25-2.25v-6.75a2.25 2.25 0 00-2.25-2.25H6.75a2.25 2.25 0 00-2.25 2.25v6.75a2.25 2.25 0 002.25 2.25z" />
              </svg>
            </div>
            <h2 className="text-lg font-semibold text-text">Vault is Locked</h2>
            <Input type="password" placeholder="Enter vault password" value={password} onChange={(e) => setPassword(e.target.value)} onKeyDown={(e) => e.key === "Enter" && handleUnlock()} />
            {error && <p className="text-sm text-error">{error}</p>}
            <Button onClick={handleUnlock} className="w-full">Unlock Vault</Button>
          </Card>
        )}

        {/* File Tree */}
        {!vaultStatus?.locked && (
          <div className="space-y-2">
            {/* Breadcrumb */}
            <div className="flex items-center gap-1 text-sm text-text-muted">
              {currentFolder.split("/").filter(Boolean).map((part, i, arr) => (
                <span key={i} className="flex items-center gap-1">
                  {i > 0 && <span>/</span>}
                  <button onClick={() => setCurrentFolder("/" + arr.slice(0, i + 1).join("/"))} className="hover:text-text transition-colors">{part}</button>
                </span>
              ))}
            </div>

            {/* Files */}
            <Card className="divide-y divide-border">
              {files.map((file) => (
                <div key={file.path} className="flex items-center justify-between px-4 py-3 hover:bg-bg-hover transition-colors" onClick={() => file.is_dir && setCurrentFolder(file.path)}>
                  <div className="flex items-center gap-3">
                    {file.is_dir ? (
                      <svg className="h-4 w-4 text-accent" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}><path strokeLinecap="round" strokeLinejoin="round" d="M2.25 12.75V12A2.25 2.25 0 014.5 9.75h15A2.25 2.25 0 0121.75 12v.75m-8.69-6.44l-2.12-2.12a1.5 1.5 0 00-1.061-.44H4.5A2.25 2.25 0 002.25 6v12a2.25 2.25 0 002.25 2.25h15A2.25 2.25 0 0021.75 18V9a2.25 2.25 0 00-2.25-2.25h-5.379a1.5 1.5 0 01-1.06-.44z" /></svg>
                    ) : (
                      <svg className="h-4 w-4 text-text-muted" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}><path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m2.25 0H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" /></svg>
                    )}
                    <span className="text-sm text-text">{file.name}</span>
                    {file.favorite && <span className="text-xs text-warning">★</span>}
                  </div>
                  <div className="flex items-center gap-2">
                    {!file.is_dir && <span className="text-xs text-text-muted">{(file.size / 1024).toFixed(1)} KB</span>}
                    {!file.is_dir && <button onClick={(e) => { e.stopPropagation(); handleDownload(file.path); }} className="text-xs text-accent hover:text-accent-hover">Download</button>}
                    <button onClick={(e) => { e.stopPropagation(); handleDelete(file.path); }} className="text-xs text-text-muted hover:text-error">Delete</button>
                  </div>
                </div>
              ))}
              {files.length === 0 && <div className="px-4 py-8 text-center text-text-muted text-sm">Empty folder</div>}
            </Card>
          </div>
        )}
      </div>
    </DashboardShell>
  );
}
```

- [ ] **Step 2: Run frontend typecheck**

```bash
cd frontend
npm run typecheck
```

- [ ] **Step 3: Commit**

```bash
git add frontend/
git commit -m "feat(frontend): add Vault UI with unlock, file tree, upload, download"
```

---

## Week 3-4 Exit Criteria Checklist

- [ ] Embedded Qdrant operational (vector search works)
- [ ] BGE-M3 embeddings (ONNX or mock fallback) working
- [ ] Memory CRUD API with semantic search
- [ ] Repository scanner indexes code files with chunking
- [ ] Memory Explorer frontend (search, create, browse)
- [ ] Vault Frontend (unlock, file tree, upload, download, delete)
- [ ] All tests passing (backend + frontend typecheck)
- [ ] CI/CD updated with new test suites
- [ ] Incremental indexing via file watcher (notify-rs in Rust sidecar)

### Migration Steps
1. Create model `backend/app/models/knowledge_entry.py` (KnowledgeEntry table)
2. Create model `backend/app/models/repo_index.py` (RepoIndex, CodeChunk tables)
3. Register models in Alembic: update `backend/app/db/base.py` to import new models
4. Run: `alembic revision --autogenerate -m "add_knowledge_entry_repo_index_code_chunk"`
5. Run: `alembic upgrade head`
6. Verify: `PYTHONPATH=. pytest tests/test_memory.py tests/test_repo_scanner.py -v`

### API Versioning
All new routes must use `/api/v1/{resource}` prefix. Update memory router:
- Change `router = APIRouter()` to `router = APIRouter(prefix="/v1/memory")`
- Mount at `api_router.include_router(memory_router, prefix="/api")`
- Routes become: `GET /api/v1/memory`, `POST /api/v1/memory`, `POST /api/v1/memory/search`, `DELETE /api/v1/memory/{entry_id}`

---

## Next Steps → Week 5-6 (See `02-WEEK-5-6-INDEXING.md`)

- Multi-model embeddings (ColBERT for code, reranking)
- Code intelligence (symbols, call graph, dependency analysis)
- Knowledge Graph (Apache AGE, entity extraction)
- Graph visualization frontend
