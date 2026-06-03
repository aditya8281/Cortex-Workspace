from typing import List, Dict
import re


class TextChunker:
    """
    Splits raw text into meaningful chunks for AI memory.
    """

    def __init__(self, max_chunk_size: int = 1000, overlap: int = 150, code_parsing: str = None):
        self.max_chunk_size = max_chunk_size
        self.overlap = overlap
        self.code_parsing = code_parsing or "Tree-sitter"

    def chunk_text(self, text: str, metadata: Dict = None) -> List[Dict]:
        """
        Returns list of chunks with metadata
        """
        if not text:
            return []

        is_code = False
        if metadata and "file" in metadata:
            file_path = str(metadata["file"]).lower()
            is_code = any(file_path.endswith(ext) for ext in [
                ".py", ".js", ".ts", ".jsx", ".tsx", ".json", ".toml", ".yaml", ".yml",
                ".html", ".css", ".md", ".sh", ".c", ".cpp", ".h", ".rs", ".go", ".java", ".kt"
            ])

        if is_code and self.code_parsing == "Tree-sitter":
            return self._structure_aware_chunk_text(text, metadata)

        chunks = []
        start = 0
        chunk_id = 0

        while start < len(text):
            end = start + self.max_chunk_size
            chunk = text[start:end]

            # clean chunk (optional light cleanup)
            chunk = self._clean_text(chunk, is_code=is_code)

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

    def _structure_aware_chunk_text(self, text: str, metadata: Dict = None) -> List[Dict]:
        import ast
        import re

        file_path = metadata.get("file", "") if metadata else ""
        blocks = []

        # If it is Python, try AST parsing for logical functions and classes
        if file_path.endswith(".py"):
            try:
                tree = ast.parse(text)
                lines = text.splitlines()
                
                def get_node_text(node):
                    if hasattr(node, "lineno") and hasattr(node, "end_lineno"):
                        node_lines = lines[node.lineno - 1:node.end_lineno]
                        return "\n".join(node_lines)
                    return None

                for node in tree.body:
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                        node_text = get_node_text(node)
                        if node_text:
                            blocks.append(node_text)
                    else:
                        node_text = get_node_text(node)
                        if node_text:
                            blocks.append(node_text)
            except Exception:
                pass

        # Fallback/generic pattern matching for other/Python fallback code blocks
        if not blocks:
            lines = text.splitlines()
            current_block = []
            block_starter = re.compile(
                r'^\s*('
                r'def |class |function |export |import |'
                r'const \w+\s*=\s*(\(.*?\)|[^=]+?)\s*=>|let \w+\s*=\s*function|var \w+\s*=\s*function|'
                r'public |private |protected |async |'
                r'fn |impl |struct |enum |trait |type |interface |package |func '
                r')'
            )
            for line in lines:
                if block_starter.match(line) and current_block and len("\n".join(current_block)) > 400:
                    blocks.append("\n".join(current_block))
                    current_block = [line]
                else:
                    current_block.append(line)
            if current_block:
                blocks.append("\n".join(current_block))

        # Now construct chunks from these blocks, ensuring none exceed max_chunk_size
        chunks = []
        chunk_id = 0
        for block in blocks:
            block = self._clean_text(block, is_code=True)
            if not block:
                continue

            if len(block) <= self.max_chunk_size:
                chunks.append({
                    "chunk_id": chunk_id,
                    "text": block,
                    "start": 0,
                    "end": len(block),
                    "metadata": metadata or {}
                })
                chunk_id += 1
            else:
                start = 0
                while start < len(block):
                    end = start + self.max_chunk_size
                    sub_chunk = block[start:end]
                    chunks.append({
                        "chunk_id": chunk_id,
                        "text": sub_chunk,
                        "start": start,
                        "end": end,
                        "metadata": metadata or {}
                    })
                    chunk_id += 1
                    start = end - self.overlap

        return chunks

    def _clean_text(self, text: str, is_code: bool = False) -> str:
        """
        Basic cleaning for better embeddings later.
        If is_code is True, we only strip trailing spaces on each line
        and preserve indentation and newlines.
        """
        if is_code:
            lines = text.splitlines()
            cleaned_lines = [line.rstrip() for line in lines]
            return "\n".join(cleaned_lines).strip()
        else:
            text = re.sub(r'\n+', '\n', text)
            text = re.sub(r'\s+', ' ', text)
            return text.strip()