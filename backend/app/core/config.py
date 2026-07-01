"""
Configuration module for CORTEX.

Key design notes:

- ALLOWED_ORIGINS: In development/test mode, the Settings.model_post_init()
  strips individually-listed localhost origins and sets a runtime flag
  (_dev_accept_any_localhost) so that any http://localhost:PORT or
  http://127.0.0.1:PORT is accepted. This is necessary because start.sh
  dynamically selects ports for the backend and frontend dev servers.
  In production, set CORS_ORIGINS as a comma-separated list of explicit origins.

- QDRANT_HOST / QDRANT_PORT: Default to "localhost" / 6333, but these are
  overridden by .env at runtime. start.sh writes QDRANT_HOST=127.0.0.1 and
  QDRANT_PORT=<dynamically-found-port> into .env before launching the backend,
  so the vector database port matches whatever port Qdrant was started on.

- Dynamic port setup via start.sh: The startup script (start.sh) discovers
  free ports for PostgreSQL (starting at 5435), Qdrant (starting at 6333),
  the backend (starting at 8000), and the frontend (starting at 3000). It
  writes DATABASE_URL, QDRANT_HOST, and QDRANT_PORT into .env so the config
  picks up the correct values automatically.
"""

from pydantic import AliasChoices, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "CORTEX"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"

    SECRET_KEY: str = ""
    PREVIOUS_SECRET_KEYS: str = ""  # Comma-separated list of previous keys for rotation
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30  # 30 minutes, refresh token rotation handles session续

    DATABASE_URL: str = ""  # Must be set via environment variable
    REDIS_URL: str = "redis://localhost:6379/0"
    ENV: str = "development"
    CORTEX_ROOT: str | None = None
    MEMORY_PATH: str | None = Field(
        default=None,
        validation_alias=AliasChoices("MEMORY_PATH", "CORTEX_MEMORY_PATH"),
    )
    VAULT_PATH: str | None = Field(
        default=None,
        validation_alias=AliasChoices("VAULT_PATH", "CORTEX_VAULT_PATH"),
    )

    ALLOWED_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:3002",
        "http://localhost:3003",
        "http://localhost:3004",
        "http://localhost:3005",
        "http://localhost:8000",
        "http://localhost:8080",
    ]
    CORS_ORIGINS: str = ""  # Comma-separated list of allowed CORS origins for production

    def model_post_init(self, __context) -> None:
        import logging
        import os
        import re

        logger = logging.getLogger(__name__)

        # Deprecation warnings for renamed env vars
        if os.environ.get("CORTEX_STORAGE_ROOT"):
            logger.warning("CORTEX_STORAGE_ROOT is deprecated. Use CORTEX_ROOT instead.")
        if os.environ.get("CORTEX_NEW_AGENT"):
            logger.warning("CORTEX_NEW_AGENT is deprecated. Use CORTEX_NEW_AGENT_LOOP instead.")

        if self.CORS_ORIGINS:
            self.ALLOWED_ORIGINS = [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

        # In dev mode, accept any localhost origin (ports are dynamic)
        if self.ENV in ("development", "test"):
            # Match http://localhost:PORT or http://127.0.0.1:PORT
            localhost_pattern = re.compile(r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$")
            self.ALLOWED_ORIGINS = [
                o for o in self.ALLOWED_ORIGINS
                if not localhost_pattern.match(o)
            ]
            # Add a wildcard-accepting origin matcher at runtime via middleware
            self._dev_accept_any_localhost = True
        else:
            self._dev_accept_any_localhost = False

        if not self.SECRET_KEY:
            import secrets

            self.SECRET_KEY = secrets.token_hex(32)

    EMBEDDING_DIM: int = 768
    EMBEDDING_MODEL_PATH: str = ""
    EMBEDDING_MODEL_NAME: str = "nomic-embed-text"

    # Qdrant vector DB settings
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333
    QDRANT_PREFER_GRPC: bool = False

    # LLM Settings
    LLM_PROVIDER: str = "auto"  # "auto", "llama_cpp", "ollama", "none"
    LLM_MODEL_PATH: str = ""  # Path to GGUF model file
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    LLM_CONTEXT_SIZE: int = 8192  # Increased from 4096 for longer chat context
    LLM_GPU_LAYERS: int = 0  # GPU offloading for llama.cpp (0 = CPU only)
    LLM_THREADS: int = 8  # CPU threads for llama.cpp (Ryzen 7840HS = 16 cores, use 8)
    LLM_BATCH_SIZE: int = 2048  # Prompt processing batch size (default 512, 2048 = faster)
    LLM_MAX_TOKENS: int = 2048  # Max tokens per generation
    LLM_TEMPERATURE: float = 0.7  # Default generation temperature
    LLM_CONCURRENCY: int = 4  # Max concurrent LLM requests
    LLM_USE_MMAP: bool = True  # Memory-map model file (fast for NVMe, disable for network drives)
    LLM_TIMEOUT: float = 120.0

    # Rate limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW_SECONDS: int = 60

    # Feature flags
    # Reserved for V1 Phase-2 streaming agent loop (loop.py).
    # When True, run_manager.py dispatches to the new single-streaming loop
    # instead of the legacy Planner→Executor path. Currently False — the
    # streaming loop is not yet built (next Phase 2 component).
    CORTEX_NEW_AGENT_LOOP: bool = Field(default=False)

    # HTTPS redirect
    HTTPS_REDIRECT_ENABLED: bool = False
    HTTPS_REDIRECT_PORT: int = 443

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @field_validator("SECRET_KEY")
    @classmethod
    def validate_secret_key(cls, value: str, info) -> str:
        env = info.data.get("ENV", "development")
        if not value and env not in ("development", "test"):
            raise ValueError("SECRET_KEY must be set in production. Generate one with: openssl rand -hex 32")
        if not value and env in ("development", "test"):
            import logging

            logging.getLogger(__name__).warning(
                "SECRET_KEY is empty. Using development/test mode — do NOT use in production."
            )
        return value

    WORKSPACE_ROOT: str = "."

    @property
    def all_secret_keys(self) -> list[str]:
        """Return current key plus all previous keys for JWT rotation verification."""
        keys = [self.SECRET_KEY] if self.SECRET_KEY else []
        if self.PREVIOUS_SECRET_KEYS:
            keys.extend(k.strip() for k in self.PREVIOUS_SECRET_KEYS.split(",") if k.strip())
        return keys

    @field_validator("DEBUG", mode="before")
    @classmethod
    def normalize_debug(cls, value):
        if isinstance(value, bool):
            return value

        if isinstance(value, str):
            normalized = value.strip().lower()

            if normalized in {"1", "true", "yes", "on"}:
                return True

            if normalized in {"0", "false", "no", "off", "release", "prod", "production"}:
                return False

        return value


settings = Settings()
