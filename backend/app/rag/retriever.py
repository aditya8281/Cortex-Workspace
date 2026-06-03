from backend.app.rag.embeddings import EmbeddingModel
from backend.app.rag.vector_store import VectorStore

from backend.app.ai.ingestion.scanner import RepoScanner
from backend.app.ai.ingestion.extractor import FileExtractor
from backend.app.ai.ingestion.chunker import TextChunker


class RepoRetriever:

    def __init__(self, embedding_model: str = None, vector_db: str = None, code_parsing: str = None):
        self.embedding_model = embedding_model or "BAAI/bge-small-en-v1.5"
        self.vector_db = vector_db or "FAISS"
        self.code_parsing = code_parsing or "Tree-sitter"

        self.embedder = None

        self.scanner = RepoScanner()
        self.extractor = FileExtractor()
        self.chunker = TextChunker(code_parsing=self.code_parsing)

        self.vector_store = None
        
        
    def _get_embedder(self):

        if self.embedder is None:
            self.embedder = EmbeddingModel(model_name=self.embedding_model)

        return self.embedder

    def build_index(
        self,
        repo_path: str
    ):
        self.vector_store = None

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

        vectors = self._get_embedder().encode(
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
        import re

        if (
            self.vector_store is None
            or len(self.vector_store.metadata) == 0
        ):
            return []

        # Split query into keywords (exclude short/common words)
        query_terms = [w.lower() for w in re.findall(r'\w+', query) if len(w) > 2]

        # Get FAISS candidates
        candidates_limit = min(len(self.vector_store.metadata), max(50, top_k * 3))
        query_vector = self._get_embedder().encode([query])

        distances, indices = self.vector_store.index.search(
            query_vector,
            candidates_limit
        )

        faiss_candidates = {}
        for i, idx in enumerate(indices[0]):
            if idx < 0 or idx >= len(self.vector_store.metadata):
                continue
            distance = float(distances[0][i])
            semantic_sim = 1.0 / (1.0 + distance)
            faiss_candidates[idx] = semantic_sim

        scored_results = []
        for idx, meta in enumerate(self.vector_store.metadata):
            chunk_text = meta.get("chunk", "")

            # Check if this index was retrieved by FAISS
            if idx in faiss_candidates:
                semantic_sim = faiss_candidates[idx]
                is_faiss = True
            else:
                semantic_sim = 0.0
                is_faiss = False

            # Calculate keyword match boost
            keyword_score = 0.0
            if query_terms:
                text_lower = chunk_text.lower()
                for term in query_terms:
                    if term in text_lower:
                        keyword_score += 0.2  # Base substring match boost
                        # Exact word boundary boost
                        if re.search(r'\b' + re.escape(term) + r'\b', text_lower):
                            keyword_score += 0.3

            if is_faiss or keyword_score > 0.0:
                final_score = semantic_sim + keyword_score
                scored_results.append({
                    "score": final_score,
                    "data": meta
                })

        scored_results.sort(key=lambda x: x["score"], reverse=True)
        return scored_results[:top_k]
