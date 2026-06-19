from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

EMBEDDING_DIM = 768


class EmbeddingService:
    """Generate embeddings using ONNX model with mock fallback."""

    def __init__(self, model_path: str | None = None):
        self.model_path = model_path
        self._model = None
        self._tokenizer = None

    def _load_model(self) -> None:
        if self._model is not None:
            return
        if self.model_path:
            try:
                import onnxruntime as ort  # type: ignore[import-untyped]

                self._model = ort.InferenceSession(self.model_path)
                logger.info("Loaded ONNX model from %s", self.model_path)
                return
            except ImportError:
                logger.warning("onnxruntime not installed — install with: pip install 'cortex-workspace[embeddings]'")
                return
            except Exception as e:
                logger.warning("Failed to load ONNX model: %s", e)
        logger.info("Using mock embeddings (no model loaded)")

    def embed(self, text: str) -> list[float]:
        self._load_model()
        if self._model:
            try:
                inputs = self._tokenize(text)
                result = self._model.run(None, inputs)
                return result[0][0].tolist()
            except Exception as e:
                logger.warning("Embedding failed: %s, using mock", e)
        return self._mock_embed(text)

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [self.embed(t) for t in texts]

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
