import os

from pydantic import AliasChoices, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "Cortex Workspace"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"

    SECRET_KEY: str = ""
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    DATABASE_URL: str = "postgresql://cortex:cortex@localhost:5432/cortex"
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

    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:8080"

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
    def validate_secret_key(cls, value: str) -> str:
        if not value and os.environ.get("ENV") not in ("development", "test"):
            raise ValueError(
                "SECRET_KEY must be set in production. "
                "Generate one with: openssl rand -hex 32"
            )
        return value

    WORKSPACE_ROOT: str = "."

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
