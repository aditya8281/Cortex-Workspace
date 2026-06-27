"""Tests for ViewRegistry and DerivedViews."""

from backend.app.agents.integrity.views import DerivedViews, ViewRegistry


def test_view_registry_creates_views():
    registry = ViewRegistry()
    views = registry.build(None)
    assert hasattr(views, "import_graph")
    assert hasattr(views, "dependency_graph")
    assert hasattr(views, "api_graph")


def test_view_registry_lazy_build():
    registry = ViewRegistry()
    v1 = registry.build(None)
    v2 = registry.build(None)
    assert v1 is v2  # same cached object


def test_view_registry_invalidation():
    registry = ViewRegistry()
    v1 = registry.build(None)
    registry.invalidate()
    v2 = registry.build(None)
    assert v1 is not v2  # new object after invalidation


def test_view_registry_invalidate_after_build():
    registry = ViewRegistry()
    registry.build(None)
    registry.invalidate()
    v = registry.build(None)
    assert v is not None


def test_derived_views_defaults():
    views = DerivedViews()
    assert views.import_graph is None
    assert views.dependency_graph is None
