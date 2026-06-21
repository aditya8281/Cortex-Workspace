"""Graph builder — creates nodes and edges from indexed code chunks."""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass

from sqlalchemy.orm import Session

from backend.app.models.graph import GraphEdge, GraphNode
from backend.app.models.repo_index import CodeChunk, RepoIndex

logger = logging.getLogger(__name__)

# Patterns for extracting relationships from code
_IMPORT_RE = re.compile(
    r"^(?:from\s+([\w.]+)\s+import|import\s+([\w.]+))",
    re.MULTILINE,
)
_CALL_RE = re.compile(r"\b(\w+)\s*\(")
_INHERIT_RE = re.compile(r"class\s+(\w+)\s*\(([^)]*)\)")


@dataclass
class BuildResult:
    repo_id: int
    nodes_created: int = 0
    edges_created: int = 0
    status: str = "completed"


class GraphBuilder:
    """Build knowledge graph from indexed code chunks."""

    def __init__(self, db: Session):
        self.db = db

    def build_graph(self, repo_id: int) -> BuildResult:
        """Build knowledge graph for a repository."""
        repo = self.db.query(RepoIndex).filter(RepoIndex.id == repo_id).first()
        if not repo:
            raise ValueError(f"Repo {repo_id} not found")

        chunks = (
            self.db.query(CodeChunk)
            .filter(CodeChunk.repo_id == repo_id)
            .order_by(CodeChunk.file_path, CodeChunk.chunk_index)
            .all()
        )

        if not chunks:
            return BuildResult(repo_id=repo_id)

        # Clear existing graph for this repo
        self._clear_graph(repo_id)

        # Create nodes from chunks
        nodes: dict[int, GraphNode] = {}
        for chunk in chunks:
            node_type = self._infer_node_type(chunk)
            name = chunk.symbol_name or self._extract_name(chunk)
            qualified_name = self._build_qualified_name(chunk)

            node = GraphNode(
                chunk_id=chunk.id,
                repo_id=repo_id,
                node_type=node_type,
                name=name,
                qualified_name=qualified_name,
                language=chunk.language,
                file_path=chunk.file_path,
                start_line=chunk.start_line,
                end_line=chunk.end_line,
                metadata_json=json.dumps(
                    {
                        "content_preview": chunk.content[:200],
                        "symbol_type": chunk.symbol_type,
                    }
                ),
            )
            self.db.add(node)
            self.db.flush()
            nodes[chunk.id] = node

        # Create edges from code analysis
        edges_created = 0
        for chunk in chunks:
            source_node = nodes.get(chunk.id)
            if not source_node:
                continue

            edges_created += self._create_import_edges(source_node, chunk, nodes)
            edges_created += self._create_call_edges(source_node, chunk, nodes)
            edges_created += self._create_inherit_edges(source_node, chunk, nodes)
            edges_created += self._create_contains_edges(source_node, chunk, nodes)

        self.db.commit()

        result = BuildResult(
            repo_id=repo_id,
            nodes_created=len(nodes),
            edges_created=edges_created,
        )
        logger.info(
            "Built graph for repo %d: %d nodes, %d edges",
            repo_id,
            result.nodes_created,
            result.edges_created,
        )
        return result

    def build_document_graph(self, document_id: int) -> dict:
        """Build graph nodes and edges from a Document's chunks."""
        from datetime import datetime

        from backend.app.models.document import Document, DocumentChunk
        from backend.app.services.entity_extractor import EntityExtractor

        extractor = EntityExtractor()
        doc = self.db.query(Document).filter(Document.id == document_id).first()
        if not doc:
            return {"nodes": 0, "edges": 0}

        chunks = self.db.query(DocumentChunk).filter(DocumentChunk.document_id == document_id).all()

        node_count = 0
        edge_count = 0
        entity_nodes: dict[str, GraphNode] = {}

        for chunk in chunks:
            if doc.doc_type.value in ("markdown", "text"):
                entities, relationships = extractor.extract_from_text(chunk.content, doc.path)
            else:
                entities, relationships = extractor.extract_from_code(chunk.content, doc.path)

            for ent in entities:
                if ent.name not in entity_nodes:
                    node = GraphNode(
                        chunk_id=chunk.id,
                        repo_id=0,
                        node_type=ent.entity_type,
                        name=ent.name,
                        file_path=doc.path,
                        metadata_json=f'{{"source": "document", "document_id": {document_id}}}',
                    )
                    self.db.add(node)
                    self.db.flush()
                    entity_nodes[ent.name] = node
                    node_count += 1

            for rel in relationships:
                source_node = entity_nodes.get(rel.source)
                target_node = entity_nodes.get(rel.target)
                if source_node and target_node:
                    existing = (
                        self.db.query(GraphEdge)
                        .filter(
                            GraphEdge.source_id == source_node.id,
                            GraphEdge.target_id == target_node.id,
                            GraphEdge.edge_type == rel.relationship_type,
                        )
                        .first()
                    )
                    if existing:
                        existing.weight += rel.weight
                        existing.last_seen = datetime.utcnow()
                    else:
                        edge = GraphEdge(
                            source_id=source_node.id,
                            target_id=target_node.id,
                            edge_type=rel.relationship_type,
                            weight=rel.weight,
                        )
                        self.db.add(edge)
                        edge_count += 1

        self.db.commit()
        return {"nodes": node_count, "edges": edge_count}

    def _clear_graph(self, repo_id: int) -> None:
        """Remove existing graph data for a repo."""
        node_ids = [n.id for n in self.db.query(GraphNode.id).filter(GraphNode.repo_id == repo_id).all()]
        if node_ids:
            self.db.query(GraphEdge).filter(
                GraphEdge.source_id.in_(node_ids) | GraphEdge.target_id.in_(node_ids)
            ).delete(synchronize_session="fetch")
            self.db.query(GraphNode).filter(GraphNode.id.in_(node_ids)).delete(synchronize_session="fetch")
            self.db.flush()

    def _infer_node_type(self, chunk: CodeChunk) -> str:
        """Infer the node type from chunk metadata."""
        if chunk.symbol_type:
            return chunk.symbol_type
        if chunk.language in {"markdown", "text", "json", "yaml", "toml"}:
            return "file"
        return "code"

    def _extract_name(self, chunk: CodeChunk) -> str:
        """Extract a name from the chunk (file basename or first line)."""
        parts = chunk.file_path.split("/")
        return parts[-1] if parts else chunk.file_path

    def _build_qualified_name(self, chunk: CodeChunk) -> str:
        """Build a qualified name from file path and symbol."""
        base = chunk.file_path.replace("/", ".").replace("\\", ".")
        if chunk.symbol_name:
            return f"{base}::{chunk.symbol_name}"
        return base

    def _create_import_edges(self, source: GraphNode, chunk: CodeChunk, nodes: dict[int, GraphNode]) -> int:
        """Create 'imports' edges from import statements."""
        imports = _IMPORT_RE.findall(chunk.content)
        count = 0
        for group in imports:
            module = group[0] or group[1]
            if not module:
                continue
            target = self._find_node_by_name(nodes, module, exclude_id=source.id)
            if target:
                self.db.add(
                    GraphEdge(
                        source_id=source.id,
                        target_id=target.id,
                        edge_type="imports",
                    )
                )
                count += 1
        return count

    def _create_call_edges(self, source: GraphNode, chunk: CodeChunk, nodes: dict[int, GraphNode]) -> int:
        """Create 'calls' edges from function call patterns."""
        calls = set(_CALL_RE.findall(chunk.content))
        # Remove common builtins and keywords
        builtins = {
            "print",
            "len",
            "range",
            "str",
            "int",
            "float",
            "list",
            "dict",
            "set",
            "tuple",
            "type",
            "isinstance",
            "getattr",
            "setattr",
            "self",
            "cls",
            "super",
            "return",
            "yield",
            "if",
            "for",
            "while",
        }
        count = 0
        for call in calls:
            if call in builtins or len(call) < 2:
                continue
            target = self._find_node_by_name(nodes, call, exclude_id=source.id)
            if target:
                self.db.add(
                    GraphEdge(
                        source_id=source.id,
                        target_id=target.id,
                        edge_type="calls",
                    )
                )
                count += 1
        return count

    def _create_inherit_edges(self, source: GraphNode, chunk: CodeChunk, nodes: dict[int, GraphNode]) -> int:
        """Create 'inherits' edges from class definitions."""
        inherits = _INHERIT_RE.findall(chunk.content)
        count = 0
        for _class_name, parents in inherits:
            for parent in parents.split(","):
                parent = parent.strip()
                if not parent or parent == "object":
                    continue
                target = self._find_node_by_name(nodes, parent, exclude_id=source.id)
                if target:
                    self.db.add(
                        GraphEdge(
                            source_id=source.id,
                            target_id=target.id,
                            edge_type="inherits",
                        )
                    )
                    count += 1
        return count

    def _create_contains_edges(self, source: GraphNode, chunk: CodeChunk, nodes: dict[int, GraphNode]) -> int:
        """Create 'contains' edges from file-level containment."""
        count = 0
        for node in nodes.values():
            if node.id == source.id:
                continue
            if (
                node.file_path == source.file_path
                and node.node_type in {"function", "class", "method"}
                and source.node_type == "file"
            ):
                self.db.add(
                    GraphEdge(
                        source_id=source.id,
                        target_id=node.id,
                        edge_type="contains",
                    )
                )
                count += 1
        return count

    def _find_node_by_name(
        self, nodes: dict[int, GraphNode], name: str, exclude_id: int | None = None
    ) -> GraphNode | None:
        """Find a node by name or qualified name."""
        for node in nodes.values():
            if exclude_id and node.id == exclude_id:
                continue
            if node.name == name or node.qualified_name == name:
                return node
        return None

    def get_graph(self, repo_id: int) -> dict:
        """Get the full graph for a repository."""
        nodes = self.db.query(GraphNode).filter(GraphNode.repo_id == repo_id).all()
        node_ids = [n.id for n in nodes]
        edges = (
            self.db.query(GraphEdge)
            .filter((GraphEdge.source_id.in_(node_ids)) | (GraphEdge.target_id.in_(node_ids)))
            .all()
        )

        return {
            "nodes": [
                {
                    "id": n.id,
                    "name": n.name,
                    "node_type": n.node_type,
                    "file_path": n.file_path,
                    "language": n.language,
                    "qualified_name": n.qualified_name,
                    "start_line": n.start_line,
                    "end_line": n.end_line,
                }
                for n in nodes
            ],
            "edges": [
                {
                    "id": e.id,
                    "source_id": e.source_id,
                    "target_id": e.target_id,
                    "edge_type": e.edge_type,
                    "weight": e.weight,
                }
                for e in edges
            ],
        }

    def get_node_context(self, node_id: int) -> dict:
        """Get graph relationships for a specific node."""
        node = self.db.query(GraphNode).filter(GraphNode.id == node_id).first()
        if not node:
            return {}

        outgoing = self.db.query(GraphEdge).filter(GraphEdge.source_id == node_id).all()
        incoming = self.db.query(GraphEdge).filter(GraphEdge.target_id == node_id).all()

        return {
            "node": {
                "id": node.id,
                "name": node.name,
                "node_type": node.node_type,
                "file_path": node.file_path,
                "language": node.language,
            },
            "calls": [
                {"id": e.target.id, "name": e.target.name, "file_path": e.target.file_path}
                for e in outgoing
                if e.edge_type == "calls"
            ],
            "called_by": [
                {"id": e.source.id, "name": e.source.name, "file_path": e.source.file_path}
                for e in incoming
                if e.edge_type == "calls"
            ],
            "imports": [
                {"id": e.target.id, "name": e.target.name, "file_path": e.target.file_path}
                for e in outgoing
                if e.edge_type == "imports"
            ],
            "imported_by": [
                {"id": e.source.id, "name": e.source.name, "file_path": e.source.file_path}
                for e in incoming
                if e.edge_type == "imports"
            ],
            "inherits": [
                {"id": e.target.id, "name": e.target.name, "file_path": e.target.file_path}
                for e in outgoing
                if e.edge_type == "inherits"
            ],
            "contains": [
                {"id": e.target.id, "name": e.target.name, "node_type": e.target.node_type}
                for e in outgoing
                if e.edge_type == "contains"
            ],
        }
