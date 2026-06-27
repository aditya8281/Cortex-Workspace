"""Memory graph Pydantic schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class MemoryNodeCreate(BaseModel):
    """Schema for creating a memory graph node."""

    memory_type: str = Field(..., description="Type: episodic or semantic")
    memory_id: int = Field(..., gt=0, description="ID of the target memory")
    label: str = Field(..., min_length=1, max_length=200, description="Short description")

    @field_validator("memory_type")
    @classmethod
    def validate_memory_type(cls, v: str) -> str:
        valid_types = {"episodic", "semantic"}
        if v not in valid_types:
            raise ValueError(f"Memory type must be one of: {valid_types}")
        return v


class MemoryNodeResponse(BaseModel):
    """Schema for returning a memory graph node."""

    id: int
    user_id: int
    memory_type: str
    memory_id: int
    label: str
    embedding_id: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class MemoryEdgeCreate(BaseModel):
    """Schema for creating a memory graph edge."""

    source_id: int = Field(..., gt=0, description="Source node ID")
    target_id: int = Field(..., gt=0, description="Target node ID")
    edge_type: str = Field(
        ..., min_length=1, max_length=100, description="Edge type"
    )
    weight: float = Field(0.5, ge=0.0, le=1.0, description="Edge weight 0.0-1.0")


class MemoryEdgeResponse(BaseModel):
    """Schema for returning a memory graph edge."""

    id: int
    source_id: int
    target_id: int
    edge_type: str
    weight: float
    created_at: datetime

    model_config = {"from_attributes": True}


class MemoryGraphResponse(BaseModel):
    """Full graph response with nodes and edges."""

    nodes: list[MemoryNodeResponse]
    edges: list[MemoryEdgeResponse]
    total_nodes: int
    total_edges: int


class MemoryGraphStats(BaseModel):
    """Graph statistics."""

    total_nodes: int
    total_edges: int
    nodes_by_type: dict
    avg_edge_weight: float
    strongest_connections: list[MemoryEdgeResponse]
