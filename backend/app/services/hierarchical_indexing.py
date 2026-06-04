import os
import re
import json
import hashlib
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional
import numpy as np
from sqlalchemy.orm import Session

from backend.app.models.hierarchical_memory import HierarchicalNode
from backend.app.rag.hierarchical_store import HierarchicalVectorStore
from backend.app.ai.ingestion.chunker import TextChunker
from backend.app.ai.ingestion.scanner import RepoScanner
from backend.app.ai.llm_router import LLMRouter
from backend.app.core.redis import redis_cache

logger = logging.getLogger(__name__)


class HierarchicalIndexingService:
    def __init__(self, dim: int = 384):
        self.vector_store = HierarchicalVectorStore(dim=dim)
        self.chunker = TextChunker()
        self.scanner = RepoScanner()
        self.router = LLMRouter()
        self._embedder = None

    def _get_embedder(self):
        if self._embedder is None:
            from backend.app.rag.embeddings import EmbeddingModel
            self._embedder = EmbeddingModel()
        return self._embedder

    def _get_file_hash(self, content: str) -> str:
        return hashlib.md5(content.encode("utf-8")).hexdigest()

    def _parse_llm_json(self, text: str) -> dict:
        try:
            clean_text = text.strip()
            if "```" in clean_text:
                match = re.search(r'```(?:json)?\s*([\s\S]+?)\s*```', clean_text)
                if match:
                    clean_text = match.group(1).strip()
            return json.loads(clean_text)
        except Exception as e:
            logger.warning(f"Failed to parse LLM response as JSON: {e}. Raw response: {text}")
            return {
                "short_description": text[:200],
                "key_topics": ["workspace"],
                "important_files": [],
                "structure_summary": "Directory structure summarized."
            }

    async def _refresh_repo_profile(self, repo_path: str, db: Session) -> Optional[HierarchicalNode]:
        """
        Refresh the repository summary/vector without rescanning the filesystem.
        """
        p = Path(repo_path).resolve()
        if not p.exists() or not p.is_dir():
            return None

        repo_path_str = str(p)
        repo_node = db.query(HierarchicalNode).filter(
            HierarchicalNode.path == repo_path_str,
            HierarchicalNode.node_type == "repo"
        ).first()
        if not repo_node:
            repo_node = HierarchicalNode(
                node_type="repo",
                path=repo_path_str,
                content=f"Repository named {p.name}",
                metadata_json="{}"
            )
            db.add(repo_node)
            db.flush()

        child_folders = db.query(HierarchicalNode).filter(
            HierarchicalNode.parent_id == repo_node.id,
            HierarchicalNode.node_type == "folder"
        ).all()
        child_files = db.query(HierarchicalNode).filter(
            HierarchicalNode.parent_id == repo_node.id,
            HierarchicalNode.node_type == "file"
        ).all()
        summary_lines = [
            f"- File {Path(f.path).name}: {f.content}" for f in child_files
        ]
        summary_lines.extend(
            f"- Folder {Path(f.path).name}: {f.content}" for f in child_folders
        )
        folder_summaries = "\n".join(summary_lines) if summary_lines else "None."

        prompt = (
            f"You are Cortex Workspace Analyzer. Analyze the repository '{p.name}' with the following main directories:\n"
            f"{folder_summaries}\n\n"
            f"Produce a JSON object containing:\n"
            f'- "short_description": "High-level description of what this codebase project does"\n'
            f'- "key_topics": ["topic1", "topic2", ...]\n'
            f'- "important_files": ["README.md", "pyproject.toml", ...]\n'
            f'- "structure_summary": "Overview of the primary entrypoints and service layers"'
        )
        try:
            llm_res = await self.router.generate(prompt=prompt)
            metadata = self._parse_llm_json(llm_res)
        except Exception as e:
            logger.warning(f"Failed to generate LLM summary for repo {repo_path_str}: {e}")
            metadata = {
                "short_description": f"Repository named {p.name}",
                "key_topics": ["codebase"],
                "important_files": ["README.md"],
                "structure_summary": "Codebase components indexed."
            }

        repo_node.content = metadata.get("short_description", f"Repository named {p.name}")
        repo_node.metadata_json = json.dumps(metadata)
        repo_node.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
        db.flush()

        embedder = self._get_embedder()
        vec = embedder.encode([repo_node.content])[0]
        self.vector_store.remove_vectors("repo", np.array([repo_node.id]))
        self.vector_store.add_vectors("repo", np.array([vec]), np.array([repo_node.id]))
        self.vector_store.save()
        db.commit()
        return repo_node

    async def refresh_branch(self, file_path: str, repo_path: str, db: Session) -> None:
        """
        Refresh folder and repository summaries that sit above a file or deleted path.
        """
        repo_resolved = Path(repo_path).resolve()
        current = Path(file_path).resolve().parent
        folder_paths: list[str] = []

        while True:
            if current == repo_resolved:
                break
            try:
                current.relative_to(repo_resolved)
            except ValueError:
                break
            folder_paths.append(str(current))
            if current.parent == current:
                break
            current = current.parent

        # Refresh deepest folder first so parent summaries consume up-to-date child summaries.
        for folder_path in folder_paths:
            await self.index_folder(folder_path, repo_path, db)

        await self._refresh_repo_profile(repo_path, db)

    def _get_or_create_parent_folder_node(self, file_path: str, repo_path: str, db: Session) -> Optional[int]:
        """
        Recursively construct folder nodes up to the repository path.
        """
        parent_dir = str(Path(file_path).parent.resolve())
        repo_resolved = str(Path(repo_path).resolve())

        if parent_dir == repo_resolved:
            # Parent is the repo itself
            repo_node = db.query(HierarchicalNode).filter(
                HierarchicalNode.path == repo_resolved,
                HierarchicalNode.node_type == "repo"
            ).first()
            return repo_node.id if repo_node else None

        if len(parent_dir) < len(repo_resolved):
            return None

        # Check if parent folder node already exists
        existing = db.query(HierarchicalNode).filter(
            HierarchicalNode.path == parent_dir,
            HierarchicalNode.node_type == "folder"
        ).first()

        if existing:
            return existing.id

        # Recursively construct parent folders
        grandparent_id = self._get_or_create_parent_folder_node(parent_dir, repo_path, db)

        new_folder = HierarchicalNode(
            node_type="folder",
            path=parent_dir,
            content=f"Folder at {parent_dir}",
            parent_id=grandparent_id,
            metadata_json=json.dumps({"name": Path(parent_dir).name})
        )
        db.add(new_folder)
        db.flush()  # Populates new_folder.id

        # Insert placeholder vector
        embedder = self._get_embedder()
        vec = embedder.encode([f"Folder at {parent_dir}"])[0]
        self.vector_store.add_vectors("folder", np.array([vec]), np.array([new_folder.id]))
        self.vector_store.save()

        return new_folder.id

    async def index_file(self, file_path: str, repo_path: str, db: Session) -> Optional[HierarchicalNode]:
        """
        Extract content, chunk, generate embeddings, and insert/update HierarchicalNodes.
        """
        p = Path(file_path).resolve()
        if not p.exists() or p.is_dir():
            return None

        try:
            content = p.read_text(encoding="utf-8", errors="ignore")
        except Exception as e:
            logger.error(f"Cannot read file {file_path}: {e}")
            return None

        file_hash = self._get_file_hash(content)

        # Check if file node already exists
        file_path_str = str(p)
        file_node = db.query(HierarchicalNode).filter(
            HierarchicalNode.path == file_path_str,
            HierarchicalNode.node_type == "file"
        ).first()

        if file_node and file_node.hash == file_hash:
            logger.info(f"Skipping unmodified file {file_path_str}")
            return file_node

        embedder = self._get_embedder()

        if file_node:
            # Hash changed: Remove existing chunks from DB and FAISS
            child_chunks = db.query(HierarchicalNode).filter(
                HierarchicalNode.parent_id == file_node.id,
                HierarchicalNode.node_type == "chunk"
            ).all()
            if child_chunks:
                chunk_ids = [c.id for c in child_chunks]
                self.vector_store.remove_vectors("chunk", np.array(chunk_ids))
                for c in child_chunks:
                    db.delete(c)
            db.flush()
        else:
            # Resolve parent folder node
            parent_folder_id = self._get_or_create_parent_folder_node(file_path_str, repo_path, db)
            file_node = HierarchicalNode(
                node_type="file",
                path=file_path_str,
                parent_id=parent_folder_id,
                content="",
                metadata_json=json.dumps({"name": p.name})
            )
            db.add(file_node)
            db.flush()

        # Generate chunk nodes
        chunks = self.chunker.chunk_text(content, metadata={"file": file_path_str})
        if chunks:
            chunk_texts = [c["text"] for c in chunks]
            vectors = embedder.encode(chunk_texts)
            chunk_nodes = []
            for idx, chunk in enumerate(chunks):
                c_node = HierarchicalNode(
                    node_type="chunk",
                    path=f"{file_path_str}::chunk_{idx}",
                    content=chunk["text"],
                    parent_id=file_node.id,
                    metadata_json=json.dumps(chunk.get("metadata", {}))
                )
                db.add(c_node)
                chunk_nodes.append(c_node)
            
            db.flush()  # Populates chunk IDs
            
            # Map chunk vectors to FAISS
            chunk_ids = np.array([c.id for c in chunk_nodes], dtype=np.int64)
            self.vector_store.add_vectors("chunk", vectors, chunk_ids)

        # Generate file summary using LLM
        prompt = (
            f"Provide a brief 1-2 sentence summary of the purpose and functionality of the file '{p.name}':\n\n"
            f"{content[:3500]}"
        )
        try:
            summary = await self.router.generate(prompt=prompt)
            summary = summary.strip()
        except Exception as e:
            logger.warning(f"Failed to generate LLM summary for file {file_path_str}: {e}")
            summary = f"Code file named {p.name}"

        file_node.content = summary
        file_node.hash = file_hash
        file_node.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
        db.flush()

        # Update file vector
        file_vec = embedder.encode([summary])[0]
        # Remove existing file vector if updating
        self.vector_store.remove_vectors("file", np.array([file_node.id]))
        self.vector_store.add_vectors("file", np.array([file_vec]), np.array([file_node.id]))

        self.vector_store.save()
        db.commit()
        return file_node

    async def index_folder(self, folder_path: str, repo_path: str, db: Session) -> Optional[HierarchicalNode]:
        """
        Summarize a directory based on child files and generate a folder-level embedding.
        """
        p = Path(folder_path).resolve()
        if not p.exists() or not p.is_dir():
            return None

        folder_path_str = str(p)
        folder_node = db.query(HierarchicalNode).filter(
            HierarchicalNode.path == folder_path_str,
            HierarchicalNode.node_type == "folder"
        ).first()

        # Get list of files under folder
        child_files = db.query(HierarchicalNode).filter(
            HierarchicalNode.parent_id == (folder_node.id if folder_node else -1),
            HierarchicalNode.node_type == "file"
        ).all()
        child_folders = db.query(HierarchicalNode).filter(
            HierarchicalNode.parent_id == (folder_node.id if folder_node else -1),
            HierarchicalNode.node_type == "folder"
        ).all()

        summary_lines = [
            f"- File {Path(f.path).name}: {f.content}" for f in child_files
        ]
        summary_lines.extend(
            f"- Folder {Path(f.path).name}: {f.content}" for f in child_folders
        )
        child_summaries = "\n".join(summary_lines) if summary_lines else "No files or subfolders."

        prompt = (
            f"You are Cortex Workspace Analyzer. Analyze the folder '{p.name}' containing the following files and descriptions:\n"
            f"{child_summaries}\n\n"
            f"Produce a JSON object containing:\n"
            f'- "short_description": "Concise description of the folder\'s purpose"\n'
            f'- "key_topics": ["topic1", "topic2", ...]\n'
            f'- "important_files": ["file1", "file2", ...]\n'
            f'- "structure_summary": "Structural description of modules inside this folder"'
        )
        try:
            llm_res = await self.router.generate(prompt=prompt)
            metadata = self._parse_llm_json(llm_res)
        except Exception as e:
            logger.warning(f"Failed to generate LLM summary for folder {folder_path_str}: {e}")
            metadata = {
                "short_description": f"Folder named {p.name}",
                "key_topics": ["modules"],
                "important_files": [],
                "structure_summary": "Directory contents indexed."
            }

        if not folder_node:
            parent_id = self._get_or_create_parent_folder_node(folder_path_str, repo_path, db)
            folder_node = HierarchicalNode(
                node_type="folder",
                path=folder_path_str,
                parent_id=parent_id,
                content=""
            )
            db.add(folder_node)
            db.flush()

        folder_node.content = metadata.get("short_description", f"Folder named {p.name}")
        folder_node.metadata_json = json.dumps(metadata)
        folder_node.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
        db.flush()

        # Update embedding
        embedder = self._get_embedder()
        vec = embedder.encode([folder_node.content])[0]
        self.vector_store.remove_vectors("folder", np.array([folder_node.id]))
        self.vector_store.add_vectors("folder", np.array([vec]), np.array([folder_node.id]))

        self.vector_store.save()
        db.commit()
        return folder_node

    async def index_repo(self, repo_path: str, db: Session) -> Optional[HierarchicalNode]:
        """
        Orchestrate full repository crawling, file/folder recursive sync, and repo-level LLM summarization.
        """
        p = Path(repo_path).resolve()
        if not p.exists() or not p.is_dir():
            return None

        repo_path_str = str(p)
        repo_node = db.query(HierarchicalNode).filter(
            HierarchicalNode.path == repo_path_str,
            HierarchicalNode.node_type == "repo"
        ).first()

        if not repo_node:
            repo_node = HierarchicalNode(
                node_type="repo",
                path=repo_path_str,
                content=f"Repository named {p.name}",
                metadata_json="{}"
            )
            db.add(repo_node)
            db.flush()

        # Walk and index files
        files = self.scanner.scan(repo_path_str)
        logger.info(f"Hierarchical Indexing: Found {len(files)} files under {repo_path_str}")

        # Index files first (will dynamically construct intermediate folder tree placeholders)
        for f in files:
            await self.index_file(f, repo_path_str, db)

        # Re-index folders to calculate proper summaries bottom-up
        folders = db.query(HierarchicalNode).filter(
            HierarchicalNode.node_type == "folder"
        ).all()
        # Sort folders by depth descending (deepest folders first) so we bubble up summaries
        folders.sort(key=lambda x: len(Path(x.path).parts), reverse=True)
        for fold in folders:
            if fold.path.startswith(repo_path_str):
                await self.index_folder(fold.path, repo_path_str, db)

        return await self._refresh_repo_profile(repo_path_str, db)

    async def incremental_update(self, file_path: str, repo_path: str, db: Session) -> Optional[HierarchicalNode]:
        """
        Exposes endpoint to update hierarchical indexing for a single file dynamically.
        """
        p = Path(file_path).resolve()
        file_path_str = str(p)

        if not p.exists():
            # File was deleted: clean up DB and FAISS
            file_node = db.query(HierarchicalNode).filter(
                HierarchicalNode.path == file_path_str,
                HierarchicalNode.node_type == "file"
            ).first()
            if file_node:
                # 1. Clean chunks
                chunks = db.query(HierarchicalNode).filter(
                    HierarchicalNode.parent_id == file_node.id,
                    HierarchicalNode.node_type == "chunk"
                ).all()
                if chunks:
                    chunk_ids = [c.id for c in chunks]
                    self.vector_store.remove_vectors("chunk", np.array(chunk_ids))
                    for c in chunks:
                        db.delete(c)

                # 2. Clean file vector
                self.vector_store.remove_vectors("file", np.array([file_node.id]))
                db.delete(file_node)
                db.commit()
                self.vector_store.save()
                logger.info(f"Successfully deleted hierarchical node and chunks for deleted file {file_path_str}")
                try:
                    await self.refresh_branch(file_path_str, repo_path, db)
                except Exception as e:
                    logger.warning(f"Failed to refresh branch after deleting {file_path_str}: {e}")
            return None

        # Re-index file (automatically does incremental check)
        node = await self.index_file(file_path_str, repo_path, db)
        try:
            await self.refresh_branch(file_path_str, repo_path, db)
        except Exception as e:
            logger.warning(f"Failed to refresh branch after indexing {file_path_str}: {e}")
        return node

    def _rank_nodes(self, query_vector: np.ndarray, nodes: List[HierarchicalNode], layer: str, top_n: int) -> List[HierarchicalNode]:
        if not nodes:
            return []
        scored_nodes = []
        for node in nodes:
            try:
                vec = self.vector_store.reconstruct(layer, node.id)
                norm_q = np.linalg.norm(query_vector)
                norm_v = np.linalg.norm(vec)
                if norm_q > 0 and norm_v > 0:
                    sim = float(np.dot(query_vector, vec) / (norm_q * norm_v))
                else:
                    sim = 0.0
                scored_nodes.append((sim, node))
            except Exception as e:
                logger.warning(f"Could not reconstruct vector for node ID {node.id} on layer {layer}: {e}")
                scored_nodes.append((0.0, node))
        scored_nodes.sort(key=lambda x: x[0], reverse=True)
        return [node for _, node in scored_nodes[:top_n]]

    async def search(self, query: str, db: Session, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Hierarchical scoped retrieval pipeline:
        Query -> Repo filter -> Folder filter -> File filter -> Chunk retrieval
        """
        # 1. Cache lookup
        query_hash = hashlib.md5(query.encode("utf-8")).hexdigest()
        cache_key = f"hierarchical_search:{query_hash}:{top_k}"
        cached = await redis_cache.get(cache_key)
        if cached:
            logger.info(f"Hierarchical search cache HIT for key {cache_key}")
            return cached

        # Encode query
        embedder = self._get_embedder()
        query_vector = embedder.encode([query])[0]

        # 2. Repo Filter
        repos = db.query(HierarchicalNode).filter(HierarchicalNode.node_type == "repo").all()
        if not repos:
            return []
        top_repos = self._rank_nodes(query_vector, repos, "repo", top_n=2)
        repo_ids = [r.id for r in top_repos]

        # 3. Folder Filter
        folders = db.query(HierarchicalNode).filter(
            HierarchicalNode.parent_id.in_(repo_ids),
            HierarchicalNode.node_type == "folder"
        ).all()
        if folders:
            top_folders = self._rank_nodes(query_vector, folders, "folder", top_n=5)
            folder_ids = [f.id for f in top_folders]
        else:
            # Fallback if no folders found directly under repos
            folder_ids = repo_ids

        # 4. File Filter
        files = db.query(HierarchicalNode).filter(
            HierarchicalNode.parent_id.in_(folder_ids),
            HierarchicalNode.node_type == "file"
        ).all()
        if not files:
            # Fallback to search all files in these repos
            files = db.query(HierarchicalNode).filter(
                HierarchicalNode.node_type == "file"
            ).all()
            files = [f for f in files if any(f.path.startswith(r.path) for r in top_repos)]

        if not files:
            return []
        
        top_files = self._rank_nodes(query_vector, files, "file", top_n=5)
        file_ids = [f.id for f in top_files]

        # 5. Chunk Retrieval
        chunks = db.query(HierarchicalNode).filter(
            HierarchicalNode.parent_id.in_(file_ids),
            HierarchicalNode.node_type == "chunk"
        ).all()

        if not chunks:
            return []

        # Rank final chunks
        scored_chunks = []
        for node in chunks:
            try:
                vec = self.vector_store.reconstruct("chunk", node.id)
                norm_q = np.linalg.norm(query_vector)
                norm_v = np.linalg.norm(vec)
                if norm_q > 0 and norm_v > 0:
                    sim = float(np.dot(query_vector, vec) / (norm_q * norm_v))
                else:
                    sim = 0.0
                
                # Fetch parent file path
                parent_file = db.query(HierarchicalNode).filter(HierarchicalNode.id == node.parent_id).first()
                file_path = parent_file.path if parent_file else ""

                scored_chunks.append({
                    "score": sim,
                    "id": node.id,
                    "text": node.content,
                    "file_path": file_path,
                    "metadata": json.loads(node.metadata_json)
                })
            except Exception as e:
                logger.warning(f"Reconstruction failed for chunk ID {node.id}: {e}")

        scored_chunks.sort(key=lambda x: x["score"], reverse=True)
        results = scored_chunks[:top_k]

        # Cache results for 30 minutes
        await redis_cache.set(cache_key, results, expire_seconds=1800)
        return results
