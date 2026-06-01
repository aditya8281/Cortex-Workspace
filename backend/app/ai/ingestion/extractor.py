from pathlib import Path
import fitz  # PyMuPDF


class FileExtractor:
    """
    Extracts raw text from supported file types.
    """

    def extract(self, file_path: str) -> str:
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        ext = path.suffix.lower()

        if ext == ".pdf":
            return self._extract_pdf(path)

        elif ext in [".txt", ".md", ".py"]:
            return self._extract_text(path)

        else:
            raise ValueError(f"Unsupported file type: {ext}")

    # -------------------------
    # PDF EXTRACTION
    # -------------------------
    def _extract_pdf(self, path: Path) -> str:
        doc = fitz.open(str(path))
        text = []

        for page in doc:
            text.append(page.get_text())

        return "\n".join(text)

    # -------------------------
    # TEXT / CODE FILES
    # -------------------------
    def _extract_text(self, path: Path) -> str:
        return path.read_text(encoding="utf-8", errors="ignore")