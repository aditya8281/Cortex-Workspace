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

        file_path = str(metadata.get("file", "")).lower() if metadata else ""
        
        is_code = any(file_path.endswith(ext) for ext in [
            ".py", ".js", ".ts", ".jsx", ".tsx", ".json", ".toml", ".yaml", ".yml",
            ".html", ".css", ".sh", ".c", ".cpp", ".h", ".rs", ".go", ".java", ".kt"
        ])
        
        is_doc = any(file_path.endswith(ext) for ext in [
            ".md", ".txt", ".pdf", ".rst", ".doc", ".docx"
        ])

        if is_code and self.code_parsing == "Tree-sitter":
            chunks = self._structure_aware_chunk_text(text, metadata)
            if chunks:
                return chunks

        if is_doc:
            return self._section_based_chunking(text, metadata)

        return self._semantic_paragraph_chunking(text, metadata)

    def _section_based_chunking(self, text: str, metadata: Dict = None) -> List[Dict]:
        import re
        lines = text.splitlines()
        chunks = []
        current_section = []
        current_header = "Intro"
        chunk_id = 0
        
        header_regex = re.compile(r'^(#+\s+.*)$')
        
        for line in lines:
            match = header_regex.match(line)
            if match:
                if current_section:
                    section_text = "\n".join(current_section).strip()
                    if section_text:
                        chunks.append({
                            "chunk_id": chunk_id,
                            "text": f"Header: {current_header}\n\n{section_text}",
                            "start": 0,
                            "end": len(section_text),
                            "metadata": {**(metadata or {}), "header": current_header}
                        })
                        chunk_id += 1
                current_header = match.group(1).strip()
                current_section = [line]
            else:
                current_section.append(line)
                
        if current_section:
            section_text = "\n".join(current_section).strip()
            if section_text:
                chunks.append({
                    "chunk_id": chunk_id,
                    "text": f"Header: {current_header}\n\n{section_text}",
                    "start": 0,
                    "end": len(section_text),
                    "metadata": {**(metadata or {}), "header": current_header}
                })
                
        if not chunks:
            return self._semantic_paragraph_chunking(text, metadata)
            
        return chunks

    def _semantic_paragraph_chunking(self, text: str, metadata: Dict = None) -> List[Dict]:
        import re
        paragraphs = text.split("\n\n")
        chunks = []
        current_chunk = []
        current_len = 0
        chunk_id = 0
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            if len(para) > self.max_chunk_size:
                sentences = re.split(r'(?<=[.!?])\s+', para)
                for sentence in sentences:
                    sentence = sentence.strip()
                    if not sentence:
                        continue
                    if current_len + len(sentence) > self.max_chunk_size and current_chunk:
                        chunk_text = " ".join(current_chunk)
                        chunks.append({
                            "chunk_id": chunk_id,
                            "text": chunk_text,
                            "start": 0,
                            "end": len(chunk_text),
                            "metadata": metadata or {}
                        })
                        chunk_id += 1
                        current_chunk = [sentence]
                        current_len = len(sentence)
                    else:
                        current_chunk.append(sentence)
                        current_len += len(sentence) + 1
            else:
                if current_len + len(para) > self.max_chunk_size and current_chunk:
                    chunk_text = "\n\n".join(current_chunk)
                    chunks.append({
                        "chunk_id": chunk_id,
                        "text": chunk_text,
                        "start": 0,
                        "end": len(chunk_text),
                        "metadata": metadata or {}
                    })
                    chunk_id += 1
                    current_chunk = [para]
                    current_len = len(para)
                else:
                    current_chunk.append(para)
                    current_len += len(para) + 2
                    
        if current_chunk:
            chunk_text = "\n\n".join(current_chunk)
            chunks.append({
                "chunk_id": chunk_id,
                "text": chunk_text,
                "start": 0,
                "end": len(chunk_text),
                "metadata": metadata or {}
            })
            
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
            current_block: list[str] = []
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