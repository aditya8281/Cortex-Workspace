from pydantic import BaseModel

from backend.app.core.config import settings


class AISettings(BaseModel):

    mode: str = settings.AI_MODE

    api_key: str | None = settings.AI_API_KEY

    api_url: str | None = settings.AI_API_URL

    model: str = settings.AI_MODEL

    local_model: str = settings.LOCAL_MODEL


ai_settings = AISettings()