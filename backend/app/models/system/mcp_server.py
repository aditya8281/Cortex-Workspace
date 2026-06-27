"""MCP server registry models — persistent server configs and discovered tools."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base


class MCPServer(Base):
    """Persistent MCP server configuration."""

    __tablename__ = "mcp_servers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    command: Mapped[str | None] = mapped_column(String(500), nullable=True)
    args: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    env: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    transport: Mapped[str] = mapped_column(String(50), nullable=False, server_default="stdio")
    sse_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    working_dir: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    health_check_interval: Mapped[int] = mapped_column(Integer, nullable=False, server_default="30")
    max_restarts: Mapped[int] = mapped_column(Integer, nullable=False, server_default="3")
    user_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    tools: Mapped[list[MCPServerTool]] = relationship(
        "MCPServerTool", back_populates="server", cascade="all, delete-orphan"
    )

    __table_args__ = (Index("ix_mcp_servers_enabled", "enabled"),)


class MCPServerTool(Base):
    """Tool discovered from an MCP server."""

    __tablename__ = "mcp_server_tools"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    server_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("mcp_servers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    tool_name: Mapped[str] = mapped_column(String(255), nullable=False)
    tool_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    tool_schema: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    server: Mapped[MCPServer] = relationship("MCPServer", back_populates="tools")

    __table_args__ = (Index("ix_mcp_server_tools_unique", "server_id", "tool_name", unique=True),)
