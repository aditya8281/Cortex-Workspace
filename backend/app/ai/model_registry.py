import httpx
import hashlib
import base64
import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
import keyring
from cryptography.fernet import Fernet

from backend.app.core.config import settings
from backend.app.models.llm_model import CortexProvider, CortexModel, CortexRoutingProfile, CortexTaskRoute

logger = logging.getLogger(__name__)

def get_fernet() -> Fernet:
    key_hash = hashlib.sha256(settings.SECRET_KEY.encode()).digest()
    fernet_key = base64.urlsafe_b64encode(key_hash)
    return Fernet(fernet_key)

def store_key_securely(provider_name: str, key_val: str) -> Optional[bytes]:
    if not key_val:
        try:
            keyring.delete_password("cortex-workspace", provider_name)
        except Exception:
            pass
        return None
    try:
        keyring.set_password("cortex-workspace", provider_name, key_val)
        return None
    except Exception as e:
        logger.warning(f"Keyring failed to save key for {provider_name}, falling back to encryption: {e}")
        f = get_fernet()
        return f.encrypt(key_val.encode())

def retrieve_key_securely(provider_name: str, encrypted_bytes: Optional[bytes]) -> str:
    try:
        val = keyring.get_password("cortex-workspace", provider_name)
        if val:
            return val
    except Exception:
        pass
    if not encrypted_bytes:
        return ""
    try:
        f = get_fernet()
        return f.decrypt(encrypted_bytes).decode()
    except Exception:
        return ""


class ModelRegistry:
    @classmethod
    def seed_if_empty(cls, db: Session):
        if db.query(CortexProvider).first() is None:
            default_providers = [
                {"name": "OpenAI", "base_url": "https://api.openai.com/v1", "is_custom": False},
                {"name": "Anthropic", "base_url": "https://api.anthropic.com/v1", "is_custom": False},
                {"name": "Google", "base_url": "https://generativelanguage.googleapis.com/v1beta", "is_custom": False},
                {"name": "OpenRouter", "base_url": "https://openrouter.ai/api/v1", "is_custom": False},
                {"name": "Groq", "base_url": "https://api.groq.com/openai/v1", "is_custom": False},
                {"name": "Together", "base_url": "https://api.together.xyz/v1", "is_custom": False},
                {"name": "DeepSeek", "base_url": "https://api.deepseek.com/v1", "is_custom": False},
            ]
            for p in default_providers:
                provider = CortexProvider(
                    name=p["name"],
                    base_url=p["base_url"],
                    is_enabled=False,
                    is_custom=p["is_custom"]
                )
                db.add(provider)
            db.commit()

            default_models = [
                # OpenAI
                {"name": "gpt-4o-mini", "provider_name": "OpenAI", "context_length": 128000, "parameters": "8B", "quantization": "None", "vram_estimate": "N/A", "is_local": False},
                {"name": "gpt-4o", "provider_name": "OpenAI", "context_length": 128000, "parameters": "unknown", "quantization": "None", "vram_estimate": "N/A", "is_local": False},
                # Anthropic
                {"name": "claude-3-5-sonnet-latest", "provider_name": "Anthropic", "context_length": 200000, "parameters": "unknown", "quantization": "None", "vram_estimate": "N/A", "is_local": False},
                {"name": "claude-3-5-haiku-latest", "provider_name": "Anthropic", "context_length": 200000, "parameters": "unknown", "quantization": "None", "vram_estimate": "N/A", "is_local": False},
                # Google
                {"name": "gemini-1.5-flash", "provider_name": "Google", "context_length": 1048576, "parameters": "unknown", "quantization": "None", "vram_estimate": "N/A", "is_local": False},
                {"name": "gemini-1.5-pro", "provider_name": "Google", "context_length": 2097152, "parameters": "unknown", "quantization": "None", "vram_estimate": "N/A", "is_local": False},
                # Groq
                {"name": "llama3-70b-8192", "provider_name": "Groq", "context_length": 8192, "parameters": "70B", "quantization": "None", "vram_estimate": "N/A", "is_local": False},
                {"name": "mixtral-8x7b-32768", "provider_name": "Groq", "context_length": 32768, "parameters": "45B", "quantization": "None", "vram_estimate": "N/A", "is_local": False},
                # DeepSeek
                {"name": "deepseek-chat", "provider_name": "DeepSeek", "context_length": 64000, "parameters": "unknown", "quantization": "None", "vram_estimate": "N/A", "is_local": False},
                {"name": "deepseek-coder", "provider_name": "DeepSeek", "context_length": 64000, "parameters": "unknown", "quantization": "None", "vram_estimate": "N/A", "is_local": False},
            ]
            for m in default_models:
                model = CortexModel(
                    name=m["name"],
                    provider_name=m["provider_name"],
                    context_length=m["context_length"],
                    parameters=m["parameters"],
                    quantization=m["quantization"],
                    vram_estimate=m["vram_estimate"],
                    status="active",
                    is_local=m["is_local"]
                )
                db.add(model)
            db.commit()

        # Seed routing profiles and default task routes if empty
        if db.query(CortexRoutingProfile).first() is None:
            # Create profiles
            profiles = [
                {"name": "Balanced", "is_active": True},
                {"name": "Coding Heavy", "is_active": False},
                {"name": "Local Only", "is_active": False},
                {"name": "Maximum Quality", "is_active": False},
                {"name": "Custom", "is_active": False}
            ]
            for p_data in profiles:
                p_obj = CortexRoutingProfile(name=p_data["name"], is_active=p_data["is_active"])
                db.add(p_obj)
            db.commit()

            # Create default mappings per profile
            default_routes = {
                "Balanced": {
                    "chat": ("gpt-4o-mini", "gemini-1.5-flash"),
                    "search": ("gpt-4o-mini", "gemini-1.5-flash"),
                    "coding": ("gpt-4o-mini", "deepseek-coder"),
                    "repository_analysis": ("gpt-4o", "claude-3-5-sonnet-latest"),
                    "architecture_review": ("gpt-4o", "claude-3-5-sonnet-latest"),
                    "planning": ("gpt-4o", "claude-3-5-sonnet-latest"),
                    "research": ("gpt-4o-mini", "gemini-1.5-flash"),
                    "debugging": ("gpt-4o", "deepseek-coder"),
                    "multi_file_modification": ("gpt-4o", "claude-3-5-sonnet-latest"),
                    "long_context": ("gemini-1.5-flash", "gpt-4o-mini"),
                },
                "Coding Heavy": {
                    "chat": ("gpt-4o-mini", "deepseek-chat"),
                    "search": ("gpt-4o-mini", "gemini-1.5-flash"),
                    "coding": ("claude-3-5-sonnet-latest", "deepseek-coder"),
                    "repository_analysis": ("claude-3-5-sonnet-latest", "deepseek-coder"),
                    "architecture_review": ("claude-3-5-sonnet-latest", "gpt-4o"),
                    "planning": ("claude-3-5-sonnet-latest", "gpt-4o"),
                    "research": ("gpt-4o-mini", "claude-3-5-haiku-latest"),
                    "debugging": ("claude-3-5-sonnet-latest", "deepseek-coder"),
                    "multi_file_modification": ("claude-3-5-sonnet-latest", "deepseek-coder"),
                    "long_context": ("claude-3-5-sonnet-latest", "gemini-1.5-pro"),
                },
                "Local Only": {
                    "chat": ("llama3", "mistral"),
                    "search": ("llama3", "mistral"),
                    "coding": ("qwen2.5-coder", "llama3"),
                    "repository_analysis": ("qwen2.5-coder", "llama3"),
                    "architecture_review": ("llama3", "mistral"),
                    "planning": ("llama3", "mistral"),
                    "research": ("llama3", "mistral"),
                    "debugging": ("qwen2.5-coder", "llama3"),
                    "multi_file_modification": ("qwen2.5-coder", "llama3"),
                    "long_context": ("llama3", "mistral"),
                },
                "Maximum Quality": {
                    "chat": ("gpt-4o", "claude-3-5-sonnet-latest"),
                    "search": ("gpt-4o", "gemini-1.5-pro"),
                    "coding": ("claude-3-5-sonnet-latest", "gpt-4o"),
                    "repository_analysis": ("claude-3-5-sonnet-latest", "gemini-1.5-pro"),
                    "architecture_review": ("claude-3-5-sonnet-latest", "gpt-4o"),
                    "planning": ("claude-3-5-sonnet-latest", "gpt-4o"),
                    "research": ("gpt-4o", "claude-3-5-sonnet-latest"),
                    "debugging": ("claude-3-5-sonnet-latest", "gpt-4o"),
                    "multi_file_modification": ("claude-3-5-sonnet-latest", "gpt-4o"),
                    "long_context": ("gemini-1.5-pro", "claude-3-5-sonnet-latest"),
                },
                "Custom": {
                    "chat": ("gpt-4o-mini", "gemini-1.5-flash"),
                    "search": ("gpt-4o-mini", "gemini-1.5-flash"),
                    "coding": ("gpt-4o-mini", "deepseek-coder"),
                    "repository_analysis": ("gpt-4o", "claude-3-5-sonnet-latest"),
                    "architecture_review": ("gpt-4o", "claude-3-5-sonnet-latest"),
                    "planning": ("gpt-4o", "claude-3-5-sonnet-latest"),
                    "research": ("gpt-4o-mini", "gemini-1.5-flash"),
                    "debugging": ("gpt-4o", "deepseek-coder"),
                    "multi_file_modification": ("gpt-4o", "claude-3-5-sonnet-latest"),
                    "long_context": ("gemini-1.5-flash", "gpt-4o-mini"),
                }
            }

            for p_name, routes in default_routes.items():
                for t_type, (prim, fallb) in routes.items():
                    route_obj = CortexTaskRoute(
                        profile_name=p_name,
                        task_type=t_type,
                        primary_model=prim,
                        fallback_model=fallb
                    )
                    db.add(route_obj)
            db.commit()

    @classmethod
    async def get_local_models(cls) -> List[Dict[str, Any]]:
        models = []

        # 1. Ollama
        ollama_url = f"{settings.OLLAMA_URL.rstrip('/')}/api/tags"
        try:
            async with httpx.AsyncClient(timeout=3) as client:
                resp = await client.get(ollama_url)
                if resp.status_code == 200:
                    data = resp.json()
                    for m in data.get("models", []):
                        name = m.get("name")
                        details = m.get("details", {})
                        param_size = details.get("parameter_size", "unknown")
                        quant = details.get("quantization_level", "unknown")
                        
                        # VRAM Estimation
                        vram = "unknown"
                        if "B" in param_size:
                            try:
                                size_val = float(param_size.replace("B", ""))
                                vram = f"{round(size_val * 0.7, 1)} GB"
                            except Exception:
                                pass

                        # Context Length Estimation
                        context_len = 8192
                        if "qwen" in name.lower():
                            context_len = 32768
                        elif "llama3" in name.lower():
                            context_len = 8192
                        elif "phi" in name.lower():
                            context_len = 128000

                        models.append({
                            "name": name,
                            "provider": "Ollama",
                            "context_length": context_len,
                            "parameters": param_size,
                            "quantization": quant,
                            "vram_estimate": vram,
                            "status": "active",
                            "is_local": True
                        })
        except Exception:
            pass

        # 2. LM Studio
        lm_url = "http://localhost:1234/v1/models"
        try:
            async with httpx.AsyncClient(timeout=3) as client:
                resp = await client.get(lm_url)
                if resp.status_code == 200:
                    data = resp.json()
                    for m in data.get("data", []):
                        name = m.get("id")
                        models.append({
                            "name": name,
                            "provider": "LM Studio",
                            "context_length": 4096,
                            "parameters": "unknown",
                            "quantization": "unknown",
                            "vram_estimate": "unknown",
                            "status": "active",
                            "is_local": True
                        })
        except Exception:
            pass

        return models

    @classmethod
    async def list_models(cls, db: Session) -> List[Dict[str, Any]]:
        cls.seed_if_empty(db)

        # Get local models dynamically
        local_models = await cls.get_local_models()
        
        # Get active cloud models from DB
        cloud_models = []
        providers = db.query(CortexProvider).filter(CortexProvider.is_enabled.is_(True)).all()
        active_provider_names = {p.name for p in providers}
        
        db_models = db.query(CortexModel).all()
        for m in db_models:
            if not m.is_local:
                is_active = m.provider_name in active_provider_names
                cloud_models.append({
                    "id": m.id,
                    "name": m.name,
                    "provider": m.provider_name,
                    "context_length": m.context_length,
                    "parameters": m.parameters,
                    "quantization": m.quantization,
                    "vram_estimate": m.vram_estimate,
                    "status": "active" if is_active else "unavailable",
                    "is_local": False
                })

        return local_models + cloud_models

    @classmethod
    async def validate_provider(cls, name: str, base_url: str, api_key: str) -> Dict[str, Any]:
        """
        Validate provider endpoint, API key, model list, and run a completion.
        """
        try:
            # 1. Endpoint & API key check: try to fetch models list
            url = base_url
            if not url:
                return {"valid": False, "error": "Base URL is required"}

            models_url = url
            if not models_url.endswith(("/models", "/v1/models")):
                models_url = f"{models_url.rstrip('/')}/models"
                if "/v1" not in models_url and "api.openai.com" in models_url:
                    models_url = f"{base_url.rstrip('/')}/v1/models"

            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }

            models = []
            async with httpx.AsyncClient(timeout=10) as client:
                # Retrieve models list
                resp = await client.get(models_url, headers=headers)
                if resp.status_code != 200:
                    # Let's try alternate OpenAI endpoint mapping
                    if "api.openai.com" in models_url:
                        alt_url = "https://api.openai.com/v1/models"
                        resp = await client.get(alt_url, headers=headers)

                if resp.status_code == 200:
                    data = resp.json()
                    # Some endpoints return list of models
                    if isinstance(data, dict):
                        for m in data.get("data", []):
                            if isinstance(m, dict) and "id" in m:
                                models.append(m["id"])
                else:
                    return {"valid": False, "error": f"Failed to connect: Status code {resp.status_code}. Response: {resp.text[:200]}"}

            # 2. Run lightweight test completion
            chat_url = url
            if not chat_url.endswith(("/chat/completions", "/generate")):
                chat_url = f"{chat_url.rstrip('/')}/chat/completions"
                if "/v1" not in chat_url and "api.openai.com" in chat_url:
                    chat_url = f"{base_url.rstrip('/')}/v1/chat/completions"

            # Select a default model for verification
            test_model = "gpt-4o-mini"
            if models:
                # Find a model matching common patterns or use the first one
                test_model = models[0]
                for m in models:
                    if "mini" in m.lower() or "flash" in m.lower() or "haiku" in m.lower():
                        test_model = m
                        break

            payload = {
                "model": test_model,
                "messages": [
                    {"role": "user", "content": "ping"}
                ],
                "max_tokens": 5
            }

            async with httpx.AsyncClient(timeout=15) as client:
                comp_resp = await client.post(chat_url, json=payload, headers=headers)
                if comp_resp.status_code == 200:
                    comp_data = comp_resp.json()
                    answer = comp_data["choices"][0]["message"]["content"]
                    return {
                        "valid": True,
                        "models": models[:25], # limit list count
                        "test_response": answer,
                        "error": None
                    }
                else:
                    return {"valid": False, "error": f"API key accepted, but test completion failed with status {comp_resp.status_code}: {comp_resp.text[:200]}"}

        except Exception as e:
            return {"valid": False, "error": f"Validation exception: {str(e)}"}
