from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from backend.app.core.config import settings


class AISettings(BaseModel):

    mode: str = settings.AI_MODE

    api_key: str | None = settings.AI_API_KEY

    api_url: str | None = settings.AI_API_URL

    model: str = settings.DEFAULT_MODEL or settings.AI_MODEL

    local_model: str = settings.LOCAL_MODEL
    default_model: str | None = settings.DEFAULT_MODEL
    model_api_keys: dict[str, str] = Field(default_factory=lambda: dict(settings.MODEL_API_KEYS))
    cloud_provider_configs: dict[str, dict[str, Any]] = Field(
        default_factory=lambda: dict(settings.CLOUD_PROVIDER_CONFIGS)
    )

    def get_model_api_key(self, provider_name: str | None) -> str | None:
        if not provider_name:
            return None
        return self.model_api_keys.get(provider_name.lower()) or self.model_api_keys.get(provider_name)

    def get_cloud_provider_config(self, provider_name: str | None) -> dict[str, Any] | None:
        if not provider_name:
            return None

        return (
            self.cloud_provider_configs.get(provider_name.lower())
            or self.cloud_provider_configs.get(provider_name)
        )


ai_settings = AISettings()
