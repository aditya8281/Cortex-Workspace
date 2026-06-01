import numpy as np

from backend.app.rag.vector_store import VectorStore
from backend.app.rag.embeddings import EmbeddingModel
from backend.app.rag.text_chunker import TextChunker
from backend.app.ai.ingestion.extractor import FileExtractor
from backend.app.ai.ingestion.scanner import RepoScanner


class RepoIndexBuilder:
    """
    Builds AI understanding of entire codebase
    """

    def __init__(self):
        self.embedder = EmbeddingModel()
        self.chunker = TextChunker()
        self.extractor = FileExtractor()
        self.scanner = RepoScanner()

        self.vector_store = None

    def build(self, repo_path: str):
        files = self.scanner.scan(repo_path)

        all_chunks = []
        metadata = []

        for file in files:
            content = self.extractor.extract(file)
            chunks = self.chunker.chunk(content)

            for chunk in chunks:
                all_chunks.append(chunk)
                metadata.append({
                    "file": file,
                    "content": chunk
                })

        vectors = self.embedder.encode(all_chunks)

        self.vector_store = VectorStore(dim=vectors.shape[1])
        self.vector_store.add(vectors, metadata)

        return self.vector_store