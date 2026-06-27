"""Document parsers for different file formats."""

from backend.app.services.parsers.archive_parser import ArchiveParser
from backend.app.services.parsers.base import BaseParser, ParsedDocument, ParsedSection
from backend.app.services.parsers.docx_parser import DocxParser
from backend.app.services.parsers.epub_parser import EPUBParser
from backend.app.services.parsers.font_parser import FontParser
from backend.app.services.parsers.gis_parser import GISParser
from backend.app.services.parsers.html_parser import HTMLParser
from backend.app.services.parsers.ical_parser import ICalParser
from backend.app.services.parsers.markdown_parser import MarkdownParser
from backend.app.services.parsers.media_parser import MediaParser
from backend.app.services.parsers.notebook_parser import NotebookParser
from backend.app.services.parsers.opendocument_parser import OpenDocumentParser
from backend.app.services.parsers.pdf_parser import PDFParser
from backend.app.services.parsers.pptx_parser import PptxParser
from backend.app.services.parsers.vcard_parser import VCardParser
from backend.app.services.parsers.xlsx_parser import XlsxParser

__all__ = [
    "ArchiveParser",
    "BaseParser",
    "FontParser",
    "GISParser",
    "ICalParser",
    "MediaParser",
    "OpenDocumentParser",
    "ParsedDocument",
    "ParsedSection",
    "DocxParser",
    "EPUBParser",
    "HTMLParser",
    "MarkdownParser",
    "NotebookParser",
    "PDFParser",
    "PptxParser",
    "VCardParser",
    "XlsxParser",
]
