"""Tests for extractor and normalizer base + Python plugin."""

from pathlib import Path

from backend.app.agents.integrity.extractors._base import (
    CollectorPlugin,
    Extractor,
    Normalizer,
)
from backend.app.agents.integrity.extractors.python_extractor import (
    PythonExtractor,
)
from backend.app.agents.integrity.extractors.python_normalizer import (
    PythonNormalizer,
)


def test_collector_plugin_defaults():
    p = CollectorPlugin(name="test", plugin_version="1.0", supported_rkm_version="1.x")
    assert p.name == "test"
    assert p.supported_rkm_version == "1.x"


def test_python_extractor_plugin():
    e = PythonExtractor()
    assert e.plugin.name == "python"
    assert e.plugin.plugin_version == "1.0"


def test_python_extractor_extract():
    e = PythonExtractor()
    result = e.extract(Path("backend/app/agents/integrity/model/_base.py"))
    assert "imports" in result
    assert "classes" in result
    assert len(result["classes"]) >= 1  # EntityBase


def test_python_normalizer():
    n = PythonNormalizer()
    raw = {"imports": ["os"], "classes": ["EntityBase"], "functions": []}
    entities = n.normalize(raw)
    assert len(entities) >= 1


def test_extractor_is_abstract():
    try:
        Extractor()
        assert False, "Should have raised TypeError"
    except TypeError:
        pass


def test_normalizer_is_abstract():
    try:
        Normalizer()
        assert False, "Should have raised TypeError"
    except TypeError:
        pass
