from backend.app.rag.index_manager import IndexManager
from backend.app.rag.retriever import RepoRetriever


class RAGService:

    def __init__(
        self,
        repo_path: str
    ):
        self.repo_path = repo_path
        # Cache retrievers per config key to avoid re-building on every call
        self._retrievers: dict = {}
        # Keep a default retriever for backward-compat warm-up calls with no config
        self._default_key = "BAAI/bge-small-en-v1.5|FAISS|Tree-sitter"

    def _get_retriever(
        self,
        embedding_model: str = None,
        vector_db: str = None,
        code_parsing: str = None
    ) -> RepoRetriever:
        em = embedding_model or "BAAI/bge-small-en-v1.5"
        vd = vector_db or "FAISS"
        cp = code_parsing or "Tree-sitter"
        key = f"{em}|{vd}|{cp}"

        if key not in self._retrievers:
            retriever = RepoRetriever(
                embedding_model=em,
                vector_db=vd,
                code_parsing=cp
            )
            manager = IndexManager(
                repo_path=self.repo_path,
                embedding_model=em,
                vector_db=vd,
                code_parsing=cp
            )
            retriever.vector_store = manager.get_store()
            self._retrievers[key] = retriever

        return self._retrievers[key]

    def initialize(
        self,
        embedding_model: str = None,
        vector_db: str = None,
        code_parsing: str = None
    ):
        """Pre-warm the retriever for the given (or default) config."""
        self._get_retriever(embedding_model, vector_db, code_parsing)

    def search(
        self,
        query: str,
        top_k: int = 5,
        embedding_model: str = None,
        vector_db: str = None,
        code_parsing: str = None
    ):
        retriever = self._get_retriever(embedding_model, vector_db, code_parsing)
        return retriever.retrieve(query, top_k)