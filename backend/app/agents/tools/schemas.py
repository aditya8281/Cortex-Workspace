"""JSON Schema generation from type hints and docstrings.

Generates OpenAI-compatible function-calling schemas from Python
function signatures and docstrings. Supports: str, int, float, bool,
Optional, List, Literal, and Union types.
"""

from __future__ import annotations

import inspect
import re
import typing
from typing import Any, get_args, get_origin


def _get_std_type(tp: Any) -> str:
    """Map a Python type to JSON Schema type string."""
    if tp is str or tp is type(None):
        return "string"
    if tp is int:
        return "integer"
    if tp is float:
        return "number"
    if tp is bool:
        return "boolean"
    if tp is bytes:
        return "string"
    return "string"


def _make_property(name: str, tp: Any, description: str = "") -> dict:
    """Build a JSON Schema property dict for a single type annotation."""
    origin = get_origin(tp)
    args = get_args(tp)

    # Literal["a", "b"] → enum
    if origin is typing.Literal:
        return {
            "type": "string",
            "enum": list(args),
            "description": description,
        }

    # Optional[X] = Union[X, None]
    if origin is typing.Union:
        non_none = [a for a in args if a is not type(None)]
        if len(non_none) == 1:
            return _make_property(name, non_none[0], description)

    # list[X]
    if origin in (list, list):
        item_type = _get_std_type(args[0]) if args else "string"
        return {
            "type": "array",
            "items": {"type": item_type, "description": description},
            "description": description,
        }

    # dict[str, X]
    if origin in (dict, dict):
        return {
            "type": "object",
            "description": description,
        }

    # Plain type
    return {
        "type": _get_std_type(tp),
        "description": description,
    }


def _parse_docstring_params(doc: str) -> dict[str, str]:
    """Extract param descriptions from a docstring.

    Supports:
        :param name: description
        Args:
            name: description
    """
    params: dict[str, str] = {}

    # :param name: description  (Sphinx / Google)
    for match in re.finditer(r":param\s+(\w+):\s*(.*)", doc):
        params[match.group(1)] = match.group(2).strip()

    # Args: / Parameters: section (Google-style)
    #   name: description
    arg_section = re.search(r"(?:Args|Parameters|Arguments):\s*\n(.*?)(?:\n\s*\n|\Z)", doc, re.DOTALL)
    if arg_section:
        for line in arg_section.group(1).split("\n"):
            m = re.match(r"\s+(\w+):\s*(.*)", line)
            if m:
                params.setdefault(m.group(1), m.group(2).strip())

    return params


def generate_schema(func: Any) -> dict:
    """Generate an OpenAI-compatible JSON Schema from a function's
    type hints and docstring.

    Args:
        func: The function to generate a schema for.

    Returns:
        A dict following the OpenAI tool-calling format:
        {"type": "function", "function": {"name": ..., "description": ..., "parameters": {...}}}
    """
    sig = inspect.signature(func)
    doc = inspect.getdoc(func) or ""
    param_docs = _parse_docstring_params(doc)

    # Resolve string annotations to actual types
    # (needed when caller uses `from __future__ import annotations`)
    try:
        hints = typing.get_type_hints(func)
    except Exception:
        hints = {}

    # Extract first line (or paragraph) as description
    desc = doc.split("\n\n")[0].strip() if doc else (func.__doc__ or "").split("\n\n")[0].strip()

    properties: dict[str, dict] = {}
    required: list[str] = []

    for param_name, param in sig.parameters.items():
        if param_name in ("self", "cls"):
            continue

        # Skip **kwargs and *args
        if param.kind in (inspect.Parameter.VAR_KEYWORD, inspect.Parameter.VAR_POSITIONAL):
            continue

        p_desc = param_docs.get(param_name, "")
        # Use resolved type from hints if available, fall back to annotation
        tp = hints.get(param_name, param.annotation)
        if tp is inspect.Parameter.empty:
            tp = str

        prop = _make_property(param_name, tp, p_desc)

        # Add default value if present
        if param.default is not inspect.Parameter.empty:
            prop["default"] = param.default
        else:
            # Check if Optional / None in union
            origin = get_origin(tp)
            args = get_args(tp)
            is_optional = origin is typing.Union and type(None) in args
            if not is_optional:
                required.append(param_name)

        properties[param_name] = prop

    return {
        "type": "function",
        "function": {
            "name": func.__name__,
            "description": desc or f"Tool: {func.__name__}",
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required,
            },
        },
    }
