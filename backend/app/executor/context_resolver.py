"""
ContextResolver — expands stub ContextItems into items with resolved_content.

Priority handled by ContextCompiler, but each resolver method populates
`resolved_content` so the LLM gets real data, not just a title + kind label.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, List

from backend.app.core.logging import get_logger

logger = get_logger(__name__)

# Max characters we'll inject per context item to avoid prompt overflow
_MAX_FILE_CHARS = 8_000
_MAX_URL_CHARS = 6_000
_MAX_FOLDER_FILES = 30


class ContextResolver:
    """Resolves a list of context item dicts/objects into enriched objects."""

    async def resolve(self, context_items: List[Any]) -> List[Any]:
        """
        Returns the same list with `resolved_content` populated where possible.
        Items that cannot be resolved are returned unchanged (no error raised).
        """
        if not context_items:
            return context_items

        resolved = []
        for item in context_items:
            try:
                enriched = await self._resolve_one(item)
                resolved.append(enriched)
            except Exception as exc:
                logger.warning(f"ContextResolver: failed to resolve item {getattr(item, 'id', '?')}: {exc}")
                resolved.append(item)

        return resolved

    # ------------------------------------------------------------------
    # Internal dispatch
    # ------------------------------------------------------------------

    async def _resolve_one(self, item: Any) -> Any:
        kind = _get(item, "kind", "")

        if kind == "file":
            return await self._resolve_file(item)
        elif kind == "folder":
            return await self._resolve_folder(item)
        elif kind == "url":
            return await self._resolve_url(item)
        elif kind == "memory":
            return await self._resolve_memory(item)
        elif kind == "repo":
            return await self._resolve_repo(item)
        elif kind == "terminal":
            # Terminal items carry their content in content_preview — just mirror it
            content = _get(item, "content_preview") or _get(item, "detail") or ""
            return _set_resolved(item, content)
        else:
            # Unknown kind — use detail / content_preview if available
            content = _get(item, "content_preview") or _get(item, "detail") or ""
            return _set_resolved(item, content)

    # ------------------------------------------------------------------
    # Per-kind resolvers
    # ------------------------------------------------------------------

    async def _resolve_file(self, item: Any) -> Any:
        path = _get(item, "path") or _get(item, "title")
        if not path:
            return item

        full_path = Path(path)
        if not full_path.is_absolute():
            # Try to resolve relative to cwd / project root
            from backend.app.core.paths import PROJECT_ROOT
            full_path = Path(PROJECT_ROOT) / path

        if not full_path.exists() or not full_path.is_file():
            return _set_resolved(item, f"[File not found: {path}]")

        try:
            text = full_path.read_text(encoding="utf-8", errors="replace")
            if len(text) > _MAX_FILE_CHARS:
                text = text[:_MAX_FILE_CHARS] + f"\n… [truncated — {len(text)} total chars]"
            content = f"```{full_path.suffix.lstrip('.')}\n{text}\n```"
            return _set_resolved(item, content)
        except Exception as exc:
            return _set_resolved(item, f"[Could not read file: {exc}]")

    async def _resolve_folder(self, item: Any) -> Any:
        path = _get(item, "path") or _get(item, "title")
        if not path:
            return item

        folder = Path(path)
        if not folder.is_absolute():
            from backend.app.core.paths import PROJECT_ROOT
            folder = Path(PROJECT_ROOT) / path

        if not folder.exists() or not folder.is_dir():
            return _set_resolved(item, f"[Folder not found: {path}]")

        total_files = 0
        total_size = 0
        tech_stack = set()
        important_files = []
        
        tree_lines = [f"{folder.name}/"]
        
        for root, dirs, files in os.walk(folder):
            dirs[:] = [d for d in dirs if not d.startswith(".") and d not in {"node_modules", "__pycache__", ".venv", "dist", "build", ".git", ".cortex", ".agents"}]
            rel_root = Path(root).relative_to(folder)
            
            for f in files:
                f_path = Path(root) / f
                if f.startswith("."):
                    continue
                try:
                    size = f_path.stat().st_size
                    total_size += size
                    total_files += 1
                except Exception:
                    continue
                
                if f == "package.json":
                    tech_stack.add("Node.js/JavaScript")
                elif f == "pyproject.toml" or f == "requirements.txt":
                    tech_stack.add("Python")
                elif f == "Cargo.toml":
                    tech_stack.add("Rust")
                elif f == "go.mod":
                    tech_stack.add("Go")
                elif f == "Makefile":
                    tech_stack.add("Makefile")
                elif f.endswith(".tsx") or f.endswith(".jsx"):
                    tech_stack.add("React")
                elif f.endswith(".ts"):
                    tech_stack.add("TypeScript")
                elif f.endswith(".py"):
                    tech_stack.add("Python")
                
                important_names = {"readme.md", "package.json", "pyproject.toml", "cargo.toml", "go.mod", "docker-compose.yml", "makefile", ".env", ".env.example", "main.py", "app.py", "index.ts", "main.tsx"}
                if f.lower() in important_names or f.endswith(".config.js") or f.endswith(".config.ts"):
                    rel_file_path = rel_root / f if rel_root != Path(".") else Path(f)
                    important_files.append(str(rel_file_path))
                    
        def build_tree_str(dir_path: Path, prefix="", max_lines=40, line_count_ref=[0]) -> list[str]:
            lines = []
            if line_count_ref[0] >= max_lines:
                return lines
            
            try:
                items = sorted([x for x in dir_path.iterdir() if not x.name.startswith(".") and x.name not in {"node_modules", "__pycache__", ".venv", "dist", "build", ".git", ".cortex", ".agents"}], key=lambda x: (not x.is_dir(), x.name.lower()))
            except Exception:
                return lines
            
            for index, x in enumerate(items):
                if line_count_ref[0] >= max_lines:
                    lines.append(f"{prefix}└── ... (tree truncated)")
                    break
                
                is_last = (index == len(items) - 1)
                connector = "└── " if is_last else "├── "
                lines.append(f"{prefix}{connector}{x.name}{'/' if x.is_dir() else ''}")
                line_count_ref[0] += 1
                
                if x.is_dir():
                    new_prefix = prefix + ("    " if is_last else "│   ")
                    lines.extend(build_tree_str(x, new_prefix, max_lines, line_count_ref))
            return lines

        tree_lines.extend(build_tree_str(folder))
        
        readme_summary = ""
        readme_path = folder / "README.md"
        if not readme_path.exists():
            for f in folder.iterdir():
                if f.name.lower() == "readme.md":
                    readme_path = f
                    break
        
        if readme_path.exists() and readme_path.is_file():
            try:
                readme_text = readme_path.read_text(encoding="utf-8", errors="ignore").strip()
                for line in readme_text.splitlines():
                    cleaned = line.strip()
                    if cleaned and not cleaned.startswith("#"):
                        readme_summary = cleaned[:400]
                        break
                if not readme_summary:
                    readme_summary = readme_text[:400]
            except Exception:
                pass
                
        stack_desc = f", Tech stack: {', '.join(sorted(tech_stack))}" if tech_stack else ""
        folder_summary = f"Folder containing {total_files} files (approx. {total_size/1024:.1f} KB){stack_desc}."
        if readme_summary:
            folder_summary += f"\nDescription: {readme_summary}"
            
        content = (
            f"=== Folder Context ===\n"
            f"Path: {path}\n"
            f"Metadata:\n"
            f"  - Total Files: {total_files}\n"
            f"  - Total Size: {total_size} bytes ({total_size/1024:.1f} KB)\n"
            f"  - Tech Stack: {', '.join(sorted(tech_stack)) if tech_stack else 'Undetected'}\n"
            f"\nFolder Summary:\n"
            f"{folder_summary}\n"
            f"\nImportant Files:\n"
            f"  - " + ("\n  - ".join(important_files[:15]) if important_files else "None identified") + ("\n  - ... (more)" if len(important_files) > 15 else "") + "\n"
            "\nFolder Tree:\n" + "\n".join(tree_lines) + "\n"
            "=== End of Folder Context ==="
        )
        
        return _set_resolved(item, content)

    async def _resolve_url(self, item: Any) -> Any:
        url = _get(item, "url") or _get(item, "title")
        if not url or not url.startswith("http"):
            return item

        try:
            import httpx
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                response = await client.get(url, headers={"User-Agent": "Cortex-ContextBot/1.0"})
                response.raise_for_status()
                ct = response.headers.get("content-type", "")
                if "html" in ct:
                    text = _strip_html(response.text)
                else:
                    text = response.text
                if len(text) > _MAX_URL_CHARS:
                    text = text[:_MAX_URL_CHARS] + "\n… [truncated]"
                return _set_resolved(item, f"URL: {url}\n\n{text}")
        except Exception as exc:
            return _set_resolved(item, f"[Failed to fetch URL {url}: {exc}]")

    async def _resolve_memory(self, item: Any) -> Any:
        """Search memory store for entries matching the item title."""
        try:
            from backend.app.ai.memory.repository import MemoryRepository
            repo = MemoryRepository()
            keyword = _get(item, "title") or _get(item, "detail") or ""
            # MemoryRepository.search returns a list of Memory objects
            results = repo.search(keyword, limit=5)
            if not results:
                return _set_resolved(item, f"[No memory entries found for: {keyword}]")
            lines = [f"Memory: {keyword}"]
            for r in results:
                lines.append(f"Q: {r.query}")
                lines.append(f"A: {r.response[:500]}")
                lines.append("---")
            return _set_resolved(item, "\n".join(lines))
        except Exception as exc:
            logger.warning(f"ContextResolver memory lookup failed: {exc}")
            return item

    async def _resolve_repo(self, item: Any) -> Any:
        """Pull architecture summary, files list, dependencies, and memory from the intelligence store."""
        path = _get(item, "path") or _get(item, "title")
        if not path:
            return item

        from backend.app.core.paths import PROJECT_ROOT
        full_path = Path(path)
        if not full_path.is_absolute():
            full_path = Path(PROJECT_ROOT) / path
        
        path_str = str(full_path.resolve())

        from backend.app.db.session import SessionLocal
        from backend.app.intelligence.models import RepositoryProfile, KnowledgeEntry
        import json

        db = SessionLocal()
        try:
            profile = db.query(RepositoryProfile).filter(RepositoryProfile.path == path_str).first()
            if not profile:
                name_val = _get(item, "title") or full_path.name
                profile = db.query(RepositoryProfile).filter(RepositoryProfile.name == name_val).first()

            source_key = f"repo:{path_str}"
            repo_memories = db.query(KnowledgeEntry).filter(
                (KnowledgeEntry.source_path == path_str) |
                (KnowledgeEntry.source_key == source_key) |
                (KnowledgeEntry.title.like(f"%{full_path.name}%"))
            ).all()

            lines = ["=== Repository Context ==="]
            
            lines.append("\n[Repository Memory]")
            if repo_memories:
                for idx, entry in enumerate(repo_memories):
                    lines.append(f"Memory {idx+1}: {entry.title}")
                    lines.append(entry.content)
                    lines.append("---")
            else:
                lines.append("No specialized repository memory or knowledge entries found.")

            if profile:
                lines.append(f"\nRepository Profile Name: {profile.name}")
                lines.append(f"Path: {profile.path}")
                lines.append(f"Summary: {profile.summary}")
                lines.append(f"Architecture Summary:\n{profile.architecture_summary}")
                lines.append(f"Tech Stack: {profile.tech_stack}")
                
                try:
                    imp_files = json.loads(profile.important_files_json or "[]")
                    lines.append("Important Files:\n  - " + "\n  - ".join(imp_files))
                except Exception:
                    lines.append("Important Files: Could not decode json")
                
                try:
                    deps = json.loads(profile.dependencies_json or "[]")
                    lines.append("Dependencies:\n  - " + "\n  - ".join(deps[:30]) + (f"\n  - ... ({len(deps)-30} more)" if len(deps) > 30 else ""))
                except Exception:
                    lines.append("Dependencies: Could not decode json")

            else:
                from backend.app.intelligence.repository_intelligence import RepositoryIntelligenceService
                service = RepositoryIntelligenceService()
                if full_path.exists():
                    try:
                        analyzed = service.analyze(full_path)
                        profile = service.upsert_profile(db, analyzed)
                        service.store_searchable_memory(db, analyzed)
                        db.commit()
                        
                        lines.append(f"\nRepository Profile Name: {profile.name}")
                        lines.append(f"Path: {profile.path}")
                        lines.append(f"Summary: {profile.summary}")
                        lines.append(f"Architecture Summary:\n{profile.architecture_summary}")
                        lines.append(f"Tech Stack: {profile.tech_stack}")
                        
                        imp_files = json.loads(profile.important_files_json or "[]")
                        lines.append("Important Files:\n  - " + "\n  - ".join(imp_files))
                        
                        deps = json.loads(profile.dependencies_json or "[]")
                        lines.append("Dependencies:\n  - " + "\n  - ".join(deps[:30]) + (f"\n  - ... ({len(deps)-30} more)" if len(deps) > 30 else ""))
                    except Exception as e:
                        lines.append(f"[Could not analyze repository path: {e}]")
                else:
                    lines.append(f"[Repository path not found: {path_str}]")

            lines.append("\n=== End of Repository Context ===")
            return _set_resolved(item, "\n".join(lines))
        finally:
            db.close()


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _get(obj: Any, attr: str, default: Any = None) -> Any:
    """Safely get attribute from either a Pydantic model or a dict."""
    if isinstance(obj, dict):
        return obj.get(attr, default)
    return getattr(obj, attr, default)


def _set_resolved(obj: Any, content: str) -> Any:
    """Return a copy of obj with resolved_content set."""
    if isinstance(obj, dict):
        return {**obj, "resolved_content": content}
    try:
        # Pydantic v2 model_copy
        return obj.model_copy(update={"resolved_content": content})
    except AttributeError:
        pass
    try:
        # Pydantic v1
        return obj.copy(update={"resolved_content": content})
    except Exception:
        pass
    # Fallback: mutate in place (last resort)
    try:
        obj.resolved_content = content
    except Exception:
        pass
    return obj


def _strip_html(html: str) -> str:
    """Very lightweight HTML-to-text (no external deps)."""
    import re
    # Remove script/style blocks
    html = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", html, flags=re.DOTALL | re.IGNORECASE)
    # Remove tags
    html = re.sub(r"<[^>]+>", " ", html)
    # Collapse whitespace
    html = re.sub(r"\s+", " ", html).strip()
    return html
