import logging
import faiss
import numpy as np

logger = logging.getLogger(__name__)


class HierarchicalVectorStore:
    """
    Manages 4 distinct FAISS IndexIDMap2 vector indices for Chunk, File, Folder, and Repo layers,
    mapping custom database 64-bit integer keys to embeddings.
    """

    def __init__(self, dim: int = 384):
        self.dim = dim
        from backend.app.services.memory_manager import memory_manager
        self.base_dir = memory_manager.get_path("vector_db") / "hierarchical"
        self.indices = {}
        self._load_or_create_indices()

    def _load_or_create_indices(self):
        self.base_dir.mkdir(parents=True, exist_ok=True)
        layers = ["chunk", "file", "folder", "repo"]
        for layer in layers:
            index_path = self.base_dir / f"{layer}_index.faiss"
            if index_path.exists():
                try:
                    self.indices[layer] = faiss.read_index(str(index_path))
                    logger.info(f"Loaded existing hierarchical FAISS index for {layer} from {index_path}")
                except Exception as e:
                    logger.warning(f"Failed to load hierarchical FAISS index for {layer}, creating new empty index: {e}")
                    flat = faiss.IndexFlatL2(self.dim)
                    self.indices[layer] = faiss.IndexIDMap2(flat)
            else:
                flat = faiss.IndexFlatL2(self.dim)
                self.indices[layer] = faiss.IndexIDMap2(flat)

    def add_vectors(self, layer: str, vectors: np.ndarray, ids: np.ndarray):
        """
        Add vectors with custom 64-bit IDs.
        vectors: shape (N, dim) np.ndarray (float32)
        ids: shape (N,) np.ndarray (int64)
        """
        if layer not in self.indices:
            raise ValueError(f"Invalid layer: {layer}")
        if vectors.size == 0 or len(ids) == 0:
            return

        if vectors.ndim == 1:
            vectors = vectors.reshape(1, -1)

        vectors = np.ascontiguousarray(vectors.astype("float32"))
        ids = np.ascontiguousarray(ids.astype("int64"))
        self.indices[layer].add_with_ids(vectors, ids)

    def search_vectors(self, layer: str, query_vector: np.ndarray, top_k: int = 5):
        """
        Search the specified layer.
        query_vector: shape (1, dim) or (dim,)
        returns: list of dicts {"id": int, "score": float}
        """
        if layer not in self.indices:
            raise ValueError(f"Invalid layer: {layer}")
        if self.indices[layer].ntotal == 0:
            return []

        if query_vector.ndim == 1:
            query_vector = query_vector.reshape(1, -1)

        query_vector = np.ascontiguousarray(query_vector.astype("float32"))
        distances, indices = self.indices[layer].search(query_vector, top_k)

        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx != -1:
                results.append({"id": int(idx), "score": float(dist)})
        return results

    def remove_vectors(self, layer: str, ids: np.ndarray):
        """
        Remove vectors by their custom IDs.
        ids: shape (N,) np.ndarray (int64) or list of ints
        """
        if layer not in self.indices:
            raise ValueError(f"Invalid layer: {layer}")
        if len(ids) == 0 or self.indices[layer].ntotal == 0:
            return

        ids_arr = np.array(ids, dtype=np.int64)
        ids_arr = np.ascontiguousarray(ids_arr)
        self.indices[layer].remove_ids(ids_arr)

    def reconstruct(self, layer: str, node_id: int) -> np.ndarray:
        """
        Reconstruct the embedding vector for a node ID.
        """
        if layer not in self.indices:
            raise ValueError(f"Invalid layer: {layer}")
        return self.indices[layer].reconstruct(node_id)

    def save(self):
        """
        Save the current state of all indices to disk.
        """
        self.base_dir.mkdir(parents=True, exist_ok=True)
        for layer, index in self.indices.items():
            index_path = self.base_dir / f"{layer}_index.faiss"
            try:
                faiss.write_index(index, str(index_path))
                logger.info(f"Saved FAISS index for {layer} to {index_path}")
            except Exception as e:
                logger.error(f"Failed to save hierarchical index {layer}: {e}")
