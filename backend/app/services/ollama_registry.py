"""Ollama model registry service - manages discovery, search, and installation"""

import json
import logging
import re
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, func
import httpx

from backend.app.models.ollama_registry import OllamaRegistryModel, OllamaDownloadProgress
from backend.app.services.ollama_scraper import OllamaLibraryScraper, FALLBACK_MODELS

logger = logging.getLogger(__name__)


# Default context lengths for common model families
FAMILY_CONTEXT_DEFAULTS = {
    "llama": 4096,
    "mistral": 32768,
    "neural-chat": 8192,
    "codellama": 16384,
    "dolphin-mixtral": 32768,
    "vicuna": 4096,
    "wizardlm": 4096,
    "openhermes": 4096,
    "neural-chat": 8192,
}


def extract_context_length(description: str, family: str) -> int:
    """
    Extract context length from model description or use family default.
    
    Looks for patterns like "4k", "8k", "32k", "context: 4096", etc.
    Falls back to family defaults, then 4096 as final default.
    
    Args:
        description: Model description text
        family: Model family name
    
    Returns:
        Context length in tokens
    """
    if not description:
        return FAMILY_CONTEXT_DEFAULTS.get(family.lower(), 4096)
    
    # Try to find context/window patterns
    description_lower = description.lower()
    
    # Pattern: "4k context", "32k window", etc.
    match = re.search(r'(\d+)([km])\s*(?:context|window|tokens?)', description_lower)
    if match:
        num = int(match.group(1))
        unit = match.group(2)
        if unit == 'k':
            return num * 1024
        elif unit == 'm':
            return num * 1024 * 1024
    
    # Pattern: "context: 4096", "4096 tokens", etc.
    match = re.search(r'(?:context|tokens?)[:\s]+(\d+)', description_lower)
    if match:
        return int(match.group(1))
    
    # Pattern: "4096" standalone (last resort)
    matches = re.findall(r'\b(\d{4,})\b', description)
    if matches:
        return int(matches[0])
    
    # Use family default
    return FAMILY_CONTEXT_DEFAULTS.get(family.lower(), 4096)


class OllamaRegistryService:
    """Core service for Ollama model discovery and management"""
    
    CACHE_DURATION = timedelta(hours=24)
    
    @staticmethod
    async def sync_registry(db: Session, force_refresh: bool = False) -> int:
        """
        Sync Ollama library models with local registry.
        Scrapes ollama.com/library and updates database.
        
        Args:
            db: Database session
            force_refresh: If True, ignore cache and re-scrape
            
        Returns:
            Number of models synced
        """
        # Check if we need to refresh
        if not force_refresh:
            last_sync = db.query(func.max(OllamaRegistryModel.last_synced_at)).scalar()
            if last_sync and (datetime.utcnow() - last_sync) < OllamaRegistryService.CACHE_DURATION:
                logger.info("Registry cache is fresh, skipping sync")
                return db.query(OllamaRegistryModel).count()
        
        logger.info("Syncing Ollama registry...")
        
        # Try to scrape, fallback to hardcoded models if scraping fails
        models_data = await OllamaLibraryScraper.scrape_library()
        
        if not models_data:
            logger.warning("Scraping failed, using fallback models")
            models_data = FALLBACK_MODELS
        
        # Update/insert models in database
        synced_count = 0
        for model_data in models_data:
            try:
                # Check if model exists
                existing = db.query(OllamaRegistryModel).filter(
                    OllamaRegistryModel.model_id == model_data["model_id"]
                ).first()
                
                if existing:
                    # Update existing model
                    existing.family = model_data["family"]
                    existing.display_name = model_data["display_name"]
                    existing.description = model_data["description"]
                    existing.tags = json.dumps(model_data.get("tags", []))
                    existing.capabilities = json.dumps(model_data.get("capabilities", []))
                    existing.parameters = model_data.get("parameters")
                    existing.quantization = model_data.get("quantization", "unknown")
                    existing.source_url = model_data["source_url"]
                    existing.pull_command = model_data["pull_command"]
                    existing.last_synced_at = datetime.utcnow()
                else:
                    # Create new model
                    model = OllamaRegistryModel(
                        model_id=model_data["model_id"],
                        family=model_data["family"],
                        display_name=model_data["display_name"],
                        description=model_data.get("description", ""),
                        tags=json.dumps(model_data.get("tags", [])),
                        capabilities=json.dumps(model_data.get("capabilities", [])),
                        parameters=model_data.get("parameters"),
                        context_length=extract_context_length(
                            model_data.get("description", ""),
                            model_data.get("family", "")
                        ),
                        quantization=model_data.get("quantization", "unknown"),
                        source_url=model_data["source_url"],
                        pull_command=model_data["pull_command"],
                        last_synced_at=datetime.utcnow(),
                    )
                    db.add(model)
                
                synced_count += 1
                
            except Exception as e:
                logger.error(f"Error syncing model {model_data.get('model_id')}: {e}")
                continue
        
        db.commit()
        logger.info(f"Registry sync complete: {synced_count} models")
        return synced_count
    
    @staticmethod
    def list_all_models(db: Session) -> list[dict]:
        """Get all models in registry with full metadata"""
        models = db.query(OllamaRegistryModel).all()
        
        return [
            OllamaRegistryService._model_to_dict(model)
            for model in models
        ]
    
    @staticmethod
    def get_model(db: Session, model_id: str) -> Optional[dict]:
        """Get single model by ID"""
        model = db.query(OllamaRegistryModel).filter(
            OllamaRegistryModel.model_id == model_id
        ).first()
        
        if not model:
            return None
        
        return OllamaRegistryService._model_to_dict(model)
    
    @staticmethod
    def search_models(
        db: Session,
        query: str,
        capability: Optional[str] = None,
        family: Optional[str] = None,
        size: Optional[str] = None,  # "small", "medium", "large"
        limit: int = 20,
    ) -> list[dict]:
        """
        Search models with multiple filters.
        
        Args:
            db: Database session
            query: Search text (model name, description, capability)
            capability: Filter by capability (chat, vision, coding, embedding, etc)
            family: Filter by model family
            size: Filter by model size ("small" for <10B, "medium" for 10-50B, "large" for >50B)
            limit: Max results to return
            
        Returns:
            List of matching models sorted by relevance
        """
        q = db.query(OllamaRegistryModel)
        
        # Apply family filter
        if family:
            q = q.filter(OllamaRegistryModel.family.ilike(f"%{family}%"))
        
        # Apply text search on model_id, display_name, description
        if query:
            query_lower = query.lower()
            q = q.filter(
                (OllamaRegistryModel.model_id.ilike(f"%{query}%")) |
                (OllamaRegistryModel.display_name.ilike(f"%{query}%")) |
                (OllamaRegistryModel.description.ilike(f"%{query}%"))
            )
        
        models = q.all()
        
        # Filter by capability
        if capability:
            capability_lower = capability.lower()
            models = [
                m for m in models
                if capability_lower in (json.loads(m.capabilities or "[]"))
            ]
        
        # Filter by size
        if size:
            models = OllamaRegistryService._filter_by_size(models, size)
        
        # Convert to dicts and sort by relevance
        model_dicts = [OllamaRegistryService._model_to_dict(m) for m in models]
        
        # Simple relevance scoring
        model_dicts = OllamaRegistryService._rank_by_relevance(model_dicts, query)
        
        return model_dicts[:limit]
    
    @staticmethod
    def list_by_capability(
        db: Session,
        capability: str,
        limit: int = 20,
    ) -> list[dict]:
        """Get models with specific capability"""
        all_models = db.query(OllamaRegistryModel).all()
        
        matching = []
        for model in all_models:
            caps = json.loads(model.capabilities or "[]")
            if capability.lower() in [c.lower() for c in caps]:
                matching.append(OllamaRegistryService._model_to_dict(model))
        
        return matching[:limit]
    
    @staticmethod
    def list_installed_models(db: Session) -> list[dict]:
        """Get only models marked as installed"""
        models = db.query(OllamaRegistryModel).filter(
            OllamaRegistryModel.is_installed == True
        ).all()
        
        return [
            OllamaRegistryService._model_to_dict(model)
            for model in models
        ]
    
    @staticmethod
    def mark_installed(db: Session, model_id: str) -> bool:
        """Mark a model as installed after successful download"""
        model = db.query(OllamaRegistryModel).filter(
            OllamaRegistryModel.model_id == model_id
        ).first()
        
        if not model:
            return False
        
        model.is_installed = True
        model.last_installed_at = datetime.utcnow()
        db.commit()
        return True
    
    @staticmethod
    def _model_to_dict(model: OllamaRegistryModel) -> dict:
        """Convert ORM model to dictionary"""
        return {
            "model_id": model.model_id,
            "family": model.family,
            "display_name": model.display_name,
            "description": model.description,
            "tags": json.loads(model.tags or "[]"),
            "capabilities": json.loads(model.capabilities or "[]"),
            "parameters": model.parameters,
            "context_length": model.context_length,
            "quantization": model.quantization,
            "source_url": model.source_url,
            "pull_command": model.pull_command,
            "is_installed": model.is_installed,
            "last_synced_at": model.last_synced_at.isoformat() if model.last_synced_at else None,
        }
    
    @staticmethod
    def _filter_by_size(models: list[OllamaRegistryModel], size: str) -> list[OllamaRegistryModel]:
        """Filter models by parameter size"""
        def get_params_as_b(model) -> float:
            """Convert parameter string to billions"""
            if not model.parameters:
                return 0
            
            param_str = str(model.parameters).upper()
            if 'B' in param_str:
                try:
                    return float(param_str.replace('B', ''))
                except:
                    return 0
            return 0
        
        if size.lower() == "small":
            return [m for m in models if get_params_as_b(m) < 10]
        elif size.lower() == "medium":
            return [m for m in models if 10 <= get_params_as_b(m) <= 50]
        elif size.lower() == "large":
            return [m for m in models if get_params_as_b(m) > 50]
        
        return models
    
    @staticmethod
    def _rank_by_relevance(models: list[dict], query: str) -> list[dict]:
        """Simple relevance ranking for search results"""
        if not query:
            return models
        
        query_lower = query.lower()
        
        def relevance_score(model) -> tuple:
            """Return tuple for sorting (higher is better)"""
            model_id = model["model_id"].lower()
            display = model["display_name"].lower()
            desc = model["description"].lower() if model["description"] else ""
            
            score = 0
            
            # Exact model_id match is most relevant
            if model_id == query_lower:
                score += 1000
            # Start with model_id
            elif model_id.startswith(query_lower):
                score += 500
            # Contains in model_id
            elif query_lower in model_id:
                score += 300
            
            # Then display name
            if display.startswith(query_lower):
                score += 200
            elif query_lower in display:
                score += 100
            
            # Then description
            if query_lower in desc:
                score += 50
            
            # Prefer installed models
            if model["is_installed"]:
                score += 10
            
            return (-score,)  # Negative for descending sort
        
        return sorted(models, key=relevance_score)


class OllamaDownloadService:
    """Manages model downloads with progress tracking"""
    
    @staticmethod
    async def start_download(db: Session, model_id: str) -> Optional[int]:
        """
        Start a model download.
        
        Args:
            db: Database session
            model_id: Model to download
            
        Returns:
            Download progress ID or None if model not found
        """
        # Verify model exists in registry
        model = db.query(OllamaRegistryModel).filter(
            OllamaRegistryModel.model_id == model_id
        ).first()
        
        if not model:
            return None
        
        # Create progress record
        progress = OllamaDownloadProgress(
            model_id=model_id,
            status="queued",
        )
        db.add(progress)
        db.commit()
        
        return progress.id
    
    @staticmethod
    async def get_download_progress(db: Session, progress_id: int) -> Optional[dict]:
        """Get current download progress"""
        progress = db.query(OllamaDownloadProgress).filter(
            OllamaDownloadProgress.id == progress_id
        ).first()
        
        if not progress:
            return None
        
        return {
            "id": progress.id,
            "model_id": progress.model_id,
            "status": progress.status,
            "progress_percent": progress.progress_percent,
            "bytes_downloaded": progress.bytes_downloaded,
            "total_bytes": progress.total_bytes,
            "error_message": progress.error_message,
            "started_at": progress.started_at.isoformat(),
            "completed_at": progress.completed_at.isoformat() if progress.completed_at else None,
        }
    
    @staticmethod
    async def execute_download(db: Session, model_id: str, progress_id: int):
        """
        Execute ollama pull command and stream progress.
        This would be called by a background task.
        """
        import asyncio
        import subprocess
        
        progress = db.query(OllamaDownloadProgress).filter(
            OllamaDownloadProgress.id == progress_id
        ).first()
        
        if not progress:
            return
        
        try:
            progress.status = "downloading"
            db.commit()
            
            # Execute ollama pull
            process = await asyncio.create_subprocess_exec(
                "ollama", "pull", model_id,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                progress.status = "complete"
                progress.progress_percent = 100.0
                progress.completed_at = datetime.utcnow()
                
                # Mark model as installed
                model = db.query(OllamaRegistryModel).filter(
                    OllamaRegistryModel.model_id == model_id
                ).first()
                if model:
                    model.is_installed = True
                    model.last_installed_at = datetime.utcnow()
            else:
                progress.status = "failed"
                progress.error_message = stderr.decode() if stderr else "Download failed"
            
        except Exception as e:
            progress.status = "failed"
            progress.error_message = str(e)
            logger.error(f"Error downloading model {model_id}: {e}")
        
        finally:
            db.commit()
