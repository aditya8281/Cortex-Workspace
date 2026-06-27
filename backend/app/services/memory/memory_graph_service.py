"""Memory graph service — nodes, edges, traversal, path finding."""

from __future__ import annotations

from collections import deque

from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from backend.app.models.memory.memory_graph import MemoryEdge, MemoryNode


class MemoryGraphService:
    """Service for managing the memory graph (nodes, edges, traversal)."""

    def __init__(self, db: Session) -> None:
        self.db = db

    # --- Node Operations ---

    def add_node(self, user_id: int, memory_type: str, memory_id: int, label: str) -> MemoryNode:
        """Add a node to the memory graph. Idempotent — returns existing if duplicate."""
        existing = (
            self.db.query(MemoryNode)
            .filter(
                MemoryNode.user_id == user_id,
                MemoryNode.memory_type == memory_type,
                MemoryNode.memory_id == memory_id,
            )
            .first()
        )

        if existing:
            return existing

        node = MemoryNode(
            user_id=user_id,
            memory_type=memory_type,
            memory_id=memory_id,
            label=label,
        )
        self.db.add(node)
        self.db.commit()
        self.db.refresh(node)
        return node

    def get_node(self, node_id: int) -> MemoryNode | None:
        """Get a node by ID."""
        return self.db.query(MemoryNode).filter(MemoryNode.id == node_id).first()

    def get_user_nodes(self, user_id: int, memory_type: str | None = None, limit: int = 100) -> list[MemoryNode]:
        """Get all nodes for a user, optionally filtered by type."""
        query = self.db.query(MemoryNode).filter(MemoryNode.user_id == user_id)
        if memory_type:
            query = query.filter(MemoryNode.memory_type == memory_type)
        return query.limit(limit).all()

    def delete_node(self, user_id: int, node_id: int) -> bool:
        """Delete a node and all its edges."""
        node = self.db.query(MemoryNode).filter(MemoryNode.id == node_id, MemoryNode.user_id == user_id).first()
        if not node:
            return False

        # Delete all edges involving this node
        self.db.query(MemoryEdge).filter((MemoryEdge.source_id == node_id) | (MemoryEdge.target_id == node_id)).delete(
            synchronize_session="fetch"
        )

        self.db.delete(node)
        self.db.commit()
        return True

    # --- Edge Operations ---

    def add_edge(
        self,
        source_id: int,
        target_id: int,
        edge_type: str,
        weight: float = 0.5,
        bidirectional: bool = False,
    ) -> MemoryEdge:
        """Add an edge to the memory graph. Strengthens existing duplicate."""
        if source_id == target_id:
            raise ValueError("Self-loops are not allowed")

        # Check for existing edge
        existing = (
            self.db.query(MemoryEdge)
            .filter(
                MemoryEdge.source_id == source_id,
                MemoryEdge.target_id == target_id,
                MemoryEdge.edge_type == edge_type,
            )
            .first()
        )

        if existing:
            existing.weight = min(1.0, existing.weight + 0.05)
            self.db.commit()
            self.db.refresh(existing)
            return existing

        edge = MemoryEdge(
            source_id=source_id,
            target_id=target_id,
            edge_type=edge_type,
            weight=weight,
        )
        self.db.add(edge)

        if bidirectional:
            reverse = MemoryEdge(
                source_id=target_id,
                target_id=source_id,
                edge_type=edge_type,
                weight=weight,
            )
            self.db.add(reverse)

        self.db.commit()
        self.db.refresh(edge)
        return edge

    def get_edges_for_node(self, node_id: int) -> list[MemoryEdge]:
        """Get all edges involving a node (incoming + outgoing)."""
        return (
            self.db.query(MemoryEdge)
            .filter((MemoryEdge.source_id == node_id) | (MemoryEdge.target_id == node_id))
            .order_by(desc(MemoryEdge.weight))
            .all()
        )

    def strengthen_edge(self, edge_id: int, amount: float = 0.1) -> MemoryEdge | None:
        """Strengthen a connection between memories."""
        edge = self.db.query(MemoryEdge).filter(MemoryEdge.id == edge_id).first()
        if edge:
            edge.weight = min(1.0, edge.weight + amount)
            self.db.commit()
            self.db.refresh(edge)
        return edge

    def weaken_edge(self, edge_id: int, amount: float = 0.1) -> MemoryEdge | None:
        """Weaken a connection between memories."""
        edge = self.db.query(MemoryEdge).filter(MemoryEdge.id == edge_id).first()
        if edge:
            edge.weight = max(0.0, edge.weight - amount)
            self.db.commit()
            self.db.refresh(edge)
        return edge

    def delete_edge(self, edge_id: int) -> bool:
        """Delete a specific edge."""
        edge = self.db.query(MemoryEdge).filter(MemoryEdge.id == edge_id).first()
        if not edge:
            return False
        self.db.delete(edge)
        self.db.commit()
        return True

    # --- Traversal Operations ---

    def get_connections(self, node_id: int, depth: int = 1) -> list[MemoryNode]:
        """Get all connected nodes up to N hops away (BFS)."""
        visited: set[int] = {node_id}
        result: list[MemoryNode] = []
        queue: deque[tuple[int, int]] = deque([(node_id, 0)])

        while queue:
            current_id, current_depth = queue.popleft()
            if current_depth >= depth:
                continue

            edges = (
                self.db.query(MemoryEdge)
                .filter((MemoryEdge.source_id == current_id) | (MemoryEdge.target_id == current_id))
                .all()
            )

            for edge in edges:
                neighbor_id = edge.target_id if edge.source_id == current_id else edge.source_id
                if neighbor_id not in visited:
                    visited.add(neighbor_id)
                    node = self.get_node(neighbor_id)
                    if node:
                        result.append(node)
                        queue.append((neighbor_id, current_depth + 1))

        return result

    def find_path(self, source_id: int, target_id: int, max_depth: int = 5) -> list[MemoryNode] | None:
        """Find shortest path between two nodes using BFS."""
        if source_id == target_id:
            node = self.get_node(source_id)
            return [node] if node else None

        visited: set[int] = {source_id}
        queue: deque[tuple[int, list[int]]] = deque([(source_id, [source_id])])

        while queue:
            current_id, path = queue.popleft()
            if len(path) > max_depth:
                continue

            edges = (
                self.db.query(MemoryEdge)
                .filter((MemoryEdge.source_id == current_id) | (MemoryEdge.target_id == current_id))
                .all()
            )

            for edge in edges:
                neighbor_id = edge.target_id if edge.source_id == current_id else edge.source_id

                if neighbor_id == target_id:
                    full_path = path + [neighbor_id]
                    nodes = []
                    for nid in full_path:
                        node = self.get_node(nid)
                        if node:
                            nodes.append(node)
                    return nodes

                if neighbor_id not in visited:
                    visited.add(neighbor_id)
                    queue.append((neighbor_id, path + [neighbor_id]))

        return None

    def get_strongest_connections(self, user_id: int, limit: int = 10) -> list[MemoryEdge]:
        """Get the strongest edges in the user's graph."""
        return (
            self.db.query(MemoryEdge)
            .join(MemoryNode, MemoryEdge.source_id == MemoryNode.id)
            .filter(MemoryNode.user_id == user_id)
            .order_by(desc(MemoryEdge.weight))
            .limit(limit)
            .all()
        )

    def get_graph_stats(self, user_id: int) -> dict:
        """Get statistics about the user's memory graph."""
        total_nodes = self.db.query(MemoryNode).filter(MemoryNode.user_id == user_id).count()

        total_edges = (
            self.db.query(MemoryEdge)
            .join(MemoryNode, MemoryEdge.source_id == MemoryNode.id)
            .filter(MemoryNode.user_id == user_id)
            .count()
        )

        nodes_by_type: dict[str, int] = {}
        for memory_type in ["episodic", "semantic"]:
            count = (
                self.db.query(MemoryNode)
                .filter(
                    MemoryNode.user_id == user_id,
                    MemoryNode.memory_type == memory_type,
                )
                .count()
            )
            nodes_by_type[memory_type] = count

        avg_weight_result = (
            self.db.query(func.avg(MemoryEdge.weight))
            .join(MemoryNode, MemoryEdge.source_id == MemoryNode.id)
            .filter(MemoryNode.user_id == user_id)
            .scalar()
        )

        return {
            "total_nodes": total_nodes,
            "total_edges": total_edges,
            "nodes_by_type": nodes_by_type,
            "avg_edge_weight": float(avg_weight_result or 0.0),
        }
