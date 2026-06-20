# Phase 4B: Smart Indexing & Retrieval

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make indexing intelligent. Add exclusion rules, real-time file watching, user-controlled indexing paths, incremental sync, and high-quality hybrid retrieval with reranking.

**Architecture:** Intelligent indexer with configurable inclusion/exclusion rules, polling-based file watcher integration, background sync with prioritization, hybrid retrieval (vector + keyword + graph) with LLM reranking.

**Tech Stack:** Python 3.12+, SQLAlchemy 2.0, Qdrant, polling-based file watcher, Next.js 15

---

## Why This Phase

Cortex's core value is "understanding the machine." Currently, indexing is naive — it indexes everything in a repo including node_modules, .git, build artifacts, and cache files. This wastes resources and pollutes search results. Users also can't control what gets indexed or see sync status.

---

## Task 1: Intelligent Indexing Rules

**Files:**
- Create: `backend/app/models/indexing_config.py`
- Create: `backend/app/services/indexing_rules.py`
- Create migration: `p00000000015_add_indexing_config.py`
- Modify: `backend/app/services/incremental_indexer.py`

**Interfaces:**
- Consumes: `IncrementalIndexer` (existing)
- Produces: `IndexingRules` — filters files before indexing

- [ ] **Step 1: Create IndexingConfig model**

```python
# backend/app/models/indexing_config.py
from __future__ import annotations
from datetime import datetime
from sqlalchemy import ForeignKey, String, Integer, JSON, DateTime, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from backend.app.db.base import Base


class IndexingConfig(Base):
    __tablename__ = "indexing_configs"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), default="default")
    include_paths: Mapped[list] = mapped_column(JSON, default=list)
    exclude_paths: Mapped[list] = mapped_column(JSON, default=list)
    include_patterns: Mapped[list] = mapped_column(JSON, default=list)
    exclude_patterns: Mapped[list] = mapped_column(JSON, default=list)
    max_file_size_bytes: Mapped[int] = mapped_column(Integer, default=1_000_000)
    follow_symlinks: Mapped[bool] = mapped_column(Boolean, default=False)
    sync_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    sync_interval_seconds: Mapped[int] = mapped_column(Integer, default=300)
    priority: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

- [ ] **Step 2: Create IndexingRules service**

```python
# backend/app/services/indexing_rules.py
from __future__ import annotations
import fnmatch
import os
from pathlib import Path
from backend.app.models.indexing_config import IndexingConfig
from backend.app.services.chunker import SKIP_DIRS

# Default exclusion rules — things that should NEVER be indexed
DEFAULT_EXCLUSIONS: dict[str, set[str] | list[str] | int] = {
    "directories": SKIP_DIRS | {
        ".pytest_cache", ".mypy_cache", ".ruff_cache",
        ".venv", "env", ".env", ".cache",
        "coverage", ".coverage", "htmlcov",
        "vendor", ".bundle", "tmp", ".tmp",
        ".DS_Store", "Thumbs.db", ".svn", ".hg",
        "logs", "dist", "build", ".next", ".nuxt",
    },
    "patterns": [
        "*.min.js", "*.min.css", "*.map", "*.pyc", "*.pyo",
        "*.so", "*.dylib", "*.dll", "*.exe", "*.bin",
        "*.jpg", "*.jpeg", "*.png", "*.gif", "*.bmp", "*.ico", "*.svg",
        "*.mp3", "*.mp4", "*.wav", "*.avi", "*.mov",
        "*.zip", "*.tar", "*.gz", "*.rar", "*.7z",
        "*.pdf", "*.doc", "*.docx", "*.xls", "*.xlsx",
        "*.lock", "*.sum", "package-lock.json", "yarn.lock",
        ".env.*", "*.log", "*.tmp", "*.temp",
    ],
    "max_size_bytes": 1_000_000,
}


class IndexingRules:
    """Determines which files should be indexed."""

    def __init__(self, config: IndexingConfig | None = None):
        self._config = config

    def should_index(self, file_path: str, base_dir: str) -> bool:
        """Check if a file should be indexed."""
        rel_path = os.path.relpath(file_path, base_dir)
        parts = Path(rel_path).parts

        if self._is_excluded_directory(parts):
            return False

        if self._is_excluded_pattern(os.path.basename(file_path)):
            return False

        try:
            size = os.path.getsize(file_path)
            max_size = self._config.max_file_size_bytes if self._config else DEFAULT_EXCLUSIONS["max_size_bytes"]
            if size > max_size:
                return False
        except OSError:
            return False

        if self._config and self._config.include_paths:
            if not any(rel_path.startswith(p) for p in self._config.include_paths):
                return False

        if self._config and self._config.exclude_paths:
            if any(rel_path.startswith(p) for p in self._config.exclude_paths):
                return False

        if self._config and self._config.include_patterns:
            if not any(fnmatch.fnmatch(file_path, p) for p in self._config.include_patterns):
                return False

        if self._config and self._config.exclude_patterns:
            if any(fnmatch.fnmatch(file_path, p) for p in self._config.exclude_patterns):
                return False

        return True

    def _is_excluded_directory(self, parts: tuple[str, ...]) -> bool:
        excluded = DEFAULT_EXCLUSIONS["directories"]
        if self._config and self._config.exclude_paths:
            excluded = excluded | set(self._config.exclude_paths)
        return any(part in excluded or part.endswith(".egg-info") for part in parts[:-1])

    def _is_excluded_pattern(self, filename: str) -> bool:
        patterns = DEFAULT_EXCLUSIONS["patterns"]
        if self._config and self._config.exclude_patterns:
            patterns = patterns + self._config.exclude_patterns
        return any(fnmatch.fnmatch(filename, p) for p in patterns)

    def get_stats(self, base_dir: str) -> dict:
        """Scan directory and return indexing stats without actually indexing."""
        total = 0
        included = 0
        excluded_by_size = 0
        excluded_by_pattern = 0
        excluded_by_directory = 0

        for root, dirs, files in os.walk(base_dir):
            for f in files:
                total += 1
                fp = os.path.join(root, f)
                rel = os.path.relpath(fp, base_dir)
                parts = Path(rel).parts

                if self._is_excluded_directory(parts):
                    excluded_by_directory += 1
                    continue
                if self._is_excluded_pattern(f):
                    excluded_by_pattern += 1
                    continue
                try:
                    if os.path.getsize(fp) > (self._config.max_file_size_bytes if self._config else DEFAULT_EXCLUSIONS["max_size_bytes"]):
                        excluded_by_size += 1
                        continue
                except OSError:
                    continue
                included += 1

        return {
            "total_files": total,
            "will_index": included,
            "excluded_by_directory": excluded_by_directory,
            "excluded_by_pattern": excluded_by_pattern,
            "excluded_by_size": excluded_by_size,
        }
```

- [ ] **Step 3: Create Alembic migration**

```bash
cd /home/adi/Desktop/Cortex-Workspace && uv run alembic revision -m "add indexing configs table" --head=n00000000014
```

Write migration file `migrations/versions/p00000000015_add_indexing_config.py`:

```python
"""add indexing configs table

Revision ID: p00000000015
Revises: n00000000014
"""
from alembic import op
import sqlalchemy as sa

revision = "p00000000015"
down_revision = "n00000000014"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "indexing_configs",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id"), nullable=False, index=True),
        sa.Column("name", sa.String(255), server_default="default"),
        sa.Column("include_paths", sa.JSON, nullable=True),
        sa.Column("exclude_paths", sa.JSON, nullable=True),
        sa.Column("include_patterns", sa.JSON, nullable=True),
        sa.Column("exclude_patterns", sa.JSON, nullable=True),
        sa.Column("max_file_size_bytes", sa.Integer, server_default="1000000"),
        sa.Column("follow_symlinks", sa.Boolean, server_default="false"),
        sa.Column("sync_enabled", sa.Boolean, server_default="true"),
        sa.Column("sync_interval_seconds", sa.Integer, server_default="300"),
        sa.Column("priority", sa.Integer, server_default="0"),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("indexing_configs")
```

- [ ] **Step 4: Integrate rules into incremental indexer**

The `IncrementalIndexer` has no `_should_index_file` method — it uses `_walk_repository()` at line 130 with `SKIP_DIRS` and `TRACKED_EXTENSIONS`. To integrate custom rules, we monkey-patch `SKIP_DIRS` at import time and add a post-filter in `_walk_repository()`.

```python
# In backend/app/services/incremental_indexer.py, add a method and modify _walk_repository:

# Add this import at the top of the file:
# from backend.app.services.indexing_rules import IndexingRules

    def _walk_repository(self, path: Path, rules: IndexingRules | None = None) -> list[Path]:
        """Walk repository files, skipping ignored directories.

        If rules is provided, applies additional IndexingRules filtering.
        """
        files: list[Path] = []
        for root, dirs, filenames in path.walk():
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
            for filename in filenames:
                file_path = Path(root) / filename
                if file_path.is_file() and file_path.suffix in TRACKED_EXTENSIONS:
                    if rules and not rules.should_index(str(file_path), str(path)):
                        continue
                    files.append(file_path)
        return sorted(files)
```

Then modify `index_repo` to accept optional rules:

```python
    def index_repo(self, repo_id: int, force: bool = False, rules: IndexingRules | None = None) -> IndexResult:
        # ... existing code up to _walk_repository call ...
        all_files = self._walk_repository(path, rules=rules)
        # ... rest unchanged ...
```

- [ ] **Step 5: Compile + migrate**

```bash
cd /home/adi/Desktop/Cortex-Workspace && uv run python -m py_compile backend/app/models/indexing_config.py && uv run python -m py_compile backend/app/services/indexing_rules.py && uv run python -m py_compile backend/app/services/incremental_indexer.py && uv run alembic upgrade head && echo "PASS"
```

- [ ] **Step 6: Commit**

```bash
git add backend/app/models/indexing_config.py backend/app/services/indexing_rules.py migrations/versions/p00000000015_add_indexing_config.py backend/app/services/incremental_indexer.py
git commit -m "feat: intelligent indexing rules with exclusion patterns and file size limits"
```

---

## Task 2: Indexing Configuration API & UI

**Files:**
- Create: `backend/app/api/v1/indexing.py`
- Modify: `backend/app/api/router.py` (register new router)
- Modify: `frontend/app/settings/page.tsx` (add indexing settings section)

**Interfaces:**
- Consumes: `IndexingConfig` model, `IndexingRules` service
- Produces: API for managing indexing rules, UI for configuring them

- [ ] **Step 1: Create indexing API**

```python
# backend/app/api/v1/indexing.py
from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from backend.app.core.db import get_current_user, get_db
from backend.app.models.user import User
from backend.app.models.indexing_config import IndexingConfig
from backend.app.services.indexing_rules import IndexingRules

router = APIRouter()


class IndexingConfigPayload(BaseModel):
    name: str = "default"
    include_paths: list[str] = Field(default_factory=list)
    exclude_paths: list[str] = Field(default_factory=list)
    include_patterns: list[str] = Field(default_factory=list)
    exclude_patterns: list[str] = Field(default_factory=list)
    max_file_size_bytes: int = 1_000_000
    follow_symlinks: bool = False
    sync_enabled: bool = True
    sync_interval_seconds: int = 300
    priority: int = 0


@router.get("/indexing/config")
async def get_indexing_config(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    config = db.query(IndexingConfig).filter(
        IndexingConfig.user_id == current_user.id
    ).first()
    if not config:
        return {"config": None, "defaults": True}
    return {
        "config": {
            "id": config.id,
            "name": config.name,
            "include_paths": config.include_paths,
            "exclude_paths": config.exclude_paths,
            "include_patterns": config.include_patterns,
            "exclude_patterns": config.exclude_patterns,
            "max_file_size_bytes": config.max_file_size_bytes,
            "follow_symlinks": config.follow_symlinks,
            "sync_enabled": config.sync_enabled,
            "sync_interval_seconds": config.sync_interval_seconds,
            "priority": config.priority,
        }
    }


@router.put("/indexing/config")
async def update_indexing_config(
    payload: IndexingConfigPayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    config = db.query(IndexingConfig).filter(
        IndexingConfig.user_id == current_user.id,
        IndexingConfig.name == payload.name,
    ).first()
    if not config:
        config = IndexingConfig(user_id=current_user.id, name=payload.name)
        db.add(config)

    for field, value in payload.model_dump().items():
        setattr(config, field, value)
    db.commit()
    return {"status": "saved"}


@router.post("/indexing/preview")
async def preview_indexing(
    repo_path: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Preview what would be indexed for a given path."""
    config = db.query(IndexingConfig).filter(
        IndexingConfig.user_id == current_user.id
    ).first()
    rules = IndexingRules(config)
    stats = rules.get_stats(repo_path)
    return stats
```

- [ ] **Step 2: Register router**

```python
# In backend/app/api/router.py, add:
from backend.app.api.v1 import indexing
# ... existing imports ...

api_router.include_router(indexing.router, tags=["indexing"])
```

- [ ] **Step 3: Compile check**

```bash
cd /home/adi/Desktop/Cortex-Workspace && uv run python -m py_compile backend/app/api/v1/indexing.py && uv run python -m py_compile backend/app/api/router.py && echo "PASS"
```

- [ ] **Step 4: Commit**

```bash
git add backend/app/api/v1/indexing.py backend/app/api/router.py
git commit -m "feat: indexing configuration API with preview endpoint"
```

---

## Task 3: File Watcher Integration

**Files:**
- Create: `backend/app/services/file_watcher.py`
- Modify: `backend/app/main.py` (start watcher on startup)

**Interfaces:**
- Consumes: `IndexingRules` (Task 1), `IncrementalIndexer` (existing)
- Produces: Real-time file change detection → background re-indexing

- [ ] **Step 1: Create file watcher service**

Uses polling (stat-based mtime comparison) for reliable cross-platform file change detection without requiring `watchdog`.

```python
# backend/app/services/file_watcher.py
from __future__ import annotations
import asyncio
import logging
import os
from pathlib import Path
from collections import defaultdict

logger = logging.getLogger(__name__)


class FileWatcher:
    """Watches directories for changes using polling and triggers re-indexing."""

    def __init__(self, poll_interval: float = 5.0):
        self._watched: dict[str, dict] = {}  # path -> config
        self._pending_changes: dict[str, set[str]] = defaultdict(set)
        self._snapshots: dict[str, dict[str, float]] = {}  # path -> {filepath: mtime}
        self._poll_interval = poll_interval
        self._debounce_task: asyncio.Task | None = None
        self._running = False

    def watch(self, repo_path: str, repo_id: int) -> None:
        """Start watching a directory. Takes initial mtime snapshot."""
        self._watched[repo_path] = {"repo_id": repo_id}
        self._snapshots[repo_path] = self._take_snapshot(repo_path)
        logger.info("Watching %s for changes (repo %d)", repo_path, repo_id)

    def unwatch(self, repo_path: str) -> None:
        """Stop watching a directory."""
        self._watched.pop(repo_path, None)
        self._snapshots.pop(repo_path, None)
        self._pending_changes.pop(repo_path, None)

    def _take_snapshot(self, repo_path: str) -> dict[str, float]:
        """Build a {filepath: mtime} snapshot, respecting SKIP_DIRS."""
        from backend.app.services.chunker import SKIP_DIRS
        snapshot: dict[str, float] = {}
        for root, dirs, files in os.walk(repo_path):
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
            for f in files:
                fp = os.path.join(root, f)
                try:
                    snapshot[fp] = os.path.getmtime(fp)
                except OSError:
                    continue
        return snapshot

    async def start(self) -> None:
        """Start the file watcher polling loop."""
        self._running = True
        self._debounce_task = asyncio.create_task(self._poll_loop())
        logger.info("File watcher started (poll interval %.1fs)", self._poll_interval)

    async def stop(self) -> None:
        """Stop the file watcher."""
        self._running = False
        if self._debounce_task:
            self._debounce_task.cancel()
            try:
                await self._debounce_task
            except asyncio.CancelledError:
                pass
        logger.info("File watcher stopped")

    async def _poll_loop(self) -> None:
        """Periodically poll filesystem for changes."""
        while self._running:
            try:
                await asyncio.sleep(self._poll_interval)
                await self._poll_and_record()
                if self._pending_changes:
                    await self._process_changes()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("File watcher poll error: %s", e)
                await asyncio.sleep(self._poll_interval)

    async def _poll_and_record(self) -> None:
        """Compare current mtime against snapshot, record changes."""
        for repo_path, config in list(self._watched.items()):
            new_snapshot = self._take_snapshot(repo_path)
            old_snapshot = self._snapshots.get(repo_path, {})

            # Detect modified or created files
            for fp, mtime in new_snapshot.items():
                if fp not in old_snapshot or old_snapshot[fp] != mtime:
                    self._pending_changes[repo_path].add(fp)

            # Detect deleted files
            for fp in old_snapshot:
                if fp not in new_snapshot:
                    self._pending_changes[repo_path].add(fp)

            # Update snapshot
            self._snapshots[repo_path] = new_snapshot

    async def _process_changes(self) -> None:
        """Process accumulated file changes by triggering incremental re-index."""
        changes = dict(self._pending_changes)
        self._pending_changes.clear()

        for repo_path, files in changes.items():
            config = self._watched.get(repo_path)
            if not config:
                continue

            logger.info("Processing %d file changes in %s", len(files), repo_path)

            try:
                from backend.app.tasks.worker import enqueue_task
                await enqueue_task("index_repo_task", config["repo_id"])
            except Exception as e:
                logger.error("Failed to trigger re-index for %s: %s", repo_path, e)

    @property
    def watched_count(self) -> int:
        return len(self._watched)

    @property
    def pending_count(self) -> int:
        return sum(len(v) for v in self._pending_changes.values())


# Singleton
file_watcher = FileWatcher()
```

- [ ] **Step 2: Integrate with app lifespan**

```python
# In backend/app/main.py, modify the lifespan function:
# Add before the yield:
    from backend.app.services.file_watcher import file_watcher
    await file_watcher.start()
# Add after the yield:
    await file_watcher.stop()
```

The full lifespan block becomes:

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"{settings.APP_NAME} started")

    ensure_system_dirs()
    import sys

    if "pytest" not in sys.modules:
        bootstrap_database()

    from backend.app.core.redis import redis_cache
    await redis_cache.ping()

    try:
        from backend.app.db import session as db_session
        if "pytest" not in sys.modules:
            db_session.get_engine()
            logger.info("System database initialized at %s", db_session.get_database_url())
    except Exception as e:
        logger.error("Failed to initialize system database on startup: %s", e)

    from backend.app.services.file_watcher import file_watcher
    await file_watcher.start()

    yield

    await file_watcher.stop()

    try:
        await redis_cache.close()
    except Exception:
        pass
    logger.info("Redis cache connection closed")
```

- [ ] **Step 3: Compile check**

```bash
cd /home/adi/Desktop/Cortex-Workspace && uv run python -m py_compile backend/app/services/file_watcher.py && uv run python -m py_compile backend/app/main.py && echo "PASS"
```

- [ ] **Step 4: Commit**

```bash
git add backend/app/services/file_watcher.py backend/app/main.py
git commit -m "feat: polling-based file watcher with debounce and background re-indexing"
```

---

## Task 4: Hybrid Retrieval

**Files:**
- Create: `backend/app/services/hybrid_retrieval.py`
- Modify: `backend/app/services/cross_file_search.py`

**Interfaces:**
- Consumes: `VectorDB`, `GraphNode`, `GraphEdge`, `CodeChunk`
- Produces: Combined vector + keyword + graph retrieval with reranking

- [ ] **Step 1: Create hybrid retrieval service**

```python
# backend/app/services/hybrid_retrieval.py
from __future__ import annotations
import json
import logging
import re
from dataclasses import dataclass
from sqlalchemy.orm import Session
from backend.app.core.vector_db import get_vector_db
from backend.app.models.graph import GraphNode, GraphEdge
from backend.app.models.repo_index import CodeChunk

logger = logging.getLogger(__name__)

CODE_COLLECTION = "cortex_code"


@dataclass
class RetrievalResult:
    content: str
    source: str  # "vector", "keyword", "graph"
    score: float
    file_path: str | None = None
    node_id: int | None = None
    context: dict | None = None


class HybridRetrieval:
    """Combines vector similarity, keyword matching, and graph traversal for retrieval."""

    def __init__(self, db: Session):
        self._db = db

    async def retrieve(
        self,
        query: str,
        repo_id: int | None = None,
        max_results: int = 20,
        use_reranking: bool = True,
    ) -> list[RetrievalResult]:
        """Hybrid retrieval: vector + keyword + graph, then rerank."""
        vector_results = await self._vector_search(query, repo_id, max_results)
        keyword_results = await self._keyword_search(query, repo_id, max_results)
        graph_results = await self._graph_search(query, repo_id, max_results)

        all_results = self._merge_results(vector_results, keyword_results, graph_results)

        if use_reranking and len(all_results) > 3:
            all_results = await self._rerank(query, all_results)

        return all_results[:max_results]

    async def _vector_search(self, query: str, repo_id: int | None, limit: int) -> list[RetrievalResult]:
        """Semantic vector search."""
        try:
            from backend.app.services.embedding_service import get_embedding_service
            embedding_svc = get_embedding_service()
            vdb = get_vector_db()

            query_vector = embedding_svc.embed_single(query)

            filter_payload: dict[str, str | int] = {}
            if repo_id is not None:
                filter_payload["repo_id"] = repo_id

            results = vdb.search(
                CODE_COLLECTION,
                query_vector,
                limit=limit,
                filter_payload=filter_payload if filter_payload else None,
            )
            return [
                RetrievalResult(
                    content=r.get("payload", {}).get("content", ""),
                    source="vector",
                    score=r.get("score", 0.0),
                    file_path=r.get("payload", {}).get("file_path"),
                    node_id=r.get("payload", {}).get("chunk_id"),
                )
                for r in results
            ]
        except Exception as e:
            logger.warning("Vector search failed: %s", e)
            return []

    async def _keyword_search(self, query: str, repo_id: int | None, limit: int) -> list[RetrievalResult]:
        """PostgreSQL full-text search."""
        try:
            query_lower = query.lower()
            q = self._db.query(CodeChunk).filter(
                CodeChunk.content.ilike(f"%{query_lower}%")
            )
            if repo_id is not None:
                q = q.filter(CodeChunk.repo_id == repo_id)
            chunks = q.limit(limit).all()
            return [
                RetrievalResult(
                    content=c.content[:500],
                    source="keyword",
                    score=0.5,
                    file_path=c.file_path,
                )
                for c in chunks
            ]
        except Exception as e:
            logger.warning("Keyword search failed: %s", e)
            return []

    async def _graph_search(self, query: str, repo_id: int | None, limit: int) -> list[RetrievalResult]:
        """Graph-based retrieval — find nodes related to query and traverse edges."""
        try:
            query_terms = query.lower().split()
            q = self._db.query(GraphNode)
            if repo_id is not None:
                q = q.filter(GraphNode.repo_id == repo_id)
            nodes = q.limit(200).all()

            matched_nodes = []
            for node in nodes:
                name = (node.name or "").lower()
                if any(term in name for term in query_terms):
                    matched_nodes.append(node)

            results = []
            for node in matched_nodes[:limit]:
                edges = self._db.query(GraphEdge).filter(
                    (GraphEdge.source_id == node.id) | (GraphEdge.target_id == node.id)
                ).limit(5).all()

                context = {
                    "node_name": node.name,
                    "node_type": node.node_type,
                    "edges": [
                        {
                            "type": e.edge_type,
                            "target": e.target_id,
                        }
                        for e in edges
                    ],
                }
                results.append(RetrievalResult(
                    content=f"Symbol: {node.name} ({node.node_type})",
                    source="graph",
                    score=0.4,
                    node_id=node.id,
                    context=context,
                ))

            return results
        except Exception as e:
            logger.warning("Graph search failed: %s", e)
            return []

    def _merge_results(
        self,
        vector: list[RetrievalResult],
        keyword: list[RetrievalResult],
        graph: list[RetrievalResult],
    ) -> list[RetrievalResult]:
        """Merge results with score boosting for multi-source matches."""
        seen: dict[str, RetrievalResult] = {}
        for result in vector + keyword + graph:
            key = result.file_path or str(result.node_id) or result.content[:100]
            if key in seen:
                existing = seen[key]
                existing.score = min(existing.score + 0.2, 1.0)
                existing.source = f"{existing.source}+{result.source}"
            else:
                seen[key] = result

        return sorted(seen.values(), key=lambda r: r.score, reverse=True)

    async def _rerank(self, query: str, results: list[RetrievalResult]) -> list[RetrievalResult]:
        """Use LLM to rerank results by relevance with robust JSON parsing."""
        try:
            from backend.app.services.llm.provider import LLMProvider

            # Take top 10 for reranking
            candidates = results[:10]
            context_text = "\n\n".join(
                f"[{i+1}] ({r.source}) {r.content[:200]}"
                for i, r in enumerate(candidates)
            )

            messages = [
                {"role": "system", "content": (
                    "You are a search ranking assistant. Given a query and search results, "
                    "return a JSON array of result indices ranked by relevance (most relevant first). "
                    "Only return the JSON array, nothing else. Example: [3, 1, 5, 2, 4]"
                )},
                {"role": "user", "content": f"Query: {query}\n\nResults:\n{context_text}"},
            ]

            # Find a usable LLM provider instance
            from backend.app.services.llm import _provider  # type: ignore[attr-defined]
            response_text, _ = await _provider.chat(messages, tools=[], config=None)

            ranking = self._parse_ranking(response_text)
            if not ranking:
                return results

            reranked = [candidates[i - 1] for i in ranking if 0 < i <= len(candidates)]
            ranked_ids = {id(r) for r in reranked}
            reranked.extend(r for r in candidates if id(r) not in ranked_ids)

            return reranked
        except Exception as e:
            logger.warning("LLM reranking failed, using original order: %s", e)
            return results

    @staticmethod
    def _parse_ranking(text: str) -> list[int] | None:
        """Robustly parse a JSON array of integers from LLM output."""
        text = text.strip()
        # Try direct JSON parse
        try:
            result = json.loads(text)
            if isinstance(result, list):
                return [int(x) for x in result]
        except (json.JSONDecodeError, ValueError):
            pass
        # Fallback: regex extract all integers from the response
        match = re.search(r"\[[\d\s,]+\]", text)
        if match:
            try:
                result = json.loads(match.group())
                return [int(x) for x in result]
            except (json.JSONDecodeError, ValueError):
                pass
        return None
```

- [ ] **Step 2: Wire into cross_file_search**

```python
# In backend/app/services/cross_file_search.py, add method to CrossFileSearch class:

    async def hybrid_search(self, query: str, repo_id: int | None = None, max_results: int = 20):
        """Use hybrid retrieval for better results."""
        from backend.app.services.hybrid_retrieval import HybridRetrieval
        retrieval = HybridRetrieval(self._db)
        return await retrieval.retrieve(query, repo_id, max_results)
```

- [ ] **Step 3: Compile check**

```bash
cd /home/adi/Desktop/Cortex-Workspace && uv run python -m py_compile backend/app/services/hybrid_retrieval.py && uv run python -m py_compile backend/app/services/cross_file_search.py && echo "PASS"
```

- [ ] **Step 4: Commit**

```bash
git add backend/app/services/hybrid_retrieval.py backend/app/services/cross_file_search.py
git commit -m "feat: hybrid retrieval with vector + keyword + graph and LLM reranking"
```

---

## Task 5: Sync Status & Indexing Dashboard

**Files:**
- Create: `backend/app/api/v1/sync.py`
- Modify: `backend/app/api/router.py` (register sync router)
- Modify: `frontend/app/app/page.tsx` (add sync status to dashboard)
- Create: `frontend/src/shared/components/SyncStatus.tsx`

**Interfaces:**
- Consumes: `FileWatcher`, `IncrementalIndexer`
- Produces: Real-time sync status display

- [ ] **Step 1: Create sync status API**

```python
# backend/app/api/v1/sync.py
from __future__ import annotations
from fastapi import APIRouter, Depends
from backend.app.core.db import get_current_user
from backend.app.models.user import User

router = APIRouter()


@router.get("/sync/status")
async def get_sync_status(
    current_user: User = Depends(get_current_user),
):
    from backend.app.services.file_watcher import file_watcher

    return {
        "watching": file_watcher.watched_count,
        "pending_changes": file_watcher.pending_count,
        "status": "syncing" if file_watcher.pending_count > 0 else "idle",
    }
```

- [ ] **Step 2: Create SyncStatus component**

```tsx
// frontend/src/shared/components/SyncStatus.tsx
"use client";

import { useEffect, useState } from "react";
import { RefreshCw, Check, Loader2 } from "lucide-react";
import { api } from "@/shared/api/client";

interface SyncStatusData {
  watching: number;
  pending_changes: number;
  status: "idle" | "syncing";
}

export default function SyncStatus() {
  const [status, setStatus] = useState<SyncStatusData | null>(null);

  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const data = await api.get<SyncStatusData>("/api/v1/sync/status");
        setStatus(data);
      } catch {}
    };
    fetchStatus();
    const interval = setInterval(fetchStatus, 5000);
    return () => clearInterval(interval);
  }, []);

  if (!status) return null;

  return (
    <div className="flex items-center gap-2 text-xs text-text-muted">
      {status.status === "syncing" ? (
        <Loader2 size={12} className="animate-spin text-accent" />
      ) : (
        <Check size={12} className="text-success" />
      )}
      <span>
        {status.status === "syncing"
          ? `Syncing ${status.pending_changes} files...`
          : `${status.watching} repos watched`}
      </span>
    </div>
  );
}
```

- [ ] **Step 3: Add sync status to dashboard header**

```tsx
// In frontend/app/app/page.tsx, add to the hero section:
import SyncStatus from "@/shared/components/SyncStatus";
// Add below the user welcome:
<SyncStatus />
```

- [ ] **Step 4: Register sync router**

```python
# In backend/app/api/router.py, add:
from backend.app.api.v1 import sync
api_router.include_router(sync.router, tags=["sync"])
```

- [ ] **Step 5: Build check**

```bash
cd /home/adi/Desktop/Cortex-Workspace/frontend && npx next build 2>&1 | tail -15
```

- [ ] **Step 6: Commit**

```bash
git add backend/app/api/v1/sync.py backend/app/api/router.py frontend/src/shared/components/SyncStatus.tsx frontend/app/app/page.tsx
git commit -m "feat: sync status API and dashboard indicator"
```

---

## Exit Criteria

- [ ] Default exclusion rules skip node_modules, .git, build artifacts, caches, binaries
- [ ] User-configurable include/exclude paths and patterns
- [ ] File size limits enforced
- [ ] Indexing preview shows what would be indexed before running
- [ ] File watcher detects changes via mtime polling with debounce
- [ ] Background re-index triggered on file changes using correct `enqueue_task("index_repo_task", repo_id)` call
- [ ] Hybrid retrieval combines vector + keyword + graph
- [ ] LLM reranking with robust JSON parsing (try/except + regex fallback)
- [ ] Keyword search filters by `repo_id`
- [ ] Sync status shows in dashboard
- [ ] All code compiles and builds clean
- [ ] Git commit for each task
