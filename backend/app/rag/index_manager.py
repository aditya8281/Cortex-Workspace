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

        retriever = RepoRetriever()

        retriever.build_index(
            self.repo_path
        )

        retriever.vector_store.save(
            self.index_path
        )

        return retriever.vector_store