"""Semantic chunking strategies for different document types."""

from __future__ import annotations

import re
from dataclasses import dataclass

from backend.app.models.document import DocumentType


@dataclass
class SemanticChunk:
    content: str
    chunk_index: int
    start_offset: int
    end_offset: int
    token_count: int
    chunk_type: str  # "heading", "paragraph", "code_block", "table", "list"
    language: str | None = None
    context_before: str | None = None
    context_after: str | None = None


def estimate_tokens(text: str) -> int:
    return max(1, len(text) // 4)


class SemanticChunker:
    """Chunks documents using semantic boundaries based on document type."""

    def __init__(self, max_tokens: int = 800, overlap_tokens: int = 150):
        self._max_tokens = max_tokens
        self._overlap_tokens = overlap_tokens

    def chunk(
        self,
        content: str,
        doc_type: DocumentType,
        file_path: str = "",
    ) -> list[SemanticChunk]:
        if doc_type == DocumentType.CODE:
            return self._chunk_code(content, file_path)
        elif doc_type == DocumentType.MARKDOWN:
            return self._chunk_markdown(content)
        elif doc_type == DocumentType.NOTEBOOK:
            return self._chunk_notebook(content)
        else:
            return self._chunk_text(content)

    def _chunk_markdown(self, content: str) -> list[SemanticChunk]:
        sections = re.split(r"\n(?=#{1,6}\s)", content)
        chunks: list[SemanticChunk] = []
        current_paras: list[str] = []
        current_tokens = 0
        offset = 0

        for section in sections:
            section = section.strip()
            if not section:
                continue

            paras = [p.strip() for p in section.split("\n\n") if p.strip()]
            for para in paras:
                para_tokens = estimate_tokens(para)
                _heading_match = re.match(r"^(#{1,6})\s+(.+)", para)

                if current_tokens + para_tokens > self._max_tokens and current_paras:
                    chunk_text = "\n\n".join(current_paras)
                    chunks.append(self._make_chunk(chunk_text, chunks, offset, "paragraph"))
                    offset += len(chunk_text) + 2
                    current_paras = []
                    current_tokens = 0

                current_paras.append(para)
                current_tokens += para_tokens

        if current_paras:
            chunk_text = "\n\n".join(current_paras)
            chunks.append(self._make_chunk(chunk_text, chunks, offset, "paragraph"))

        return self._add_context(chunks)

    def _chunk_code(self, content: str, file_path: str) -> list[SemanticChunk]:
        from backend.app.services.chunker import detect_language

        lang = detect_language(file_path)
        lines = content.splitlines(keepends=True)
        chunks: list[SemanticChunk] = []
        current_block: list[str] = []
        current_tokens = 0
        offset = 0
        in_docstring = False

        for line in lines:
            stripped = line.strip()
            if '"""' in stripped or "'''" in stripped:
                in_docstring = not in_docstring
                current_block.append(line)
                current_tokens += estimate_tokens(line)
            elif in_docstring:
                current_block.append(line)
                current_tokens += estimate_tokens(line)
            elif stripped.startswith(("def ", "class ", "async def ", "fn ", "func ", "struct ")):
                if current_block and current_tokens > 50:
                    chunk_text = "".join(current_block)
                    chunks.append(self._make_chunk(chunk_text, chunks, offset, "code_block", lang))
                    offset += len(chunk_text)
                    current_block = []
                    current_tokens = 0
                current_block.append(line)
                current_tokens += estimate_tokens(line)
            else:
                current_block.append(line)
                current_tokens += estimate_tokens(line)

            if current_tokens >= self._max_tokens:
                chunk_text = "".join(current_block)
                chunks.append(self._make_chunk(chunk_text, chunks, offset, "code_block", lang))
                offset += len(chunk_text)
                current_block = []
                current_tokens = 0

        if current_block:
            chunk_text = "".join(current_block)
            chunks.append(self._make_chunk(chunk_text, chunks, offset, "code_block", lang))

        return self._add_context(chunks)

    def _chunk_notebook(self, content: str) -> list[SemanticChunk]:
        import json

        try:
            nb = json.loads(content)
            cells = nb.get("cells", [])
        except (json.JSONDecodeError, TypeError):
            return self._chunk_text(content)

        chunks: list[SemanticChunk] = []
        offset = 0

        for _i, cell in enumerate(cells):
            cell_type = cell.get("cell_type", "code")
            source = "".join(cell.get("source", []))
            if not source.strip():
                continue

            chunk_type = "paragraph" if cell_type == "markdown" else "code_block"
            language = "python" if cell_type == "code" else None
            chunk_text = source

            chunks.append(self._make_chunk(chunk_text, chunks, offset, chunk_type, language))
            offset += len(chunk_text)

        return self._add_context(chunks)

    def _chunk_text(self, content: str) -> list[SemanticChunk]:
        paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]
        chunks: list[SemanticChunk] = []
        current_paras: list[str] = []
        current_tokens = 0
        offset = 0

        for para in paragraphs:
            para_tokens = estimate_tokens(para)
            if current_tokens + para_tokens > self._max_tokens and current_paras:
                chunk_text = "\n\n".join(current_paras)
                chunks.append(self._make_chunk(chunk_text, chunks, offset, "paragraph"))
                offset += len(chunk_text) + 2
                current_paras = []
                current_tokens = 0
            current_paras.append(para)
            current_tokens += para_tokens

        if current_paras:
            chunk_text = "\n\n".join(current_paras)
            chunks.append(self._make_chunk(chunk_text, chunks, offset, "paragraph"))

        return self._add_context(chunks)

    def _make_chunk(
        self,
        text: str,
        existing: list[SemanticChunk],
        offset: int,
        chunk_type: str,
        language: str | None = None,
    ) -> SemanticChunk:
        return SemanticChunk(
            content=text,
            chunk_index=len(existing),
            start_offset=offset,
            end_offset=offset + len(text),
            token_count=estimate_tokens(text),
            chunk_type=chunk_type,
            language=language,
        )

    def _add_context(self, chunks: list[SemanticChunk]) -> list[SemanticChunk]:
        for i, chunk in enumerate(chunks):
            if i > 0:
                prev_content = chunks[i - 1].content
                chunk.context_before = prev_content[-200:] if len(prev_content) > 200 else prev_content
            if i < len(chunks) - 1:
                next_content = chunks[i + 1].content
                chunk.context_after = next_content[:200] if len(next_content) > 200 else next_content
        return chunks
