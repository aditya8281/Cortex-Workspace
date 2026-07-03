"""Base parser interface for document parsing."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class ParsedSection:
    title: str | None = None
    content: str = ""
    section_type: str = "paragraph"  # "heading", "paragraph", "table", "code", "list"
    level: int = 0  # heading level (1-6)


@dataclass
class ParsedDocument:
    sections: list[ParsedSection] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    total_chars: int = 0

    @property
    def full_text(self) -> str:
        return "\n\n".join(s.content for s in self.sections if s.content)


class BaseParser(ABC):
    """Base class for document parsers."""

    @abstractmethod
    def parse(self, file_path: str) -> ParsedDocument:
        """Parse a document and return structured sections."""
