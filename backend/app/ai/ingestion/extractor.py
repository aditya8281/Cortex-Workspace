from pathlib import Path


class FileExtractor:
    """
    Reads files from disk (code, txt, md, etc.)
    """

    def extract(self, file_path: str) -> str:
        path = Path(file_path)

        if not path.exists():
            return ""

        try:
            return path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            return ""