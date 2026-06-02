from backend.app.rag.index_manager import IndexManager
from backend.app.rag.retriever import RepoRetriever


class RAGService:

    def __init__(
        self,
        repo_path: str
    ):

        self.repo_path = repo_path

        self.retriever = RepoRetriever()

        self.initialized = False

    def initialize(self):

        if self.initialized:
            return

        manager = IndexManager(
            repo_path=self.repo_path
        )

        self.retriever.vector_store = (
            manager.get_store()
        )

        self.initialized = True

    def search(
        self,
        query: str,
        top_k: int = 5
    ):

        if not self.initialized:
            self.initialize()

        return self.retriever.retrieve(
            query,
            top_k
        )