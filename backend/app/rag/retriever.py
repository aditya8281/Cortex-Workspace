from backend.app.rag.embeddings import EmbeddingModel
from backend.app.rag.vector_store import VectorStore

from backend.app.ai.ingestion.scanner import RepoScanner
from backend.app.ai.ingestion.extractor import FileExtractor
from backend.app.ai.ingestion.chunker import TextChunker


class RepoRetriever:

    def __init__(self):
        self.embedder = EmbeddingModel()
        self.scanner = RepoScanner()
        self.extractor = FileExtractor()
        self.chunker = TextChunker()

        self.vector_store = None

    def build_index(
        self,
        repo_path: str
    ):

        files = self.scanner.scan(repo_path)

        all_texts = []
        metadata = []

        for file_path in files:

            content = self.extractor.extract(
                file_path
            )

            if not content:
                continue

            chunks = self.chunker.chunk_text(
                content,
                metadata={
                    "file": file_path
                }
            )

            for chunk in chunks:

                all_texts.append(
                    chunk["text"]
                )

                metadata.append(
                    {
                        "file": file_path,
                        "chunk": chunk["text"]
                    }
                )

        if not all_texts:
            return

        vectors = self.embedder.encode(
            all_texts
        )

        self.vector_store = VectorStore(
            dim=vectors.shape[1]
        )

        self.vector_store.add(
            vectors,
            metadata
        )

    def retrieve(
        self,
        query: str,
        top_k: int = 5
    ):

        if self.vector_store is None:
            return []

        query_vector = self.embedder.encode(
            [query]
        )

        return self.vector_store.search(
            query_vector,
            top_k
        )