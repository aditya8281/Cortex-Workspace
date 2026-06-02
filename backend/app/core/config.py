from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "Cortex Workspace"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"

    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    DATABASE_URL: str
    ENV: str = "development"

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
