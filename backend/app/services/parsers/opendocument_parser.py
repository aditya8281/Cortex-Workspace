"""Parser for OpenDocument files (.odt, .ods, .odp)."""

from __future__ import annotations

import logging
from pathlib import Path

from backend.app.services.parsers.base import BaseParser, ParsedDocument, ParsedSection

logger = logging.getLogger(__name__)


def _extract_odt_content(file_path: str) -> ParsedDocument:
    """Extract text from ODF text documents (.odt)."""
    try:
        import odf.text
        from odf import teletype
        from odf.opendocument import load

        doc = load(file_path)
        paragraphs = doc.getElementsByType(odf.text.P)
        lines: list[str] = []
        for p in paragraphs:
            text = teletype.extractText(p)
            if text and text.strip():
                lines.append(text)

        content = "\n".join(lines)
        sections = (
            [
                ParsedSection(
                    title=Path(file_path).name,
                    content=content,
                    section_type="paragraph",
                )
            ]
            if content
            else []
        )

        return ParsedDocument(
            sections=sections,
            metadata={"format": "ODT", "paragraph_count": len(paragraphs)},
            total_chars=len(content),
        )
    except ImportError:
        return ParsedDocument(
            sections=[ParsedSection(content="odfpy not installed — cannot parse .odt files")],
            total_chars=0,
        )
    except Exception as e:
        return ParsedDocument(
            sections=[ParsedSection(content=f"Error parsing ODT file: {e}")],
            total_chars=0,
        )


def _extract_ods_content(file_path: str) -> ParsedDocument:
    """Extract tables from ODF spreadsheet documents (.ods)."""
    try:
        from odf.opendocument import load
        from odf.table import Table, TableCell, TableRow
        from odf.text import P

        doc = load(file_path)
        tables = doc.getElementsByType(Table)
        sections: list[ParsedSection] = []
        total_chars = 0

        for table in tables:
            table_name = table.getAttribute("name") or "Unnamed"
            rows = table.getElementsByType(TableRow)
            table_lines: list[str] = []
            table_lines.append(f"Table: {table_name}")
            table_lines.append(f"Rows: {len(rows)}")
            table_lines.append("")

            for row in rows:
                cells = row.getElementsByType(TableCell)
                cell_texts: list[str] = []
                for cell in cells:
                    repeat = cell.getAttribute("numbercolumnsrepeated")
                    paragraphs = cell.getElementsByType(P)
                    cell_text = (
                        " ".join(
                            p.firstChild.data if p.firstChild and hasattr(p.firstChild, "data") else ""
                            for p in paragraphs
                        ).strip()
                        if paragraphs
                        else ""
                    )

                    if repeat and cell_text:
                        count = int(repeat) if repeat.isdigit() else 1
                        cell_texts.extend([cell_text] * min(count, 100))
                    elif cell_text:
                        cell_texts.append(cell_text)
                    elif repeat:
                        count = int(repeat) if repeat.isdigit() else 1
                        cell_texts.extend([""] * min(count, 100))

                if cell_texts:
                    table_lines.append("\t".join(cell_texts))

            table_content = "\n".join(table_lines)
            total_chars += len(table_content)
            sections.append(
                ParsedSection(
                    title=f"Table: {table_name}",
                    content=table_content,
                    section_type="table",
                )
            )

        return ParsedDocument(
            sections=sections,
            metadata={"format": "ODS", "table_count": len(tables)},
            total_chars=total_chars,
        )
    except ImportError:
        return ParsedDocument(
            sections=[ParsedSection(content="odfpy not installed — cannot parse .ods files")],
            total_chars=0,
        )
    except Exception as e:
        return ParsedDocument(
            sections=[ParsedSection(content=f"Error parsing ODS file: {e}")],
            total_chars=0,
        )


def _extract_odp_content(file_path: str) -> ParsedDocument:
    """Extract text from ODF presentation documents (.odp)."""
    try:
        from odf import teletype
        from odf.opendocument import load
        from odf.text import P

        doc = load(file_path)
        paragraphs = doc.getElementsByType(P)
        lines: list[str] = []
        for p in paragraphs:
            text = teletype.extractText(p)
            if text and text.strip():
                lines.append(text)

        content = "\n".join(lines)
        sections = (
            [
                ParsedSection(
                    title=Path(file_path).name,
                    content=content,
                    section_type="paragraph",
                )
            ]
            if content
            else []
        )

        return ParsedDocument(
            sections=sections,
            metadata={"format": "ODP", "paragraph_count": len(paragraphs)},
            total_chars=len(content),
        )
    except ImportError:
        return ParsedDocument(
            sections=[ParsedSection(content="odfpy not installed — cannot parse .odp files")],
            total_chars=0,
        )
    except Exception as e:
        return ParsedDocument(
            sections=[ParsedSection(content=f"Error parsing ODP file: {e}")],
            total_chars=0,
        )


class OpenDocumentParser(BaseParser):
    """Parser for OpenDocument files (.odt, .ods, .odp)."""

    def parse(self, file_path: str) -> ParsedDocument:
        ext = Path(file_path).suffix.lower()
        if ext == ".odt":
            return _extract_odt_content(file_path)
        elif ext == ".ods":
            return _extract_ods_content(file_path)
        elif ext == ".odp":
            return _extract_odp_content(file_path)
        else:
            return ParsedDocument(
                sections=[ParsedSection(content=f"Unsupported OpenDocument format: {ext}")],
                total_chars=0,
            )
