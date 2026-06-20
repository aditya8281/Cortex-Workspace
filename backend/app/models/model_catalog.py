from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint, func
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
    primary_provider_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("providers.id"), nullable=True
    )
    popularity_score: Mapped[float] = mapped_column(Float, default=0)
    recency_score: Mapped[float] = mapped_column(Float, default=0)
    efficiency_score: Mapped[float] = mapped_column(Float, default=0)
    trending_score: Mapped[float] = mapped_column(Float, default=0)
    total_downloads: Mapped[int] = mapped_column(Integer, default=0)
    avg_rating: Mapped[float | None] = mapped_column(Float, nullable=True)
    rating_count: Mapped[int] = mapped_column(Integer, default=0)
    last_updated: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    variants: Mapped[list[ModelVariant]] = relationship(
        "ModelVariant", back_populates="catalog_entry", cascade="all, delete-orphan"
    )
    statistics: Mapped[ModelStatistics | None] = relationship(
        "ModelStatistics", back_populates="catalog_entry", uselist=False
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
    provider_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("providers.id"), nullable=True
    )
    provider_model_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("provider_models.id"), nullable=True
    )
    bits_per_param: Mapped[float | None] = mapped_column(Float, nullable=True)
    quality_multiplier: Mapped[float | None] = mapped_column(Float, nullable=True)
    speed_multiplier: Mapped[float | None] = mapped_column(Float, nullable=True)
    file_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    file_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    architecture: Mapped[str | None] = mapped_column(String(100), nullable=True)
    quantization_bits: Mapped[float | None] = mapped_column(Float, nullable=True)
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


class Provider(Base):
    __tablename__ = "providers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)
    provider_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    base_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    api_key_required: Mapped[bool] = mapped_column(Boolean, default=False)
    config_schema: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    capabilities: Mapped[list | None] = mapped_column(JSONB, nullable=True, default=list)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    health_status: Mapped[str] = mapped_column(String(20), default="unknown")
    last_health_check: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    provider_models: Mapped[list[ProviderModel]] = relationship(
        "ProviderModel", back_populates="provider", cascade="all, delete-orphan"
    )
    sync_jobs: Mapped[list[SyncJob]] = relationship(
        "SyncJob", back_populates="provider", cascade="all, delete-orphan"
    )


class Capability(Base):
    __tablename__ = "capabilities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    icon: Mapped[str | None] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class ProviderModel(Base):
    __tablename__ = "provider_models"
    __table_args__ = (
        UniqueConstraint("provider_id", "provider_model_id", name="uq_provider_model"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    provider_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("providers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    provider_model_id: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    family: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    parameter_count: Mapped[float | None] = mapped_column(Float, nullable=True)
    architecture: Mapped[str | None] = mapped_column(String(100), nullable=True)
    context_length: Mapped[int | None] = mapped_column(Integer, nullable=True)
    capabilities: Mapped[list | None] = mapped_column(JSONB, nullable=True, default=list)
    license: Mapped[str | None] = mapped_column(String(100), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    tags: Mapped[list | None] = mapped_column(JSONB, nullable=True, default=list)
    source_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    download_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    size_bytes: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    quantization: Mapped[str | None] = mapped_column(String(50), nullable=True)
    extra_metadata: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    discovered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    provider: Mapped[Provider] = relationship("Provider", back_populates="provider_models")


class Quantization(Base):
    __tablename__ = "quantizations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)
    bits_per_param: Mapped[float] = mapped_column(Float, nullable=False)
    quality_score: Mapped[float] = mapped_column(Float, nullable=False)
    speed_multiplier: Mapped[float | None] = mapped_column(Float, nullable=True)
    memory_multiplier: Mapped[float] = mapped_column(Float, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class HardwareProfile(Base):
    __tablename__ = "hardware_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    gpu_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    gpu_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    vram_gb: Mapped[float | None] = mapped_column(Float, nullable=True)
    ram_gb: Mapped[float] = mapped_column(Float, nullable=False)
    gpu_bandwidth_gbps: Mapped[float | None] = mapped_column(Float, nullable=True)
    compute_capability: Mapped[str | None] = mapped_column(String(20), nullable=True)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    is_user_defined: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class ModelStatistics(Base):
    __tablename__ = "model_statistics"
    __table_args__ = (
        UniqueConstraint("model_catalog_id", name="uq_model_statistics"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    model_catalog_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("model_catalog.id", ondelete="CASCADE"), nullable=False, index=True
    )
    download_count_total: Mapped[int] = mapped_column(Integer, default=0)
    download_count_period: Mapped[int] = mapped_column(Integer, default=0)
    average_rating: Mapped[float | None] = mapped_column(Float, nullable=True)
    rating_count: Mapped[int] = mapped_column(Integer, default=0)
    trending_score: Mapped[float] = mapped_column(Float, default=0, index=True)
    last_downloaded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    average_tps: Mapped[float | None] = mapped_column(Float, nullable=True)
    average_vram_usage_gb: Mapped[float | None] = mapped_column(Float, nullable=True)
    benchmark_scores: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    catalog_entry: Mapped[ModelCatalog] = relationship("ModelCatalog", back_populates="statistics")


class SyncJob(Base):
    __tablename__ = "sync_jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    provider_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("providers.id", ondelete="CASCADE"), nullable=True, index=True
    )
    sync_type: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    models_discovered: Mapped[int] = mapped_column(Integer, default=0)
    models_updated: Mapped[int] = mapped_column(Integer, default=0)
    models_added: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    provider: Mapped[Provider | None] = relationship("Provider", back_populates="sync_jobs")
