from datetime import datetime
from sqlalchemy import Integer, String, DateTime, Boolean, Float, func, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base


class OllamaRegistryModel(Base):
    """Ollama model registry - stores scraped models from ollama.com/library"""
    __tablename__ = "ollama_registry_models"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    model_id: Mapped[str] = mapped_column(String(128), unique=True, index=True, nullable=False)  # "llama3", "mistral", etc
    family: Mapped[str] = mapped_column(String(64), index=True, nullable=False)  # "llama", "mistral", "qwen"
    display_name: Mapped[str] = mapped_column(String(256), nullable=False)  # "Llama 3", "Mistral", etc
    description: Mapped[str] = mapped_column(Text, nullable=True)
    tags: Mapped[str] = mapped_column(Text, nullable=True)  # JSON array of tag strings
    capabilities: Mapped[str] = mapped_column(Text, nullable=True)  # JSON array: ["chat", "reasoning", "coding", "vision"]
    
    # Model specifications
    parameters: Mapped[str] = mapped_column(String(64), nullable=True)  # "7B", "13B", "70B"
    context_length: Mapped[int | None] = mapped_column(Integer, nullable=True)
    quantization: Mapped[str] = mapped_column(String(64), default="unknown", nullable=False)  # "4-bit", "8-bit", "fp16"
    
    # Source and installation
    source_url: Mapped[str] = mapped_column(String(512), nullable=False)  # https://ollama.com/library/llama3
    pull_command: Mapped[str] = mapped_column(String(256), nullable=False)  # "ollama pull llama3"
    
    # Installation tracking
    is_installed: Mapped[bool] = mapped_column(Boolean, default=False, index=True, nullable=False)
    last_installed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    
    # Sync and cache
    last_synced_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)


class OllamaDownloadProgress(Base):
    """Track active model downloads with streaming progress"""
    __tablename__ = "ollama_download_progress"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    model_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="queued", nullable=False)  # queued, downloading, extracting, complete, failed
    progress_percent: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    bytes_downloaded: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_bytes: Mapped[int] = mapped_column(Integer, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
