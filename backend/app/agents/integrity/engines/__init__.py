"""Integrity engine implementations — structural, semantic, evolution.

Engine subpackages are auto-loaded by EngineRegistry.get_instance() to
trigger @register decorators. This __init__.py stays empty to avoid
circular imports (registry.py imports engines._base at module level).
"""
