"""Entity extraction from code and text content."""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class ExtractedEntity:
    name: str
    entity_type: str  # "function", "class", "concept", "tool", "file", "import"
    context: str = ""
    start_offset: int = 0
    end_offset: int = 0
    confidence: float = 1.0


@dataclass
class EntityRelationship:
    source: str
    target: str
    relationship_type: str  # "imports", "calls", "inherits", "mentions", "contains"
    weight: int = 1


_IMPORT_RE = re.compile(
    r"^(?:from\s+([\w.]+)\s+import\s+([\w*, ]+)|import\s+([\w*, ]+))",
    re.MULTILINE,
)
_CALL_RE = re.compile(r"\b(\w+)\s*\(", re.MULTILINE)
_INHERIT_RE = re.compile(r"class\s+(\w+)\s*\(([^)]*)\)", re.MULTILINE)
_FUNC_DEF_RE = re.compile(
    r"(?:async\s+)?def\s+(\w+)\s*\(",
    re.MULTILINE,
)
_CLASS_DEF_RE = re.compile(r"class\s+(\w+)", re.MULTILINE)
_CONCEPT_RE = re.compile(
    r"\b(?:algorithm|architecture|pattern|framework|protocol|interface|abstraction|pipeline|registry|cache|queue|stack|hook|plugin|module|service|handler|manager|controller|validator|serializer|transformer|analyzer|optimizer|compiler|interpreter|runtime|kernel|daemon|worker|scheduler|broker|gateway|proxy|adapter|facade|mediator|observer|strategy|factory|builder|singleton)\b",
    re.IGNORECASE,
)
_TOOL_RE = re.compile(
    r"\b(?:Python|JavaScript|TypeScript|Rust|Go|Java|React|Vue|Angular|Django|FastAPI|Flask|Express|Node|Docker|Kubernetes|PostgreSQL|MySQL|Redis|Qdrant|SQLite|Git|GitHub|GitLab|VSCode|PyCharm|Neovim|Vim|tmux|Linux|macOS|Windows|AWS|GCP|Azure|OpenAI|Anthropic|HuggingFace|Ollama|LlamaIndex|LangChain|ChromaDB|Pinecone|Weaviate|Milvus)\b",
)
_FILE_REF_RE = re.compile(r"[\w/]+\.(?:py|js|ts|tsx|jsx|rs|go|java|md|txt|json|yaml|yml|toml|xml|html|css)")

_BUILTIN_NAMES = {
    "print",
    "len",
    "range",
    "int",
    "str",
    "float",
    "list",
    "dict",
    "set",
    "tuple",
    "type",
    "class",
    "def",
    "return",
    "if",
    "else",
    "for",
    "while",
    "import",
    "from",
    "with",
    "as",
    "try",
    "except",
    "finally",
    "raise",
    "pass",
    "break",
    "continue",
    "True",
    "False",
    "None",
    "self",
    "cls",
    "__init__",
    "__name__",
    "__main__",
}


class EntityExtractor:
    """Extract entities and relationships from code and text."""

    def extract_from_code(
        self, content: str, file_path: str = ""
    ) -> tuple[list[ExtractedEntity], list[EntityRelationship]]:
        entities: list[ExtractedEntity] = []
        relationships: list[EntityRelationship] = []

        for match in _FUNC_DEF_RE.finditer(content):
            name = match.group(1)
            if name not in _BUILTIN_NAMES:
                entities.append(
                    ExtractedEntity(
                        name=name,
                        entity_type="function",
                        start_offset=match.start(),
                        end_offset=match.end(),
                    )
                )

        for match in _CLASS_DEF_RE.finditer(content):
            name = match.group(1)
            entities.append(
                ExtractedEntity(
                    name=name,
                    entity_type="class",
                    start_offset=match.start(),
                    end_offset=match.end(),
                )
            )

        for match in _IMPORT_RE.finditer(content):
            module = match.group(1) or match.group(3)
            if module:
                entities.append(
                    ExtractedEntity(
                        name=module.split(".")[-1],
                        entity_type="import",
                        context=module,
                    )
                )
                relationships.append(
                    EntityRelationship(
                        source=file_path or "this_file",
                        target=module,
                        relationship_type="imports",
                    )
                )

        for match in _INHERIT_RE.finditer(content):
            child = match.group(1)
            parents = [p.strip() for p in match.group(2).split(",") if p.strip()]
            for parent in parents:
                if parent not in _BUILTIN_NAMES:
                    relationships.append(
                        EntityRelationship(
                            source=child,
                            target=parent,
                            relationship_type="inherits",
                        )
                    )

        func_names = [e.name for e in entities if e.entity_type == "function"]
        for match in _CALL_RE.finditer(content):
            called = match.group(1)
            if called in func_names and called not in _BUILTIN_NAMES:
                caller = func_names[0] if func_names else "module"
                relationships.append(
                    EntityRelationship(
                        source=caller,
                        target=called,
                        relationship_type="calls",
                    )
                )

        return entities, relationships

    def extract_from_text(
        self, content: str, file_path: str = ""
    ) -> tuple[list[ExtractedEntity], list[EntityRelationship]]:
        entities: list[ExtractedEntity] = []
        relationships: list[EntityRelationship] = []

        for match in _CONCEPT_RE.finditer(content):
            entities.append(
                ExtractedEntity(
                    name=match.group(0).lower(),
                    entity_type="concept",
                    start_offset=match.start(),
                    end_offset=match.end(),
                    confidence=0.8,
                )
            )

        for match in _TOOL_RE.finditer(content):
            entities.append(
                ExtractedEntity(
                    name=match.group(0),
                    entity_type="tool",
                    start_offset=match.start(),
                    end_offset=match.end(),
                )
            )

        for match in _FILE_REF_RE.finditer(content):
            ref = match.group(0)
            if len(ref) > 3:
                entities.append(
                    ExtractedEntity(
                        name=ref,
                        entity_type="file",
                        start_offset=match.start(),
                        end_offset=match.end(),
                    )
                )

        seen: set[tuple[str, str]] = set()
        for e in entities:
            for other in entities:
                if e.name != other.name and e.name.lower() in (content.lower().split()):
                    key = (e.name, other.name)
                    if key not in seen:
                        seen.add(key)
                        relationships.append(
                            EntityRelationship(
                                source=e.name,
                                target=other.name,
                                relationship_type="mentions",
                            )
                        )

        return entities, relationships
