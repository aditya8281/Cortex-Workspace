import time
import asyncio
import logging
from datetime import datetime
from typing import List, Dict, Any, Tuple, Optional

from backend.app.db.session import SessionLocal
from backend.app.models.llm_model import (
    CortexProvider, CortexModel, CortexRoutingProfile, CortexTaskRoute,
    CortexModelMetric, CortexModelEvent,
)
from backend.app.ai.task_classifier import TaskClassifier
from backend.app.ai.model_registry import retrieve_key_securely
from backend.app.ai.local_llm import LocalLLM
from backend.app.ai.api_llm import APILLM
from backend.app.ai.providers.registry import ProviderRegistry
from backend.app.ai.providers.http_clients import (
    build_provider_llm,
    normalize_provider_name,
    provider_default_base_url,
)

logger = logging.getLogger(__name__)

class IntelligentRouter:
    """
    Intelligent Model Router that implements:
    1. Query Classification (using TaskClassifier)
    2. Dynamic profile-based model routing (Balanced, Coding Heavy, Local Only, etc.)
    3. Auto Mode (Cortex decides best model for task)
    4. Fallback/Failover handling (resilient automatic failover to fallback models)
    5. Observability metrics tracing
    """

    def __init__(self):
        self.fallback_llm = ProviderRegistry.get_provider()

    async def route_and_generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        history: Optional[List[Dict[str, str]]] = None,
        inference_engine: Optional[str] = None,
        api_key: Optional[str] = None,
        api_base_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Classifies task, routes request, applies fallback rules, and executes LLM generation.
        Returns a dict containing:
          - "response": str (generated text)
          - "routing_info": dict (observability data)
        """
        db = SessionLocal()
        
        # 1. Classify Task
        task_type, classification_reason = TaskClassifier.classify(prompt, history)
        logger.info(f"IntelligentRouter classified query as '{task_type}' (Reason: {classification_reason})")

        # 2. Determine Primary and Fallback model names based on config
        primary_name = model
        fallback_name = None
        routing_reason = ""
        is_auto_mode = (not model or model.lower() == "auto")

        active_profile_name = "Balanced"

        try:
            if is_auto_mode:
                # Retrieve active profile
                active_profile = db.query(CortexRoutingProfile).filter(CortexRoutingProfile.is_active.is_(True)).first()
                if active_profile:
                    active_profile_name = active_profile.name
                
                # Fetch route configuration for task
                route = db.query(CortexTaskRoute).filter(
                    CortexTaskRoute.profile_name == active_profile_name,
                    CortexTaskRoute.task_type == task_type
                ).first()
                
                if route:
                    primary_name = route.primary_model
                    fallback_name = route.fallback_model
                    routing_reason = f"Auto Mode ({active_profile_name} Profile): {TaskClassifier.CATEGORIES.get(task_type, task_type)} task detected. Reason: {classification_reason}."
                else:
                    primary_name = "gpt-4o-mini"
                    fallback_name = "gemini-1.5-flash"
                    routing_reason = "Auto Mode: Fallback defaults applied."
            else:
                routing_reason = f"Manual override: Model '{model}' selected by user."
        except Exception as e:
            logger.error(f"Failed to fetch routing configuration: {e}")
            primary_name = model or "gpt-4o-mini"
            routing_reason = f"Fallback due to database error: {e}"
        finally:
            db.close()

        # 3. Resolve and Run Inference (with fallback logic)
        start_time = time.time()
        fallback_used = False
        fallback_error_msg = ""
        resolved_model_used = ""
        resolved_provider = ""

        # First attempt: Try primary model
        try:
            llm_inst, resolved_model_used, resolved_provider = self._resolve_model(
                db_model_name=primary_name or "gpt-4o-mini",
                inference_engine=inference_engine,
                api_key=api_key,
                api_base_url=api_base_url
            )
            
            logger.info(f"Executing prompt on primary model '{resolved_model_used}' ({resolved_provider})")
            response = await llm_inst.generate(
                prompt,
                system_prompt,
                model=resolved_model_used
            )
        except Exception as primary_error:
            logger.warning(f"Primary model '{primary_name}' failed or is not configured: {primary_error}")
            
            # Switch to fallback model
            fallback_used = True
            fallback_error_msg = str(primary_error)
            
            # If no fallback model configured in route, pick a sensible default
            fallback_target = fallback_name or "gpt-4o-mini"
            if fallback_target == primary_name:
                fallback_target = "gpt-4o-mini" if primary_name != "gpt-4o-mini" else "gemini-1.5-flash"

            try:
                llm_inst, resolved_model_used, resolved_provider = self._resolve_model(
                    db_model_name=fallback_target,
                    inference_engine=inference_engine,
                    api_key=api_key,
                    api_base_url=api_base_url
                )
                
                logger.info(f"Executing prompt on fallback model '{resolved_model_used}' ({resolved_provider})")
                response = await llm_inst.generate(
                    prompt,
                    system_prompt,
                    model=resolved_model_used
                )
                
                # Append fallback indicator to the response to notify the user
                fallback_alert_prefix = f"⚠️ [Notice: Primary model ({primary_name}) failed. Automatically fell back to {resolved_model_used} ({resolved_provider})]\n\n"
                response = fallback_alert_prefix + response
                
            except Exception as fallback_error:
                logger.error(f"Fallback model '{fallback_target}' also failed: {fallback_error}")
                # Ultimate default fallback
                resolved_model_used = "Default Fallback"
                resolved_provider = "System"
                response = await self.fallback_llm.generate(
                    prompt,
                    system_prompt,
                    model=model
                )
                response = "⚠️ [Notice: Both primary and fallback models failed. Using system default provider]\n\n" + response

        response_time = time.time() - start_time
        latency_ms = response_time * 1000
        success = not fallback_used or resolved_model_used != "Default Fallback"

        # Compile Routing Information
        routing_info = {
            "model_used": resolved_model_used,
            "provider": resolved_provider,
            "response_time": response_time,
            "selection_reason": routing_reason,
            "fallback_used": fallback_used,
            "fallback_reason": fallback_error_msg if fallback_used else None,
            "classified_task": task_type
        }

        # Fire-and-forget metric recording (non-blocking)
        asyncio.ensure_future(
            self._record_event(
                model_name=resolved_model_used,
                provider_name=resolved_provider,
                task_type=task_type,
                latency_ms=latency_ms,
                success=success,
                fallback_used=fallback_used,
                routed_by="auto" if is_auto_mode else "manual",
            )
        )

        return {
            "response": response,
            "routing_info": routing_info
        }

    def _resolve_model(
        self,
        db_model_name: str,
        inference_engine: Optional[str] = None,
        api_key: Optional[str] = None,
        api_base_url: Optional[str] = None
    ) -> Tuple[Any, str, str]:
        """
        Resolves model name to an executable LLM class instance (LocalLLM or APILLM)
        and returns (llm_instance, model_name, provider_name).
        """
        db = SessionLocal()
        try:
            # 1. Resolve from database
            db_model = db.query(CortexModel).filter(CortexModel.name == db_model_name).first()
            if db_model:
                if db_model.is_local:
                    if db_model.provider_name.lower() in ("lm studio", "lm-studio"):
                        return APILLM(
                            api_key="lm-studio",
                            base_url="http://localhost:1234/v1",
                            model=db_model_name
                        ), db_model_name, "LM Studio"
                    else:
                        return LocalLLM(model=db_model_name), db_model_name, "Ollama"
                else:
                    provider = db.query(CortexProvider).filter(CortexProvider.name == db_model.provider_name).first()
                    if provider:
                        if not provider.is_enabled:
                            raise ValueError(f"Provider {provider.name} is disabled. Enable it in Models settings.")
                        
                        key = api_key or retrieve_key_securely(provider.name, provider.api_key_encrypted)
                        base_url = api_base_url or provider.base_url or provider_default_base_url(provider.name)
                        
                        if not key:
                            raise ValueError(f"API Key is missing for provider {provider.name}")
                        if not base_url:
                            raise ValueError(f"Base URL is missing for provider {provider.name}")
                            
                        return build_provider_llm(
                            provider.name,
                            api_key=key,
                            base_url=base_url,
                            model=db_model_name,
                        ), db_model_name, provider.name
            
            # 2. Check fallback mapping if model name contains prefix (e.g. "openai/gpt-4o")
            if "/" in db_model_name:
                parts = db_model_name.split("/", 1)
                prov_name = parts[0]
                mod_name = parts[1]
                provider = db.query(CortexProvider).filter(CortexProvider.name.ilike(normalize_provider_name(prov_name))).first()
                if provider and provider.is_enabled:
                    key = api_key or retrieve_key_securely(provider.name, provider.api_key_encrypted)
                    base_url = api_base_url or provider.base_url or provider_default_base_url(provider.name)
                    if key and base_url:
                        return build_provider_llm(
                            provider.name,
                            api_key=key,
                            base_url=base_url,
                            model=mod_name,
                        ), mod_name, provider.name
            
            # 3. Check for any enabled provider matches or fall back to manual config
            if inference_engine:
                engine_lower = inference_engine.lower()
                if "ollama" in engine_lower:
                    return LocalLLM(model=db_model_name), db_model_name, "Ollama"
                elif "api" in engine_lower or "openai" in engine_lower:
                    from backend.app.ai.config import ai_settings
                    _raw_key = api_key or ai_settings.api_key
                    _raw_url = api_base_url or ai_settings.api_url
                    if not _raw_key or not _raw_url:
                        raise ValueError("Credentials missing for manual API configuration")
                    return build_provider_llm(
                        "OpenAI",
                        api_key=str(_raw_key),
                        base_url=str(_raw_url),
                        model=db_model_name,
                    ), db_model_name, "External API"

            # If model name matches one of our default local models, try local routing
            if db_model_name in ("llama3", "mistral", "qwen2.5-coder"):
                return LocalLLM(model=db_model_name), db_model_name, "Ollama"

            raise ValueError(f"Model '{db_model_name}' could not be resolved or its provider is disabled.")
            
        finally:
            db.close()

    async def _record_event(
        self,
        model_name: str,
        provider_name: str,
        task_type: str,
        latency_ms: float,
        success: bool,
        fallback_used: bool,
        routed_by: str,
    ) -> None:
        """Write inference event and upsert aggregate metrics (fire-and-forget)."""
        if not model_name or model_name in ("Default Fallback", ""):
            return
        try:
            db = SessionLocal()
            try:
                # Append event row
                event = CortexModelEvent(
                    model_name=model_name,
                    provider_name=provider_name,
                    task_type=task_type,
                    latency_ms=latency_ms,
                    success=success,
                    fallback_used=fallback_used,
                    routed_by=routed_by,
                )
                db.add(event)

                # Upsert aggregate metric
                metric = db.query(CortexModelMetric).filter(
                    CortexModelMetric.model_name == model_name
                ).first()

                if metric is None:
                    metric = CortexModelMetric(
                        model_name=model_name,
                        provider_name=provider_name,
                        total_requests=0,
                        success_count=0,
                        failure_count=0,
                        avg_latency_ms=0.0,
                    )
                    db.add(metric)

                # Rolling average: (old_avg * old_count + new_value) / new_count
                new_total = metric.total_requests + 1
                metric.avg_latency_ms = (
                    (metric.avg_latency_ms * metric.total_requests + latency_ms) / new_total
                )
                metric.total_requests = new_total
                if success:
                    metric.success_count += 1
                else:
                    metric.failure_count += 1
                metric.last_used_at = datetime.utcnow()
                metric.provider_name = provider_name  # keep current

                db.commit()
            finally:
                db.close()
        except Exception as exc:
            logger.warning(f"Failed to record model event: {exc}")
