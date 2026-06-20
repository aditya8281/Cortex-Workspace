from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base


class ModelCatalog(Base):
    __tablename__ = "model_catalog"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    model_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    family: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    parameter_count: Mapped[float | None] = mapped_column(Float, nullable=True)
    architecture: Mapped[str | None] = mapped_column(String(100), nullable=True)
    context_length_default: Mapped[int | None] = mapped_column(Integer, nullable=True)
    context_length_max: Mapped[int | None] = mapped_column(Integer, nullable=True)
    capabilities: Mapped[list | None] = mapped_column(JSONB, nullable=True, default=list)
    license: Mapped[str | None] = mapped_column(String(100), nullable=True)
    recommended_use_cases: Mapped[list | None] = mapped_column(JSONB, nullable=True, default=list)
    not_recommended_for: Mapped[list | None] = mapped_column(JSONB, nullable=True, default=list)
    release_date: Mapped[str | None] = mapped_column(String(20), nullable=True)
    version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    family_version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    benchmarks: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    source_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    ollama_library_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    huggingface_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    tags: Mapped[list | None] = mapped_column(JSONB, nullable=True, default=list)
    last_updated: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    variants: Mapped[list[ModelVariant]] = relationship(
        "ModelVariant", back_populates="catalog_entry", cascade="all, delete-orphan"
    )


class ModelVariant(Base):
    __tablename__ = "model_variants"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    model_catalog_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("model_catalog.id", ondelete="CASCADE"), index=True
    )
    variant_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    quantization: Mapped[str] = mapped_column(String(50), nullable=False)
    quantization_level: Mapped[str | None] = mapped_column(String(20), nullable=True)
    parameter_count: Mapped[float | None] = mapped_column(Float, nullable=True)
    size_bytes: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    size_gb: Mapped[float | None] = mapped_column(Float, nullable=True)
    vram_required_gb: Mapped[float | None] = mapped_column(Float, nullable=True)
    ram_required_gb: Mapped[float | None] = mapped_column(Float, nullable=True)
    recommended_vram_gb: Mapped[float | None] = mapped_column(Float, nullable=True)
    estimated_tps_gpu: Mapped[float | None] = mapped_column(Float, nullable=True)
    estimated_tps_cpu: Mapped[float | None] = mapped_column(Float, nullable=True)
    quality_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    compatible_backends: Mapped[list | None] = mapped_column(JSONB, nullable=True, default=lambda: ["ollama", "llama_cpp"])
    downloaded: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    download_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    ollama_tag: Mapped[str | None] = mapped_column(String(255), nullable=True)
    huggingface_repo: Mapped[str | None] = mapped_column(String(255), nullable=True)
    huggingface_file: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_downloaded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    download_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    catalog_entry: Mapped[ModelCatalog] = relationship("ModelCatalog", back_populates="variants")


class ModelDownload(Base):
    __tablename__ = "model_downloads"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    model_variant_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("model_variants.id"), nullable=True
    )
    user_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    progress: Mapped[float] = mapped_column(Float, default=0)
    download_speed_bytes_sec: Mapped[float | None] = mapped_column(Float, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    file_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    file_size_bytes: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    checksum: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class ModelUsage(Base):
    __tablename__ = "model_usage"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    model_variant_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("model_variants.id"), nullable=True, index=True
    )
    user_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    usage_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    tokens_prompt: Mapped[int | None] = mapped_column(Integer, nullable=True)
    tokens_completion: Mapped[int | None] = mapped_column(Integer, nullable=True)
    duration_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    tps_generation: Mapped[float | None] = mapped_column(Float, nullable=True)
    tps_prompt: Mapped[float | None] = mapped_column(Float, nullable=True)
    context_length: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
