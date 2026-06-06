import json
from typing import Any

from pydantic import AliasChoices, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "Cortex Workspace"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"

    SECRET_KEY: str = ""
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    DATABASE_URL: str = ""
    REDIS_URL: str = "redis://localhost:6379/0"
    LLM_CACHE_TTL_SECONDS: int = 1800
    ENV: str = "development"
    MEMORY_PATH: str | None = Field(
        default=None,
        validation_alias=AliasChoices("MEMORY_PATH", "CORTEX_MEMORY_PATH"),
    )
    VAULT_PATH: str | None = Field(
        default=None,
        validation_alias=AliasChoices("VAULT_PATH", "CORTEX_VAULT_PATH"),
    )
    DEFAULT_MODEL: str | None = Field(default=None, validation_alias="DEFAULT_MODEL")
    MODEL_API_KEYS: dict[str, str] = Field(default_factory=dict)
    CLOUD_PROVIDER_CONFIGS: dict[str, dict[str, Any]] = Field(default_factory=dict)

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    WORKSPACE_ROOT: str = "."
    
    # =========================
    # AI CONFIGURATION
    # =========================

    AI_MODE: str = "local"

    AI_MODEL: str = "gpt-4o-mini"

    AI_API_KEY: str | None = None

    AI_API_URL: str | None = None

    LOCAL_MODEL: str = "llama3"
    OLLAMA_URL: str = "http://localhost:11434"

    @field_validator("MODEL_API_KEYS", "CLOUD_PROVIDER_CONFIGS", mode="before")
    @classmethod
    def parse_json_mapping(cls, value):
        if value in (None, ""):
            return {}

        if isinstance(value, dict):
            return value

        if isinstance(value, str):
            try:
                parsed = json.loads(value)
            except json.JSONDecodeError as exc:
                raise ValueError("Expected a JSON object") from exc

            if isinstance(parsed, dict):
                return parsed

        raise ValueError("Expected a JSON object")

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
