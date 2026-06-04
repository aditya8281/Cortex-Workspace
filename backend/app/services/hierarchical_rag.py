import os
import re
import json
import hashlib
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
import numpy as np
from sqlalchemy.orm import Session

from backend.app.models.hierarchical_memory import HierarchicalNode
from backend.app.services.hierarchical_indexing import HierarchicalIndexingService
from backend.app.core.redis import redis_cache

logger = logging.getLogger(__name__)


class HierarchicalRAGService:
    def __init__(self, dim: int = 384, executor: Any = None):
        self.executor = executor
        self.indexing_service = HierarchicalIndexingService(dim=dim)
        self.vector_store = self.indexing_service.vector_store

    def classify_query(self, query: str) -> str:
        """
        FAST PATH: filename lookup, simple file lists, specific file paths.
        DEEP PATH: conceptual questions, code logic explanation, semantic search.
        """
        query_lower = query.lower().strip()
        
        # Key phrases matching filename/metadata searches
        fast_keywords = [
            "where is", "find file", "locate", "path of", "show file", 
            "file named", "folder named", "directory of", "get file",
            "list files", "structure of", "layout of", "entrypoint",
            "show path", "which folder"
        ]
        if any(kw in query_lower for kw in fast_keywords):
            return "fast"
            
        # Match short queries with extensions e.g. "main.py", "pyproject.toml"
        words = query_lower.split()
        if len(words) <= 3:
            for w in words:
                if any(w.endswith(ext) for ext in [".py", ".json", ".ts", ".js", ".tsx", ".jsx", ".md", ".toml", ".yml", ".yaml"]):
                    return "fast"
                    
        return "deep"

    async def search(self, query: str, db: Session, top_k: int = 5, mode: str = "auto") -> List[Dict[str, Any]]:
        """
        Hybrid search combining Fast Path and Deep Path based on classification.
        """
        selected_mode = mode if mode in ["fast", "deep"] else self.classify_query(query)
        logger.info(f"Hierarchical RAG: routing query '{query}' to '{selected_mode}' path.")

        if selected_mode == "fast":
            return await self._search_fast(query, db, top_k)
        else:
            return await self._search_deep(query, db, top_k)

    async def _search_fast(self, query: str, db: Session, top_k: int) -> List[Dict[str, Any]]:
        """
        FAST PATH: filenames, metadata, and exact text substring match.
        """
        query_terms = [w.strip().lower() for w in re.findall(r'\w+', query) if len(w.strip()) > 2]
        if not query_terms:
            query_terms = [query.lower().strip()]

        candidates = []
        seen_ids = set()

        # 1. Filename lookup in path column
        for term in query_terms:
            nodes = db.query(HierarchicalNode).filter(
                HierarchicalNode.path.like(f"%{term}%"),
                HierarchicalNode.node_type.in_(["file", "folder", "repo"])
            ).limit(top_k).all()
            for n in nodes:
                if n.id not in seen_ids:
                    seen_ids.add(n.id)
                    candidates.append({
                        "score": 1.0,  # Max score for exact path match
                        "id": n.id,
                        "node_type": n.node_type,
                        "text": n.content,
                        "file_path": n.path,
                        "metadata": json.loads(n.metadata_json) if n.metadata_json else {}
                    })

        # 2. SQLite exact substring match in contents
        for term in query_terms:
            nodes = db.query(HierarchicalNode).filter(
                HierarchicalNode.content.like(f"%{term}%"),
                HierarchicalNode.node_type == "chunk"
            ).limit(top_k).all()
            for n in nodes:
                if n.id not in seen_ids:
                    seen_ids.add(n.id)
                    
                    # Fetch file path
                    parent_file = db.query(HierarchicalNode).filter(HierarchicalNode.id == n.parent_id).first()
                    file_path = parent_file.path if parent_file else ""

                    candidates.append({
                        "score": 0.8,
                        "id": n.id,
                        "node_type": n.node_type,
                        "text": n.content,
                        "file_path": file_path,
                        "metadata": json.loads(n.metadata_json) if n.metadata_json else {}
                    })

        return candidates[:top_k]

    async def _search_deep(self, query: str, db: Session, top_k: int) -> List[Dict[str, Any]]:
        """
        DEEP PATH: semantic vector search + query understanding + graph expansion + reranking.
        """
        # Execute the multi-stage filter pipeline from indexing service
        initial_chunks = await self.indexing_service.search(query, db, top_k=top_k * 2)
        if not initial_chunks:
            return []

        query_terms = [w.strip().lower() for w in re.findall(r'\w+', query) if len(w.strip()) > 2]

        # Hybrid Scoring & Graph association boosts
        scored_candidates = []
        for r in initial_chunks:
            chunk_id = r["id"]
            chunk_text = r["text"]
            file_path = r["file_path"]
            base_score = r["score"]  # Semantic cosine sim

            # Keyword boost (exact matches on query tokens)
            keyword_matches = sum(1 for term in query_terms if term in chunk_text.lower())
            keyword_score = min(1.0, keyword_matches * 0.2)

            # Boost if query matches filename directly (path matching)
            filename_match = 0.0
            if any(term in Path(file_path).name.lower() for term in query_terms):
                filename_match = 0.4

            # Hybrid Score calculation
            combined_score = 0.5 * base_score + 0.3 * keyword_score + 0.2 * filename_match

            scored_candidates.append({
                "score": combined_score,
                "id": chunk_id,
                "node_type": "chunk",
                "text": chunk_text,
                "file_path": file_path,
                "metadata": r["metadata"]
            })

        # Run Reranking
        reranked = self.rerank_candidates(query, scored_candidates, top_k)

        # Graph Expansion for Top matches
        expanded_results = []
        seen_paths = set()
        for c in reranked:
            expanded_results.append(c)
            seen_paths.add(c["file_path"] + "::" + str(c["id"]))

            # Expand graph to include imports or siblings
            associations = self.expand_graph(c["id"], db)
            for assoc in associations:
                assoc_path_key = assoc["file_path"] + "::" + str(assoc["id"])
                if assoc_path_key not in seen_paths:
                    seen_paths.add(assoc_path_key)
                    # Add with slightly discounted score to preserve original matches on top
                    assoc["score"] = c["score"] * 0.7
                    expanded_results.append(assoc)

        # Sort combined results by score descending
        expanded_results.sort(key=lambda x: x["score"], reverse=True)
        return expanded_results[:top_k]

    def _resolve_imports(self, chunk_text: str, current_file_path: str, db: Session) -> List[HierarchicalNode]:
        """
        Parse imports (Python/JS/TS syntax) from the chunk text and match them to database file nodes.
        """
        resolved_nodes = []
        
        # 1. Python imports: from x.y import z OR import x.y
        py_imports = re.findall(r'^\s*(?:import|from)\s+([a-zA-Z0-9_\.]+)', chunk_text, re.MULTILINE)
        # 2. JS/TS imports: import { x } from 'y' OR require('y')
        js_imports = re.findall(r'from\s+[\'"](.*?)[\'"]', chunk_text) + re.findall(r'require\s*\(\s*[\'"](.*?)[\'"]\s*\)', chunk_text)
        
        all_import_names = set(py_imports + js_imports)
        
        for imp in all_import_names:
            # Normalize python dotted path or js relative path
            imp_normalized = imp.replace(".", "/").strip("/")
            # Remove relative notations
            imp_name = Path(imp_normalized).name.lower()
            if len(imp_name) <= 2:
                continue

            # Look up a matching file node in SQLite
            nodes = db.query(HierarchicalNode).filter(
                HierarchicalNode.path.like(f"%{imp_name}.%"),
                HierarchicalNode.node_type == "file"
            ).limit(2).all()
            resolved_nodes.extend(nodes)

        return resolved_nodes

    def expand_graph(self, node_id: int, db: Session) -> List[Dict[str, Any]]:
        """
        Retrieve associated parent folder summaries, sibling files, and code imports.
        Creates "human-like memory association".
        """
        node = db.query(HierarchicalNode).filter(HierarchicalNode.id == node_id).first()
        if not node:
            return []

        associations = []

        # Case 1: Node is a chunk
        if node.node_type == "chunk":
            # 1. Parent File
            parent_file = db.query(HierarchicalNode).filter(HierarchicalNode.id == node.parent_id).first()
            if parent_file:
                # 2. Sibling files in same folder
                siblings = db.query(HierarchicalNode).filter(
                    HierarchicalNode.parent_id == parent_file.parent_id,
                    HierarchicalNode.node_type == "file",
                    HierarchicalNode.id != parent_file.id
                ).limit(3).all()
                
                for sib in siblings:
                    associations.append({
                        "id": sib.id,
                        "node_type": "file",
                        "text": f"Sibling file summary of '{Path(sib.path).name}': {sib.content}",
                        "file_path": sib.path,
                        "metadata": json.loads(sib.metadata_json) if sib.metadata_json else {}
                    })

                # 3. Resolved imports from chunk
                current_file_path = parent_file.path
                imported_nodes = self._resolve_imports(node.content, current_file_path, db)
                for imp_node in imported_nodes:
                    if imp_node.id != parent_file.id:
                        associations.append({
                            "id": imp_node.id,
                            "node_type": "file",
                            "text": f"Imported module summary of '{Path(imp_node.path).name}': {imp_node.content}",
                            "file_path": imp_node.path,
                            "metadata": json.loads(imp_node.metadata_json) if imp_node.metadata_json else {}
                        })

        # Case 2: Node is a file
        elif node.node_type == "file":
            # Get parent folder details
            parent_folder = db.query(HierarchicalNode).filter(HierarchicalNode.id == node.parent_id).first()
            if parent_folder:
                associations.append({
                    "id": parent_folder.id,
                    "node_type": "folder",
                    "text": f"Parent folder summary of '{Path(parent_folder.path).name}': {parent_folder.content}",
                    "file_path": parent_folder.path,
                    "metadata": json.loads(parent_folder.metadata_json) if parent_folder.metadata_json else {}
                })

        return associations

    def rerank_candidates(self, query: str, candidates: List[Dict[str, Any]], top_k: int) -> List[Dict[str, Any]]:
        """
        Sort and filter candidates using a fast heuristic based on query term frequency and path overlaps.
        """
        query_words = [w.strip().lower() for w in re.findall(r'\w+', query) if len(w.strip()) > 2]
        if not query_words:
            return candidates[:top_k]

        reranked = []
        for cand in candidates:
            score = cand["score"]
            text = cand["text"].lower()
            file_path = cand["file_path"].lower()

            # Boost if precise terms are matching the basename/filename
            file_name = Path(file_path).name
            for word in query_words:
                if word in file_name:
                    score += 0.3
                if word in text:
                    score += 0.1

            cand["score"] = score
            reranked.append(cand)

        reranked.sort(key=lambda x: x["score"], reverse=True)
        return reranked[:top_k]

    async def retrieve_context(self, query: str, db: Session) -> str:
        """
        Formats search results into a clean, markdown retrieval context block.
        """
        results = await self.search(query, db, top_k=4)
        if not results:
            return "No relevant context found in workspace memory."

        blocks = []
        for idx, r in enumerate(results):
            node_type = r.get("node_type", "chunk")
            file_name = Path(r["file_path"]).name if r.get("file_path") else "Unknown"
            blocks.append(
                f"[{idx+1}] File: {file_name} ({node_type})\n"
                f"Path: {r.get('file_path', 'N/A')}\n"
                f"Content:\n{r['text']}\n"
                f"---"
            )
        return "\n\n".join(blocks)

    async def build_context(
        self,
        query: str,
        db: Session,
        context_items: Optional[List[Any]] = None,
        history: Optional[List[Dict[str, str]]] = None,
        user_id: Optional[int] = None
    ) -> str:
        """
        Compiles the final context payload with compression logic.
        Priority: User-Attached -> Repo -> Folder -> File -> Chunk.
        """
        blocks = []

        # 1. Attached Context (Highest priority)
        if context_items:
            from backend.app.executor.context_compiler import ContextCompiler
            compiler = ContextCompiler()
            attached_block = compiler._format_context_items(context_items)
            if attached_block:
                blocks.append(attached_block)

        # 2. Repository/Workspace Context
        repo_nodes = db.query(HierarchicalNode).filter(HierarchicalNode.node_type == "repo").all()
        if repo_nodes:
            # Use query vector matching to select the most relevant repository summary
            top_repos = self.indexing_service._rank_nodes(
                self.indexing_service._get_embedder().encode([query])[0],
                repo_nodes,
                "repo",
                top_n=1
            )
            if top_repos:
                repo = top_repos[0]
                metadata = json.loads(repo.metadata_json) if repo.metadata_json else {}
                blocks.append(
                    f"=== Repository Context ===\n"
                    f"Project: {Path(repo.path).name}\n"
                    f"Summary: {repo.content}\n"
                    f"Structure summary: {metadata.get('structure_summary', 'N/A')}\n"
                    f"Important files: {', '.join(metadata.get('important_files', []))}\n"
                    f"=== End of Repository Context ==="
                )

        # 3. Conversation Context
        if history:
            history_str = "=== Conversation History ===\n"
            for turn in history:
                role = turn.get("role", "user")
                content = turn.get("content", "")
                role_display = "User" if role == "user" else "Assistant"
                history_str += f"{role_display}: {content}\n"
            history_str += "=== End of Conversation History ==="
            blocks.append(history_str)

        # 4. Hierarchical Scoped retrieval context (Folders -> Files -> Chunks)
        rag_str = "=== Retrieval Context (Hierarchical RAG) ===\n"
        results = await self.search(query, db, top_k=4)
        if results:
            for idx, r in enumerate(results):
                rag_str += f"[{idx+1}] Source: {r.get('file_path', 'N/A')}\nContent:\n{r['text']}\n---\n"
        else:
            rag_str += "No relevant files or chunks matched in workspace."
        rag_str += "=== End of Retrieval Context ==="
        blocks.append(rag_str)

        compiled_context = "\n\n".join(blocks)

        # Context Compression Layer (Triggers if character count > 8,000)
        if len(compiled_context) > 8000:
            logger.info(f"ContextBuilder: Context size is {len(compiled_context)} characters. Compressing context...")
            compressed_blocks = []

            # Keep attached context intact (user explicitly requested these)
            if context_items and attached_block:
                compressed_blocks.append(attached_block)

            # Compressed Repo profile
            if repo_nodes and top_repos:
                repo = top_repos[0]
                compressed_blocks.append(
                    f"=== Repository Context (Compressed) ===\n"
                    f"Project: {Path(repo.path).name}\n"
                    f"Summary: {repo.content}\n"
                    f"=== End of Repository Context ==="
                )

            # Compress History: Keep only last 3 turns
            if history:
                truncated_history = history[-3:]
                history_str = "=== Conversation History (Compressed) ===\n"
                for turn in truncated_history:
                    role = turn.get("role", "user")
                    content = turn.get("content", "")
                    role_display = "User" if role == "user" else "Assistant"
                    history_str += f"{role_display}: {content}\n"
                history_str += "=== End of Conversation History ==="
                compressed_blocks.append(history_str)

            # Compress RAG Results: Keep top 3, truncate each chunk to 400 characters
            rag_str = "=== Retrieval Context (Compressed RAG) ===\n"
            if results:
                for idx, r in enumerate(results[:3]):
                    truncated_text = r["text"][:400] + "..." if len(r["text"]) > 400 else r["text"]
                    rag_str += f"[{idx+1}] Source: {r.get('file_path', 'N/A')}\nContent:\n{truncated_text}\n---\n"
            else:
                rag_str += "No relevant files or chunks matched in workspace."
            rag_str += "=== End of Retrieval Context ==="
            compressed_blocks.append(rag_str)

            compiled_context = "\n\n".join(compressed_blocks)
            logger.info(f"ContextBuilder: Compressed context to {len(compiled_context)} characters.")

        return compiled_context
