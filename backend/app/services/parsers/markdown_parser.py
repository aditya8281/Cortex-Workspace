"""Markdown document parser."""

from __future__ import annotations

import re

from backend.app.services.parsers.base import BaseParser, ParsedDocument, ParsedSection


class MarkdownParser(BaseParser):
    """Parse Markdown files into sections by splitting on headings, code blocks, tables, and lists."""

    def parse(self, file_path: str) -> ParsedDocument:
        with open(file_path) as f:
            content = f.read()
        return self.parse_string(content)

    def parse_string(self, content: str) -> ParsedDocument:
        if not content.strip():
            return ParsedDocument()

        sections: list[ParsedSection] = []
        lines = content.split("\n")
        i = 0

        while i < len(lines):
            line = lines[i]

            # Code block
            if line.strip().startswith("```"):
                lang_match = re.match(r"```(\w*)", line.strip())
                lang = lang_match.group(1) if lang_match else ""
                code_lines = []
                i += 1
                while i < len(lines) and not lines[i].strip().startswith("```"):
                    code_lines.append(lines[i])
                    i += 1
                i += 1  # skip closing ```
                sections.append(
                    ParsedSection(
                        content="\n".join(code_lines),
                        section_type="code",
                        title=lang or None,
                    )
                )
                continue

            # Heading
            heading_match = re.match(r"^(#{1,6})\s+(.+)", line)
            if heading_match:
                level = len(heading_match.group(1))
                title = heading_match.group(2).strip()
                sections.append(
                    ParsedSection(
                        title=title,
                        content=title,
                        section_type="heading",
                        level=level,
                    )
                )
                i += 1
                continue

            # Table (line starting with |)
            if line.strip().startswith("|"):
                table_lines = []
                while i < len(lines) and lines[i].strip().startswith("|"):
                    table_lines.append(lines[i].strip())
                    i += 1
                # Remove separator line if present
                if len(table_lines) > 1 and re.match(r"^\|[\s\-:|]+\|$", table_lines[1]):
                    table_lines.pop(1)
                sections.append(
                    ParsedSection(
                        content="\n".join(table_lines),
                        section_type="table",
                    )
                )
                continue

            # List items
            if re.match(r"^\s*[-*+]\s+", line) or re.match(r"^\s*\d+\.\s+", line):
                list_lines = []
                while i < len(lines) and (re.match(r"^\s*[-*+]\s+", lines[i]) or re.match(r"^\s*\d+\.\s+", lines[i])):
                    list_lines.append(lines[i].strip())
                    i += 1
                sections.append(
                    ParsedSection(
                        content="\n".join(list_lines),
                        section_type="list",
                    )
                )
                continue

            # Paragraph (non-empty lines)
            if line.strip():
                para_lines = []
                while (
                    i < len(lines)
                    and lines[i].strip()
                    and not lines[i].strip().startswith("#")
                    and not lines[i].strip().startswith("```")
                    and not lines[i].strip().startswith("|")
                    and not re.match(r"^\s*[-*+]\s+", lines[i])
                    and not re.match(r"^\s*\d+\.\s+", lines[i])
                ):
                    para_lines.append(lines[i].strip())
                    i += 1
                sections.append(
                    ParsedSection(
                        content=" ".join(para_lines),
                        section_type="paragraph",
                    )
                )
                continue

            i += 1

        total_chars = sum(len(s.content) for s in sections)
        return ParsedDocument(sections=sections, total_chars=total_chars)
