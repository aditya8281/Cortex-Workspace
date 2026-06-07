import logging

import faiss
import numpy as np

logger = logging.getLogger(__name__)


class HierarchicalVectorStore:
    """Manages 4 distinct FAISS IndexIDMap2 vector indices for Chunk, File,
    Folder, and Repo layers, mapping custom database 64-bit integer keys
    to embeddings.

    All indices are stored under ``SystemPaths["vector_db"] / "hierarchical"``.
    """

    def __init__(self, dim: int = 384):
        self.dim = dim
        from backend.app.core import storage
        self.base_dir = storage.get_vector_db_root() / "hierarchical"
        self.indices = {}
        self._load_or_create_indices()

    def _load_or_create_indices(self):
        self.base_dir.mkdir(parents=True, exist_ok=True)
        layers = ["chunk", "file", "folder", "repo"]
        for layer in layers:
            index_path = self.base_dir / f"{layer}_index.faiss"
            if index_path.exists():
                try:
                    loaded = faiss.read_index(str(index_path))

                    def _index_dim(idx):
                        d = getattr(idx, "d", None)
                        if d is None and hasattr(idx, "index"):
                            d = getattr(idx.index, "d", None)
                        return d

                    existing_dim = _index_dim(loaded)
                    if existing_dim is not None and existing_dim != self.dim:
                        logger.warning(
                            "Existing FAISS index for %s has dim=%s, requested dim=%s; recreating",
                            layer, existing_dim, self.dim,
                        )
                        flat = faiss.IndexFlatL2(self.dim)
                        self.indices[layer] = faiss.IndexIDMap2(flat)
                    else:
                        self.indices[layer] = loaded
                        logger.info(
                            "Loaded existing hierarchical FAISS index for %s from %s",
                            layer, index_path,
                        )
                except Exception as e:
                    logger.warning(
                        "Failed to load hierarchical FAISS index for %s, creating new: %s",
                        layer, e,
                    )
                    flat = faiss.IndexFlatL2(self.dim)
                    self.indices[layer] = faiss.IndexIDMap2(flat)
            else:
                flat = faiss.IndexFlatL2(self.dim)
                self.indices[layer] = faiss.IndexIDMap2(flat)

    def add_vectors(self, layer: str, vectors: np.ndarray, ids: np.ndarray):
        """Add vectors with custom 64-bit IDs."""
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
        """Search the specified layer."""
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
        """Remove vectors by their custom IDs."""
        if layer not in self.indices:
            raise ValueError(f"Invalid layer: {layer}")
        if len(ids) == 0 or self.indices[layer].ntotal == 0:
            return

        ids_arr = np.array(ids, dtype=np.int64)
        ids_arr = np.ascontiguousarray(ids_arr)
        self.indices[layer].remove_ids(ids_arr)

    def reconstruct(self, layer: str, node_id: int) -> np.ndarray:
        """Reconstruct the embedding vector for a node ID."""
        if layer not in self.indices:
            raise ValueError(f"Invalid layer: {layer}")
        return self.indices[layer].reconstruct(node_id)

    def save(self):
        """Save the current state of all indices to disk."""
        self.base_dir.mkdir(parents=True, exist_ok=True)
        for layer, index in self.indices.items():
            index_path = self.base_dir / f"{layer}_index.faiss"
            try:
                faiss.write_index(index, str(index_path))
                logger.info("Saved FAISS index for %s to %s", layer, index_path)
            except Exception as e:
                logger.error("Failed to save hierarchical index %s: %s", layer, e)
