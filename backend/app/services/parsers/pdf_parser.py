"""PDF text extraction using pdfplumber."""

from __future__ import annotations

import logging

from backend.app.services.parsers.base import BaseParser, ParsedDocument, ParsedSection

logger = logging.getLogger(__name__)


class PDFParser(BaseParser):
    """Extract text and tables from PDF files using pdfplumber."""

    def parse(self, file_path: str) -> ParsedDocument:
        try:
            import pdfplumber
        except ImportError:
            logger.warning("pdfplumber not installed — run: pip install pdfplumber")
            return ParsedDocument(metadata={"error": "pdfplumber not installed"})

        sections = []
        metadata = {}

        try:
            with pdfplumber.open(file_path) as pdf:
                metadata["page_count"] = len(pdf.pages)
                metadata["title"] = pdf.metadata.get("Title", "") if pdf.metadata else ""

                for i, page in enumerate(pdf.pages):
                    text = page.extract_text() or ""
                    if text.strip():
                        sections.append(ParsedSection(
                            content=text.strip(),
                            section_type="paragraph",
                            title=f"Page {i + 1}",
                        ))

                    tables = page.extract_tables()
                    for table in tables:
                        if table:
                            table_text = self._format_table(table)
                            if table_text.strip():
                                sections.append(ParsedSection(
                                    content=table_text,
                                    section_type="table",
                                ))

        except Exception as e:
            logger.warning("Failed to parse PDF %s: %s", file_path, e)
            return ParsedDocument(metadata={"error": str(e)})

        total_chars = sum(len(s.content) for s in sections)
        return ParsedDocument(sections=sections, metadata=metadata, total_chars=total_chars)

    @staticmethod
    def _format_table(table: list[list]) -> str:
        if not table or not table[0]:
            return ""
        headers = [str(h or "") for h in table[0]]
        rows = []
        for row in table[1:]:
            cells = [str(c or "") for c in row]
            rows.append(" | ".join(cells))
        header_line = " | ".join(headers)
        separator = " | ".join(["---"] * len(headers))
        return "\n".join([header_line, separator] + rows)
