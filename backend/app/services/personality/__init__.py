"""Personality service — builds Cortex's system prompt from config + memories."""

from backend.app.services.personality.builder import build_system_prompt

__all__ = ["build_system_prompt"]
