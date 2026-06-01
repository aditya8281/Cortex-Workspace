from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "AI Engineering Workspace"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"
    DATABASE_URL: str = "sqlite:///./app.db"

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore"
    )


settings = Settings()