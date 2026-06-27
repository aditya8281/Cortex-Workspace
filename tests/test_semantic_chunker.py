"""Tests for SemanticChunker."""

import pytest

from backend.app.models.document import DocumentType
from backend.app.services.intelligence.semantic_chunker import SemanticChunker, estimate_tokens


@pytest.fixture()
def chunker():
    return SemanticChunker(max_tokens=200, overlap_tokens=50)


def test_estimate_tokens():
    assert estimate_tokens("hello") == 1
    assert estimate_tokens("a" * 400) == 100


def test_chunk_markdown_headings(chunker):
    content = "# Title\n\nFirst section content.\n\n## Subtitle\n\nSecond section content."
    chunks = chunker.chunk(content, DocumentType.MARKDOWN)
    assert len(chunks) >= 1
    assert all(c.chunk_type == "paragraph" for c in chunks)


def test_chunk_markdown_respects_max_tokens(chunker):
    content = "\n\n".join([f"Paragraph {i}: {'word ' * 20}" for i in range(20)])
    chunks = chunker.chunk(content, DocumentType.MARKDOWN)
    for c in chunks:
        assert c.token_count <= 250


def test_chunk_code_by_function(chunker):
    content = "def foo():\n    pass\n\ndef bar():\n    pass\n"
    chunks = chunker.chunk(content, DocumentType.CODE, file_path="test.py")
    assert len(chunks) >= 1
    assert all(c.chunk_type == "code_block" for c in chunks)


def test_chunk_text_paragraphs(chunker):
    content = "First paragraph.\n\nSecond paragraph.\n\nThird paragraph."
    chunks = chunker.chunk(content, DocumentType.TEXT)
    assert len(chunks) >= 1


def test_chunk_notebook(chunker):
    import json

    nb = {
        "cells": [
            {"cell_type": "markdown", "source": ["# Title"]},
            {"cell_type": "code", "source": ["print('hello')"]},
        ]
    }
    chunks = chunker.chunk(json.dumps(nb), DocumentType.NOTEBOOK)
    assert len(chunks) == 2
    assert chunks[0].chunk_type == "paragraph"
    assert chunks[1].chunk_type == "code_block"


def test_chunk_notebook_invalid_json(chunker):
    chunks = chunker.chunk("not json", DocumentType.NOTEBOOK)
    assert len(chunks) >= 1


def test_context_enrichment(chunker):
    content = "First paragraph.\n\nSecond paragraph.\n\nThird paragraph."
    chunks = chunker.chunk(content, DocumentType.TEXT)
    if len(chunks) >= 2:
        assert chunks[1].context_before is not None
    if len(chunks) >= 3:
        assert chunks[1].context_after is not None


def test_empty_content(chunker):
    chunks = chunker.chunk("", DocumentType.TEXT)
    assert len(chunks) == 0


def test_chunk_offsets(chunker):
    content = "First paragraph.\n\nSecond paragraph."
    chunks = chunker.chunk(content, DocumentType.TEXT)
    for c in chunks:
        assert c.start_offset >= 0
        assert c.end_offset > c.start_offset
