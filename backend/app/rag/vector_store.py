import faiss
import numpy as np
from typing import List


class VectorStore:
    """
    Simple FAISS-based vector store for embeddings.
    """

    def __init__(self, dim: int):
        self.dim = dim
        self.index = faiss.IndexFlatL2(dim)
        self.metadata: List[dict] = []

    def add(self, vectors: np.ndarray, meta: List[dict]):
        """
        Add embeddings + metadata
        """
        self.index.add(vectors)
        self.metadata.extend(meta)

    def search(self, query_vector: np.ndarray, top_k: int = 5):
        """
        Search similar vectors
        """
        distances, indices = self.index.search(query_vector, top_k)

        results = []
        for i, idx in enumerate(indices[0]):
            if idx < len(self.metadata):
                results.append({
                    "score": float(distances[0][i]),
                    "data": self.metadata[idx]
                })

        return results