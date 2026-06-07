import json
from pathlib import Path

from backend.app.rag.vector_store import VectorStore
from backend.app.core.runtime import get_runtime
from backend.app.core.storage_abstraction import should_exclude_from_rag


class IndexManager:

    def __init__(
        self,
        repo_path: str,
        index_path: str | None = None,
        embedding_model: str = None,
        vector_db: str = None,
        code_parsing: str = None
    ):
        self.repo_path = repo_path
        self.embedding_model = embedding_model or "BAAI/bge-small-en-v1.5"
        self.vector_db = vector_db or "FAISS"
        self.code_parsing = code_parsing or "Tree-sitter"

        if index_path is None or index_path == ".cortex":
            from backend.app.core import storage
            index_dir = storage.get_indexes_root()
        else:
            index_dir = Path(index_path).expanduser().resolve()

        # Build an isolated subfolder key per config so indices never collide
        def safe(s):
            return s.replace("/", "_").replace(" ", "-").replace("(", "").replace(")", "")
        index_key = f"index_{safe(self.embedding_model)}_{safe(self.vector_db)}_{safe(self.code_parsing)}"
        self.index_path = str(index_dir / index_key)

    def get_store(self):
        from backend.app.rag.retriever import RepoRetriever

        base = Path(self.index_path)
        state_file = base / "file_states.json"

        if should_exclude_from_rag(self.repo_path):
            base.mkdir(parents=True, exist_ok=True)
            empty_store = VectorStore(dim=384)
            empty_store.save(self.index_path)
            return empty_store
        
        retriever = RepoRetriever(
            embedding_model=self.embedding_model,
            vector_db=self.vector_db,
            code_parsing=self.code_parsing
        )
        files = [
            file_path
            for file_path in retriever.scanner.scan(self.repo_path)
            if not should_exclude_from_rag(file_path)
        ]
        
        # Calculate current file modification times using safe abstraction
        runtime = get_runtime()
        current_states = {}
        for f in files:
            try:
                current_states[f] = runtime.get_file_modification_time(f)
            except Exception:
                pass

        # Load existing index & metadata
        existing = VectorStore.load(self.index_path)
        
        # Load cached file states
        cached_states = {}
        if state_file.exists():
            try:
                with open(state_file, "r") as f:
                    cached_states = json.load(f)
            except Exception:
                pass

        # Check if rebuild is needed
        rebuild_needed = (existing is None) or (cached_states != current_states)

        if rebuild_needed:
            if existing is not None and cached_states:
                try:
                    ntotal = existing.index.ntotal
                    if ntotal > 0 and len(existing.metadata) == ntotal:
                        all_vectors = existing.index.reconstruct_n(0, ntotal)
                        
                        # Group existing vectors and metadata by file path
                        existing_by_file = {}
                        for idx, meta in enumerate(existing.metadata):
                            file_path = meta.get("file")
                            if file_path:
                                if file_path not in existing_by_file:
                                    existing_by_file[file_path] = {"vectors": [], "metadata": []}
                                existing_by_file[file_path]["vectors"].append(all_vectors[idx])
                                existing_by_file[file_path]["metadata"].append(meta)
                        
                        # Determine changes
                        new_or_modified_files = []
                        retained_vectors = []
                        retained_metadata = []
                        
                        for f in current_states:
                            if f in cached_states and cached_states[f] == current_states[f]:
                                # Unmodified: retain its vectors and metadata
                                if f in existing_by_file:
                                    retained_vectors.extend(existing_by_file[f]["vectors"])
                                    retained_metadata.extend(existing_by_file[f]["metadata"])
                            else:
                                # New or modified: we must re-process this file
                                new_or_modified_files.append(f)
                                
                        # Process new and modified files
                        new_vectors = []
                        new_metadata = []
                        
                        for f in new_or_modified_files:
                            content = retriever.extractor.extract(f)
                            if not content:
                                continue
                            chunks = retriever.chunker.chunk_text(content, metadata={"file": f})
                            chunk_texts = [chunk["text"] for chunk in chunks]
                            if not chunk_texts:
                                continue
                            
                            # Generate embeddings for new chunks
                            file_vectors = retriever._get_embedder().encode(chunk_texts)
                            for idx, vec in enumerate(file_vectors):
                                new_vectors.append(vec)
                                new_metadata.append({
                                    "file": f,
                                    "chunk": chunk_texts[idx]
                                })
                        
                        # Combine and construct the final index
                        final_vectors = []
                        if retained_vectors:
                            final_vectors.extend(retained_vectors)
                        if new_vectors:
                            final_vectors.extend(new_vectors)
                            
                        final_metadata = retained_metadata + new_metadata
                        
                        if final_vectors:
                            import numpy as np
                            final_vectors_np = np.array(final_vectors).astype("float32")
                            new_store = VectorStore(dim=final_vectors_np.shape[1])
                            new_store.add(final_vectors_np, final_metadata)
                            
                            new_store.save(self.index_path)
                            try:
                                base.mkdir(parents=True, exist_ok=True)
                                with open(state_file, "w") as f:
                                    json.dump(current_states, f)
                            except Exception:
                                pass
                            return new_store
                        else:
                            empty_store = VectorStore(dim=384)
                            empty_store.save(self.index_path)
                            try:
                                base.mkdir(parents=True, exist_ok=True)
                                with open(state_file, "w") as f:
                                    json.dump(current_states, f)
                            except Exception:
                                pass
                            return empty_store
                    else:
                        retriever.build_index(self.repo_path)
                except Exception as e:
                    print(f"Incremental update failed, falling back: {e}")
                    retriever.build_index(self.repo_path)
            else:
                retriever.build_index(self.repo_path)
            
            if retriever.vector_store is not None:
                # Save the new index, metadata, and state cache
                retriever.vector_store.save(self.index_path)
                try:
                    base.mkdir(parents=True, exist_ok=True)
                    with open(state_file, "w") as f:
                        json.dump(current_states, f)
                except Exception:
                    pass
                return retriever.vector_store
            else:
                return VectorStore(dim=384)

        return existing
