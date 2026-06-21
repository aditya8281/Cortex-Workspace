"""Parser for iCalendar files (.ics)."""

from __future__ import annotations

import logging
import re
from datetime import datetime
from pathlib import Path

from backend.app.services.parsers.base import BaseParser, ParsedDocument, ParsedSection

logger = logging.getLogger(__name__)


def _parse_ical_datetime(value: str) -> str:
    """Parse an iCalendar datetime string into a readable format."""
    value = value.strip()

    if value.endswith("Z"):
        value = value[:-1]

    formats = [
        "%Y%m%dT%H%M%S",
        "%Y%m%d",
    ]
    for fmt in formats:
        try:
            dt = datetime.strptime(value, fmt)
            if fmt == "%Y%m%d":
                return dt.strftime("%Y-%m-%d")
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            continue

    return value


def _unescape_text(text: str) -> str:
    """Unescape iCalendar text values."""
    text = text.replace("\\n", "\n").replace("\\N", "\n")
    text = text.replace("\\,", ",").replace("\\;", ";")
    text = text.replace("\\\\", "\\")
    return text


def _parse_vevent(lines: list[str]) -> dict:
    """Parse VEVENT component lines into a dict."""
    props: dict = {}

    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line or line.upper().startswith("END:"):
            i += 1
            continue

        match = re.match(r"^([^;:]+)(?:;([^:]*))?(:(.*))?$", line)
        if not match:
            i += 1
            continue

        prop_name = match.group(1).strip().upper()
        params_str = match.group(2) or ""
        value = (match.group(4) or "").strip()

        if not value and line.endswith(":"):
            i += 1
            continue

        i += 1

        if prop_name in ("SUMMARY", "DESCRIPTION", "LOCATION", "CATEGORIES", "STATUS", "UID", "URL"):
            props[prop_name.lower()] = _unescape_text(value)

        elif prop_name in ("DTSTART", "DTEND", "DTSTAMP", "CREATED", "LAST-MODIFIED"):
            params_lower = params_str.lower()
            if "date" in params_lower:
                props[prop_name.lower()] = _parse_ical_datetime(value)
            else:
                props[prop_name.lower()] = _parse_ical_datetime(value)

        elif prop_name == "RRULE":
            props["recurrence"] = value

    return props


def _format_event(event: dict) -> str:
    """Format a parsed event dict into readable text."""
    lines: list[str] = []

    summary = event.get("summary", "Untitled Event")
    lines.append(f"Event: {summary}")

    if event.get("dtstart"):
        lines.append(f"Start: {event['dtstart']}")
    if event.get("dtend"):
        lines.append(f"End: {event['dtend']}")
    if event.get("location"):
        lines.append(f"Location: {event['location']}")
    if event.get("description"):
        desc = event["description"]
        if len(desc) > 500:
            desc = desc[:500] + "..."
        lines.append(f"Description: {desc}")
    if event.get("status"):
        lines.append(f"Status: {event['status']}")
    if event.get("categories"):
        lines.append(f"Categories: {event['categories']}")
    if event.get("url"):
        lines.append(f"URL: {event['url']}")
    if event.get("recurrence"):
        lines.append(f"Recurrence: {event['recurrence']}")
    if event.get("uid"):
        lines.append(f"UID: {event['uid']}")

    return "\n".join(lines)


class ICalParser(BaseParser):
    """Parser for iCalendar files (.ics)."""

    def parse(self, file_path: str) -> ParsedDocument:
        try:
            with open(file_path, encoding="utf-8", errors="replace") as f:
                content = f.read()
        except Exception as e:
            return ParsedDocument(
                sections=[ParsedSection(content=f"Error reading iCalendar file: {e}")],
                total_chars=0,
            )

        sections: list[ParsedSection] = []
        total_chars = 0

        block_pattern = re.compile(
            r"(?i)BEGIN:(VEVENT|VTODO|VJOURNAL|VFREEBUSY|VALARM)\s*\n(.*?)\s*END:\1",
            re.DOTALL,
        )

        for match in block_pattern.finditer(content):
            comp_type = match.group(1).upper()
            comp_lines = match.group(2).splitlines()

            if comp_type == "VEVENT":
                event = _parse_vevent(comp_lines)
                formatted = _format_event(event)
                title = event.get("summary", "Event")
            elif comp_type == "VTODO":
                event = _parse_vevent(comp_lines)
                formatted = f"TODO: {event.get('summary', 'Untitled')}\n"
                if event.get("dtstart"):
                    formatted += f"Start: {event['dtstart']}\n"
                if event.get("status"):
                    formatted += f"Status: {event['status']}\n"
                if event.get("description"):
                    formatted += f"Description: {event['description']}\n"
                title = f"TODO: {event.get('summary', 'Untitled')}"
            elif comp_type == "VJOURNAL":
                event = _parse_vevent(comp_lines)
                formatted = f"Journal: {event.get('summary', 'Untitled')}\n"
                if event.get("dtstart"):
                    formatted += f"Date: {event['dtstart']}\n"
                if event.get("description"):
                    formatted += f"Description: {event['description']}\n"
                title = f"Journal: {event.get('summary', 'Untitled')}"
            else:
                event = _parse_vevent(comp_lines)
                formatted = f"{comp_type}: {event.get('summary', 'Untitled')}"
                title = f"{comp_type}: {event.get('summary', 'Untitled')}"

            total_chars += len(formatted)
            sections.append(
                ParsedSection(
                    title=title,
                    content=formatted,
                    section_type="paragraph",
                )
            )

        if not sections:
            sections.append(
                ParsedSection(
                    title=Path(file_path).name,
                    content=content[:2000] if len(content) > 2000 else content,
                    section_type="paragraph",
                )
            )
            total_chars = len(sections[0].content)

        return ParsedDocument(
            sections=sections,
            metadata={
                "format": "ICS",
                "component_count": len(sections),
            },
            total_chars=total_chars,
        )
