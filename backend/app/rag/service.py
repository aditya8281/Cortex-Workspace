from backend.app.rag.retriever import RepoRetriever


class RAGService:

    def __init__(self):

        self.retriever = RepoRetriever()

        self.initialized = False

    def initialize(
        self,
        repo_path: str
    ):

        if self.initialized:
            return

        self.retriever.build_index(
            repo_path
        )

        self.initialized = True

    def search(
        self,
        query: str,
        top_k: int = 5
    ):

        return self.retriever.retrieve(
            query,
            top_k
        )