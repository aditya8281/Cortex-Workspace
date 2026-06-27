"""HTML/XML document parser using lxml."""

from __future__ import annotations

import logging
import os

from backend.app.services.intelligence.parsers.base import BaseParser, ParsedDocument, ParsedSection

logger = logging.getLogger(__name__)

HEADING_TAGS = {"h1", "h2", "h3", "h4", "h5", "h6"}
BLOCK_TAGS = {"p", "div", "article", "section", "header", "footer", "main", "aside", "nav"}
LIST_TAGS = {"ul", "ol", "dl"}
TABLE_TAGS = {"table", "thead", "tbody", "tfoot", "tr", "td", "th"}
INLINE_SKIP = {"script", "style", "noscript", "svg", "math"}


class HTMLParser(BaseParser):
    """Parse HTML and XML files into structured sections using lxml."""

    def parse(self, file_path: str) -> ParsedDocument:
        try:
            from lxml import etree  # type: ignore[import-untyped]
        except ImportError:
            logger.warning("lxml not installed — run: pip install lxml")
            return ParsedDocument(metadata={"error": "lxml not installed"})

        sections: list[ParsedSection] = []
        metadata: dict = {}

        try:
            with open(file_path, "rb") as f:
                raw = f.read()

            ext = os.path.splitext(file_path)[1].lower()
            is_xml = ext in (".xml", ".xhtml", ".xht")

            if is_xml:
                try:
                    tree = etree.HTML(raw)
                except etree.XMLSyntaxError:
                    try:
                        tree = etree.fromstring(raw)
                    except etree.XMLSyntaxError:
                        return ParsedDocument(metadata={"error": "Invalid XML"})
                    if tree is None:
                        return ParsedDocument()
                    root = tree
                    _walk_xml_element(root, sections)
                    total_chars = sum(len(s.content) for s in sections)
                    return ParsedDocument(sections=sections, metadata=metadata, total_chars=total_chars)
            else:
                try:
                    tree = etree.HTML(raw)
                except Exception:
                    return ParsedDocument(metadata={"error": "Invalid HTML"})

                if tree is None:
                    return ParsedDocument()

                head = tree.find(".//head")
                if head is not None:
                    title_el = head.find(".//title")
                    if title_el is not None and title_el.text:
                        metadata["title"] = title_el.text.strip()

                for tag in INLINE_SKIP:
                    for el in tree.iter(tag):
                        el.getparent().remove(el)

                body = tree.find(".//body") or tree
                _walk_lxml_tree(body, sections)

        except Exception as e:
            logger.warning("Failed to parse HTML/XML %s: %s", file_path, e)
            return ParsedDocument(metadata={"error": str(e)})

        total_chars = sum(len(s.content) for s in sections)
        return ParsedDocument(sections=sections, metadata=metadata, total_chars=total_chars)


def _walk_lxml_tree(element, sections: list[ParsedSection]) -> None:
    """Walk an lxml element tree and extract sections."""
    from lxml import etree  # type: ignore[import-untyped]

    for child in element:
        tag = etree.QName(child.tag).localname if isinstance(child.tag, str) else None
        if tag is None or tag in ("head", "script", "style", "noscript"):
            continue

        if tag in HEADING_TAGS:
            text = _get_text_content(child)
            if text:
                level = int(tag[1])
                sections.append(
                    ParsedSection(
                        title=text,
                        content=text,
                        section_type="heading",
                        level=level,
                    )
                )
            continue

        if tag == "table":
            table_text = _extract_table(child)
            if table_text.strip():
                sections.append(
                    ParsedSection(
                        content=table_text,
                        section_type="table",
                    )
                )
            continue

        if tag in LIST_TAGS:
            items = []
            for li in child.iter("li"):
                li_text = _get_text_content(li)
                if li_text:
                    items.append(li_text)
            if items:
                list_type = "list"
                sections.append(
                    ParsedSection(
                        content="\n".join(items),
                        section_type=list_type,
                    )
                )
            continue

        if tag in BLOCK_TAGS or tag in ("blockquote", "pre", "figcaption", "caption"):
            text = _get_text_content(child)
            if text:
                section_type = "code" if tag == "pre" else "paragraph"
                sections.append(
                    ParsedSection(
                        content=text,
                        section_type=section_type,
                    )
                )
            continue

        if child.getchildren():
            _walk_lxml_tree(child, sections)
        else:
            text = _get_text_content(child)
            if text:
                sections.append(
                    ParsedSection(
                        content=text,
                        section_type="paragraph",
                    )
                )


def _walk_xml_element(element, sections: list[ParsedSection]) -> None:
    """Walk a raw XML element tree (non-HTML) and extract text sections."""
    from lxml import etree  # type: ignore[import-untyped]

    if element.text and element.text.strip():
        sections.append(
            ParsedSection(
                content=element.text.strip(),
                section_type="paragraph",
            )
        )

    for child in element:
        tag = etree.QName(child.tag).localname if isinstance(child.tag, str) else str(child.tag)

        if tag in HEADING_TAGS:
            text = _get_text_content(child)
            if text:
                level = int(tag[1]) if tag[1].isdigit() else 1
                sections.append(
                    ParsedSection(
                        title=text,
                        content=text,
                        section_type="heading",
                        level=level,
                    )
                )
        else:
            _walk_xml_element(child, sections)

        if child.tail and child.tail.strip():
            sections.append(
                ParsedSection(
                    content=child.tail.strip(),
                    section_type="paragraph",
                )
            )


def _get_text_content(element) -> str:
    """Recursively get all text content from an element, skipping unwanted tags."""
    from lxml import etree  # type: ignore[import-untyped]

    parts = []
    if element.text:
        parts.append(element.text.strip())

    for child in element:
        tag = etree.QName(child.tag).localname if isinstance(child.tag, str) else None
        if tag in ("script", "style", "noscript"):
            continue
        child_text = _get_text_content(child)
        if child_text:
            parts.append(child_text)
        if child.tail:
            parts.append(child.tail.strip())

    return " ".join(part for part in parts if part)


def _extract_table(table_element) -> str:
    """Extract text from an HTML table as a readable text table."""
    rows = []
    for tr in table_element.iter("tr"):
        cells = []
        for td in tr.iter("td", "th"):
            text = _get_text_content(td)
            cells.append(text)
        if cells:
            rows.append(cells)

    if not rows:
        return ""

    header = rows[0]
    data_rows = rows[1:]

    lines = []
    header_line = " | ".join(str(h) for h in header)
    separator = " | ".join(["---"] * len(header))
    lines.append(header_line)
    lines.append(separator)
    for row in data_rows:
        padded = row + [""] * (len(header) - len(row))
        lines.append(" | ".join(str(c) for c in padded[: len(header)]))

    return "\n".join(lines)
