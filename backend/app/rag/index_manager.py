from pathlib import Path

from backend.app.rag.retriever import RepoRetriever
from backend.app.rag.vector_store import VectorStore


class IndexManager:

    def __init__(
        self,
        repo_path: str,
        index_path: str = ".cortex"
    ):
        self.repo_path = repo_path
        self.index_path = index_path

    def get_store(self):

        existing = VectorStore.load(
            self.index_path
        )

        if existing:
            return existing

        # Return a fresh empty vector store to avoid blocking application startup/testing.
        # The index should be rebuilt explicitly using scripts/rebuild_index.py.
        return VectorStore(dim=384)