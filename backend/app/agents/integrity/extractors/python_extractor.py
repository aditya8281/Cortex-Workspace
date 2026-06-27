"""Python file extractor — AST-based extraction of imports, classes, functions."""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

from backend.app.agents.integrity.extractors._base import (
    CollectorPlugin,
    Extractor,
)


class PythonExtractor(Extractor):
    def __init__(self) -> None:
        super().__init__(
            CollectorPlugin(
                name="python",
                plugin_version="1.0",
                supported_rkm_version="1.x",
                supported_language_version="3.9+",
            )
        )

    def extract(self, path: Path) -> dict[str, Any]:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        classes = [node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
        functions = [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for alias in node.names:
                    full = f"{module}.{alias.name}" if module else alias.name
                    imports.append(full)

        return {
            "path": str(path),
            "classes": classes,
            "functions": functions,
            "imports": imports,
            "raw_tree": tree,
        }
