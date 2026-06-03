from sentence_transformers import SentenceTransformer
import numpy as np


class EmbeddingModel:
    """
    Lazily loads embedding model only when needed.
    """

    def __init__(
        self,
        model_name: str = "BAAI/bge-small-en-v1.5"
    ):
        if model_name == "bge-small-en-v1.5":
            model_name = "BAAI/bge-small-en-v1.5"
        self.model_name = model_name
        self.model = None

    def _ensure_loaded(self):

        if self.model is None:
            self.model = SentenceTransformer(
                self.model_name
            )

    def encode(
        self,
        texts: list[str]
    ) -> np.ndarray:

        self._ensure_loaded()

        vectors = self.model.encode(
            texts
        )

        return np.array(
            vectors
        ).astype(
            "float32"
        )