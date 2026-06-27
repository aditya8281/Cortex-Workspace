"""Parser for archive files (zip, tar, gz, bz2, 7z, rar)."""

from __future__ import annotations

import gzip
import logging
import tarfile
import zipfile
from datetime import datetime
from pathlib import Path

from backend.app.services.intelligence.parsers.base import BaseParser, ParsedDocument, ParsedSection

logger = logging.getLogger(__name__)

_TEXT_EXTENSIONS = frozenset(
    {
        ".txt",
        ".md",
        ".rst",
        ".csv",
        ".json",
        ".yaml",
        ".yml",
        ".toml",
        ".xml",
        ".html",
        ".htm",
        ".css",
        ".js",
        ".ts",
        ".py",
        ".rb",
        ".go",
        ".rs",
        ".java",
        ".c",
        ".cpp",
        ".h",
        ".hpp",
        ".sh",
        ".bash",
        ".zsh",
        ".log",
        ".ini",
        ".cfg",
        ".conf",
        ".env",
        ".gitignore",
        ".dockerignore",
        ".makefile",
        ".cmake",
    }
)


def _is_text_file(name: str) -> bool:
    ext = Path(name).suffix.lower()
    if ext in _TEXT_EXTENSIONS:
        return True
    basename = Path(name).name.lower()
    return basename in ("makefile", "dockerfile", "readme", "license", "changelog", "authors")


def _format_size(size: int) -> str:
    size_f = float(size)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if size_f < 1024:
            return f"{size_f:.1f} {unit}" if unit != "B" else f"{size} B"
        size_f /= 1024
    return f"{size_f:.1f} PB"


def _format_time(ts: float | None) -> str:
    if ts is None:
        return "unknown"
    try:
        return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")
    except (OSError, ValueError):
        return "unknown"


class ArchiveParser(BaseParser):
    """Parser for archive files — lists contents and extracts text from text files."""

    def parse(self, file_path: str) -> ParsedDocument:
        ext = Path(file_path).suffix.lower()

        if ext == ".zip":
            return self._parse_zip(file_path)
        elif ext in (".tar", ".tar.gz", ".tgz", ".tar.bz2", ".tbz2", ".tar.xz", ".txz"):
            return self._parse_tar(file_path)
        elif ext == ".gz":
            return self._parse_gzip(file_path)
        elif ext == ".bz2":
            return self._parse_bz2(file_path)
        elif ext == ".7z":
            return self._parse_7z(file_path)
        elif ext == ".rar":
            return self._parse_rar(file_path)
        else:
            return ParsedDocument(
                sections=[ParsedSection(content=f"Unsupported archive format: {ext}")],
                total_chars=0,
            )

    def _parse_zip(self, file_path: str) -> ParsedDocument:
        sections: list[ParsedSection] = []
        metadata: dict = {"format": "ZIP"}
        all_text: list[str] = []

        try:
            with zipfile.ZipFile(file_path, "r") as zf:
                metadata["file_count"] = len(zf.infolist())
                metadata["compressed_size"] = sum(i.compress_size for i in zf.infolist())
                metadata["uncompressed_size"] = sum(i.file_size for i in zf.infolist())

                lines = [f"Archive: {Path(file_path).name}", "Format: ZIP", f"Files: {len(zf.infolist())}", ""]
                lines.append(f"{'Name':<50} {'Size':>10} {'Modified':<20}")
                lines.append("-" * 82)

                for info in sorted(zf.infolist(), key=lambda x: x.filename):
                    size_str = _format_size(info.file_size)
                    mod_time = _format_time(info.date_time if isinstance(info.date_time, float) else None)
                    lines.append(f"{info.filename:<50} {size_str:>10} {mod_time:<20}")

                    if _is_text_file(info.filename) and info.file_size < 1_000_000:
                        # Reject path traversal attempts
                        if ".." in info.filename or info.filename.startswith("/") or info.filename.startswith("\\"):
                            logger.warning("Skipping zip member with suspicious path: %s", info.filename)
                            continue
                        try:
                            raw = zf.read(info.filename)
                            for enc in ("utf-8", "latin-1"):
                                try:
                                    text = raw.decode(enc)
                                    all_text.append(f"\n--- {info.filename} ---\n{text}")
                                    break
                                except UnicodeDecodeError:
                                    continue
                        except Exception:
                            pass

                sections.append(
                    ParsedSection(
                        title="Archive Contents",
                        content="\n".join(lines),
                        section_type="list",
                    )
                )

                if all_text:
                    sections.append(
                        ParsedSection(
                            title="Extracted Text",
                            content="\n".join(all_text),
                            section_type="paragraph",
                        )
                    )

        except zipfile.BadZipFile:
            sections.append(ParsedSection(content="Error: Corrupt or invalid ZIP file"))

        full_text = "\n\n".join(s.content for s in sections)
        return ParsedDocument(sections=sections, metadata=metadata, total_chars=len(full_text))

    def _parse_tar(self, file_path: str) -> ParsedDocument:
        sections: list[ParsedSection] = []
        metadata: dict = {"format": "TAR"}
        all_text: list[str] = []

        try:
            with tarfile.open(file_path, "r:*") as tf:
                members = tf.getmembers()
                metadata["file_count"] = len(members)
                metadata["uncompressed_size"] = sum(m.size for m in members if m.isfile())

                lines = [f"Archive: {Path(file_path).name}", "Format: TAR", f"Files: {len(members)}", ""]
                lines.append(f"{'Name':<50} {'Size':>10} {'Modified':<20} {'Type':<6}")
                lines.append("-" * 88)

                for m in sorted(members, key=lambda x: x.name):
                    size_str = _format_size(m.size)
                    mod_time = _format_time(m.mtime)
                    ftype = "dir" if m.isdir() else ("link" if m.issym() else "file")
                    lines.append(f"{m.name:<50} {size_str:>10} {mod_time:<20} {ftype:<6}")

                    if m.isfile() and _is_text_file(m.name) and m.size < 1_000_000:
                        # Reject path traversal attempts
                        if ".." in m.name or m.name.startswith("/") or m.name.startswith("\\"):
                            logger.warning("Skipping tar member with suspicious path: %s", m.name)
                            continue
                        try:
                            f = tf.extractfile(m)
                            if f:
                                raw = f.read()
                                for enc in ("utf-8", "latin-1"):
                                    try:
                                        text = raw.decode(enc)
                                        all_text.append(f"\n--- {m.name} ---\n{text}")
                                        break
                                    except UnicodeDecodeError:
                                        continue
                        except Exception:
                            pass

                sections.append(
                    ParsedSection(
                        title="Archive Contents",
                        content="\n".join(lines),
                        section_type="list",
                    )
                )

                if all_text:
                    sections.append(
                        ParsedSection(
                            title="Extracted Text",
                            content="\n".join(all_text),
                            section_type="paragraph",
                        )
                    )

        except Exception as e:
            sections.append(ParsedSection(content=f"Error reading tar archive: {e}"))

        full_text = "\n\n".join(s.content for s in sections)
        return ParsedDocument(sections=sections, metadata=metadata, total_chars=len(full_text))

    def _parse_gzip(self, file_path: str) -> ParsedDocument:
        sections: list[ParsedSection] = []
        metadata: dict = {"format": "GZIP"}

        try:
            with gzip.open(file_path, "rb") as gz:
                raw = gz.read(1_000_000)

            text = None
            for enc in ("utf-8", "latin-1"):
                try:
                    text = raw.decode(enc)
                    break
                except UnicodeDecodeError:
                    continue

            if text is not None:
                basename = Path(file_path).stem
                sections.append(
                    ParsedSection(
                        title=basename,
                        content=text,
                        section_type="paragraph",
                    )
                )
                metadata["extracted_text_length"] = len(text)
            else:
                sections.append(
                    ParsedSection(
                        content="Binary gzip file — no text content extracted",
                        section_type="paragraph",
                    )
                )

        except Exception as e:
            sections.append(ParsedSection(content=f"Error reading gzip file: {e}"))

        full_text = "\n\n".join(s.content for s in sections)
        return ParsedDocument(sections=sections, metadata=metadata, total_chars=len(full_text))

    def _parse_bz2(self, file_path: str) -> ParsedDocument:
        sections: list[ParsedSection] = []
        metadata: dict = {"format": "BZ2"}

        try:
            import bz2

            with bz2.open(file_path, "rb") as bz:
                raw = bz.read(1_000_000)

            text = None
            for enc in ("utf-8", "latin-1"):
                try:
                    text = raw.decode(enc)
                    break
                except UnicodeDecodeError:
                    continue

            if text is not None:
                basename = Path(file_path).stem
                sections.append(
                    ParsedSection(
                        title=basename,
                        content=text,
                        section_type="paragraph",
                    )
                )
                metadata["extracted_text_length"] = len(text)
            else:
                sections.append(
                    ParsedSection(
                        content="Binary bz2 file — no text content extracted",
                        section_type="paragraph",
                    )
                )

        except Exception as e:
            sections.append(ParsedSection(content=f"Error reading bz2 file: {e}"))

        full_text = "\n\n".join(s.content for s in sections)
        return ParsedDocument(sections=sections, metadata=metadata, total_chars=len(full_text))

    def _parse_7z(self, file_path: str) -> ParsedDocument:
        sections: list[ParsedSection] = []
        metadata: dict = {"format": "7Z"}
        all_text: list[str] = []

        try:
            import py7zr  # type: ignore[import-not-found]

            with py7zr.SevenZipFile(file_path, mode="r") as sz:
                names = sz.getnames()
                metadata["file_count"] = len(names)

                lines = [f"Archive: {Path(file_path).name}", "Format: 7Z", f"Files: {len(names)}", ""]
                lines.extend(sorted(names))

                for entry in sz.list():
                    if entry.is_directory:
                        continue
                    if _is_text_file(entry.filename) and entry.uncompressed < 1_000_000:
                        try:
                            extracted = sz.read([entry.filename])
                            if extracted:
                                _, bio = extracted[0]
                                raw = bio.read()
                                for enc in ("utf-8", "latin-1"):
                                    try:
                                        text = raw.decode(enc)
                                        all_text.append(f"\n--- {entry.filename} ---\n{text}")
                                        break
                                    except UnicodeDecodeError:
                                        continue
                        except Exception:
                            pass

                sections.append(
                    ParsedSection(
                        title="Archive Contents",
                        content="\n".join(lines),
                        section_type="list",
                    )
                )

                if all_text:
                    sections.append(
                        ParsedSection(
                            title="Extracted Text",
                            content="\n".join(all_text),
                            section_type="paragraph",
                        )
                    )

        except ImportError:
            sections.append(ParsedSection(content="py7zr not installed — cannot parse .7z files"))
        except Exception as e:
            sections.append(ParsedSection(content=f"Error reading 7z archive: {e}"))

        full_text = "\n\n".join(s.content for s in sections)
        return ParsedDocument(sections=sections, metadata=metadata, total_chars=len(full_text))

    def _parse_rar(self, file_path: str) -> ParsedDocument:
        sections: list[ParsedSection] = []
        metadata: dict = {"format": "RAR"}
        all_text: list[str] = []

        try:
            import rarfile  # type: ignore[import-not-found]

            with rarfile.RarFile(file_path) as rf:
                infos = rf.infolist()
                metadata["file_count"] = len(infos)

                lines = [f"Archive: {Path(file_path).name}", "Format: RAR", f"Files: {len(infos)}", ""]
                lines.append(f"{'Name':<50} {'Size':>10} {'Packed':>10}")
                lines.append("-" * 72)

                for info in sorted(infos, key=lambda x: x.filename):
                    lines.append(
                        f"{info.filename:<50} {_format_size(info.file_size):>10} {_format_size(info.compress_size):>10}"
                    )

                    if not info.is_dir() and _is_text_file(info.filename) and info.file_size < 1_000_000:
                        try:
                            raw = rf.read(info.filename)
                            for enc in ("utf-8", "latin-1"):
                                try:
                                    text = raw.decode(enc)
                                    all_text.append(f"\n--- {info.filename} ---\n{text}")
                                    break
                                except UnicodeDecodeError:
                                    continue
                        except Exception:
                            pass

                sections.append(
                    ParsedSection(
                        title="Archive Contents",
                        content="\n".join(lines),
                        section_type="list",
                    )
                )

                if all_text:
                    sections.append(
                        ParsedSection(
                            title="Extracted Text",
                            content="\n".join(all_text),
                            section_type="paragraph",
                        )
                    )

        except ImportError:
            sections.append(ParsedSection(content="rarfile not installed — cannot parse .rar files"))
        except Exception as e:
            sections.append(ParsedSection(content=f"Error reading RAR archive: {e}"))

        full_text = "\n\n".join(s.content for s in sections)
        return ParsedDocument(sections=sections, metadata=metadata, total_chars=len(full_text))
