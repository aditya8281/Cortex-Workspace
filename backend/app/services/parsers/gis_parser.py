"""Parser for GIS formats (.geojson, .kml, .gpx)."""

from __future__ import annotations

import json
import logging
import xml.etree.ElementTree as ET
from pathlib import Path

from backend.app.services.parsers.base import BaseParser, ParsedDocument, ParsedSection

logger = logging.getLogger(__name__)


def _format_coord(coord: list | tuple) -> str:
    """Format coordinate list to string."""
    if len(coord) >= 2:
        lat, lon = coord[1], coord[0]
        return f"({lat:.6f}, {lon:.6f})"
    return str(coord)


def _format_geometry(geom: dict) -> str:
    """Format a GeoJSON geometry to readable text."""
    gtype = geom.get("type", "unknown")
    coords = geom.get("coordinates")

    if coords is None:
        return gtype

    if gtype == "Point":
        return f"Point {_format_coord(coords)}"
    elif gtype == "MultiPoint":
        pts = ", ".join(_format_coord(c) for c in coords[:5])
        suffix = f" (+{len(coords) - 5} more)" if len(coords) > 5 else ""
        return f"MultiPoint: {pts}{suffix}"
    elif gtype == "LineString":
        pts = ", ".join(_format_coord(c) for c in coords[:5])
        suffix = f" (+{len(coords) - 5} more)" if len(coords) > 5 else ""
        return f"LineString ({len(coords)} points): {pts}{suffix}"
    elif gtype == "Polygon":
        total = sum(len(ring) for ring in coords)
        return f"Polygon ({len(coords)} rings, {total} points)"
    elif gtype == "MultiPolygon":
        return f"MultiPolygon ({len(coords)} polygons)"
    elif gtype == "GeometryCollection":
        geoms = geom.get("geometries", [])
        return f"GeometryCollection ({len(geoms)} geometries)"
    return gtype


def _parse_geojson(file_path: str) -> ParsedDocument:
    """Parse GeoJSON files."""
    try:
        with open(file_path, encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        return ParsedDocument(
            sections=[ParsedSection(content=f"Error reading GeoJSON: {e}")],
            total_chars=0,
        )

    sections: list[ParsedSection] = []
    total_chars = 0
    feature_count = 0

    def _process_feature(feature: dict) -> None:
        nonlocal total_chars, feature_count
        feature_count += 1
        props = feature.get("properties", {})
        geom = feature.get("geometry", {})

        name = props.get("name") or props.get("NAME") or props.get("title") or f"Feature {feature_count}"
        lines = [f"Feature: {name}"]
        lines.append(f"Geometry: {_format_geometry(geom)}")

        for key, val in sorted(props.items()):
            if key in ("name", "NAME", "title") or val is None:
                continue
            if isinstance(val, (str, int, float, bool)):
                lines.append(f"{key}: {val}")

        content = "\n".join(lines)
        total_chars += len(content)
        sections.append(
            ParsedSection(
                title=name,
                content=content,
                section_type="paragraph",
            )
        )

    ftype = data.get("type", "")

    if ftype == "FeatureCollection":
        for feature in data.get("features", []):
            _process_feature(feature)
    elif ftype == "Feature":
        _process_feature(data)
    else:
        content = json.dumps(data, indent=2)
        if len(content) > 5000:
            content = content[:5000] + "\n... (truncated)"
        total_chars = len(content)
        sections.append(
            ParsedSection(
                title=Path(file_path).name,
                content=content,
                section_type="paragraph",
            )
        )

    return ParsedDocument(
        sections=sections,
        metadata={"format": "GeoJSON", "feature_count": feature_count},
        total_chars=total_chars,
    )


def _parse_kml(file_path: str) -> ParsedDocument:
    """Parse KML files."""
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
    except ET.ParseError as e:
        return ParsedDocument(
            sections=[ParsedSection(content=f"Error parsing KML: {e}")],
            total_chars=0,
        )

    ns = {"kml": "http://www.opengis.net/kml/2.2"}
    sections: list[ParsedSection] = []
    total_chars = 0

    def _extract_coords_text(coord_str: str) -> str:
        if not coord_str:
            return "no coordinates"
        coords = coord_str.strip().split()
        if len(coords) == 1:
            parts = coords[0].split(",")
            return f"({parts[1]}, {parts[0]})" if len(parts) >= 2 else coords[0]
        return f"{len(coords)} coordinates"

    def _process_placemark(pm: ET.Element, ns: dict) -> None:
        nonlocal total_chars
        name_el = pm.find("kml:name", ns)
        name = name_el.text if name_el is not None and name_el.text else "Unnamed"
        desc_el = pm.find("kml:description", ns)
        description = desc_el.text if desc_el is not None and desc_el.text else ""

        lines = [f"Placemark: {name}"]

        coords_el = pm.find(".//kml:coordinates", ns)
        if coords_el is not None and coords_el.text:
            lines.append(f"Location: {_extract_coords_text(coords_el.text)}")

        if description:
            lines.append(f"Description: {description[:500]}")

        extended = pm.find("kml:ExtendedData", ns)
        if extended is not None:
            for data in extended.findall("kml:Data", ns):
                dname = data.get("name", "")
                dval = data.find("kml:value", ns)
                if dval is not None and dval.text:
                    lines.append(f"{dname}: {dval.text}")

        content = "\n".join(lines)
        total_chars += len(content)
        sections.append(
            ParsedSection(
                title=name,
                content=content,
                section_type="paragraph",
            )
        )

    for doc in root.findall(".//kml:Document", ns):
        doc_name = doc.find("kml:name", ns)
        if doc_name is not None and doc_name.text:
            sections.append(
                ParsedSection(
                    title=doc_name.text,
                    content=f"KML Document: {doc_name.text}",
                    section_type="heading",
                    level=1,
                )
            )

        for pm in doc.findall("kml:Placemark", ns):
            _process_placemark(pm, ns)

        for folder in doc.findall("kml:Folder", ns):
            folder_name = folder.find("kml:name", ns)
            if folder_name is not None and folder_name.text:
                sections.append(
                    ParsedSection(
                        title=folder_name.text,
                        content=f"Folder: {folder_name.text}",
                        section_type="heading",
                        level=2,
                    )
                )
            for pm in folder.findall("kml:Placemark", ns):
                _process_placemark(pm, ns)

    for pm in root.findall(".//kml:Placemark", ns):
        _process_placemark(pm, ns)

    return ParsedDocument(
        sections=sections,
        metadata={"format": "KML"},
        total_chars=total_chars,
    )


def _parse_gpx(file_path: str) -> ParsedDocument:
    """Parse GPX files."""
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
    except ET.ParseError as e:
        return ParsedDocument(
            sections=[ParsedSection(content=f"Error parsing GPX: {e}")],
            total_chars=0,
        )

    ns = {"gpx": "http://www.topografix.com/GPX/1/1"}
    sections: list[ParsedSection] = []
    total_chars = 0

    metadata = root.find("gpx:metadata", ns)
    if metadata is not None:
        name_el = metadata.find("gpx:name", ns)
        if name_el is not None and name_el.text:
            sections.append(
                ParsedSection(
                    title="Track Metadata",
                    content=f"Track: {name_el.text}",
                    section_type="heading",
                    level=1,
                )
            )

    def _format_pt(pt: ET.Element, ns: dict, pt_type: str) -> str:
        lat = pt.get("lat", "?")
        lon = pt.get("lon", "?")
        ele_el = pt.find("gpx:ele", ns)
        time_el = pt.find("gpx:time", ns)
        name_el = pt.find("gpx:name", ns)

        parts = [f"{pt_type}: ({lat}, {lon})"]
        if name_el is not None and name_el.text:
            parts.append(f"Name: {name_el.text}")
        if ele_el is not None and ele_el.text:
            parts.append(f"Elevation: {ele_el.text}m")
        if time_el is not None and time_el.text:
            parts.append(f"Time: {time_el.text}")
        return "\n  ".join(parts)

    for track in root.findall("gpx:trk", ns):
        name_el = track.find("gpx:name", ns)
        track_name = name_el.text if name_el is not None and name_el.text else "Unnamed Track"

        segments = track.findall("gpx:trkseg", ns)
        total_pts = sum(len(seg.findall("gpx:trkpt", ns)) for seg in segments)

        lines = [f"Track: {track_name}", f"Segments: {len(segments)}, Points: {total_pts}"]

        for seg in segments:
            for pt in seg.findall("gpx:trkpt", ns)[:50]:
                lines.append(_format_pt(pt, ns, "Point"))
            if total_pts > 50:
                lines.append(f"  ... (+{total_pts - 50} more points)")

        content = "\n".join(lines)
        total_chars += len(content)
        sections.append(
            ParsedSection(
                title=track_name,
                content=content,
                section_type="paragraph",
            )
        )

    for route in root.findall("gpx:rte", ns):
        name_el = route.find("gpx:name", ns)
        route_name = name_el.text if name_el is not None and name_el.text else "Unnamed Route"

        rtepts = route.findall("gpx:rtept", ns)
        lines = [f"Route: {route_name}", f"Points: {len(rtepts)}"]

        for pt in rtepts[:50]:
            lat = pt.get("lat", "?")
            lon = pt.get("lon", "?")
            name_el = pt.find("gpx:name", ns)
            name = name_el.text if name_el is not None and name_el.text else ""
            lines.append(f"  ({lat}, {lon})" + (f" - {name}" if name else ""))

        if len(rtepts) > 50:
            lines.append(f"  ... (+{len(rtepts) - 50} more points)")

        content = "\n".join(lines)
        total_chars += len(content)
        sections.append(
            ParsedSection(
                title=route_name,
                content=content,
                section_type="paragraph",
            )
        )

    for wpt in root.findall("gpx:wpt", ns):
        lat = wpt.get("lat", "?")
        lon = wpt.get("lon", "?")
        name_el = wpt.find("gpx:name", ns)
        name = name_el.text if name_el is not None and name_el.text else "Waypoint"
        desc_el = wpt.find("gpx:desc", ns)
        desc = desc_el.text if desc_el is not None and desc_el.text else ""

        lines = [f"Waypoint: {name}", f"Location: ({lat}, {lon})"]
        if desc:
            lines.append(f"Description: {desc}")

        content = "\n".join(lines)
        total_chars += len(content)
        sections.append(
            ParsedSection(
                title=name,
                content=content,
                section_type="paragraph",
            )
        )

    return ParsedDocument(
        sections=sections,
        metadata={"format": "GPX"},
        total_chars=total_chars,
    )


class GISParser(BaseParser):
    """Parser for GIS formats (.geojson, .kml, .gpx)."""

    def parse(self, file_path: str) -> ParsedDocument:
        ext = Path(file_path).suffix.lower()
        if ext == ".geojson":
            return _parse_geojson(file_path)
        elif ext == ".kml":
            return _parse_kml(file_path)
        elif ext == ".gpx":
            return _parse_gpx(file_path)
        else:
            return ParsedDocument(
                sections=[ParsedSection(content=f"Unsupported GIS format: {ext}")],
                total_chars=0,
            )
