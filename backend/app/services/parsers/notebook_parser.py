"""Jupyter Notebook (.ipynb) parser."""

from __future__ import annotations

import json

from backend.app.services.parsers.base import BaseParser, ParsedDocument, ParsedSection


class NotebookParser(BaseParser):
    """Parse Jupyter Notebook .ipynb files into sections."""

    def parse(self, file_path: str) -> ParsedDocument:
        with open(file_path) as f:
            content = f.read()
        return self.parse_string(content)

    def parse_string(self, content: str) -> ParsedDocument:
        try:
            nb = json.loads(content)
        except (json.JSONDecodeError, TypeError):
            return ParsedDocument()

        cells = nb.get("cells", [])
        if not cells:
            metadata = nb.get("metadata", {})
            return ParsedDocument(metadata=metadata)

        sections: list[ParsedSection] = []
        for cell in cells:
            cell_type = cell.get("cell_type", "")
            source = "".join(cell.get("source", []))

            if not source.strip():
                continue

            if cell_type == "code":
                sections.append(ParsedSection(
                    content=source.strip(),
                    section_type="code",
                ))
            elif cell_type == "markdown":
                first_line = source.strip().split("\n")[0]
                heading_match = None
                if first_line.startswith("#"):
                    import re
                    heading_match = re.match(r"^(#{1,6})\s+(.+)", first_line)

                if heading_match:
                    level = len(heading_match.group(1))
                    sections.append(ParsedSection(
                        title=heading_match.group(2).strip(),
                        content=source.strip(),
                        section_type="heading",
                        level=level,
                    ))
                else:
                    sections.append(ParsedSection(
                        content=source.strip(),
                        section_type="paragraph",
                    ))
            elif cell_type == "raw":
                sections.append(ParsedSection(
                    content=source.strip(),
                    section_type="paragraph",
                ))

        metadata = nb.get("metadata", {})
        total_chars = sum(len(s.content) for s in sections)
        return ParsedDocument(sections=sections, metadata=metadata, total_chars=total_chars)
