"""Parser for font files (.ttf, .otf, .woff, .woff2)."""

from __future__ import annotations

import logging
import os
from pathlib import Path

from backend.app.services.parsers.base import BaseParser, ParsedDocument, ParsedSection

logger = logging.getLogger(__name__)


def _parse_font_metadata(file_path: str) -> dict:
    """Extract font metadata using fonttools."""
    try:
        from fontTools.ttLib import TTFont  # type: ignore[import-not-found]

        font = TTFont(file_path, fontNumber=0)
        meta: dict = {}

        name_table = font.get("name")
        if name_table:
            name_map = {}
            for record in name_table.names:
                try:
                    name_str = record.toUnicode()
                except Exception:
                    continue
                name_map[record.nameID] = name_str

            meta["font_family"] = name_map.get(1, "")
            meta["font_subfamily"] = name_map.get(2, "")
            meta["unique_id"] = name_map.get(3, "")
            meta["full_name"] = name_map.get(4, "")
            meta["version"] = name_map.get(5, "")
            meta["postscript_name"] = name_map.get(6, "")
            meta["trademark"] = name_map.get(7, "")
            meta["manufacturer"] = name_map.get(8, "")
            meta["designer"] = name_map.get(9, "")
            meta["description"] = name_map.get(10, "")
            meta["vendor_url"] = name_map.get(11, "")
            meta["license"] = name_map.get(13, "")
            meta["license_url"] = name_map.get(14, "")
            meta["typographic_family"] = name_map.get(16, "")
            meta["typographic_subfamily"] = name_map.get(17, "")

        os2_table = font.get("OS/2")
        if os2_table:
            weight_map = {
                100: "Thin",
                200: "ExtraLight",
                300: "Light",
                400: "Regular",
                500: "Medium",
                600: "SemiBold",
                700: "Bold",
                800: "ExtraBold",
                900: "Black",
            }
            weight_val = os2_table.usWeightClass
            meta["weight"] = weight_map.get(weight_val, str(weight_val))
            meta["weight_class"] = weight_val
            meta["is_fixed_pitch"] = bool(os2_table.fsType & 0x08)

        head_table = font.get("head")
        if head_table:
            meta["units_per_em"] = head_table.unitsPerEm
            meta["created"] = head_table.created
            meta["modified"] = head_table.modified
            meta["font_version"] = f"{head_table.fontRevision:.3f}"

        cmap_table = font.get("cmap")
        if cmap_table:
            for subtable in cmap_table.tables:
                if subtable.isUnicode():
                    meta["glyph_count"] = len(subtable.cmap)
                    meta["character_range"] = _get_char_range(subtable.cmap)
                    break

        if "glyph_count" not in meta:
            glyf_table = font.get("glyf")
            if glyf_table:
                meta["glyph_count"] = len(glyf_table.glyphs)

        post_table = font.get("post")
        if post_table:
            meta["italic_angle"] = post_table.italicAngle
            meta["fixed_pitch"] = post_table.isFixedPitch

        meta["format"] = Path(file_path).suffix.lower().lstrip(".").upper()
        meta["file_size"] = os.path.getsize(file_path)

        try:
            font.close()
        except Exception:
            pass

        return meta
    except ImportError:
        logger.debug("fonttools not installed, skipping font metadata for %s", file_path)
        return {"format": Path(file_path).suffix.lower().lstrip(".").upper()}
    except Exception as e:
        logger.debug("Font metadata extraction failed for %s: %s", file_path, e)
        return {"format": Path(file_path).suffix.lower().lstrip(".").upper()}


def _get_char_range(cmap: dict) -> str:
    """Get a human-readable character range from a cmap dict."""
    if not cmap:
        return "unknown"
    codes = sorted(cmap.keys())
    ranges: list[str] = []
    start = codes[0]
    end = codes[0]

    for code in codes[1:]:
        if code == end + 1:
            end = code
        else:
            if start == end:
                ranges.append(f"U+{start:04X}")
            else:
                ranges.append(f"U+{start:04X}-U+{end:04X}")
            start = code
            end = code

    if start == end:
        ranges.append(f"U+{start:04X}")
    else:
        ranges.append(f"U+{start:04X}-U+{end:04X}")

    if len(ranges) > 5:
        return f"{len(codes)} characters ({ranges[0]}, {ranges[1]}, ...)"
    return ", ".join(ranges)


class FontParser(BaseParser):
    """Parser for font files (.ttf, .otf, .woff, .woff2)."""

    def parse(self, file_path: str) -> ParsedDocument:
        meta = _parse_font_metadata(file_path)
        filename = Path(file_path).name

        lines: list[str] = [f"Font: {filename}"]

        display_name = meta.get("full_name") or meta.get("font_family") or filename
        if display_name:
            lines.append(f"Name: {display_name}")

        for key, label in (
            ("font_family", "Family"),
            ("font_subfamily", "Subfamily"),
            ("weight", "Weight"),
            ("italic_angle", "Italic Angle"),
            ("font_version", "Version"),
            ("postscript_name", "PostScript Name"),
            ("license", "License"),
            ("manufacturer", "Manufacturer"),
            ("designer", "Designer"),
            ("description", "Description"),
            ("glyph_count", "Glyphs"),
            ("character_range", "Character Range"),
            ("units_per_em", "Units per Em"),
            ("format", "Format"),
            ("file_size", "File Size"),
        ):
            val = meta.get(key)
            if val:
                if key == "file_size":
                    lines.append(f"{label}: {val:,} bytes")
                elif key == "glyph_count":
                    lines.append(f"{label}: {val:,}")
                else:
                    lines.append(f"{label}: {val}")

        content = "\n".join(lines)
        sections = [
            ParsedSection(
                title=display_name,
                content=content,
                section_type="metadata",
            )
        ]

        return ParsedDocument(
            sections=sections,
            metadata=meta,
            total_chars=len(content),
        )
