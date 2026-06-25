"""Tests for loop.py internal helpers — TOOL_CALL parsing, completion signal, arg coercion."""

from __future__ import annotations

from backend.app.agents.loop import (
    _coerce_args,
    _is_completion_signal,
    _parse_tool_calls,
    _strip_tool_calls,
)


class TestParseToolCalls:
    """TOOL_CALL directive parsing with the paren-depth-aware implementation."""

    def test_simple_call(self):
        result = _parse_tool_calls('TOOL_CALL: search(query="hello")')
        assert len(result) == 1
        assert result[0]["name"] == "search"
        assert result[0]["args"]["query"] == "hello"

    def test_multiple_calls(self):
        result = _parse_tool_calls('TOOL_CALL: search(q="x") and TOOL_CALL: read_file(path="y")')
        assert len(result) == 2
        assert result[0]["name"] == "search"
        assert result[1]["name"] == "read_file"

    def test_no_tool_calls(self):
        result = _parse_tool_calls("Just a regular response with no tools.")
        assert result == []

    def test_nested_parens_in_value(self):
        """P1: parens inside argument values should NOT break parsing."""
        result = _parse_tool_calls('TOOL_CALL: read_file(path="some/file(1).txt")')
        assert len(result) == 1
        assert result[0]["name"] == "read_file"
        assert result[0]["args"]["path"] == "some/file(1).txt"

    def test_multiple_nested_parens(self):
        result = _parse_tool_calls('TOOL_CALL: search(pattern="a(b(c))d", limit=5)')
        assert len(result) == 1
        assert result[0]["name"] == "search"
        assert result[0]["args"]["pattern"] == "a(b(c))d"
        assert result[0]["args"]["limit"] == "5"

    def test_empty_args(self):
        result = _parse_tool_calls("TOOL_CALL: do_thing()")
        assert len(result) == 1
        assert result[0]["name"] == "do_thing"
        assert result[0]["args"] == {}

    def test_case_insensitive(self):
        result = _parse_tool_calls("tool_call: my_tool(x=1)")
        assert len(result) == 1
        assert result[0]["name"] == "my_tool"

    def test_args_with_spaces(self):
        result = _parse_tool_calls('TOOL_CALL: search(query="hello world", limit=10)')
        assert len(result) == 1
        assert result[0]["args"]["query"] == "hello world"
        assert result[0]["args"]["limit"] == "10"


class TestStripToolCalls:
    """Strip TOOL_CALL directives leaving only user-visible text."""

    def test_strip_simple(self):
        result = _strip_tool_calls('TOOL_CALL: search(q="x")')
        assert result == ""

    def test_strip_with_text(self):
        result = _strip_tool_calls('Looking up the file.\nTOOL_CALL: read_file(path="x.py")')
        assert result == "Looking up the file."

    def test_strip_multiple(self):
        result = _strip_tool_calls('Step 1.\nTOOL_CALL: search(q="a")\nThen.\nTOOL_CALL: search(q="b")')
        assert "Step 1." in result
        assert "Then." in result

    def test_strip_nested_parens(self):
        result = _strip_tool_calls('Processing\nTOOL_CALL: read_file(path="a(b).txt")')
        assert result == "Processing"

    def test_no_calls(self):
        result = _strip_tool_calls("Just text.")
        assert result == "Just text."


class TestIsCompletionSignal:
    """Completion signal detection."""

    def test_exact_match(self):
        assert _is_completion_signal("Task complete") is True

    def test_with_period(self):
        """P0: trailing period must NOT defeat detection."""
        assert _is_completion_signal("Task complete.") is True

    def test_with_exclamation(self):
        assert _is_completion_signal("All done!") is True

    def test_with_question(self):
        assert _is_completion_signal("Finished?") is True

    def test_no_match(self):
        assert _is_completion_signal("Still working on it") is False

    def test_all_done(self):
        assert _is_completion_signal("All done") is True

    def test_finished(self):
        assert _is_completion_signal("finished.") is True

    def test_substring_does_not_match(self):
        """Words after 'task complete' should NOT trigger signal."""
        assert _is_completion_signal("Here is the task complete summary") is False

    def test_empty_string(self):
        assert _is_completion_signal("") is False


class TestCoerceArgs:
    """Type coercion of tool arguments from strings to schema-declared types."""

    def test_no_schema(self):
        assert _coerce_args({"x": "1"}, {}) == {"x": "1"}

    def test_empty_args(self):
        assert _coerce_args({}, {"function": {}}) == {}

    def test_string_default(self):
        schema = {
            "function": {
                "parameters": {
                    "properties": {
                        "name": {"type": "string"},
                    }
                }
            }
        }
        result = _coerce_args({"name": "hello"}, schema)
        assert result["name"] == "hello"

    def test_integer_coercion(self):
        schema = {
            "function": {
                "parameters": {
                    "properties": {
                        "limit": {"type": "integer"},
                    }
                }
            }
        }
        result = _coerce_args({"limit": "42"}, schema)
        assert result["limit"] == 42
        assert isinstance(result["limit"], int)

    def test_boolean_coercion(self):
        schema = {
            "function": {
                "parameters": {
                    "properties": {
                        "recursive": {"type": "boolean"},
                    }
                }
            }
        }
        assert _coerce_args({"recursive": "true"}, schema)["recursive"] is True
        assert _coerce_args({"recursive": "false"}, schema)["recursive"] is False

    def test_none_coercion(self):
        schema = {
            "function": {
                "parameters": {
                    "properties": {
                        "optional": {"type": "string"},
                    }
                }
            }
        }
        result = _coerce_args({"optional": "null"}, schema)
        assert result["optional"] is None

    def test_float_coercion(self):
        schema = {
            "function": {
                "parameters": {
                    "properties": {
                        "score": {"type": "number"},
                    }
                }
            }
        }
        result = _coerce_args({"score": "3.14"}, schema)
        assert result["score"] == 3.14
        assert isinstance(result["score"], float)

    def test_type_error_fallback(self):
        """If coercion fails (e.g. "abc" -> int), return original args."""
        schema = {
            "function": {
                "parameters": {
                    "properties": {
                        "limit": {"type": "integer"},
                    }
                }
            }
        }
        result = _coerce_args({"limit": "not_a_number"}, schema)
        # Falls through to original due to exception handler
        assert result == {"limit": "not_a_number"}
