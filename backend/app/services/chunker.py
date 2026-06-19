"""Text chunking service for code and documents."""

from __future__ import annotations

import re
from dataclasses import dataclass

LANGUAGE_MAP: dict[str, str] = {
    ".py": "python",
    ".js": "javascript",
    ".ts": "typescript",
    ".tsx": "tsx",
    ".jsx": "jsx",
    ".rs": "rust",
    ".go": "go",
    ".java": "java",
    ".c": "c",
    ".cpp": "cpp",
    ".h": "c",
    ".rb": "ruby",
    ".php": "php",
    ".swift": "swift",
    ".kt": "kotlin",
    ".sql": "sql",
    ".sh": "shell",
    ".md": "markdown",
    ".json": "json",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".toml": "toml",
    ".xml": "xml",
    ".html": "html",
    ".css": "css",
}

SKIP_DIRS: set[str] = {
    ".git",
    "node_modules",
    "__pycache__",
    "venv",
    ".venv",
    "dist",
    "build",
    ".next",
    "target",
}

_SYMBOL_RE = re.compile(
    r"^\s*"
    r"(?:(?:async|export|default|public|private|protected|static)\s+)*?"
    r"(def|function|class|struct|enum|trait|fn|func)"
    r"(?:\s+|\s*\()(\w*)"
)

_TYPE_MAP: dict[str, str] = {
    "def": "function",
    "function": "function",
    "fn": "function",
    "func": "function",
    "class": "class",
    "struct": "struct",
    "enum": "enum",
    "trait": "trait",
}


@dataclass
class Chunk:
    content: str
    file_path: str
    chunk_index: int
    language: str | None = None
    symbol_type: str | None = None
    symbol_name: str | None = None
    start_line: int | None = None
    end_line: int | None = None


def detect_language(file_path: str) -> str | None:
    """Detect programming language from file extension."""
    idx = file_path.rfind(".")
    if idx == -1:
        return None
    return LANGUAGE_MAP.get(file_path[idx:].lower())


def _extract_symbol(line: str) -> tuple[str | None, str | None]:
    """Extract symbol type and name from a code line."""
    m = _SYMBOL_RE.match(line)
    if not m:
        return None, None
    keyword = m.group(1)
    name = m.group(2) or None
    return _TYPE_MAP.get(keyword), name


def _estimate_tokens(text: str) -> int:
    """Rough token estimation (~4 chars per token)."""
    return max(1, len(text) // 4)


def chunk_code(content: str, file_path: str, max_tokens: int = 500) -> list[Chunk]:
    """Split code into semantic chunks (functions, classes, or by line count)."""
    lines = content.splitlines(keepends=True)
    chunks: list[Chunk] = []
    current_chunk: list[str] = []
    current_start = 1
    current_tokens = 0
    current_sym_type: str | None = None
    current_sym_name: str | None = None

    def _flush():
        nonlocal current_chunk, current_start, current_tokens
        nonlocal current_sym_type, current_sym_name
        if not current_chunk:
            return
        chunk_content = "".join(current_chunk)
        chunks.append(
            Chunk(
                content=chunk_content,
                file_path=file_path,
                chunk_index=len(chunks),
                language=detect_language(file_path),
                symbol_type=current_sym_type,
                symbol_name=current_sym_name,
                start_line=current_start,
                end_line=current_start + len(current_chunk) - 1,
            )
        )
        current_chunk = []
        current_tokens = 0
        current_sym_type = None
        current_sym_name = None

    for i, line in enumerate(lines, start=1):
        line_tokens = _estimate_tokens(line)
        sym_type, sym_name = _extract_symbol(line)

        if sym_type and current_chunk:
            _flush()
            current_start = i

        if sym_type:
            current_sym_type = sym_type
            current_sym_name = sym_name

        current_chunk.append(line)
        current_tokens += line_tokens

        if current_tokens >= max_tokens:
            _flush()
            current_start = i + 1

    if current_chunk:
        _flush()

    return chunks


def chunk_text(content: str, file_path: str, max_tokens: int = 500) -> list[Chunk]:
    """Split text into chunks by paragraph or token limit."""
    paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]
    chunks: list[Chunk] = []
    current_paras: list[str] = []
    current_tokens = 0

    for para in paragraphs:
        para_tokens = _estimate_tokens(para)
        if current_tokens + para_tokens > max_tokens and current_paras:
            chunk_content = "\n\n".join(current_paras)
            chunks.append(
                Chunk(
                    content=chunk_content,
                    file_path=file_path,
                    chunk_index=len(chunks),
                    language=detect_language(file_path),
                )
            )
            current_paras = []
            current_tokens = 0
        current_paras.append(para)
        current_tokens += para_tokens

    if current_paras:
        chunk_content = "\n\n".join(current_paras)
        chunks.append(
            Chunk(
                content=chunk_content,
                file_path=file_path,
                chunk_index=len(chunks),
                language=detect_language(file_path),
            )
        )

    return chunks
