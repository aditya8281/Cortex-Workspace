"""Parser for image, audio, and video files — extracts metadata."""

from __future__ import annotations

import json
import logging
import os
import struct
import subprocess
from pathlib import Path

from backend.app.services.parsers.base import BaseParser, ParsedDocument, ParsedSection

logger = logging.getLogger(__name__)


def _extract_image_metadata(file_path: str) -> dict:
    """Extract image metadata using Pillow."""
    try:
        from PIL import Image
        from PIL.ExifTags import TAGS

        with Image.open(file_path) as img:
            meta: dict = {
                "format": img.format,
                "mode": img.mode,
                "width": img.size[0],
                "height": img.size[1],
            }

            exif_data = img.getexif()
            if exif_data:
                for tag_id, value in exif_data.items():
                    tag_name = TAGS.get(tag_id, str(tag_id))
                    if isinstance(value, (str, int, float)):
                        meta[tag_name] = value
                    elif isinstance(value, bytes):
                        try:
                            meta[tag_name] = value.decode("utf-8", errors="replace")
                        except Exception:
                            pass

            info = img.info
            for key in ("dpi", "progressive", "progressive_level"):
                if key in info:
                    val = info[key]
                    if isinstance(val, (str, int, float, bool)):
                        meta[key] = val

            return meta
    except ImportError:
        logger.debug("Pillow not installed, skipping image metadata for %s", file_path)
        return {}
    except Exception as e:
        logger.debug("Image metadata extraction failed for %s: %s", file_path, e)
        return {}


def _extract_media_metadata_ffprobe(file_path: str) -> dict:
    """Extract audio/video metadata using ffprobe."""
    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v",
                "quiet",
                "-print_format",
                "json",
                "-show_format",
                "-show_streams",
                file_path,
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode != 0:
            return {}

        data = json.loads(result.stdout)
        meta: dict = {}

        fmt = data.get("format", {})
        for key in ("duration", "bit_rate", "format_name", "format_long_name", "size"):
            if key in fmt:
                try:
                    meta[key] = float(fmt[key]) if key in ("duration", "bit_rate", "size") else fmt[key]
                except (ValueError, TypeError):
                    meta[key] = fmt[key]

        tags = fmt.get("tags", {})
        for key, val in tags.items():
            if isinstance(val, (str, int, float)):
                meta[key] = val

        streams = data.get("streams", [])
        for i, stream in enumerate(streams):
            codec_type = stream.get("codec_type", "unknown")
            prefix = f"stream_{i}_{codec_type}"
            for key in ("codec_name", "width", "height", "sample_rate", "channels", "channel_layout", "bit_rate"):
                if key in stream:
                    meta[f"{prefix}_{key}"] = stream[key]

        return meta
    except FileNotFoundError:
        logger.debug("ffprobe not available, skipping for %s", file_path)
        return {}
    except Exception as e:
        logger.debug("ffprobe metadata extraction failed for %s: %s", file_path, e)
        return {}


def _extract_audio_metadata(file_path: str) -> dict:
    """Extract audio metadata — try ffprobe, fall back to header parsing."""
    meta = _extract_media_metadata_ffprobe(file_path)
    if meta:
        return meta

    ext = Path(file_path).suffix.lower()
    try:
        with open(file_path, "rb") as f:
            header = f.read(12)

            if header[:4] == b"ID3":
                return _parse_id3_header(header, f)

            if header[:4] == b"RIFF" and header[8:12] == b"WAVE":
                f.seek(0)
                return _parse_wav_header(f)

            if header[:3] == b"Ogg":
                return {"format": "Ogg"}

            if header[:4] == b"fLaC":
                return {"format": "FLAC"}

            if ext == ".m4a" and (header[4:8] == b"ftyp" or b"ftyp" in header):
                return {"format": "M4A/AAC"}
    except Exception as e:
        logger.debug("Audio header parsing failed for %s: %s", file_path, e)

    return {"format": ext.lstrip(".").upper()}


def _parse_id3_header(header: bytes, f) -> dict:
    """Parse basic ID3v2 header."""
    meta = {"format": "MP3", "id3_version": f"{header[3]}.{header[4]}"}
    size_bytes = header[6:10]
    tag_size = (size_bytes[0] << 21) | (size_bytes[1] << 14) | (size_bytes[2] << 7) | size_bytes[3]
    meta["id3_tag_size_bytes"] = tag_size
    return meta


def _parse_wav_header(f) -> dict:
    """Parse WAV file header."""
    meta = {"format": "WAV"}
    try:
        f.read(4)
        file_size = struct.unpack("<I", f.read(4))[0]
        f.read(4)
        f.read(4)
        struct.unpack("<I", f.read(4))[0]
        struct.unpack("<H", f.read(2))[0]
        channels = struct.unpack("<H", f.read(2))[0]
        sample_rate = struct.unpack("<I", f.read(4))[0]
        byte_rate = struct.unpack("<I", f.read(4))[0]
        struct.unpack("<H", f.read(2))[0]
        bits_per_sample = struct.unpack("<H", f.read(2))[0]

        meta["channels"] = channels
        meta["sample_rate"] = sample_rate
        meta["bits_per_sample"] = bits_per_sample
        meta["byte_rate"] = byte_rate

        if byte_rate > 0:
            meta["duration"] = round((file_size - 44) / byte_rate, 2)
    except Exception:
        pass
    return meta


def _extract_video_metadata(file_path: str) -> dict:
    """Extract video metadata — try ffprobe, fall back to header parsing."""
    meta = _extract_media_metadata_ffprobe(file_path)
    if meta:
        return meta

    ext = Path(file_path).suffix.lower()
    try:
        with open(file_path, "rb") as f:
            header = f.read(12)

            if header[4:8] == b"ftyp":
                return {"format": ext.lstrip(".").upper(), "container": "MP4/MOV"}

            if header[:3] == b"\x1a\x45\xdf":
                return {"format": ext.lstrip(".").upper(), "container": "Matroska/WebM"}

            if header[:4] == b"RIFF":
                return {"format": "AVI", "container": "AVI"}
    except Exception as e:
        logger.debug("Video header parsing failed for %s: %s", file_path, e)

    return {"format": ext.lstrip(".").upper()}


def _format_duration(seconds: float | str) -> str:
    """Format duration in seconds to HH:MM:SS."""
    try:
        secs = float(seconds)
    except (ValueError, TypeError):
        return str(seconds)

    hours = int(secs // 3600)
    minutes = int((secs % 3600) // 60)
    secs = secs % 60
    if hours:
        return f"{hours:02d}:{minutes:02d}:{secs:05.2f}"
    return f"{minutes:02d}:{secs:05.2f}"


class MediaParser(BaseParser):
    """Parser for image, audio, and video files — extracts metadata only."""

    def parse(self, file_path: str) -> ParsedDocument:
        ext = Path(file_path).suffix.lower()
        file_size = os.path.getsize(file_path)
        filename = Path(file_path).name

        if ext in (".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".webp", ".svg"):
            meta = _extract_image_metadata(file_path)
            media_type = "image"
        elif ext in (".mp3", ".wav", ".flac", ".ogg", ".m4a", ".wma"):
            meta = _extract_audio_metadata(file_path)
            media_type = "audio"
        elif ext in (".mp4", ".mkv", ".avi", ".mov", ".wmv", ".webm"):
            meta = _extract_video_metadata(file_path)
            media_type = "video"
        else:
            meta = {"format": ext.lstrip(".").upper()}
            media_type = "media"

        meta["file_size"] = file_size
        meta["file_name"] = filename

        lines = [f"File: {filename}"]
        lines.append(f"Type: {media_type}")
        lines.append(f"Size: {file_size:,} bytes")

        if "width" in meta and "height" in meta:
            lines.append(f"Dimensions: {meta['width']}×{meta['height']}")
        if "format" in meta:
            lines.append(f"Format: {meta['format']}")
        if "duration" in meta:
            lines.append(f"Duration: {_format_duration(meta['duration'])}")
        if "sample_rate" in meta:
            lines.append(f"Sample Rate: {meta['sample_rate']} Hz")
        if "channels" in meta:
            lines.append(f"Channels: {meta['channels']}")
        if "bit_rate" in meta:
            br = meta["bit_rate"]
            if isinstance(br, (int, float)) and br > 1000:
                lines.append(f"Bitrate: {br / 1000:.1f} kbps")
            else:
                lines.append(f"Bitrate: {br}")
        if "mode" in meta:
            lines.append(f"Color Mode: {meta['mode']}")

        extra_keys = [
            k
            for k in meta
            if k
            not in {
                "file_size",
                "file_name",
                "format",
                "width",
                "height",
                "duration",
                "sample_rate",
                "channels",
                "bit_rate",
                "mode",
            }
        ]
        if extra_keys:
            lines.append("")
            lines.append("Additional Metadata:")
            for k in sorted(extra_keys):
                val = meta[k]
                if isinstance(val, (int, float)) or isinstance(val, str) and len(val) < 200:
                    lines.append(f"  {k}: {val}")

        content = "\n".join(lines)
        sections = [ParsedSection(title=filename, content=content, section_type="metadata")]

        return ParsedDocument(
            sections=sections,
            metadata=meta,
            total_chars=len(content),
        )
