"""Tests for document parsers."""

import json
import os
import tempfile

from backend.app.services.intelligence.parsers.base import ParsedDocument, ParsedSection
from backend.app.services.intelligence.parsers.markdown_parser import MarkdownParser
from backend.app.services.intelligence.parsers.notebook_parser import NotebookParser
from backend.app.services.intelligence.parsers.pdf_parser import PDFParser


def test_parsed_document_full_text():
    doc = ParsedDocument(
        sections=[
            ParsedSection(content="Hello"),
            ParsedSection(content="World"),
        ]
    )
    assert doc.full_text == "Hello\n\nWorld"


def test_parsed_document_empty():
    doc = ParsedDocument()
    assert doc.full_text == ""


class TestPDFParser:
    def test_parse_nonexistent(self):
        parser = PDFParser()
        result = parser.parse("/nonexistent/file.pdf")
        assert result.sections == []

    def test_parse_invalid_pdf(self):
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            f.write(b"not a pdf")
            f.flush()
            parser = PDFParser()
            result = parser.parse(f.name)
        os.unlink(f.name)
        assert result.sections == []

    def test_format_table(self):
        table = [["Name", "Age"], ["Alice", "30"], ["Bob", "25"]]
        result = PDFParser._format_table(table)
        assert "Name | Age" in result
        assert "Alice | 30" in result

    def test_format_table_empty(self):
        assert PDFParser._format_table([]) == ""
        assert PDFParser._format_table([[]]) == ""


class TestMarkdownParser:
    def test_parse_headings(self):
        parser = MarkdownParser()
        content = "# Title\n\nParagraph one.\n\n## Subtitle\n\nParagraph two."
        result = parser.parse_string(content)
        assert len(result.sections) >= 2
        headings = [s for s in result.sections if s.section_type == "heading"]
        assert len(headings) >= 2

    def test_parse_code_blocks(self):
        parser = MarkdownParser()
        content = "# Doc\n\nSome text.\n\n```python\nprint('hello')\n```\n\nMore text."
        result = parser.parse_string(content)
        code_blocks = [s for s in result.sections if s.section_type == "code"]
        assert len(code_blocks) >= 1

    def test_parse_tables(self):
        parser = MarkdownParser()
        content = "# Doc\n\n| Col1 | Col2 |\n| --- | --- |\n| A | B |"
        result = parser.parse_string(content)
        tables = [s for s in result.sections if s.section_type == "table"]
        assert len(tables) >= 1

    def test_parse_empty(self):
        parser = MarkdownParser()
        result = parser.parse_string("")
        assert len(result.sections) == 0

    def test_full_text(self):
        parser = MarkdownParser()
        content = "# Title\n\nHello world."
        result = parser.parse_string(content)
        assert "Hello world" in result.full_text


class TestNotebookParser:
    def test_parse_code_cells(self):
        parser = NotebookParser()
        nb = {
            "cells": [
                {"cell_type": "code", "source": ["print('hello')"]},
                {"cell_type": "markdown", "source": ["# Title"]},
            ]
        }
        result = parser.parse_string(json.dumps(nb))
        assert len(result.sections) == 2
        assert result.sections[0].section_type == "code"
        assert result.sections[1].section_type == "heading"

    def test_parse_empty_notebook(self):
        parser = NotebookParser()
        result = parser.parse_string(json.dumps({"cells": []}))
        assert len(result.sections) == 0

    def test_parse_invalid_json(self):
        parser = NotebookParser()
        result = parser.parse_string("not json")
        assert len(result.sections) == 0

    def test_metadata(self):
        parser = NotebookParser()
        nb = {"cells": [], "metadata": {"kernelspec": {"display_name": "Python 3"}}}
        result = parser.parse_string(json.dumps(nb))
        assert "kernelspec" in result.metadata

    def test_parse_file(self):
        parser = NotebookParser()
        nb = {"cells": [{"cell_type": "code", "source": ["x = 1"]}]}
        with tempfile.NamedTemporaryFile(mode="w", suffix=".ipynb", delete=False) as f:
            json.dump(nb, f)
            f.flush()
            result = parser.parse(f.name)
        os.unlink(f.name)
        assert len(result.sections) == 1
