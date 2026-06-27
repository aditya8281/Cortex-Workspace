"""Memory graph models — nodes and edges for the memory knowledge graph."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Index, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base


class MemoryNode(Base):
    """A node in the memory graph, pointing to an episodic or semantic memory."""

    __tablename__ = "memory_nodes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False, index=True
    )
    memory_type: Mapped[str] = mapped_column(String(50), nullable=False)
    memory_id: Mapped[int] = mapped_column(Integer, nullable=False)
    label: Mapped[str] = mapped_column(String(200), nullable=False)
    embedding_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Relationships — no FK, so no back_populates
    outgoing_edges = relationship(
        "MemoryEdge", foreign_keys="MemoryEdge.source_id", back_populates="source"
    )
    incoming_edges = relationship(
        "MemoryEdge", foreign_keys="MemoryEdge.target_id", back_populates="target"
    )

    __table_args__ = (
        UniqueConstraint(
            "user_id", "memory_type", "memory_id", name="uq_memory_node_target"
        ),
        Index("ix_memory_node_user_type", "user_id", "memory_type"),
    )


class MemoryEdge(Base):
    """A weighted, directed edge between two memory nodes."""

    __tablename__ = "memory_edges"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    source_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("memory_nodes.id"), nullable=False, index=True
    )
    target_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("memory_nodes.id"), nullable=False, index=True
    )
    edge_type: Mapped[str] = mapped_column(String(100), nullable=False)
    weight: Mapped[float] = mapped_column(Float, nullable=False, default=0.5)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Relationships
    source = relationship(
        "MemoryNode", foreign_keys=[source_id], back_populates="outgoing_edges"
    )
    target = relationship(
        "MemoryNode", foreign_keys=[target_id], back_populates="incoming_edges"
    )

    __table_args__ = (
        UniqueConstraint(
            "source_id", "target_id", "edge_type", name="uq_memory_edge"
        ),
        Index("ix_memory_edge_source", "source_id"),
        Index("ix_memory_edge_target", "target_id"),
        Index("ix_memory_edge_weight", "weight"),
    )
