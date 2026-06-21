from __future__ import annotations

import logging
import warnings
from typing import Any

from backend.app.core.config import settings

logger = logging.getLogger(__name__)

EMBEDDING_DIM = settings.EMBEDDING_DIM


class EmbeddingService:
    """Generate embeddings using ONNX model, Ollama, or mock fallback."""

    def __init__(self, model_path: str | None = None):
        self.model_path = model_path or settings.EMBEDDING_MODEL_PATH
        self._model = None
        self._tokenizer = None
        self._load_failed = False
        self._backend: str | None = None  # "onnx" | "ollama" | "mock"

    def _load_model(self) -> None:
        if self._backend is not None:
            return

        # Try ONNX first
        model_path = self.model_path
        if model_path:
            try:
                import onnxruntime as ort  # type: ignore[import-untyped]

                self._model = ort.InferenceSession(model_path)
                self._backend = "onnx"
                logger.info("Loaded ONNX model from %s", model_path)
                # Verify tokenizer works (detect stub tokenizers)
                test_inputs = self._tokenize("test")
                if test_inputs.get("input_ids") == [[0]] and test_inputs.get("attention_mask") == [[1]]:
                    logger.warning("ONNX tokenizer returned stub tensors — falling back")
                    self._backend = None
                    raise RuntimeError("Stub tokenizer detected")
                return
            except ImportError:
                logger.warning("onnxruntime not installed — install with: pip install 'cortex-workspace[embeddings]'")
            except Exception as e:
                logger.warning("Failed to load ONNX model: %s", e)

        # Try Ollama next
        try:
            import httpx  # noqa: F401

            self._backend = "ollama"
            logger.info(
                "Using Ollama embeddings (model=%s, base_url=%s)",
                settings.EMBEDDING_MODEL_NAME,
                settings.OLLAMA_BASE_URL,
            )
            return
        except ImportError:
            logger.warning("httpx not installed — install with: pip install httpx")

        # Mock fallback — last resort
        self._backend = "mock"
        warnings.warn(
            "No embedding backend available (ONNX missing, httpx missing). "
            "Using deterministic mock embeddings — these are NOT semantically meaningful. "
            "Install httpx for Ollama embeddings or cortex-workspace[embeddings] for ONNX.",
            UserWarning,
            stacklevel=2,
        )
        logger.warning("Using mock embeddings (no real backend available)")

    def embed(self, text: str) -> list[float]:
        self._load_model()
        if self._backend == "onnx" and self._model:
            try:
                inputs = self._tokenize(text)
                result = self._model.run(None, inputs)
                return result[0][0].tolist()
            except Exception as e:
                logger.warning("ONNX embedding failed: %s, falling back to mock", e)
                return self._mock_embed(text)
        if self._backend == "ollama":
            try:
                return self._run_async(self._embed_via_ollama([text]))[0]
            except Exception as e:
                logger.warning("Ollama embedding failed: %s, falling back to mock", e)
                return self._mock_embed(text)
        return self._mock_embed(text)

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        self._load_model()
        if self._backend == "onnx" and self._model:
            try:
                return [self.embed(t) for t in texts]
            except Exception as e:
                logger.warning("ONNX batch embedding failed: %s, falling back to mock", e)
                return [self._mock_embed(t) for t in texts]
        if self._backend == "ollama":
            try:
                return self._run_async(self._embed_via_ollama(texts))
            except Exception as e:
                logger.warning("Ollama batch embedding failed: %s, falling back to mock", e)
                return [self._mock_embed(t) for t in texts]
        return [self._mock_embed(t) for t in texts]

    def _run_async(self, coro):
        """Run an async coroutine from sync context safely."""
        import asyncio

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None
        if loop and loop.is_running():
            raise RuntimeError("Cannot call async Ollama from running event loop")
        return asyncio.run(coro)

    async def _embed_via_ollama(self, texts: list[str]) -> list[list[float]]:
        import httpx

        vectors = []
        async with httpx.AsyncClient(
            base_url=settings.OLLAMA_BASE_URL, timeout=30.0
        ) as client:
            for text in texts:
                resp = await client.post(
                    "/api/embeddings",
                    json={
                        "model": settings.EMBEDDING_MODEL_NAME,
                        "prompt": text,
                    },
                )
                resp.raise_for_status()
                vectors.append(resp.json()["embedding"])
        return vectors

    def _tokenize(self, text: str) -> dict[str, Any]:
        return {"input_ids": [[0]], "attention_mask": [[1]]}

    def _mock_embed(self, text: str) -> list[float]:
        import hashlib

        h = hashlib.md5(text.encode()).digest()
        vec = [b / 255.0 for b in h]
        vec = vec * (EMBEDDING_DIM // len(vec)) + vec[: EMBEDDING_DIM % len(vec)]
        norm = sum(v * v for v in vec) ** 0.5
        return [v / norm for v in vec]

    def embed_single(self, text: str) -> list[float]:
        """Embed a single text into a vector (alias for embed)."""
        return self.embed(text)

    def embed_with_cache(self, text: str, cache_service: Any) -> list[float]:
        """Embed text using cache when available, computing only on miss."""
        import hashlib

        content_hash = hashlib.sha256(text.encode()).hexdigest()[:32]
        cached = cache_service.get(content_hash, model_name=self._get_model_name())
        if cached is not None:
            return cached

        embedding = self.embed(text)
        cache_service.put(
            content_hash=content_hash,
            embedding=embedding,
            model_name=self._get_model_name(),
            token_count=len(text) // 4,
        )
        return embedding

    def _get_model_name(self) -> str:
        if self._backend == "onnx":
            return "onnx-nomic-embed-text"
        elif self._backend == "ollama":
            from backend.app.core.config import settings
            return settings.EMBEDDING_MODEL_NAME
        return "mock-embedding"

    def compute_embedding_id(self, text: str) -> str:
        """Compute a deterministic embedding ID for deduplication."""
        import hashlib

        return hashlib.sha256(text.encode()).hexdigest()[:32]


_embedding_service: EmbeddingService | None = None


def get_embedding_service() -> EmbeddingService:
    """Get or create the global EmbeddingService singleton."""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service
