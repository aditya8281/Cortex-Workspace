from pydantic import AliasChoices, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "Cortex Workspace"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"

    SECRET_KEY: str = ""
    PREVIOUS_SECRET_KEYS: str = ""  # Comma-separated list of previous keys for rotation
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30  # 30 minutes, refresh token rotation handles session续

    DATABASE_URL: str = ""  # Must be set via environment variable
    REDIS_URL: str = "redis://localhost:6379/0"
    ENV: str = "development"
    CORTEX_ROOT: str | None = Field(
        default=None,
        validation_alias=AliasChoices("CORTEX_ROOT", "CORTEX_STORAGE_ROOT"),
    )
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
        "http://localhost:8000",
        "http://localhost:8080",
    ]
    CORS_ORIGINS: str = ""  # Comma-separated list of allowed CORS origins for production

    def model_post_init(self, __context) -> None:
        if self.CORS_ORIGINS:
            self.ALLOWED_ORIGINS = [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

        if not self.SECRET_KEY:
            import secrets
            self.SECRET_KEY = secrets.token_hex(32)

    EMBEDDING_DIM: int = 768
    EMBEDDING_MODEL_PATH: str = ""
    EMBEDDING_MODEL_NAME: str = "nomic-embed-text"

    # LLM Settings
    LLM_PROVIDER: str = "auto"  # "auto", "llama_cpp", "ollama", "none"
    LLM_MODEL_PATH: str = ""  # Path to GGUF model file
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    LLM_CONTEXT_SIZE: int = 4096
    LLM_GPU_LAYERS: int = 0
    LLM_TIMEOUT: float = 120.0

    # Rate limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW_SECONDS: int = 60

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
