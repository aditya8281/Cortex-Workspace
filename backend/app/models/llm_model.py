from datetime import datetime
from sqlalchemy import Integer, String, LargeBinary, Boolean, DateTime, Float, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base


class CortexProvider(Base):
    __tablename__ = "cortex_providers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    base_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    api_key_encrypted: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_custom: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    default_model_name: Mapped[str | None] = mapped_column(String(256), nullable=True)
    provider_type: Mapped[str | None] = mapped_column(String(32), nullable=True)  # "local" | "cloud" | "custom"
    headers_json: Mapped[str | None] = mapped_column(String(2048), nullable=True)  # Custom headers for API calls
    model_fetch_endpoint: Mapped[str | None] = mapped_column(String(256), nullable=True)  # /v1/models endpoint
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)


class CortexModel(Base):
    __tablename__ = "cortex_models"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(256), index=True, nullable=False)
    provider_name: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    context_length: Mapped[int | None] = mapped_column(Integer, nullable=True)
    parameters: Mapped[str | None] = mapped_column(String(64), nullable=True)
    quantization: Mapped[str | None] = mapped_column(String(64), nullable=True)
    vram_estimate: Mapped[str | None] = mapped_column(String(64), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="active", nullable=False)
    is_local: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_custom: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    # New fields for better model management
    provider_type: Mapped[str | None] = mapped_column(String(32), nullable=True)  # "local" | "cloud" | "custom"
    source: Mapped[str | None] = mapped_column(String(64), nullable=True)  # "ollama" | "openai" | "anthropic" | "custom_api"
    model_identifier: Mapped[str | None] = mapped_column(String(256), nullable=True)  # String used in API calls (can differ from display name)
    api_endpoint: Mapped[str | None] = mapped_column(String(512), nullable=True)  # Custom API endpoint for this model
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)


class CortexRoutingProfile(Base):
    __tablename__ = "cortex_routing_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)


class CortexTaskRoute(Base):
    __tablename__ = "cortex_task_routes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    profile_name: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    task_type: Mapped[str] = mapped_column(String(64), nullable=False)
    primary_model: Mapped[str] = mapped_column(String(256), nullable=False)
    fallback_model: Mapped[str] = mapped_column(String(256), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)


class CortexModelMetric(Base):
    """Aggregate per-model performance metrics — upserted after every inference."""
    __tablename__ = "cortex_model_metrics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    model_name: Mapped[str] = mapped_column(String(256), unique=True, index=True, nullable=False)
    provider_name: Mapped[str] = mapped_column(String(64), nullable=False)
    total_requests: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    success_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    failure_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    avg_latency_ms: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)


class CortexModelEvent(Base):
    """Append-only inference event log — powers analytics and health monitoring."""
    __tablename__ = "cortex_model_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    model_name: Mapped[str] = mapped_column(String(256), index=True, nullable=False)
    provider_name: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    task_type: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    latency_ms: Mapped[float] = mapped_column(Float, nullable=False)
    success: Mapped[bool] = mapped_column(Boolean, nullable=False)
    fallback_used: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    routed_by: Mapped[str] = mapped_column(String(32), default="auto", nullable=False)  # "auto" | "manual"
    ts: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
