"""Ollama library scraper - fetches and parses model data from ollama.com/library"""

import logging
from datetime import timedelta
from typing import Optional
import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class OllamaLibraryScraper:
    """Scrapes Ollama official library and extracts model metadata"""
    
    BASE_URL = "https://ollama.com/library"
    CACHE_DURATION = timedelta(hours=24)
    
    # Capability mapping based on model families and descriptions
    CAPABILITY_MAP = {
        "llama": ["chat", "reasoning", "coding", "long-context"],
        "mistral": ["chat", "coding", "fast"],
        "neural-chat": ["chat"],
        "neural-embed": ["embedding"],
        "nomic-embed": ["embedding"],
        "all-minilm": ["embedding"],
        "dolphin": ["chat", "reasoning"],
        "deepseek-coder": ["coding", "reasoning"],
        "codeqwen": ["coding"],
        "qwen": ["chat", "coding"],
        "phi": ["chat", "reasoning", "fast"],
        "openchat": ["chat"],
        "starling": ["chat", "reasoning"],
        "vicuna": ["chat"],
        "wizard": ["chat", "reasoning"],
        "orca": ["chat", "reasoning"],
        "zephyr": ["chat", "reasoning"],
        "solar": ["chat", "reasoning"],
        "llava": ["vision", "chat"],
        "bakllava": ["vision", "chat"],
        "moondream": ["vision"],
        "yi": ["chat", "reasoning"],
        "embedding": ["embedding"],
    }
    
    PARAMETER_MAP = {
        "7b": "7B", "7B": "7B",
        "13b": "13B", "13B": "13B",
        "70b": "70B", "70B": "70B",
        "34b": "34B", "34B": "34B",
        "3b": "3B", "3B": "3B",
        "8b": "8B", "8B": "8B",
        "405b": "405B", "405B": "405B",
        "405b-instruct": "405B",
    }
    
    @staticmethod
    async def scrape_library() -> list[dict]:
        """
        Scrapes ollama.com/library and returns structured model data.
        
        Returns:
            List of model dictionaries with: model_id, family, display_name, 
            description, tags, capabilities, parameters, source_url, pull_command
        """
        models = []
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(OllamaLibraryScraper.BASE_URL)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Find all model cards (adjust selectors based on actual HTML structure)
                model_cards = soup.find_all('a', class_='model-card')
                
                if not model_cards:
                    # Fallback: look for any links that might be models
                    model_cards = soup.find_all('a', href=lambda x: x and '/library/' in x)
                
                for card in model_cards:
                    try:
                        model_data = OllamaLibraryScraper._parse_model_card(card)
                        if model_data:
                            models.append(model_data)
                    except Exception as e:
                        logger.warning(f"Failed to parse model card: {e}")
                        continue
                
                logger.info(f"Scraped {len(models)} models from Ollama library")
                return models
                
        except Exception as e:
            logger.error(f"Error scraping Ollama library: {e}")
            return []
    
    @staticmethod
    def _parse_model_card(card) -> Optional[dict]:
        """
        Parse a single model card element and extract metadata.
        
        Args:
            card: BeautifulSoup element representing a model card
            
        Returns:
            Dictionary with model metadata or None if parsing fails
        """
        try:
            # Extract model ID from href
            href = card.get('href', '')
            if '/library/' not in href:
                return None
            
            model_id = href.split('/library/')[-1].strip('/')
            if not model_id:
                return None
            
            # Extract display name and description
            title_elem = card.find('h3') or card.find('h2')
            display_name = title_elem.get_text(strip=True) if title_elem else model_id.title()
            
            desc_elem = card.find('p', class_='description') or card.find('p')
            description = desc_elem.get_text(strip=True) if desc_elem else ""
            
            # Extract tags if available
            tags_elem = card.find_all('span', class_='tag')
            tags = [tag.get_text(strip=True) for tag in tags_elem]
            
            # Determine family from model_id
            family = model_id.split(':')[0].split('-')[0].lower()
            
            # Extract or infer parameters
            parameters = OllamaLibraryScraper._extract_parameters(model_id, tags)
            
            # Infer capabilities
            capabilities = OllamaLibraryScraper._infer_capabilities(model_id, description, tags)
            
            # Infer quantization
            quantization = OllamaLibraryScraper._infer_quantization(model_id, tags)
            
            return {
                "model_id": model_id,
                "family": family,
                "display_name": display_name,
                "description": description,
                "tags": tags,
                "capabilities": capabilities,
                "parameters": parameters,
                "quantization": quantization,
                "source_url": f"https://ollama.com/library/{model_id}",
                "pull_command": f"ollama pull {model_id}",
            }
            
        except Exception as e:
            logger.warning(f"Error parsing model card: {e}")
            return None
    
    @staticmethod
    def _extract_parameters(model_id: str, tags: list) -> Optional[str]:
        """Extract model parameter count from ID or tags"""
        id_lower = model_id.lower()
        
        for tag in tags:
            tag_lower = tag.lower()
            for param_key, param_val in OllamaLibraryScraper.PARAMETER_MAP.items():
                if param_key in tag_lower:
                    return param_val
        
        for param_key, param_val in OllamaLibraryScraper.PARAMETER_MAP.items():
            if param_key in id_lower:
                return param_val
        
        return None
    
    @staticmethod
    def _infer_quantization(model_id: str, tags: list) -> str:
        """Infer quantization from model ID or tags"""
        id_lower = model_id.lower()
        all_text = id_lower + " " + " ".join(tag.lower() for tag in tags)
        
        if "gguf" in all_text or "q4" in all_text or "4-bit" in all_text:
            return "4-bit"
        if "q5" in all_text or "5-bit" in all_text:
            return "5-bit"
        if "q8" in all_text or "8-bit" in all_text:
            return "8-bit"
        if "fp16" in all_text or "float16" in all_text:
            return "fp16"
        if "fp32" in all_text or "float32" in all_text:
            return "fp32"
        
        return "unknown"
    
    @staticmethod
    def _infer_capabilities(model_id: str, description: str, tags: list) -> list[str]:
        """Infer model capabilities from ID, description, and tags"""
        capabilities = set()
        
        id_lower = model_id.lower()
        desc_lower = description.lower()
        tags_lower = [t.lower() for t in tags]
        all_text = id_lower + " " + desc_lower + " " + " ".join(tags_lower)
        
        # Check capability keywords
        if "chat" in all_text or "assistant" in all_text or "instruct" in all_text:
            capabilities.add("chat")
        
        if "code" in all_text or "coder" in all_text or "programming" in all_text:
            capabilities.add("coding")
        
        if "vision" in all_text or "image" in all_text or "visual" in all_text or "llava" in id_lower:
            capabilities.add("vision")
        
        if "embed" in id_lower or "embedding" in all_text:
            capabilities.add("embedding")
        
        if "reason" in desc_lower or "reasoning" in all_text or "deepseek" in id_lower or "qwen" in id_lower:
            capabilities.add("reasoning")
        
        if "small" in tags_lower or "fast" in all_text or "phi" in id_lower or "tiny" in tags_lower:
            capabilities.add("fast")
        
        if "long" in all_text or "context" in all_text or "128k" in all_text or "200k" in all_text:
            capabilities.add("long-context")
        
        # Ensure at least one capability
        if not capabilities:
            if "embed" in id_lower:
                capabilities.add("embedding")
            else:
                capabilities.add("chat")
        
        return sorted(list(capabilities))


# Hardcoded fallback models (in case scraping fails)
FALLBACK_MODELS = [
    {
        "model_id": "llama3",
        "family": "llama",
        "display_name": "Llama 3",
        "description": "Meta's Llama 3 - fast, accurate general-purpose model",
        "tags": ["chat", "reasoning"],
        "capabilities": ["chat", "reasoning"],
        "parameters": "8B",
        "quantization": "4-bit",
        "source_url": "https://ollama.com/library/llama3",
        "pull_command": "ollama pull llama3",
    },
    {
        "model_id": "mistral",
        "family": "mistral",
        "display_name": "Mistral",
        "description": "Mistral 7B - efficient, fast inference",
        "tags": ["chat", "fast"],
        "capabilities": ["chat", "coding", "fast"],
        "parameters": "7B",
        "quantization": "4-bit",
        "source_url": "https://ollama.com/library/mistral",
        "pull_command": "ollama pull mistral",
    },
    {
        "model_id": "neural-chat",
        "family": "neural-chat",
        "display_name": "Neural Chat",
        "description": "Intel's Neural Chat - optimized for conversational AI",
        "tags": ["chat"],
        "capabilities": ["chat"],
        "parameters": "7B",
        "quantization": "4-bit",
        "source_url": "https://ollama.com/library/neural-chat",
        "pull_command": "ollama pull neural-chat",
    },
    {
        "model_id": "llava",
        "family": "llava",
        "display_name": "LLaVA",
        "description": "Vision-language model combining CLIP and Llama for image understanding",
        "tags": ["vision", "chat"],
        "capabilities": ["vision", "chat"],
        "parameters": "7B",
        "quantization": "4-bit",
        "source_url": "https://ollama.com/library/llava",
        "pull_command": "ollama pull llava",
    },
    {
        "model_id": "neural-embed",
        "family": "neural-embed",
        "display_name": "Neural Embed",
        "description": "Text embeddings model",
        "tags": ["embedding"],
        "capabilities": ["embedding"],
        "parameters": None,
        "quantization": "unknown",
        "source_url": "https://ollama.com/library/neural-embed",
        "pull_command": "ollama pull neural-embed:v1.5",
    },
    {
        "model_id": "dolphin-mixtral",
        "family": "mixtral",
        "display_name": "Dolphin Mixtral",
        "description": "Uncensored reasoning and coding model based on Mixtral",
        "tags": ["chat", "reasoning", "coding"],
        "capabilities": ["chat", "reasoning", "coding"],
        "parameters": "46.7B",
        "quantization": "unknown",
        "source_url": "https://ollama.com/library/dolphin-mixtral",
        "pull_command": "ollama pull dolphin-mixtral",
    },
    {
        "model_id": "deepseek-coder",
        "family": "deepseek",
        "display_name": "DeepSeek Coder",
        "description": "DeepSeek's specialized coding model",
        "tags": ["code", "reasoning"],
        "capabilities": ["coding", "reasoning"],
        "parameters": "6.7B",
        "quantization": "unknown",
        "source_url": "https://ollama.com/library/deepseek-coder",
        "pull_command": "ollama pull deepseek-coder:6.7b",
    },
]
