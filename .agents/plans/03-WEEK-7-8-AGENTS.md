# Unified Search, Agents & Local Models Plan (Weeks 7-8)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build unified search across all data types, a local agent runtime with Coder and Researcher agents, and on-device model management — enabling autonomous AI assistance by end of Week 8.

**Architecture:** Unified search federates across Qdrant (vectors), PostgreSQL (graph + metadata), and filesystem (files) with reciprocal rank fusion. Agent runtime is an async task executor with tool-use loop. Local models run via llama.cpp Python bindings with automatic GGUF download. Coder agent has file-read/write/execute tools. Researcher agent has search/browse tools.

**Tech Stack:** llama-cpp-python, Qdrant client, SQLAlchemy 2.0, Next.js 15, React 19, SSE for streaming, asyncio TaskGroups.

## Global Constraints

- Python 3.12+, Node.js 20+, Rust 2024 edition
- TypeScript strict mode, ESLint zero warnings
- Python: ruff line-length 120, mypy strict
- All async handlers, no blocking in event loop
- Agent runtime: max 100 iterations, 30s per tool call timeout
- Local models: GGUF format, auto-detect GPU (CUDA/Metal/Vulkan) or CPU fallback
- Streaming: Server-Sent Events (SSE) for agent output and search progress
- No external API calls for inference — 100% local unless user opts in

---

## Task 1: Unified Search Engine

**Files:**
- Create: `backend/app/services/unified_search.py`
- Create: `backend/tests/test_unified_search.py`

**Interfaces:**
- Consumes: Task 1 from 01-WEEK-3-4-MEMORY.md (VectorDB), Task 1 from 02-WEEK-5-6-INDEXING.md (CodeIntelligence)
- Produces: `unified_search(query, filters, limit) -> SearchResults` — consumed by agents and frontend

- [ ] **Step 1: Create app/services/unified_search.py**

```python
"""Unified search across vectors, graph, and filesystem with reciprocal rank fusion."""
from __future__ import annotations
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class SearchDomain(Enum):
    MEMORY = "memory"
    CODE = "code"
    GRAPH = "graph"
    FILES = "files"
    ALL = "all"


@dataclass
class SearchResult:
    id: str
    domain: SearchDomain
    score: float
    title: str
    snippet: str
    file_path: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class SearchResults:
    results: list[SearchResult]
    query: str
    total: int
    domain_counts: dict[str, int] = field(default_factory=dict)
    search_time_ms: float = 0.0


class UnifiedSearch:
    """Federated search across all Cortex data stores.
    
    Uses reciprocal rank fusion (RRF) to combine results from:
    - Qdrant vector search (memory + code embeddings)
    - PostgreSQL full-text search (graph entities, metadata)
    - Filesystem glob (file names, paths)
    """

    def __init__(self, vector_db, db_session_factory):
        self._vector_db = vector_db
        self._db_session_factory = db_session_factory

    async def search(
        self,
        query: str,
        domains: list[SearchDomain] | None = None,
        limit: int = 20,
        filters: dict[str, Any] | None = None,
    ) -> SearchResults:
        """Run federated search across all domains."""
        import time
        start = time.monotonic()
        
        if domains is None:
            domains = [SearchDomain.ALL]
        
        search_all = SearchDomain.ALL in domains
        active_domains = (
            list(SearchDomain) if search_all
            else domains
        )
        
        all_results: list[SearchResult] = []
        
        # Parallel search across domains
        import asyncio
        tasks = []
        
        if SearchDomain.MEMORY in active_domains or search_all:
            tasks.append(self._search_vectors(query, "cortex_memory", SearchDomain.MEMORY, limit))
        
        if SearchDomain.CODE in active_domains or search_all:
            tasks.append(self._search_vectors(query, "cortex_code", SearchDomain.CODE, limit))
        
        if SearchDomain.GRAPH in active_domains or search_all:
            tasks.append(self._search_graph(query, limit))
        
        if SearchDomain.FILES in active_domains or search_all:
            tasks.append(self._search_files(query, limit))
        
        domain_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in domain_results:
            if isinstance(result, list):
                all_results.extend(result)
            elif isinstance(result, Exception):
                logger.warning("Search domain failed: %s", result)
        
        # Reciprocal rank fusion
        fused = self._reciprocal_rank_fusion(all_results, k=60)
        
        # Apply filters
        if filters:
            fused = [r for r in fused if self._matches_filters(r, filters)]
        
        # Deduplicate by id
        seen = set()
        deduped = []
        for r in fused:
            if r.id not in seen:
                seen.add(r.id)
                deduped.append(r)
        
        elapsed = (time.monotonic() - start) * 1000
        
        return SearchResults(
            results=deduped[:limit],
            query=query,
            total=len(deduped),
            domain_counts=self._count_domains(deduped),
            search_time_ms=elapsed,
        )

    async def _search_vectors(
        self, query: str, collection: str, domain: SearchDomain, limit: int
    ) -> list[SearchResult]:
        """Search Qdrant vector store."""
        try:
            from app.services.embedding_service import EmbeddingService
            embedder = EmbeddingService()
            query_vector = await embedder.embed(query)
            
            raw = self._vector_db.search(
                collection=collection,
                query=query_vector,
                limit=limit,
            )
            
            return [
                SearchResult(
                    id=r.id,
                    domain=domain,
                    score=r.score,
                    title=r.payload.get("title", r.payload.get("file_path", "Untitled")),
                    snippet=r.payload.get("snippet", r.payload.get("content", "")[:200]),
                    file_path=r.payload.get("file_path"),
                    metadata=r.payload,
                )
                for r in raw
            ]
        except Exception as e:
            logger.debug("Vector search failed for %s: %s", collection, e)
            return []

    async def _search_graph(self, query: str, limit: int) -> list[SearchResult]:
        """Search PostgreSQL knowledge graph via full-text search."""
        try:
            async with self._db_session_factory() as session:
                from sqlalchemy import text
                result = await session.execute(
                    text("""
                        SELECT id, name, entity_type, description,
                               ts_rank_cd(to_tsvector('english', name || ' ' || COALESCE(description, '')),
                                          plainto_tsquery('english', :query)) as rank
                        FROM graph_entities
                        WHERE to_tsvector('english', name || ' ' || COALESCE(description, ''))
                              @@ plainto_tsquery('english', :query)
                        ORDER BY rank DESC
                        LIMIT :limit
                    """),
                    {"query": query, "limit": limit},
                )
                
                return [
                    SearchResult(
                        id=str(row.id),
                        domain=SearchDomain.GRAPH,
                        score=float(row.rank),
                        title=row.name,
                        snippet=row.description or f"{row.entity_type} entity",
                        metadata={"entity_type": row.entity_type},
                    )
                    for row in result.fetchall()
                ]
        except Exception as e:
            logger.debug("Graph search failed: %s", e)
            return []

    async def _search_files(self, query: str, limit: int) -> list[SearchResult]:
        """Search filesystem by filename and path."""
        from pathlib import Path
        import fnmatch
        
        cortex_root = Path("./CortexMemory")
        results = []
        
        query_lower = query.lower()
        
        for path in cortex_root.rglob("*"):
            if path.is_file() and query_lower in path.name.lower():
                results.append(SearchResult(
                    id=f"file:{path}",
                    domain=SearchDomain.FILES,
                    score=0.5,
                    title=path.name,
                    snippet=str(path.relative_to(cortex_root)),
                    file_path=str(path),
                ))
                if len(results) >= limit:
                    break
        
        return results

    def _reciprocal_rank_fusion(
        self, results: list[SearchResult], k: int = 60
    ) -> list[SearchResult]:
        """Combine results using Reciprocal Rank Fusion (RRF)."""
        scores: dict[str, float] = {}
        result_map: dict[str, SearchResult] = {}
        
        for result in results:
            if result.id in scores:
                # Same item from multiple domains — boost score
                scores[result.id] += 1.0 / (k + result.score * 100)
            else:
                scores[result.id] = 1.0 / (k + result.score * 100)
                result_map[result.id] = result
        
        sorted_ids = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)
        
        return [
            result_map[id_]
            for id_ in sorted_ids
        ]

    def _matches_filters(self, result: SearchResult, filters: dict[str, Any]) -> bool:
        """Check if result matches filter criteria."""
        if "domain" in filters and result.domain.value != filters["domain"]:
            return False
        if "file_path" in filters and filters["file_path"] not in (result.file_path or ""):
            return False
        return True

    def _count_domains(self, results: list[SearchResult]) -> dict[str, int]:
        counts: dict[str, int] = {}
        for r in results:
            counts[r.domain.value] = counts.get(r.domain.value, 0) + 1
        return counts
```

- [ ] **Step 2: Write test for unified search**

```python
# backend/tests/test_unified_search.py
"""Tests for unified search engine."""
from __future__ import annotations
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.unified_search import UnifiedSearch, SearchDomain, SearchResult


@pytest.fixture
def mock_vector_db():
    db = MagicMock()
    db.search.return_value = [
        SearchResult(id="v1", score=0.9, payload={"title": "Auth module", "snippet": "JWT tokens"}),
        SearchResult(id="v2", score=0.7, payload={"title": "Vault service", "snippet": "Encryption"}),
    ]
    return db


@pytest.fixture
def mock_db_session_factory():
    factory = AsyncMock()
    session = AsyncMock()
    factory.return_value.__aenter__ = AsyncMock(return_value=session)
    factory.return_value.__aexit__ = AsyncMock(return_value=False)
    session.execute.return_value.fetchall.return_value = []
    return factory


@pytest.mark.asyncio
async def test_unified_search_returns_results(mock_vector_db, mock_db_session_factory):
    search = UnifiedSearch(mock_vector_db, mock_db_session_factory)
    results = await search.search("authentication")
    
    assert results.query == "authentication"
    assert len(results.results) > 0
    assert results.search_time_ms >= 0


@pytest.mark.asyncio
async def test_unified_search_domain_filter(mock_vector_db, mock_db_session_factory):
    search = UnifiedSearch(mock_vector_db, mock_db_session_factory)
    results = await search.search("auth", domains=[SearchDomain.MEMORY])
    
    for r in results.results:
        assert r.domain == SearchDomain.MEMORY


@pytest.mark.asyncio
async def test_unified_search_empty_query(mock_vector_db, mock_db_session_factory):
    search = UnifiedSearch(mock_vector_db, mock_db_session_factory)
    results = await search.search("")
    
    assert results.query == ""
    assert isinstance(results.results, list)
```

- [ ] **Step 3: Run tests**

Run: `PYTHONPATH=. pytest backend/tests/test_unified_search.py -v`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add backend/app/services/unified_search.py backend/tests/test_unified_search.py
git commit -m "feat: add unified search with reciprocal rank fusion"
```

---

## Task 2: Embedding Service with Model Management

**Files:**
- Create: `backend/app/services/embedding_service.py`
- Create: `backend/app/core/model_manager.py`
- Create: `backend/tests/test_embedding_service.py`

**Interfaces:**
- Consumes: None (standalone)
- Produces: `EmbeddingService.embed(text) -> list[float]`, `ModelManager.list_models()`, `ModelManager.download_model(name)`

- [ ] **Step 1: Create app/core/model_manager.py**

```python
"""Local model management: download, cache, and manage GGUF models."""
from __future__ import annotations
import logging
import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class ModelInfo:
    name: str
    filename: str
    size_bytes: int
    description: str
    quantization: str
    context_length: int
    embedding_dim: int
    required: bool = False


AVAILABLE_MODELS = {
    "bge-m3": ModelInfo(
        name="bge-m3",
        filename="bge-m3-Q8_0.gguf",
        size_bytes=400_000_000,
        description="Multilingual embedding model (1024 dims)",
        quantization="Q8_0",
        context_length=8192,
        embedding_dim=1024,
        required=True,
    ),
    "nomic-embed": ModelInfo(
        name="nomic-embed",
        filename="nomic-embed-text-v1.5-Q8_0.gguf",
        size_bytes=260_000_000,
        description="Fast English embedding model (768 dims)",
        quantization="Q8_0",
        context_length=8192,
        embedding_dim=768,
    ),
    "codellama-7b": ModelInfo(
        name="codellama-7b",
        filename="codellama-7b-instruct.Q4_K_M.gguf",
        size_bytes=4_000_000_000,
        description="Code generation model (7B params)",
        quantization="Q4_K_M",
        context_length=16384,
        embedding_dim=0,
    ),
    "phi-3-mini": ModelInfo(
        name="phi-3-mini",
        filename="phi-3-mini-4k-Q4_K_M.gguf",
        size_bytes=2_200_000_000,
        description="General assistant model (3.8B params)",
        quantization="Q4_K_M",
        context_length=4096,
        embedding_dim=0,
    ),
}


class ModelManager:
    """Manage local GGUF model downloads and caching."""

    def __init__(self, models_dir: Path | None = None):
        self._models_dir = models_dir or Path("./CortexMemory/models").resolve()
        self._models_dir.mkdir(parents=True, exist_ok=True)

    def list_models(self) -> list[dict[str, Any]]:
        """List all available models with download status."""
        results = []
        for name, info in AVAILABLE_MODELS.items():
            path = self._models_dir / info.filename
            results.append({
                "name": info.name,
                "description": info.description,
                "size_mb": info.size_bytes // 1_000_000,
                "quantization": info.quantization,
                "context_length": info.context_length,
                "embedding_dim": info.embedding_dim,
                "required": info.required,
                "downloaded": path.exists(),
                "path": str(path) if path.exists() else None,
            })
        return results

    def get_model_path(self, name: str) -> Path | None:
        """Get local path to model if downloaded."""
        info = AVAILABLE_MODELS.get(name)
        if info is None:
            return None
        path = self._models_dir / info.filename
        return path if path.exists() else None

    async def download_model(self, name: str, progress_callback=None) -> Path:
        """Download a model from Hugging Face."""
        import httpx
        
        info = AVAILABLE_MODELS.get(name)
        if info is None:
            raise ValueError(f"Unknown model: {name}")
        
        dest = self._models_dir / info.filename
        if dest.exists():
            return dest
        
        url = f"https://huggingface.co/TheBloke/{info.name}/resolve/main/{info.filename}"
        tmp = dest.with_suffix(".tmp")
        
        async with httpx.AsyncClient() as client:
            async with client.stream("GET", url) as response:
                response.raise_for_status()
                total = int(response.headers.get("content-length", 0))
                downloaded = 0
                
                with open(tmp, "wb") as f:
                    async for chunk in response.aiter_bytes(chunk_size=8192):
                        f.write(chunk)
                        downloaded += len(chunk)
                        if progress_callback:
                            progress_callback(downloaded, total)
        
        tmp.rename(dest)
        logger.info("Downloaded model %s to %s", name, dest)
        return dest

    def delete_model(self, name: str) -> bool:
        """Delete a downloaded model."""
        info = AVAILABLE_MODELS.get(name)
        if info is None:
            return False
        path = self._models_dir / info.filename
        if path.exists():
            path.unlink()
            return True
        return False
```

- [ ] **Step 2: Create app/services/embedding_service.py**

```python
"""Embedding service with local model support and mock fallback."""
from __future__ import annotations
import hashlib
import logging
from typing import Any

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Generate embeddings using local ONNX models.
    
    Falls back to deterministic hash-based embeddings for testing
    when models are not available.
    """

    def __init__(self, model_name: str = "bge-m3"):
        self._model_name = model_name
        self._model = None
        self._tokenizer = None
        self._dimension = 1024

    def _load_model(self):
        """Lazy-load the embedding model."""
        if self._model is not None:
            return
        
        try:
            from app.core.model_manager import ModelManager
            manager = ModelManager()
            model_path = manager.get_model_path(self._model_name)
            
            if model_path is None:
                logger.warning("Model %s not downloaded, using mock embeddings", self._model_name)
                return
            
            try:
                from llama_cpp import Llama
                self._model = Llama(
                    model_path=str(model_path),
                    embedding=True,
                    n_ctx=2048,
                )
                logger.info("Loaded embedding model: %s", self._model_name)
            except ImportError:
                logger.warning("llama-cpp-python not available, using mock embeddings")
        except Exception as e:
            logger.warning("Failed to load embedding model: %s", e)

    async def embed(self, text: str) -> list[float]:
        """Generate embedding for a single text."""
        self._load_model()
        
        if self._model is not None:
            try:
                result = self._model.embed(text)
                return result[:self._dimension]
            except Exception as e:
                logger.debug("Model embedding failed, using mock: %s", e)
        
        return self._mock_embed(text)

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple texts."""
        return [await self.embed(t) for t in texts]

    def _mock_embed(self, text: str) -> list[float]:
        """Deterministic mock embedding based on text hash."""
        h = hashlib.sha512(text.encode()).digest()
        vec = []
        for i in range(0, min(len(h), self._dimension * 4), 4):
            byte_val = h[i:i+4]
            if len(byte_val) == 4:
                val = int.from_bytes(byte_val, "big") / (2**32) - 0.5
                vec.append(val)
        
        while len(vec) < self._dimension:
            vec.append(0.0)
        
        norm = sum(v*v for v in vec) ** 0.5
        if norm > 0:
            vec = [v / norm for v in vec]
        
        return vec[:self._dimension]

    @property
    def dimension(self) -> int:
        return self._dimension
```

- [ ] **Step 3: Write tests**

```python
# backend/tests/test_embedding_service.py
"""Tests for embedding service."""
from __future__ import annotations
import pytest
from app.services.embedding_service import EmbeddingService
from app.core.model_manager import ModelManager


@pytest.mark.asyncio
async def test_mock_embedding_deterministic():
    service = EmbeddingService()
    vec1 = await service.embed("hello world")
    vec2 = await service.embed("hello world")
    assert vec1 == vec2
    assert len(vec1) == 1024


@pytest.mark.asyncio
async def test_mock_embedding_normalized():
    service = EmbeddingService()
    vec = await service.embed("test input")
    norm = sum(v*v for v in vec) ** 0.5
    assert abs(norm - 1.0) < 0.01


@pytest.mark.asyncio
async def test_mock_embedding_different_inputs():
    service = EmbeddingService()
    vec1 = await service.embed("hello")
    vec2 = await service.embed("world")
    assert vec1 != vec2


def test_model_manager_list_models():
    manager = ModelManager()
    models = manager.list_models()
    assert len(models) >= 3
    assert any(m["name"] == "bge-m3" for m in models)


def test_model_manager_get_unknown_model():
    manager = ModelManager()
    assert manager.get_model_path("nonexistent") is None
```

- [ ] **Step 4: Run tests**

Run: `PYTHONPATH=. pytest backend/tests/test_embedding_service.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/embedding_service.py backend/app/core/model_manager.py backend/tests/test_embedding_service.py
git commit -m "feat: add embedding service with model management"
```

---

## Task 3: Agent Runtime Core

**Files:**
- Create: `backend/app/services/agents/runtime.py`
- Create: `backend/app/services/agents/tools.py`
- Create: `backend/app/services/agents/registry.py`
- Create: `backend/tests/test_agent_runtime.py`

**Interfaces:**
- Consumes: Task 1 (UnifiedSearch), Task 2 (EmbeddingService)
- Produces: `AgentRuntime.run(agent_config, messages) -> AgentResponse`, `ToolRegistry.register(tool)`

- [ ] **Step 1: Create app/services/agents/tools.py**

```python
"""Agent tool definitions and base classes."""
from __future__ import annotations
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class ToolParameter:
    name: str
    type: str  # "string", "integer", "boolean", "array"
    description: str
    required: bool = True
    default: Any = None


@dataclass
class ToolResult:
    success: bool
    output: str
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class Tool(ABC):
    """Base class for agent tools."""

    @property
    @abstractmethod
    def name(self) -> str: ...

    @property
    @abstractmethod
    def description(self) -> str: ...

    @property
    @abstractmethod
    def parameters(self) -> list[ToolParameter]: ...

    @abstractmethod
    async def execute(self, **kwargs) -> ToolResult: ...

    def to_schema(self) -> dict[str, Any]:
        """Convert to JSON Schema for LLM tool calling."""
        props = {}
        required = []
        for param in self.parameters:
            props[param.name] = {
                "type": param.type,
                "description": param.description,
            }
            if param.required:
                required.append(param.name)
        
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": props,
                    "required": required,
                },
            },
        }


class ReadFileTool(Tool):
    """Read a file from the filesystem."""

    @property
    def name(self) -> str:
        return "read_file"

    @property
    def description(self) -> str:
        return "Read the contents of a file at the given path"

    @property
    def parameters(self) -> list[ToolParameter]:
        return [
            ToolParameter(name="path", type="string", description="Absolute file path to read"),
            ToolParameter(name="offset", type="integer", description="Line number to start from", required=False),
            ToolParameter(name="limit", type="integer", description="Max lines to read", required=False),
        ]

    async def execute(self, path: str, offset: int = 0, limit: int = 1000) -> ToolResult:
        try:
            from pathlib import Path
            file_path = Path(path)
            if not file_path.exists():
                return ToolResult(success=False, output="", error=f"File not found: {path}")
            
            content = file_path.read_text()
            lines = content.splitlines()
            selected = lines[offset:offset + limit]
            
            return ToolResult(
                success=True,
                output="\n".join(selected),
                metadata={"total_lines": len(lines), "returned_lines": len(selected)},
            )
        except Exception as e:
            return ToolResult(success=False, output="", error=str(e))


class WriteFileTool(Tool):
    """Write content to a file."""

    @property
    def name(self) -> str:
        return "write_file"

    @property
    def description(self) -> str:
        return "Write content to a file (creates or overwrites)"

    @property
    def parameters(self) -> list[ToolParameter]:
        return [
            ToolParameter(name="path", type="string", description="Absolute file path to write"),
            ToolParameter(name="content", type="string", description="Content to write to the file"),
        ]

    async def execute(self, path: str, content: str) -> ToolResult:
        try:
            from pathlib import Path
            file_path = Path(path)
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content)
            return ToolResult(success=True, output=f"Written {len(content)} bytes to {path}")
        except Exception as e:
            return ToolResult(success=False, output="", error=str(e))


class ExecuteCommandTool(Tool):
    """Execute a shell command."""

    @property
    def name(self) -> str:
        return "execute_command"

    @property
    def description(self) -> str:
        return "Execute a shell command and return its output"

    @property
    def parameters(self) -> list[ToolParameter]:
        return [
            ToolParameter(name="command", type="string", description="Shell command to execute"),
            ToolParameter(name="timeout", type="integer", description="Timeout in seconds", required=False, default=30),
        ]

    async def execute(self, command: str, timeout: int = 30) -> ToolResult:
        try:
            import asyncio
            proc = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
            
            return ToolResult(
                success=proc.returncode == 0,
                output=stdout.decode(),
                error=stderr.decode() if stderr else None,
                metadata={"return_code": proc.returncode},
            )
        except asyncio.TimeoutError:
            return ToolResult(success=False, output="", error=f"Command timed out after {timeout}s")
        except Exception as e:
            return ToolResult(success=False, output="", error=str(e))


class SearchTool(Tool):
    """Search across all Cortex data."""

    @property
    def name(self) -> str:
        return "search"

    @property
    def description(self) -> str:
        return "Search across memory, code, graph, and files in Cortex"

    @property
    def parameters(self) -> list[ToolParameter]:
        return [
            ToolParameter(name="query", type="string", description="Search query"),
            ToolParameter(name="limit", type="integer", description="Max results", required=False, default=10),
        ]

    async def execute(self, query: str, limit: int = 10) -> ToolResult:
        try:
            from app.services.unified_search import UnifiedSearch
            from app.core.vector_db import VectorDB
            from app.db.session import async_session_factory
            
            search = UnifiedSearch(VectorDB(), async_session_factory)
            results = await search.search(query, limit=limit)
            
            output_lines = []
            for r in results.results:
                output_lines.append(f"[{r.domain.value}] {r.title} (score: {r.score:.2f})")
                output_lines.append(f"  {r.snippet[:150]}")
                output_lines.append("")
            
            return ToolResult(
                success=True,
                output="\n".join(output_lines) if output_lines else "No results found",
                metadata={"total": results.total, "search_time_ms": results.search_time_ms},
            )
        except Exception as e:
            return ToolResult(success=False, output="", error=str(e))
```

- [ ] **Step 2: Create app/services/agents/registry.py**

```python
"""Tool registry for agent tools."""
from __future__ import annotations
import logging
from typing import Any

logger = logging.getLogger(__name__)


class ToolRegistry:
    """Central registry for agent tools."""

    def __init__(self):
        self._tools: dict[str, Any] = {}

    def register(self, tool):
        """Register a tool instance."""
        self._tools[tool.name] = tool
        logger.debug("Registered tool: %s", tool.name)

    def get(self, name: str):
        """Get a tool by name."""
        return self._tools.get(name)

    def list_tools(self) -> list[dict[str, Any]]:
        """List all registered tools."""
        return [tool.to_schema() for tool in self._tools.values()]

    def list_names(self) -> list[str]:
        return list(self._tools.keys())


def get_default_registry() -> ToolRegistry:
    """Create a registry with all default tools."""
    from app.services.agents.tools import (
        ReadFileTool, WriteFileTool, ExecuteCommandTool, SearchTool,
    )
    
    registry = ToolRegistry()
    registry.register(ReadFileTool())
    registry.register(WriteFileTool())
    registry.register(ExecuteCommandTool())
    registry.register(SearchTool())
    return registry
```

- [ ] **Step 3: Create app/services/agents/runtime.py**

```python
"""Agent runtime: async task executor with tool-use loop."""
from __future__ import annotations
import json
import logging
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class AgentStatus(Enum):
    IDLE = "idle"
    THINKING = "thinking"
    USING_TOOL = "using_tool"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class AgentMessage:
    role: str  # "system", "user", "assistant", "tool"
    content: str
    tool_call_id: str | None = None
    tool_name: str | None = None


@dataclass
class AgentConfig:
    name: str
    system_prompt: str
    model: str = "phi-3-mini"
    max_iterations: int = 50
    tool_timeout: int = 30
    temperature: float = 0.7
    tools: list[str] | None = None  # None = all tools


@dataclass
class AgentResponse:
    agent_name: str
    messages: list[AgentMessage]
    status: AgentStatus
    iterations: int
    tool_calls: list[dict[str, Any]]
    output: str
    error: str | None = None


class AgentRuntime:
    """Execute agents with tool-use loop.
    
    The runtime:
    1. Sends messages + tools to local LLM
    2. If LLM returns tool_call, executes tool and loops
    3. If LLM returns text, agent is done
    4. Max iterations prevents infinite loops
    """

    def __init__(self, tool_registry, llm_provider=None):
        self._registry = tool_registry
        self._llm = llm_provider

    async def run(self, config: AgentConfig, messages: list[AgentMessage]) -> AgentResponse:
        """Run an agent to completion."""
        tool_calls_log = []
        conversation = list(messages)
        
        # Get available tools
        available_tools = self._get_tools(config.tools)
        
        for iteration in range(config.max_iterations):
            # Get LLM response
            response_text, tool_calls = await self._call_llm(
                conversation, available_tools, config
            )
            
            if tool_calls:
                # Execute each tool call
                conversation.append(AgentMessage(
                    role="assistant",
                    content=response_text or "",
                ))
                
                for tc in tool_calls:
                    tool = self._registry.get(tc["name"])
                    if tool is None:
                        result_output = f"Error: Unknown tool '{tc['name']}'"
                    else:
                        try:
                            result = await tool.execute(**tc["arguments"])
                            result_output = result.output
                            if result.error:
                                result_output += f"\nError: {result.error}"
                        except Exception as e:
                            result_output = f"Tool execution failed: {e}"
                    
                    conversation.append(AgentMessage(
                        role="tool",
                        content=result_output,
                        tool_call_id=tc.get("id", str(uuid.uuid4())),
                        tool_name=tc["name"],
                    ))
                    
                    tool_calls_log.append({
                        "tool": tc["name"],
                        "arguments": tc["arguments"],
                        "result_preview": result_output[:200],
                    })
            else:
                # No tool calls — agent is done
                return AgentResponse(
                    agent_name=config.name,
                    messages=conversation,
                    status=AgentStatus.COMPLETED,
                    iterations=iteration + 1,
                    tool_calls=tool_calls_log,
                    output=response_text or "",
                )
        
        return AgentResponse(
            agent_name=config.name,
            messages=conversation,
            status=AgentStatus.FAILED,
            iterations=config.max_iterations,
            tool_calls=tool_calls_log,
            output="",
            error="Max iterations reached",
        )

    def _get_tools(self, tool_names: list[str] | None) -> list[dict]:
        """Get tool schemas for the LLM."""
        if tool_names is None:
            return self._registry.list_tools()
        return [
            self._registry.get(name).to_schema()
            for name in tool_names
            if self._registry.get(name) is not None
        ]

    async def _call_llm(
        self,
        messages: list[AgentMessage],
        tools: list[dict],
        config: AgentConfig,
    ) -> tuple[str, list[dict] | None]:
        """Call LLM and parse response."""
        if self._llm is not None:
            return await self._llm.chat(messages, tools, config)
        
        # Mock LLM for testing
        last_msg = messages[-1] if messages else None
        if last_msg and last_msg.role == "tool":
            return "I've completed the task using the tool results.", None
        
        if tools:
            # Simulate tool call on first interaction
            return None, [{
                "id": str(uuid.uuid4()),
                "name": tools[0]["function"]["name"],
                "arguments": {"query": "test"},
            }]
        
        return "Hello! How can I help?", None
```

- [ ] **Step 4: Write tests**

```python
# backend/tests/test_agent_runtime.py
"""Tests for agent runtime."""
from __future__ import annotations
import pytest
from app.services.agents.runtime import AgentRuntime, AgentConfig, AgentMessage, AgentStatus
from app.services.agents.registry import ToolRegistry
from app.services.agents.tools import SearchTool, ReadFileTool


@pytest.fixture
def registry():
    reg = ToolRegistry()
    reg.register(SearchTool())
    reg.register(ReadFileTool())
    return reg


@pytest.mark.asyncio
async def test_agent_runtime_completes(registry):
    runtime = AgentRuntime(registry)
    config = AgentConfig(name="test", system_prompt="You are a test agent.")
    messages = [AgentMessage(role="user", content="hello")]
    
    response = await runtime.run(config, messages)
    
    assert response.status == AgentStatus.COMPLETED
    assert response.iterations >= 1
    assert response.output


@pytest.mark.asyncio
async def test_agent_max_iterations(registry):
    runtime = AgentRuntime(registry)
    config = AgentConfig(name="test", system_prompt="test", max_iterations=2)
    messages = [AgentMessage(role="user", content="hello")]
    
    # Mock LLM that always calls tools
    class MockLLM:
        async def chat(self, messages, tools, config):
            return None, [{"id": "1", "name": "search", "arguments": {"query": "test"}}]
    
    runtime._llm = MockLLM()
    response = await runtime.run(config, messages)
    
    assert response.status == AgentStatus.FAILED
    assert "Max iterations" in response.error


def test_tool_registry():
    registry = ToolRegistry()
    registry.register(SearchTool())
    registry.register(ReadFileTool())
    
    assert len(registry.list_names()) == 2
    assert registry.get("search") is not None
    assert registry.get("nonexistent") is None
```

- [ ] **Step 5: Run tests**

Run: `PYTHONPATH=. pytest backend/tests/test_agent_runtime.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add backend/app/services/agents/ backend/tests/test_agent_runtime.py
git commit -m "feat: add agent runtime with tool-use loop"
```

---

## Task 4: Coder Agent

**Files:**
- Create: `backend/app/services/agents/coder.py`
- Create: `backend/tests/test_coder_agent.py`

**Interfaces:**
- Consumes: Task 3 (AgentRuntime, ToolRegistry)
- Produces: `coder_agent.run(task) -> AgentResponse`

- [ ] **Step 1: Create app/services/agents/coder.py**

```python
"""Coder agent: reads, writes, and executes code autonomously."""
from __future__ import annotations
import logging
from app.services.agents.runtime import AgentConfig

logger = logging.getLogger(__name__)

CODER_SYSTEM_PROMPT = """You are Cortex Coder, an AI assistant specialized in software development.

Your capabilities:
- Read and understand code files
- Write new code or modify existing code
- Execute shell commands to test your work
- Search across the codebase for context

Rules:
1. Always read files before modifying them
2. Test your changes when possible
3. Explain what you're doing and why
4. If unsure, ask for clarification
5. Never commit secrets or credentials
6. Follow the project's coding conventions

When writing code:
- Use proper type hints
- Handle errors gracefully
- Write clean, readable code
- Follow existing patterns in the codebase
"""


def create_coder_config(model: str = "codellama-7b") -> AgentConfig:
    """Create a Coder agent configuration."""
    return AgentConfig(
        name="coder",
        system_prompt=CODER_SYSTEM_PROMPT,
        model=model,
        max_iterations=50,
        tool_timeout=60,
        temperature=0.3,
        tools=["read_file", "write_file", "execute_command", "search"],
    )
```

- [ ] **Step 2: Write tests**

```python
# backend/tests/test_coder_agent.py
"""Tests for coder agent."""
from __future__ import annotations
import pytest
from app.services.agents.coder import create_coder_config
from app.services.agents.runtime import AgentRuntime, AgentMessage, AgentStatus
from app.services.agents.registry import get_default_registry


@pytest.mark.asyncio
async def test_coder_agent_config():
    config = create_coder_config()
    assert config.name == "coder"
    assert "read_file" in config.tools
    assert "write_file" in config.tools
    assert config.temperature == 0.3


@pytest.mark.asyncio
async def test_coder_agent_runs():
    registry = get_default_registry()
    runtime = AgentRuntime(registry)
    config = create_coder_config()
    messages = [AgentMessage(role="user", content="Read the file /tmp/test.txt")]
    
    response = await runtime.run(config, messages)
    
    assert response.status == AgentStatus.COMPLETED
    assert response.agent_name == "coder"
```

- [ ] **Step 3: Run tests**

Run: `PYTHONPATH=. pytest backend/tests/test_coder_agent.py -v`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add backend/app/services/agents/coder.py backend/tests/test_coder_agent.py
git commit -m "feat: add coder agent"
```

---

## Task 5: Researcher Agent

**Files:**
- Create: `backend/app/services/agents/researcher.py`
- Create: `backend/tests/test_researcher_agent.py`

**Interfaces:**
- Consumes: Task 3 (AgentRuntime, ToolRegistry), Task 1 (UnifiedSearch)
- Produces: `researcher_agent.run(query) -> AgentResponse`

- [ ] **Step 1: Create app/services/agents/researcher.py**

```python
"""Researcher agent: searches, reads, and synthesizes information."""
from __future__ import annotations
import logging
from app.services.agents.runtime import AgentConfig

logger = logging.getLogger(__name__)

RESEARCHER_SYSTEM_PROMPT = """You are Cortex Researcher, an AI assistant specialized in finding and synthesizing information.

Your capabilities:
- Search across memory, code, knowledge graph, and files
- Read and analyze code and documents
- Synthesize findings into clear summaries
- Identify relationships between concepts

Rules:
1. Always search before reading files
2. Use multiple search queries for broad coverage
3. Cite sources when possible
4. Distinguish between facts and inferences
5. Highlight uncertainty when present
6. Provide actionable summaries

When researching:
- Start with broad searches, then narrow down
- Cross-reference multiple sources
- Look for patterns and relationships
- Identify gaps in available information
"""


def create_researcher_config(model: str = "phi-3-mini") -> AgentConfig:
    """Create a Researcher agent configuration."""
    return AgentConfig(
        name="researcher",
        system_prompt=RESEARCHER_SYSTEM_PROMPT,
        model=model,
        max_iterations=30,
        tool_timeout=30,
        temperature=0.5,
        tools=["search", "read_file"],
    )
```

- [ ] **Step 2: Write tests**

```python
# backend/tests/test_researcher_agent.py
"""Tests for researcher agent."""
from __future__ import annotations
import pytest
from app.services.agents.researcher import create_researcher_config
from app.services.agents.runtime import AgentRuntime, AgentMessage, AgentStatus
from app.services.agents.registry import get_default_registry


@pytest.mark.asyncio
async def test_researcher_agent_config():
    config = create_researcher_config()
    assert config.name == "researcher"
    assert "search" in config.tools
    assert "read_file" in config.tools
    assert config.temperature == 0.5


@pytest.mark.asyncio
async def test_researcher_agent_runs():
    registry = get_default_registry()
    runtime = AgentRuntime(registry)
    config = create_researcher_config()
    messages = [AgentMessage(role="user", content="How does authentication work in this codebase?")]
    
    response = await runtime.run(config, messages)
    
    assert response.status == AgentStatus.COMPLETED
    assert response.agent_name == "researcher"
```

- [ ] **Step 3: Run tests**

Run: `PYTHONPATH=. pytest backend/tests/test_researcher_agent.py -v`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add backend/app/services/agents/researcher.py backend/tests/test_researcher_agent.py
git commit -m "feat: add researcher agent"
```

---

## Task 6: Agent API Endpoints

**Files:**
- Create: `backend/app/api/v1/agents.py`
- Create: `backend/tests/test_agent_api.py`

**Interfaces:**
- Consumes: Task 3-5 (AgentRuntime, Coder, Researcher)
- Produces: `POST /api/v1/agents/run`, `GET /api/v1/agents`, `GET /api/v1/agents/{id}`

- [ ] **Step 1: Create app/api/v1/agents.py**

```python
"""Agent API endpoints."""
from __future__ import annotations
import uuid
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

router = APIRouter(prefix="/agents", tags=["agents"])


class AgentRunRequest(BaseModel):
    agent_name: str
    task: str
    model: str | None = None


class AgentRunResponse(BaseModel):
    id: str
    agent_name: str
    status: str
    output: str
    tool_calls: list[dict]
    iterations: int


class AgentInfo(BaseModel):
    name: str
    description: str
    tools: list[str]


# In-memory store for demo (replace with DB in production)
_running_agents: dict[str, AgentRunResponse] = {}


@router.get("", response_model=list[AgentInfo])
async def list_agents():
    """List available agents."""
    from app.services.agents.coder import create_coder_config
    from app.services.agents.researcher import create_researcher_config
    
    return [
        AgentInfo(
            name="coder",
            description="AI coding assistant that reads, writes, and executes code",
            tools=["read_file", "write_file", "execute_command", "search"],
        ),
        AgentInfo(
            name="researcher",
            description="AI research assistant that searches and synthesizes information",
            tools=["search", "read_file"],
        ),
    ]


@router.post("/run", response_model=AgentRunResponse)
async def run_agent(request: AgentRunRequest):
    """Run an agent with a task."""
    from app.services.agents.runtime import AgentRuntime, AgentConfig, AgentMessage
    from app.services.agents.registry import get_default_registry
    from app.services.agents.coder import create_coder_config
    from app.services.agents.researcher import create_researcher_config
    
    configs = {
        "coder": create_coder_config,
        "researcher": create_researcher_config,
    }
    
    factory = configs.get(request.agent_name)
    if factory is None:
        raise HTTPException(status_code=404, detail=f"Unknown agent: {request.agent_name}")
    
    config = factory(model=request.model) if request.model else factory()
    registry = get_default_registry()
    runtime = AgentRuntime(registry)
    
    messages = [AgentMessage(role="user", content=request.task)]
    response = await runtime.run(config, messages)
    
    run_id = str(uuid.uuid4())
    result = AgentRunResponse(
        id=run_id,
        agent_name=response.agent_name,
        status=response.status.value,
        output=response.output,
        tool_calls=response.tool_calls,
        iterations=response.iterations,
    )
    
    _running_agents[run_id] = result
    return result


@router.get("/{run_id}", response_model=AgentRunResponse)
async def get_agent_run(run_id: str):
    """Get status of a running or completed agent."""
    result = _running_agents.get(run_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Agent run not found")
    return result
```

- [ ] **Step 2: Register router**

Modify `backend/app/api/router.py` to include agent routes:

```python
# Add after existing router includes
from app.api.v1.agents import router as agents_router
api_router.include_router(agents_router, prefix="/v1")
```

- [ ] **Step 3: Write tests**

```python
# backend/tests/test_agent_api.py
"""Tests for agent API."""
from __future__ import annotations
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_list_agents():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/agents")
    
    assert response.status_code == 200
    agents = response.json()
    assert len(agents) >= 2
    assert any(a["name"] == "coder" for a in agents)


@pytest.mark.asyncio
async def test_run_agent():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/v1/agents/run", json={
            "agent_name": "coder",
            "task": "list files in the current directory",
        })
    
    assert response.status_code == 200
    data = response.json()
    assert data["agent_name"] == "coder"
    assert data["status"] in ("completed", "failed")
```

- [ ] **Step 4: Run tests**

Run: `PYTHONPATH=. pytest backend/tests/test_agent_api.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/api/v1/agents.py backend/app/api/router.py backend/tests/test_agent_api.py
git commit -m "feat: add agent API endpoints"
```

---

## Task 7: Agent Frontend — Chat Interface

**Files:**
- Create: `frontend/app/app/agents/page.tsx`
- Create: `frontend/src/shared/components/AgentChat.tsx`
- Create: `frontend/src/shared/components/AgentMessage.tsx`
- Create: `frontend/src/shared/components/AgentToolCall.tsx`

**Interfaces:**
- Consumes: `POST /api/v1/agents/run`, `GET /api/v1/agents`
- Produces: Agent chat UI with streaming output

- [ ] **Step 1: Create AgentChat component**

```tsx
// frontend/src/shared/components/AgentChat.tsx
"use client";

import { useState, useRef, useEffect } from "react";

interface Message {
  role: "user" | "assistant";
  content: string;
  toolCalls?: Array<{
    tool: string;
    arguments: Record<string, unknown>;
    resultPreview: string;
  }>;
}

interface AgentChatProps {
  agentName: string;
  onRun?: (taskId: string) => void;
}

export function AgentChat({ agentName, onRun }: AgentChatProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isRunning, setIsRunning] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleRun = async () => {
    if (!input.trim() || isRunning) return;

    const userMessage: Message = { role: "user", content: input.trim() };
    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsRunning(true);

    try {
      const response = await fetch("/api/v1/agents/run", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          agent_name: agentName,
          task: userMessage.content,
        }),
      });

      const data = await response.json();

      const assistantMessage: Message = {
        role: "assistant",
        content: data.output,
        toolCalls: data.tool_calls,
      };
      setMessages((prev) => [...prev, assistantMessage]);

      if (onRun) onRun(data.id);
    } catch (error) {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: `Error: ${error}` },
      ]);
    } finally {
      setIsRunning(false);
    }
  };

  return (
    <div className="flex flex-col h-full bg-bg-card border border-border rounded-lg">
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((msg, i) => (
          <div
            key={i}
            className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
          >
            <div
              className={`max-w-[80%] rounded-lg p-3 ${
                msg.role === "user"
                  ? "bg-accent text-white"
                  : "bg-bg-surface border border-border"
              }`}
            >
              <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
              {msg.toolCalls?.map((tc, j) => (
                <div
                  key={j}
                  className="mt-2 p-2 bg-bg-elevated rounded text-xs font-mono"
                >
                  <span className="text-accent">{tc.tool}</span>
                  <span className="text-text-muted ml-2">
                    {JSON.stringify(tc.arguments)}
                  </span>
                </div>
              ))}
            </div>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      <div className="border-t border-border p-4">
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleRun()}
            placeholder={`Ask ${agentName}...`}
            className="flex-1 h-10 rounded-md bg-bg-surface border border-border px-3 text-sm"
            disabled={isRunning}
          />
          <button
            onClick={handleRun}
            disabled={isRunning || !input.trim()}
            className="px-4 h-10 rounded-md bg-accent text-white text-sm font-medium hover:bg-accent-hover disabled:opacity-50"
          >
            {isRunning ? "Running..." : "Run"}
          </button>
        </div>
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Create agents page**

```tsx
// frontend/app/app/agents/page.tsx
"use client";

import { useState } from "react";
import { AgentChat } from "@/shared/components/AgentChat";

const AGENTS = [
  {
    name: "coder",
    description: "AI coding assistant that reads, writes, and executes code",
    icon: "code", // Use SVG icon, not emoji
  },
  {
    name: "researcher",
    description: "AI research assistant that searches and synthesizes information",
    icon: "search", // Use SVG icon, not emoji
  },
];

export default function AgentsPage() {
  const [selectedAgent, setSelectedAgent] = useState("coder");

  return (
    <div className="h-[calc(100vh-4rem)] flex">
      <div className="w-64 border-r border-border p-4">
        <h2 className="text-lg font-display font-semibold mb-4">Agents</h2>
        <div className="space-y-2">
          {AGENTS.map((agent) => (
            <button
              key={agent.name}
              onClick={() => setSelectedAgent(agent.name)}
              className={`w-full text-left p-3 rounded-lg transition-colors ${
                selectedAgent === agent.name
                  ? "bg-accent/10 border border-accent/30"
                  : "hover:bg-bg-hover"
              }`}
            >
              <div className="flex items-center gap-2">
                <span>{agent.icon}</span>
                <span className="font-medium capitalize">{agent.name}</span>
              </div>
              <p className="text-xs text-text-muted mt-1">{agent.description}</p>
            </button>
          ))}
        </div>
      </div>

      <div className="flex-1 p-4">
        <AgentChat agentName={selectedAgent} />
      </div>
    </div>
  );
}
```

- [ ] **Step 3: Add agents link to sidebar**

Modify the dashboard sidebar to include agents navigation:

```tsx
// Add to sidebar navigation items
{ name: "Agents", href: "/app/agents", icon: "..." }
```

- [ ] **Step 4: Verify build**

Run: `cd frontend && npx tsc --noEmit`
Expected: No errors

- [ ] **Step 5: Commit**

```bash
git add frontend/app/app/agents/ frontend/src/shared/components/AgentChat.tsx
git commit -m "feat: add agent chat frontend"
```

### Migration Steps
No new SQLAlchemy models created in this plan. Agent state uses in-memory storage. For production, persist agent runs to PostgreSQL:
1. Create `backend/app/models/agent_task.py` (AgentTask table)
2. Run: `alembic revision --autogenerate -m "add_agent_task"`
3. Run: `alembic upgrade head`
4. Verify: `PYTHONPATH=. pytest tests/test_agent_runtime.py tests/test_agent_api.py -v`

### API Versioning
All new endpoints must use `/api/v1/{resource}` prefix. Agent routes already conform:
- `POST /api/v1/agents/run` ✓
- `GET /api/v1/agents` ✓
- `GET /api/v1/agents/{id}` ✓

---

## Summary

By end of Week 8, Cortex has:

1. **Unified Search** — Federated search across vectors, graph, and files with reciprocal rank fusion
2. **Embedding Service** — Local ONNX models with deterministic mock fallback
3. **Agent Runtime** — Async tool-use loop with iteration limits and timeout
4. **Coder Agent** — Reads, writes, and executes code autonomously
5. **Researcher Agent** — Searches and synthesizes information
6. **Agent API** — REST endpoints for running agents and checking status
7. **Agent Frontend** — Chat interface with tool call visualization
8. **Model Manager** — GGUF model download and caching

### Cross-References
- **From 01-WEEK-3-4-MEMORY.md**: VectorDB used by unified search and embedding service
- **From 02-WEEK-5-6-INDEXING.md**: CodeIntelligence used by researcher agent
- **To 04-WEEK-9-10-INTELLIGENCE.md**: Agent runtime extended by reasoning and planning engines
- **To 05-WEEK-11-12-LAUNCH.md**: Agents integrated into desktop launcher and system tray
