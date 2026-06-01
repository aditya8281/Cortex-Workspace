from typing import List, Dict
import re


class TextChunker:
    """
    Splits raw text into meaningful chunks for AI memory.
    """

    def __init__(self, max_chunk_size: int = 1000, overlap: int = 150):
        self.max_chunk_size = max_chunk_size
        self.overlap = overlap

    def chunk_text(self, text: str, metadata: Dict = None) -> List[Dict]:
        """
        Returns list of chunks with metadata
        """
        if not text:
            return []

        chunks = []
        start = 0
        chunk_id = 0

        while start < len(text):
            end = start + self.max_chunk_size
            chunk = text[start:end]

            # clean chunk (optional light cleanup)
            chunk = self._clean_text(chunk)

            chunks.append({
                "chunk_id": chunk_id,
                "text": chunk,
                "start": start,
                "end": end,
                "metadata": metadata or {}
            })

            chunk_id += 1
            start = end - self.overlap  # overlap for context continuity

        return chunks

    def _clean_text(self, text: str) -> str:
        """
        Basic cleaning for better embeddings later
        """
        text = re.sub(r'\n+', '\n', text)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()