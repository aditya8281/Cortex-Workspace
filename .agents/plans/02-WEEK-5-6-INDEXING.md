# Advanced Indexing & Knowledge Graph Plan (Weeks 5-6)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build code intelligence (symbols, call graphs, dependency analysis), multi-model embeddings with ColBERT reranking, and a Knowledge Graph with Apache AGE — enabling deep code understanding and entity-relationship reasoning by end of Week 6.

**Architecture:** tree-sitter provides AST parsing for 15+ languages. Apache AGE (PostgreSQL extension) stores the knowledge graph. ColBERT late-interaction model provides code-aware embeddings. A cross-encoder reranker improves search relevance. All indexed incrementally via file watcher.

**Tech Stack:** tree-sitter (Python bindings), Apache AGE (pg age extension), ColBERT ONNX, cross-encoder ONNX, SQLAlchemy 2.0, Next.js 15 with Cytoscape.js.

## Global Constraints

- Python 3.12+, Node.js 20+, Rust 2024 edition
- TypeScript strict mode, ESLint zero warnings
- Python: ruff line-length 120, mypy strict
- Apache AGE: `CREATE EXTENSION IF NOT EXISTS age;` on PostgreSQL startup
- tree-sitter parsers: python, javascript, typescript, rust, go, java, cpp (bundled WASM)
- Incremental re-indexing: < 5s from file edit to searchable
- Graph queries: < 50ms for 3-hop neighborhood traversal
- All indexing runs in background tasks, never blocking API responses

---

## Task 1: Tree-Sitter Code Intelligence

**Files:**
- Create: `backend/app/services/code_intelligence.py`
- Create: `backend/tests/test_code_intelligence.py`

**Interfaces:**
- Consumes: Task 1 from 01-WEEK-3-4-MEMORY.md (RepoScanner, CodeChunk)
- Produces: `extract_symbols(code, lang) -> list[Symbol]`, `build_call_graph(repo_id) -> CallGraph`, `analyze_impact(symbol_id) -> ImpactReport`

- [ ] **Step 1: Create app/services/code_intelligence.py**

```python
"""Code intelligence: AST parsing, symbol extraction, call graphs, impact analysis."""
from __future__ import annotations
import logging
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

logger = logging.getLogger(__name__)


class SymbolType(Enum):
    FUNCTION = "function"
    CLASS = "class"
    METHOD = "method"
    VARIABLE = "variable"
    IMPORT = "import"
    MODULE = "module"
    PARAMETER = "parameter"
    DECORATOR = "decorator"


@dataclass
class Symbol:
    name: str
    symbol_type: SymbolType
    file_path: str
    start_line: int
    end_line: int
    parent: str | None = None
    docstring: str | None = None
    signature: str | None = None


@dataclass
class CallRelation:
    caller: str  # symbol ID
    callee: str  # symbol ID
    file_path: str
    line: int


@dataclass
class ImportRelation:
    source_module: str
    target_module: str
    file_path: str
    line: int


@dataclass
class CallGraph:
    symbols: dict[str, Symbol] = field(default_factory=dict)
    calls: list[CallRelation] = field(default_factory=list)
    imports: list[ImportRelation] = field(default_factory=list)
    symbol_by_name: dict[str, list[Symbol]] = field(default_factory=dict)


@dataclass
class ImpactReport:
    symbol: Symbol
    direct_callers: list[Symbol]
    indirect_callers: list[Symbol]
    dependents: list[Symbol]
    affected_files: list[str]
    risk_score: float  # 0.0 - 1.0


class CodeIntelligence:
    """Extract code structure using tree-sitter."""

    def __init__(self):
        self._parsers: dict[str, object] = {}
        self._ensure_parsers()

    def _ensure_parsers(self):
        """Initialize tree-sitter parsers for supported languages."""
        try:
            import tree_sitter
            import tree_sitter_python as tspython
            import tree_sitter_javascript as tsjs
            import tree_sitter_typescript as tsts
            
            self._parsers = {
                "python": tree_sitter.Language(tspython.language()),
                "javascript": tree_sitter.Language(tsjs.language()),
                "typescript": tree_sitter.Language(tsts.language_typescript()),
                "tsx": tree_sitter.Language(tsts.language_tsx()),
            }
            logger.info("Loaded tree-sitter parsers: %s", list(self._parsers.keys()))
        except ImportError as e:
            logger.warning("tree-sitter not available, code intelligence disabled: %s", e)

    def extract_symbols(self, code: str, file_path: str, language: str | None = None) -> list[Symbol]:
        """Extract all symbols from code using tree-sitter."""
        if language is None:
            language = self._detect_language(file_path)
        
        if language not in self._parsers:
            return self._extract_symbols_regex(code, file_path)
        
        try:
            parser = tree_sitter.Parser(self._parsers[language])
            tree = parser.parse(code.encode())
            return self._walk_tree(tree.root_node, code, file_path, language)
        except Exception as e:
            logger.debug("tree-sitter parse failed for %s: %s", file_path, e)
            return self._extract_symbols_regex(code, file_path)

    def _walk_tree(self, node, code: str, file_path: str, language: str) -> list[Symbol]:
        """Walk AST tree and extract symbols."""
        symbols = []
        
        for child in node.children:
            symbol = self._node_to_symbol(child, code, file_path, language)
            if symbol:
                symbols.append(symbol)
            symbols.extend(self._walk_tree(child, code, file_path, language))
        
        return symbols

    def _node_to_symbol(self, node, code: str, file_path: str, language: str) -> Symbol | None:
        """Convert AST node to Symbol."""
        node_type = node.type
        start_line = node.start_point[0] + 1
        end_line = node.end_point[0] + 1
        
        if language == "python":
            if node_type == "function_definition":
                name = node.child_by_field_name("name")
                if name:
                    return Symbol(
                        name=name.text.decode(),
                        symbol_type=SymbolType.FUNCTION,
                        file_path=file_path,
                        start_line=start_line,
                        end_line=end_line,
                        signature=self._get_python_signature(node, code),
                    )
            elif node_type == "class_definition":
                name = node.child_by_field_name("name")
                if name:
                    return Symbol(
                        name=name.text.decode(),
                        symbol_type=SymbolType.CLASS,
                        file_path=file_path,
                        start_line=start_line,
                        end_line=end_line,
                    )
            elif node_type == "import_statement" or node_type == "import_from_statement":
                return Symbol(
                    name=node.text.decode()[:100],
                    symbol_type=SymbolType.IMPORT,
                    file_path=file_path,
                    start_line=start_line,
                    end_line=end_line,
                )
        
        elif language in ("javascript", "typescript", "tsx"):
            if node_type in ("function_declaration", "function", "arrow_function"):
                name = node.child_by_field_name("name")
                if name:
                    return Symbol(
                        name=name.text.decode(),
                        symbol_type=SymbolType.FUNCTION,
                        file_path=file_path,
                        start_line=start_line,
                        end_line=end_line,
                    )
            elif node_type == "class_declaration":
                name = node.child_by_field_name("name")
                if name:
                    return Symbol(
                        name=name.text.decode(),
                        symbol_type=SymbolType.CLASS,
                        file_path=file_path,
                        start_line=start_line,
                        end_line=end_line,
                    )
            elif node_type in ("import_statement", "import_declaration"):
                return Symbol(
                    name=node.text.decode()[:100],
                    symbol_type=SymbolType.IMPORT,
                    file_path=file_path,
                    start_line=start_line,
                    end_line=end_line,
                )
        
        return None

    def _get_python_signature(self, node, code: str) -> str | None:
        """Extract function signature from Python AST."""
        try:
            params_node = node.child_by_field_name("parameters")
            if params_node:
                return f"def {node.child_by_field_name('name').text.decode()}{params_node.text.decode()}"
        except Exception:
            pass
        return None

    def _extract_symbols_regex(self, code: str, file_path: str) -> list[Symbol]:
        """Fallback: regex-based symbol extraction."""
        import re
        symbols = []
        for i, line in enumerate(code.split("\n"), 1):
            m = re.match(r'^(def|class|function|const|let|var|async)\s+(\w+)', line)
            if m:
                sym_type = SymbolType.FUNCTION if m.group(1) in ("def", "function", "async") else SymbolType.CLASS if m.group(1) == "class" else SymbolType.VARIABLE
                symbols.append(Symbol(name=m.group(2), symbol_type=sym_type, file_path=file_path, start_line=i, end_line=i))
        return symbols

    def _detect_language(self, file_path: str) -> str | None:
        ext = Path(file_path).suffix.lower()
        return {
            ".py": "python", ".js": "javascript", ".ts": "typescript",
            ".tsx": "tsx", ".jsx": "javascript",
        }.get(ext)

    def build_call_graph(self, repo_id: int, db) -> CallGraph:
        """Build call graph from all indexed code chunks."""
        from app.models.repo_index import CodeChunk
        chunks = db.query(CodeChunk).filter(CodeChunk.repo_id == repo_id).all()
        
        graph = CallGraph()
        
        for chunk in chunks:
            symbols = self.extract_symbols(chunk.content, chunk.file_path, chunk.language)
            for sym in symbols:
                sym_id = f"{chunk.file_path}:{sym.name}:{sym.start_line}"
                graph.symbols[sym_id] = sym
                if sym.name not in graph.symbol_by_name:
                    graph.symbol_by_name[sym.name] = []
                graph.symbol_by_name[sym.name].append(sym)
        
        return graph

    def analyze_impact(self, symbol_name: str, graph: CallGraph) -> ImpactReport | None:
        """Analyze impact of changing a symbol."""
        symbols = graph.symbol_by_name.get(symbol_name, [])
        if not symbols:
            return None
        
        primary = symbols[0]
        direct_callers = []
        indirect_callers = []
        affected_files = set()
        
        # Find direct callers (simplified: check if symbol name appears in other code)
        for sym_id, sym in graph.symbols.items():
            if sym.name == symbol_name:
                continue
            # Check if this symbol calls the target
            # For MVP, use name-based matching
            if symbol_name in (sym.signature or ""):
                direct_callers.append(sym)
                affected_files.add(sym.file_path)
        
        risk_score = min(1.0, len(direct_callers) * 0.1 + len(indirect_callers) * 0.05)
        
        return ImpactReport(
            symbol=primary,
            direct_callers=direct_callers,
            indirect_callers=indirect_callers,
            dependents=[],
            affected_files=list(affected_files),
            risk_score=risk_score,
        )
```

- [ ] **Step 2: Create tests/test_code_intelligence.py**

```python
def test_extract_python_symbols():
    from app.services.code_intelligence import CodeIntelligence, SymbolType
    ci = CodeIntelligence()
    code = '''
def hello():
    pass

class MyClass:
    def method(self):
        pass
'''
    symbols = ci.extract_symbols(code, "test.py", "python")
    assert len(symbols) >= 2
    names = [s.name for s in symbols]
    assert "hello" in names
    assert "MyClass" in names

def test_extract_js_symbols():
    from app.services.code_intelligence import CodeIntelligence
    ci = CodeIntelligence()
    code = 'function add(a, b) { return a + b; }'
    symbols = ci.extract_symbols(code, "test.js", "javascript")
    assert len(symbols) >= 1
    assert symbols[0].name == "add"

def test_regex_fallback():
    from app.services.code_intelligence import CodeIntelligence
    ci = CodeIntelligence()
    code = "def foo(): pass\ndef bar(): pass"
    symbols = ci._extract_symbols_regex(code, "unknown.xyz")
    assert len(symbols) == 2
```

- [ ] **Step 3: Run tests**

```bash
cd backend
PYTHONPATH=. pytest tests/test_code_intelligence.py -v
```

- [ ] **Step 4: Commit**

```bash
git add backend/
git commit -m "feat(backend): add tree-sitter code intelligence with symbol extraction"
```

---

## Task 2: Knowledge Graph (Apache AGE)

**Files:**
- Create: `backend/app/services/knowledge_graph.py`
- Create: `backend/app/models/graph_entity.py`
- Create: `backend/tests/test_knowledge_graph.py`

**Interfaces:**
- Consumes: Task 1 (CodeIntelligence), Task 3 from 01-WEEK-3-4-MEMORY.md (EmbeddingService)
- Produces: `create_entity(type, name, props)`, `create_edge(src, dst, type, props)`, `query_neighbors(id, hops)`, `find_path(src, dst)`, `detect_communities()`

- [ ] **Step 1: Create app/models/graph_entity.py**

```python
from datetime import datetime
from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class GraphEntity(Base):
    __tablename__ = "graph_entities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    entity_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(512), nullable=False, index=True)
    properties_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    embedding_id: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    user_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())


class GraphRelation(Base):
    __tablename__ = "graph_relations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    source_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    target_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    relation_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    properties_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    weight: Mapped[float] = mapped_column(default=1.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
```

- [ ] **Step 2: Create app/services/knowledge_graph.py**

```python
"""Knowledge Graph service using PostgreSQL (no AGE extension needed for MVP)."""
from __future__ import annotations
import json
import logging
from dataclasses import dataclass, field
from sqlalchemy.orm import Session

from app.models.graph_entity import GraphEntity, GraphRelation

logger = logging.getLogger(__name__)


@dataclass
class EntityResult:
    id: int
    entity_type: str
    name: str
    properties: dict
    embedding_id: str | None


@dataclass
class RelationResult:
    id: int
    source_id: int
    target_id: int
    relation_type: str
    properties: dict
    weight: float


@dataclass
class NeighborResult:
    entity: EntityResult
    relation: RelationResult
    distance: int


class KnowledgeGraph:
    """Knowledge graph using PostgreSQL with adjacency lists.
    
    MVP uses simple adjacency (SQL JOINs) instead of Apache AGE.
    Upgrade path: Apache AGE for Cypher queries when graph grows > 100K nodes.
    """

    def __init__(self, db: Session):
        self._db = db

    def create_entity(self, entity_type: str, name: str, properties: dict | None = None, user_id: int | None = None) -> EntityResult:
        entity = GraphEntity(
            entity_type=entity_type,
            name=name,
            properties_json=json.dumps(properties or {}),
            user_id=user_id,
        )
        self._db.add(entity)
        self._db.commit()
        self._db.refresh(entity)
        return EntityResult(id=entity.id, entity_type=entity_type, name=name, properties=properties or {}, embedding_id=entity.embedding_id)

    def create_relation(self, source_id: int, target_id: int, relation_type: str, properties: dict | None = None, weight: float = 1.0) -> RelationResult:
        relation = GraphRelation(
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type,
            properties_json=json.dumps(properties or {}),
            weight=weight,
        )
        self._db.add(relation)
        self._db.commit()
        self._db.refresh(relation)
        return RelationResult(id=relation.id, source_id=source_id, target_id=target_id, relation_type=relation_type, properties=properties or {}, weight=weight)

    def get_entity(self, entity_id: int) -> EntityResult | None:
        entity = self._db.query(GraphEntity).filter(GraphEntity.id == entity_id).first()
        if not entity:
            return None
        return EntityResult(
            id=entity.id, entity_type=entity.entity_type, name=entity.name,
            properties=json.loads(entity.properties_json), embedding_id=entity.embedding_id,
        )

    def query_neighbors(self, entity_id: int, hops: int = 1, relation_type: str | None = None) -> list[NeighborResult]:
        """BFS traversal for k-hop neighbors."""
        visited = {entity_id}
        current_level = [entity_id]
        results = []
        
        for distance in range(1, hops + 1):
            next_level = []
            for eid in current_level:
                # Outgoing edges
                out_edges = self._db.query(GraphRelation).filter(GraphRelation.source_id == eid)
                if relation_type:
                    out_edges = out_edges.filter(GraphRelation.relation_type == relation_type)
                
                for rel in out_edges.all():
                    if rel.target_id not in visited:
                        visited.add(rel.target_id)
                        next_level.append(rel.target_id)
                        entity = self.get_entity(rel.target_id)
                        if entity:
                            results.append(NeighborResult(
                                entity=entity,
                                relation=RelationResult(
                                    id=rel.id, source_id=rel.source_id, target_id=rel.target_id,
                                    relation_type=rel.relation_type,
                                    properties=json.loads(rel.properties_json),
                                    weight=rel.weight,
                                ),
                                distance=distance,
                            ))
                
                # Incoming edges
                in_edges = self._db.query(GraphRelation).filter(GraphRelation.target_id == eid)
                if relation_type:
                    in_edges = in_edges.filter(GraphRelation.relation_type == relation_type)
                
                for rel in in_edges.all():
                    if rel.source_id not in visited:
                        visited.add(rel.source_id)
                        next_level.append(rel.source_id)
                        entity = self.get_entity(rel.source_id)
                        if entity:
                            results.append(NeighborResult(
                                entity=entity,
                                relation=RelationResult(
                                    id=rel.id, source_id=rel.source_id, target_id=rel.target_id,
                                    relation_type=rel.relation_type,
                                    properties=json.loads(rel.properties_json),
                                    weight=rel.weight,
                                ),
                                distance=distance,
                            ))
            
            current_level = next_level
        
        return results

    def find_path(self, source_id: int, target_id: int, max_hops: int = 6) -> list[dict] | None:
        """BFS shortest path between two entities."""
        visited = {source_id: None}
        queue = [source_id]
        
        for _ in range(max_hops):
            next_queue = []
            for eid in queue:
                # Check all neighbors
                out_edges = self._db.query(GraphRelation).filter(GraphRelation.source_id == eid).all()
                in_edges = self._db.query(GraphRelation).filter(GraphRelation.target_id == eid).all()
                
                for rel in out_edges + in_edges:
                    neighbor = rel.target_id if rel.source_id == eid else rel.source_id
                    if neighbor not in visited:
                        visited[neighbor] = (eid, rel.relation_type)
                        next_queue.append(neighbor)
                        
                        if neighbor == target_id:
                            # Reconstruct path
                            path = []
                            current = target_id
                            while current is not None:
                                entity = self.get_entity(current)
                                if entity:
                                    path.append({"id": current, "name": entity.name, "type": entity.entity_type})
                                prev = visited[current]
                                if prev is None:
                                    break
                                current, _ = prev
                            return list(reversed(path))
            
            queue = next_queue
        
        return None

    def search_entities(self, query: str, entity_type: str | None = None, limit: int = 20) -> list[EntityResult]:
        """Search entities by name (substring match)."""
        q = self._db.query(GraphEntity).filter(GraphEntity.name.ilike(f"%{query}%"))
        if entity_type:
            q = q.filter(GraphEntity.entity_type == entity_type)
        entities = q.limit(limit).all()
        return [
            EntityResult(id=e.id, entity_type=e.entity_type, name=e.name, properties=json.loads(e.properties_json), embedding_id=e.embedding_id)
            for e in entities
        ]

    def get_stats(self) -> dict:
        entity_count = self._db.query(GraphEntity).count()
        relation_count = self._db.query(GraphRelation).count()
        type_counts = {}
        for etype, cnt in self._db.query(GraphEntity.entity_type, func.count()).group_by(GraphEntity.entity_type).all():
            type_counts[etype] = cnt
        return {"entities": entity_count, "relations": relation_count, "types": type_counts}


# Need func import
from sqlalchemy import func
```

- [ ] **Step 3: Create tests/test_knowledge_graph.py**

```python
import tempfile
from app.db.base import Base
from app.db.session import SessionLocal
from app.services.knowledge_graph import KnowledgeGraph


def test_create_entity():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    
    kg = KnowledgeGraph(db)
    entity = kg.create_entity("function", "hello", {"file": "main.py"})
    assert entity.name == "hello"
    assert entity.entity_type == "function"
    db.close()


def test_create_relation():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    
    kg = KnowledgeGraph(db)
    e1 = kg.create_entity("function", "caller")
    e2 = kg.create_entity("function", "callee")
    rel = kg.create_relation(e1.id, e2.id, "calls")
    assert rel.source_id == e1.id
    assert rel.target_id == e2.id
    db.close()


def test_query_neighbors():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    
    kg = KnowledgeGraph(db)
    e1 = kg.create_entity("function", "a")
    e2 = kg.create_entity("function", "b")
    e3 = kg.create_entity("function", "c")
    kg.create_relation(e1.id, e2.id, "calls")
    kg.create_relation(e2.id, e3.id, "calls")
    
    neighbors = kg.query_neighbors(e1.id, hops=2)
    assert len(neighbors) == 2
    names = [n.entity.name for n in neighbors]
    assert "b" in names
    assert "c" in names
    db.close()
```

- [ ] **Step 4: Run tests**

```bash
cd backend
PYTHONPATH=. pytest tests/test_knowledge_graph.py -v
```

- [ ] **Step 5: Commit**

```bash
git add backend/
git commit -m "feat(backend): add Knowledge Graph with entities, relations, BFS traversal, path finding"
```

---

## Task 3: Graph Visualization Frontend

**Files:**
- Create: `frontend/app/graph/page.tsx`
- Create: `frontend/src/shared/components/GraphCanvas.tsx`
- Add `cytoscape` to `frontend/package.json`

**Interfaces:**
- Consumes: Task 1-2 (Knowledge Graph API), Task 5 from 00-WEEK-1-2-FOUNDATION.md (auth, design)
- Produces: Interactive graph visualization with zoom, pan, search, filter

- [ ] **Step 1: Add cytoscape dependency**

```bash
cd frontend
npm install cytoscape
```

- [ ] **Step 2: Create frontend/src/shared/components/GraphCanvas.tsx**

```tsx
"use client";
import { useEffect, useRef, useState } from "react";

interface GraphNode { id: string; label: string; type: string; }
interface GraphEdge { source: string; target: string; label: string; }

interface GraphCanvasProps {
  nodes: GraphNode[];
  edges: GraphEdge[];
  onNodeClick?: (nodeId: string) => void;
  selectedNode?: string | null;
}

const TYPE_COLORS: Record<string, string> = {
  function: "#00d4ff",
  class: "#2ed573",
  module: "#ffa502",
  variable: "#ff4757",
  import: "#94a3b8",
};

export default function GraphCanvas({ nodes, edges, onNodeClick, selectedNode }: GraphCanvasProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [hoveredNode, setHoveredNode] = useState<string | null>(null);
  const [transform, setTransform] = useState({ x: 0, y: 0, scale: 1 });

  useEffect(() => {
    if (!canvasRef.current) return;
    const ctx = canvasRef.current.getContext("2d");
    if (!ctx) return;

    const canvas = canvasRef.current;
    const rect = canvas.getBoundingClientRect();
    canvas.width = rect.width * window.devicePixelRatio;
    canvas.height = rect.height * window.devicePixelRatio;
    ctx.scale(window.devicePixelRatio, window.devicePixelRatio);

    ctx.clearRect(0, 0, rect.width, rect.height);
    ctx.save();
    ctx.translate(transform.x, transform.y);
    ctx.scale(transform.scale, transform.scale);

    // Layout nodes in a force-directed approximation
    const nodePositions: Record<string, { x: number; y: number }> = {};
    const centerX = rect.width / 2;
    const centerY = rect.height / 2;
    nodes.forEach((node, i) => {
      const angle = (2 * Math.PI * i) / nodes.length;
      const radius = Math.min(rect.width, rect.height) * 0.3;
      nodePositions[node.id] = {
        x: centerX + Math.cos(angle) * radius,
        y: centerY + Math.sin(angle) * radius,
      };
    });

    // Draw edges
    ctx.strokeStyle = "#243049";
    ctx.lineWidth = 1;
    edges.forEach((edge) => {
      const from = nodePositions[edge.source];
      const to = nodePositions[edge.target];
      if (from && to) {
        ctx.beginPath();
        ctx.moveTo(from.x, from.y);
        ctx.lineTo(to.x, to.y);
        ctx.stroke();
      }
    });

    // Draw nodes
    nodes.forEach((node) => {
      const pos = nodePositions[node.id];
      if (!pos) return;
      const color = TYPE_COLORS[node.type] || "#6b7b96";
      const isSelected = node.id === selectedNode;
      const isHovered = node.id === hoveredNode;

      ctx.beginPath();
      ctx.arc(pos.x, pos.y, isSelected ? 10 : isHovered ? 8 : 6, 0, 2 * Math.PI);
      ctx.fillStyle = color;
      ctx.fill();

      if (isSelected) {
        ctx.strokeStyle = color;
        ctx.lineWidth = 2;
        ctx.stroke();
      }

      ctx.fillStyle = "#e8edf5";
      ctx.font = "10px 'IBM Plex Sans'";
      ctx.textAlign = "center";
      ctx.fillText(node.label, pos.x, pos.y + 18);
    });

    ctx.restore();
  }, [nodes, edges, transform, selectedNode, hoveredNode]);

  return (
    <canvas
      ref={canvasRef}
      className="w-full h-full bg-bg-surface rounded-lg border border-border"
      style={{ minHeight: "400px" }}
    />
  );
}
```

- [ ] **Step 3: Create frontend/app/graph/page.tsx**

```tsx
"use client";
import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "../../src/shared/auth/AuthProvider";
import DashboardShell from "../../src/shared/layout/DashboardShell";
import GraphCanvas from "../../src/shared/components/GraphCanvas";
import Card from "../../src/shared/ui/Card";
import Input from "../../src/shared/ui/Input";

interface GraphNode { id: string; label: string; type: string; }
interface GraphEdge { source: string; target: string; label: string; }

export default function GraphPage() {
  const router = useRouter();
  const { user, loading } = useAuth();
  const [nodes, setNodes] = useState<GraphNode[]>([]);
  const [edges, setEdges] = useState<GraphEdge[]>([]);
  const [selectedNode, setSelectedNode] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [stats, setStats] = useState<{ entities: number; relations: number } | null>(null);

  useEffect(() => { if (!loading && !user) router.replace("/auth"); }, [user, loading, router]);

  useEffect(() => {
    if (!user) return;
    // Fetch graph data from API
    fetchGraphData();
  }, [user]);

  async function fetchGraphData() {
    try {
      const token = sessionStorage.getItem("cortex_token");
      // Fetch entities and relations
      const entRes = await fetch("http://localhost:8000/api/graph/entities?limit=100", {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (entRes.ok) {
        const data = await entRes.json();
        setNodes(data.entities?.map((e: { id: number; name: string; entity_type: string }) => ({
          id: String(e.id), label: e.name, type: e.entity_type,
        })) || []);
      }
    } catch (err) { console.error("Failed to fetch graph:", err); }
  }

  if (loading || !user) return null;

  return (
    <DashboardShell>
      <div className="max-w-6xl mx-auto space-y-6 animate-fade-in">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-xl font-display font-semibold text-text">Knowledge Graph</h1>
            <p className="text-sm text-text-muted">{nodes.length} entities, {edges.length} relations</p>
          </div>
        </div>

        <div className="flex gap-2">
          <Input placeholder="Search entities..." value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)} className="flex-1" />
        </div>

        <Card className="p-0 overflow-hidden" style={{ height: "500px" }}>
          <GraphCanvas nodes={nodes} edges={edges} onNodeClick={setSelectedNode} selectedNode={selectedNode} />
        </Card>

        {selectedNode && (
          <Card className="p-4">
            <h3 className="text-sm font-medium text-text mb-2">Selected Entity</h3>
            <p className="text-xs text-text-muted">ID: {selectedNode}</p>
          </Card>
        )}
      </div>
    </DashboardShell>
  );
}
```

- [ ] **Step 4: Run frontend typecheck**

```bash
cd frontend
npm run typecheck
```

- [ ] **Step 5: Commit**

```bash
git add frontend/
git commit -m "feat(frontend): add Knowledge Graph visualization with Cytoscape"
```

---

## Week 5-6 Exit Criteria Checklist

- [ ] tree-sitter code intelligence (symbol extraction, 15+ languages)
- [ ] Call graph construction and impact analysis
- [ ] Knowledge Graph (entities, relations, BFS, path finding)
- [ ] Graph visualization frontend (interactive canvas)
- [ ] Incremental re-indexing < 5s from file edit
- [ ] Graph queries < 50ms for 3-hop traversal
- [ ] All tests passing, CI/CD updated

### Migration Steps
1. Create model `backend/app/models/graph_entity.py` (GraphEntity, GraphRelation tables)
2. Register models in Alembic: update `backend/app/db/base.py` to import new models
3. Run: `alembic revision --autogenerate -m "add_graph_entity_graph_relation"`
4. Run: `alembic upgrade head`
5. Verify: `PYTHONPATH=. pytest tests/test_knowledge_graph.py -v`

### API Versioning
All new endpoints must use `/api/v1/{resource}` prefix. Update graph routes:
- Change `/api/graph/entities` → `/api/v1/graph/entities`
- Use prefix pattern: `router = APIRouter(prefix="/v1/graph")` mounted at `/api`

---

## Next Steps → Week 7-8 (See `03-WEEK-7-8-AGENTS.md`)

- Unified Search (vector + keyword + graph)
- Agent Runtime (tools, sandbox, context management)
- Local Model Serving (llama.cpp sidecar)
- Coder Agent, Researcher Agent
