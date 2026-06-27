"""Tests for EntityExtractor."""

import pytest

from backend.app.services.intelligence.entity_extraction import (
    EntityExtractor,
)


@pytest.fixture()
def extractor():
    return EntityExtractor()


def test_extract_functions(extractor):
    code = "def hello():\n    pass\n\ndef world():\n    pass"
    entities, _ = extractor.extract_from_code(code)
    funcs = [e for e in entities if e.entity_type == "function"]
    assert len(funcs) == 2
    assert funcs[0].name == "hello"
    assert funcs[1].name == "world"


def test_extract_classes(extractor):
    code = "class MyClass(Base):\n    pass"
    entities, _ = extractor.extract_from_code(code)
    classes = [e for e in entities if e.entity_type == "class"]
    assert len(classes) == 1
    assert classes[0].name == "MyClass"


def test_extract_imports(extractor):
    code = "from os import path\nimport json"
    entities, rels = extractor.extract_from_code(code)
    imports = [e for e in entities if e.entity_type == "import"]
    assert len(imports) >= 1
    import_rels = [r for r in rels if r.relationship_type == "imports"]
    assert len(import_rels) >= 1


def test_extract_inheritance(extractor):
    code = "class Child(Parent1, Parent2):\n    pass"
    _, rels = extractor.extract_from_code(code)
    inherit_rels = [r for r in rels if r.relationship_type == "inherits"]
    assert len(inherit_rels) == 2


def test_extract_function_calls(extractor):
    code = "def foo():\n    bar()\n\ndef bar():\n    pass"
    _, rels = extractor.extract_from_code(code)
    call_rels = [r for r in rels if r.relationship_type == "calls"]
    assert len(call_rels) >= 1


def test_extract_concepts(extractor):
    text = "The architecture uses a pipeline pattern with a cache layer."
    entities, _ = extractor.extract_from_text(text)
    concepts = [e for e in entities if e.entity_type == "concept"]
    assert len(concepts) >= 2


def test_extract_tools(extractor):
    text = "Built with Python and PostgreSQL, deployed on Docker."
    entities, _ = extractor.extract_from_text(text)
    tools = [e for e in entities if e.entity_type == "tool"]
    assert len(tools) >= 2


def test_extract_file_refs(extractor):
    text = "See main.py and utils.py for details."
    entities, _ = extractor.extract_from_text(text)
    files = [e for e in entities if e.entity_type == "file"]
    assert len(files) >= 2


def test_empty_code(extractor):
    entities, rels = extractor.extract_from_code("")
    assert len(entities) == 0
    assert len(rels) == 0


def test_empty_text(extractor):
    entities, rels = extractor.extract_from_text("")
    assert len(entities) == 0
    assert len(rels) == 0


def test_builtin_names_excluded(extractor):
    code = "def print():\n    pass"
    entities, _ = extractor.extract_from_code(code)
    funcs = [e for e in entities if e.entity_type == "function"]
    assert len(funcs) == 0
