"""Tests for JSON Schema generation from type hints and docstrings."""

from __future__ import annotations

import textwrap
from typing import Literal

from backend.app.agents.tools.schemas import generate_schema


def test_generate_basic_types():
    def func(name: str, count: int, factor: float, enabled: bool) -> str:
        """Do something."""

    schema = generate_schema(func)
    func_schema = schema["function"]
    params = func_schema["parameters"]

    assert func_schema["name"] == "func"
    assert params["properties"]["name"]["type"] == "string"
    assert params["properties"]["count"]["type"] == "integer"
    assert params["properties"]["factor"]["type"] == "number"
    assert params["properties"]["enabled"]["type"] == "boolean"
    assert sorted(params["required"]) == sorted(["name", "count", "factor", "enabled"])


def test_default_values_not_required():
    def func(name: str, limit: int = 10) -> str:
        """Do something."""

    schema = generate_schema(func)
    params = schema["function"]["parameters"]
    assert "name" in params["required"]
    assert "limit" not in params["required"]
    assert params["properties"]["limit"]["default"] == 10


def test_optional_param():
    def func(name: str | None = None) -> str:
        """Do something."""

    schema = generate_schema(func)
    params = schema["function"]["parameters"]
    assert "name" not in params["required"]


def test_literal_enum():
    def func(mode: Literal["fast", "slow", "auto"]) -> str:
        """Do something."""

    schema = generate_schema(func)
    prop = schema["function"]["parameters"]["properties"]["mode"]
    assert prop["type"] == "string"
    assert sorted(prop["enum"]) == sorted(["fast", "slow", "auto"])


def test_list_param():
    def func(items: list[str]) -> str:
        """Do something."""

    schema = generate_schema(func)
    prop = schema["function"]["parameters"]["properties"]["items"]
    assert prop["type"] == "array"
    assert prop["items"]["type"] == "string"


def test_docstring_description():
    def search(query: str, limit: int = 10) -> str:
        """Search the codebase for matching patterns.

        Args:
            query: The search term
            limit: Max results to return
        """

    schema = generate_schema(func=search)
    prop_query = schema["function"]["parameters"]["properties"]["query"]
    prop_limit = schema["function"]["parameters"]["properties"]["limit"]
    assert prop_query["description"] == "The search term"
    assert prop_limit["description"] == "Max results to return"


def test_sphinx_docstring():
    def func(query: str) -> str:
        """Run a query.

        :param query: The query string
        """

    schema = generate_schema(func=func)
    prop = schema["function"]["parameters"]["properties"]["query"]
    assert prop["description"] == "The query string"


def test_self_skip():
    class Foo:
        def method(self, value: str) -> str:
            """Do something."""
            return value

    schema = generate_schema(Foo().method)
    params = schema["function"]["parameters"]["properties"]
    assert "self" not in params
    assert "value" in params


def test_kwargs_skip():
    def func(name: str, **kwargs: str) -> str:
        """Do something."""

    schema = generate_schema(func)
    params = schema["function"]["parameters"]["properties"]
    assert "name" in params
    assert "kwargs" not in params


def test_func_name_used():
    def my_custom_tool(query: str) -> str:
        """Do something."""

    schema = generate_schema(my_custom_tool)
    assert schema["function"]["name"] == "my_custom_tool"


def test_empty_docstring_fallback():
    def func(x: str) -> str:
        return x

    schema = generate_schema(func)
    desc = schema["function"]["description"]
    assert desc == "" or desc == f"Tool: {func.__name__}"


def test_pep563_future_annotations():
    """Regression: `from __future__ import annotations` makes all annotations
    strings. generate_schema must resolve them via typing.get_type_hints().
    Without the fix, 'int' resolves to 'string' instead of 'integer'.
    """
    import typing

    # exec() is needed because `from __future__ import annotations` only
    # applies at module level in the module where it's written. We simulate
    # a separate module with future annotations active.
    ns = {"generate_schema": generate_schema, "typing": typing}
    exec(
        textwrap.dedent("""\
        from __future__ import annotations
        def f(x: int, y: str) -> str:
            \"\"\"Test.\"\"\"
            return ""
        """),
        ns,
    )
    f = ns["f"]
    schema = generate_schema(f)
    params = schema["function"]["parameters"]["properties"]
    assert params["x"]["type"] == "integer", f"Expected integer, got {params['x']['type']}"
    assert params["y"]["type"] == "string", f"Expected string, got {params['y']['type']}"


def test_union_multiple_types_fallback():
    def func(value: str | int) -> str:
        """Do something."""
        return str(value)

    schema = generate_schema(func)
    params = schema["function"]["parameters"]
    # Union with 2+ non-None types falls back to string
    assert params["properties"]["value"]["type"] == "string"
