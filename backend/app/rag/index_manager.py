import json
import os
from pathlib import Path

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
        from backend.app.rag.retriever import RepoRetriever

        base = Path(self.index_path)
        state_file = base / "file_states.json"
        
        retriever = RepoRetriever()
        files = retriever.scanner.scan(self.repo_path)
        
        # Calculate current file modification times
        current_states = {}
        for f in files:
            try:
                current_states[f] = os.path.getmtime(f)
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
            # Rebuild vector store index
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