import faiss
import numpy as np
from typing import List

from backend.app.rag.storage import VectorStorage


class VectorStore:
    """
    FAISS vector store with persistence support.
    """

    def __init__(self, dim: int):
        self.dim = dim
        self.index = faiss.IndexFlatL2(dim)
        self.metadata: List[dict] = []

    def add(
        self,
        vectors: np.ndarray,
        meta: List[dict]
    ):
        """
        Add embeddings and metadata.
        """
        self.index.add(vectors)
        self.metadata.extend(meta)

    def search(
        self,
        query_vector: np.ndarray,
        top_k: int = 5
    ):
        """
        Search nearest vectors.
        """
        distances, indices = self.index.search(
            query_vector,
            top_k
        )

        results = []

        for i, idx in enumerate(indices[0]):

            if idx < 0:
                continue

            if idx >= len(self.metadata):
                continue

            results.append(
                {
                    "score": float(distances[0][i]),
                    "data": self.metadata[idx]
                }
            )

        return results

    def save(
        self,
        path: str
    ):
        """
        Persist FAISS index and metadata.
        """
        VectorStorage.save(
            self.index,
            self.metadata,
            path
        )

    @classmethod
    def load(
        cls,
        path: str
    ):
        """
        Load FAISS index and metadata from disk.
        """
        loaded = VectorStorage.load(path)

        if loaded is None:
            return None

        index, metadata = loaded

        store = cls(index.d)

        store.index = index
        store.metadata = metadata

        return store