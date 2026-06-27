"""Memory graph API endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.app.core.db import get_current_user, get_db
from backend.app.models.interaction.user import User
from backend.app.schemas.memory.graph import (
    MemoryEdgeCreate,
    MemoryEdgeResponse,
    MemoryGraphStats,
    MemoryNodeCreate,
    MemoryNodeResponse,
)
from backend.app.services.memory.memory_graph_service import MemoryGraphService

router = APIRouter(prefix="/graph", tags=["memory-graph"])


@router.get("/stats", response_model=MemoryGraphStats)
def get_graph_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MemoryGraphStats:
    """Get memory graph statistics."""
    service = MemoryGraphService(db)
    stats = service.get_graph_stats(current_user.id)
    strongest = service.get_strongest_connections(current_user.id, 5)
    return MemoryGraphStats(
        total_nodes=stats["total_nodes"],
        total_edges=stats["total_edges"],
        nodes_by_type=stats["nodes_by_type"],
        avg_edge_weight=stats["avg_edge_weight"],
        strongest_connections=[MemoryEdgeResponse.model_validate(e) for e in strongest],
    )


@router.get("/strongest")
def get_strongest_connections(
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[dict]:
    """Get the strongest edges in the graph."""
    service = MemoryGraphService(db)
    edges = service.get_strongest_connections(current_user.id, limit)
    return [MemoryEdgeResponse.model_validate(e).model_dump() for e in edges]


@router.post("/node", response_model=MemoryNodeResponse, status_code=201)
def create_node(
    data: MemoryNodeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MemoryNodeResponse:
    """Create a graph node for a memory."""
    service = MemoryGraphService(db)
    return service.add_node(
        user_id=current_user.id,
        memory_type=data.memory_type,
        memory_id=data.memory_id,
        label=data.label,
    )


@router.get("/node/{node_id}/connections")
def get_connections(
    node_id: int,
    depth: int = Query(1, ge=1, le=5),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Get all connected nodes up to N hops."""
    service = MemoryGraphService(db)
    connections = service.get_connections(node_id, depth)
    return {"node_id": node_id, "depth": depth, "connections": connections}


@router.get("/path/{source_id}/{target_id}")
def find_path(
    source_id: int,
    target_id: int,
    max_depth: int = Query(5, ge=1, le=10),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Find shortest path between two nodes."""
    service = MemoryGraphService(db)
    path = service.find_path(source_id, target_id, max_depth)
    if not path:
        raise HTTPException(status_code=404, detail="No path found")
    return {"path": path, "length": len(path)}


@router.post("/edge", response_model=MemoryEdgeResponse, status_code=201)
def create_edge(
    data: MemoryEdgeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MemoryEdgeResponse:
    """Create an edge between two nodes."""
    service = MemoryGraphService(db)
    try:
        return service.add_edge(
            source_id=data.source_id,
            target_id=data.target_id,
            edge_type=data.edge_type,
            weight=data.weight,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/edge/{edge_id}/strengthen")
def strengthen_edge(
    edge_id: int,
    amount: float = Query(0.1, ge=0.01, le=0.5),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MemoryEdgeResponse:
    """Strengthen an edge weight."""
    service = MemoryGraphService(db)
    edge = service.strengthen_edge(edge_id, amount)
    if not edge:
        raise HTTPException(status_code=404, detail="Edge not found")
    return edge


@router.delete("/edge/{edge_id}", status_code=204)
def delete_edge(
    edge_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """Delete an edge."""
    service = MemoryGraphService(db)
    deleted = service.delete_edge(edge_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Edge not found")
