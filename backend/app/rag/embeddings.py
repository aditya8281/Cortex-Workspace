from sentence_transformers import SentenceTransformer
import numpy as np


class EmbeddingModel:
    """
    Converts text → vectors
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)

    def encode(self, texts: list[str]) -> np.ndarray:
        vectors = self.model.encode(texts)
        return np.array(vectors).astype("float32")