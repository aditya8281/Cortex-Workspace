"""Parser for vCard files (.vcf)."""

from __future__ import annotations

import logging
import re
from pathlib import Path

from backend.app.services.parsers.base import BaseParser, ParsedDocument, ParsedSection

logger = logging.getLogger(__name__)


def _folded_lines(text: str) -> list[str]:
    """Unfold continuation lines (RFC 6350: lines starting with space/tab)."""
    lines = text.splitlines()
    unfolded: list[str] = []
    for line in lines:
        if line and line[0] in (" ", "\t") and unfolded:
            unfolded[-1] += line[1:]
        else:
            unfolded.append(line)
    return unfolded


def _parse_vcard(text: str) -> dict[str, str | list[str]]:
    """Parse a single vCard block into a dict."""
    result: dict[str, str | list[str]] = {}

    for line in _folded_lines(text):
        if not line or line.startswith("BEGIN") or line.startswith("END"):
            continue

        match = re.match(r"^([^;:]+)(?:;([^:]*))?:(.*)$", line)
        if not match:
            continue

        prop_name = match.group(1).strip().upper()
        params = match.group(2) or ""
        value = match.group(3).strip()

        if not value:
            continue

        if prop_name in ("N", "FN"):
            if prop_name == "N":
                parts = [p.strip() for p in value.split(";")]
                parts = [p for p in parts if p]
                result["name"] = " ".join(parts) if parts else value
            else:
                result["full_name"] = value
        elif prop_name == "TEL":
            params_lower = params.lower()
            tel_type = "work" if "work" in params_lower else ("home" if "home" in params_lower else "other")
            key = f"phone_{tel_type}"
            if key in result:
                existing = result[key]
                if isinstance(existing, list):
                    existing.append(value)
                else:
                    result[key] = [existing, value]
            else:
                result[key] = value
        elif prop_name == "EMAIL":
            params_lower = params.lower()
            email_type = "work" if "work" in params_lower else ("home" if "home" in params_lower else "other")
            key = f"email_{email_type}"
            if key in result:
                existing = result[key]
                if isinstance(existing, list):
                    existing.append(value)
                else:
                    result[key] = [existing, value]
            else:
                result[key] = value
        elif prop_name == "ADR":
            parts = [p.strip() for p in value.split(";")]
            parts = [p for p in parts if p]
            result["address"] = ", ".join(parts)
        elif prop_name == "ORG":
            parts = [p.strip() for p in value.split(";")]
            parts = [p for p in parts if p]
            result["organization"] = " - ".join(parts)
        elif prop_name == "TITLE":
            result["title"] = value
        elif prop_name == "NOTE":
            if "notes" in result:
                result["notes"] = result["notes"] + "\n" + value
            else:
                result["notes"] = value
        elif prop_name == "URL":
            result["url"] = value
        elif prop_name == "BDAY":
            result["birthday"] = value
        elif prop_name == "NICKNAME":
            result["nickname"] = value
        elif prop_name in ("PREFIX", "SUFFIX", "ROLE", "GEO", "IMPP", "X-SOCIALPROFILE"):
            key = prop_name.lower().replace("-", "_")
            if key in result:
                if isinstance(result[key], list):
                    result[key].append(value)
                else:
                    result[key] = [result[key], value]
            else:
                result[key] = value

    return result


def _format_contact(contact: dict[str, str | list[str]]) -> str:
    """Format a parsed contact dict into readable text."""
    lines: list[str] = []

    name = contact.get("full_name") or contact.get("name", "Unknown")
    lines.append(f"Name: {name}")

    for key in ("nickname", "title", "organization", "address", "birthday", "url", "notes"):
        val = contact.get(key)
        if val:
            if isinstance(val, list):
                val = ", ".join(str(v) for v in val)
            lines.append(f"{key.replace('_', ' ').title()}: {val}")

    phone_keys = sorted(k for k in contact if k.startswith("phone_"))
    if phone_keys:
        lines.append("Phone(s):")
        for pk in phone_keys:
            vals = contact[pk]
            if isinstance(vals, list):
                for v in vals:
                    lines.append(f"  ({pk.split('_', 1)[1]}): {v}")
            else:
                lines.append(f"  ({pk.split('_', 1)[1]}): {vals}")

    email_keys = sorted(k for k in contact if k.startswith("email_"))
    if email_keys:
        lines.append("Email(s):")
        for ek in email_keys:
            vals = contact[ek]
            if isinstance(vals, list):
                for v in vals:
                    lines.append(f"  ({ek.split('_', 1)[1]}): {v}")
            else:
                lines.append(f"  ({ek.split('_', 1)[1]}): {vals}")

    return "\n".join(lines)


class VCardParser(BaseParser):
    """Parser for vCard files (.vcf)."""

    def parse(self, file_path: str) -> ParsedDocument:
        try:
            with open(file_path, encoding="utf-8", errors="replace") as f:
                content = f.read()
        except Exception as e:
            return ParsedDocument(
                sections=[ParsedSection(content=f"Error reading vCard file: {e}")],
                total_chars=0,
            )

        blocks = re.split(r"(?i)BEGIN:VCARD", content)
        sections: list[ParsedSection] = []
        total_chars = 0

        for block in blocks:
            block = block.strip()
            if not block:
                continue

            card_text = "BEGIN:VCARD\n" + block
            contact = _parse_vcard(card_text)

            if contact:
                formatted = _format_contact(contact)
                name = contact.get("full_name") or contact.get("name", "Contact")
                total_chars += len(formatted)
                sections.append(
                    ParsedSection(
                        title=name,
                        content=formatted,
                        section_type="paragraph",
                    )
                )

        if not sections:
            sections.append(
                ParsedSection(
                    title=Path(file_path).name,
                    content=content[:500] if len(content) > 500 else content,
                    section_type="paragraph",
                )
            )
            total_chars = len(sections[0].content)

        return ParsedDocument(
            sections=sections,
            metadata={"format": "VCARD", "contact_count": len(sections)},
            total_chars=total_chars,
        )
