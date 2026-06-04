from datetime import datetime, timezone
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.db.base import Base


class HierarchicalNode(Base):
    __tablename__ = "hierarchical_nodes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    node_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)  # "chunk", "file", "folder", "repo"
    path: Mapped[str] = mapped_column(String(1024), nullable=False, unique=True, index=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)  # Raw text or generated summary
    hash: Mapped[str | None] = mapped_column(String(64), nullable=True)  # Content hash to detect updates
    parent_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("hierarchical_nodes.id", ondelete="CASCADE"), nullable=True, index=True
    )
    vector_index: Mapped[int | None] = mapped_column(Integer, nullable=True)  # Mapping offset in IndexIDMap2 if needed
    metadata_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")  # Extra structured tags
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False
    )

    # Self-referential hierarchy mapping
    parent = relationship("HierarchicalNode", remote_side=[id], backref="children")
