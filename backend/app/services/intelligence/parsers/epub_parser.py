"""EPUB eBook parser using ebooklib."""

from __future__ import annotations

import logging

from backend.app.services.intelligence.parsers.base import BaseParser, ParsedDocument, ParsedSection

logger = logging.getLogger(__name__)


class EPUBParser(BaseParser):
    """Extract text from EPUB eBook files using ebooklib."""

    def parse(self, file_path: str) -> ParsedDocument:
        try:
            import epub  # type: ignore[import-not-found]
        except ImportError:
            logger.warning("ebooklib not installed — run: pip install ebooklib")
            return ParsedDocument(metadata={"error": "ebooklib not installed"})

        try:
            from bs4 import BeautifulSoup
        except ImportError:
            logger.warning("beautifulsoup4 not installed — run: pip install beautifulsoup4")
            return ParsedDocument(metadata={"error": "beautifulsoup4 not installed"})

        sections: list[ParsedSection] = []
        metadata: dict = {}

        try:
            book = epub.read_epub(file_path)

            dc_metadata = book.get_metadata("DC", {})
            if dc_metadata:
                title = dc_metadata.get("title", "")
                if title:
                    metadata["title"] = title[0] if isinstance(title, list) else title
                creator = dc_metadata.get("creator", "")
                if creator:
                    metadata["author"] = creator[0] if isinstance(creator, list) else creator
                language = dc_metadata.get("language", "")
                if language:
                    metadata["language"] = language[0] if isinstance(language, list) else language
                description = dc_metadata.get("description", "")
                if description:
                    metadata["description"] = description[0] if isinstance(description, list) else description

            spine_items = [item_id for item_id, _ in book.spine]
            items_by_id = {item.get_id(): item for item in book.get_items()}

            for item_id in spine_items:
                item = items_by_id.get(item_id)
                if item is None:
                    continue

                if item.get_type() != 9:  # ITEM_DOCUMENT
                    continue

                content = item.get_content()
                if not content:
                    continue

                soup = BeautifulSoup(content, "html.parser")

                for tag in soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"]):
                    tag.decompose()

                text = soup.get_text(separator="\n", strip=True)
                if not text.strip():
                    continue

                title_tag = soup.title
                section_title = title_tag.string.strip() if title_tag and title_tag.string else None

                sections.append(
                    ParsedSection(
                        content=text.strip(),
                        section_type="paragraph",
                        title=section_title,
                    )
                )

        except Exception as e:
            logger.warning("Failed to parse EPUB %s: %s", file_path, e)
            return ParsedDocument(metadata={"error": str(e)})

        total_chars = sum(len(s.content) for s in sections)
        return ParsedDocument(sections=sections, metadata=metadata, total_chars=total_chars)
