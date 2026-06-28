"""Tests for ToolRegistry and ActionVerifier."""

import pytest

from backend.app.services.execution.action_verifier import ActionVerifier
from backend.app.services.execution.tool_registry import (
    ToolNotFoundError,
    ToolRegistry,
    ToolValidationError,
)


class TestToolRegistry:
    @pytest.fixture
    def registry(self):
        return ToolRegistry()

    def test_register_tool(self, registry):
        def my_tool(x: int = 1):
            return {"result": x}

        registry.register("my_tool", my_tool, "Test tool", {"x": {"type": "integer"}})
        assert registry.has_tool("my_tool")
        assert len(registry.list_tools()) == 1

    def test_duplicate_registration(self, registry):
        def tool():
            return {}

        registry.register("tool1", tool, "T1", {})
        with pytest.raises(ValueError, match="already registered"):
            registry.register("tool1", tool, "T1 again", {})

    def test_validate_params_valid(self, registry):
        def tool(name: str, count: int):
            return {}

        registry.register(
            "tool",
            tool,
            "T",
            {
                "name": {"type": "string", "required": True},
                "count": {"type": "integer", "required": True},
            },
        )
        errors = registry.validate_params("tool", {"name": "test", "count": 5})
        assert len(errors) == 0

    def test_validate_params_missing_required(self, registry):
        def tool(name: str):
            return {}

        registry.register(
            "tool",
            tool,
            "T",
            {
                "name": {"type": "string", "required": True},
            },
        )
        errors = registry.validate_params("tool", {})
        assert len(errors) == 1
        assert "Missing required parameter" in errors[0]

    def test_validate_params_wrong_type(self, registry):
        def tool(count: int):
            return {}

        registry.register(
            "tool",
            tool,
            "T",
            {
                "count": {"type": "integer", "required": True},
            },
        )
        errors = registry.validate_params("tool", {"count": "not_a_number"})
        assert len(errors) == 1
        assert "expected integer" in errors[0]

    def test_validate_params_unexpected(self, registry):
        def tool():
            return {}

        registry.register("tool", tool, "T", {})
        errors = registry.validate_params("tool", {"extra": "param"})
        assert len(errors) == 1
        assert "Unexpected parameter" in errors[0]

    def test_execute_sync_tool(self, registry):
        def add(a: int, b: int):
            return {"result": a + b}

        registry.register(
            "add",
            add,
            "Add",
            {
                "a": {"type": "integer"},
                "b": {"type": "integer"},
            },
        )
        result = registry.execute_sync("add", {"a": 3, "b": 4})
        assert result == {"result": 7}

    def test_execute_sync_not_found(self, registry):
        with pytest.raises(ToolNotFoundError):
            registry.execute_sync("nonexistent", {})

    def test_execute_sync_validation_error(self, registry):
        def tool(x: int):
            return {}

        registry.register("tool", tool, "T", {"x": {"type": "integer"}})
        with pytest.raises(ToolValidationError):
            registry.execute_sync("tool", {"x": "bad"})

    def test_execute_sync_confirmation_required(self, registry):
        def dangerous():
            return {}

        registry.register("dangerous", dangerous, "Dangerous", {}, requires_confirmation=True)
        with pytest.raises(PermissionError, match="requires confirmation"):
            registry.execute_sync("dangerous", {})

        result = registry.execute_sync("dangerous", {}, confirmed=True)
        assert result == {}

    def test_unregister(self, registry):
        def tool():
            return {}

        registry.register("tool", tool, "T", {})
        assert registry.unregister("tool") is True
        assert registry.unregister("tool") is False
        assert not registry.has_tool("tool")

    def test_list_by_category(self, registry):
        def t1():
            return {}

        def t2():
            return {}

        registry.register("t1", t1, "T1", {}, category="memory")
        registry.register("t2", t2, "T2", {}, category="file")

        assert len(registry.list_tools(category="memory")) == 1
        assert len(registry.list_tools(category="file")) == 1
        assert len(registry.list_tools()) == 2

    def test_get_tool_metadata(self, registry):
        def tool():
            return {}

        registry.register("tool", tool, "Desc", {"x": {"type": "integer"}})
        meta = registry.get_tool("tool")
        assert meta["name"] == "tool"
        assert meta["description"] == "Desc"
        assert meta["requires_confirmation"] is False

    def test_get_tool_not_found(self, registry):
        assert registry.get_tool("nope") is None

    def test_sync_rejects_async_func(self, registry):
        async def async_tool():
            return {}

        registry.register("async_tool", async_tool, "Async", {})
        with pytest.raises(RuntimeError, match="async"):
            registry.execute_sync("async_tool", {})


class TestActionVerifier:
    def test_safe_action_approved(self):
        verifier = ActionVerifier()
        result = verifier.verify("echo", {"message": "hello"})
        assert result["approved"] is True
        assert len(result["errors"]) == 0

    def test_dangerous_pattern_blocked(self):
        verifier = ActionVerifier()
        result = verifier.verify("shell", {"command": "rm -rf /"})
        assert result["approved"] is False
        assert any("rm" in e for e in result["errors"])

    def test_sql_injection_detected(self):
        verifier = ActionVerifier()
        result = verifier.verify("db", {"query": "DROP TABLE users"})
        assert result["approved"] is False

    def test_custom_rule_block(self):
        verifier = ActionVerifier()
        verifier.add_rule("no_admin", lambda t, p, c: p.get("role") != "admin", "Admin not allowed")
        result = verifier.verify("tool", {"role": "admin"})
        assert result["approved"] is False

    def test_custom_rule_pass(self):
        verifier = ActionVerifier()
        verifier.add_rule("check", lambda t, p, c: True, "Always ok")
        result = verifier.verify("tool", {})
        assert result["approved"] is True
        assert len(result["warnings"]) == 1

    def test_text_length_limit(self):
        verifier = ActionVerifier()
        result = verifier.verify("tool", {"text": "x" * 2_000_000})
        assert result["approved"] is False

    def test_list_length_limit(self):
        verifier = ActionVerifier()
        result = verifier.verify("tool", {"items": list(range(20_000))})
        assert result["approved"] is False

    def test_severity_ordering(self):
        verifier = ActionVerifier()
        result = verifier.verify("shell", {"command": "rm -rf /"})
        assert result["severity"] == "CRITICAL"

    def test_sudo_detected(self):
        verifier = ActionVerifier()
        result = verifier.verify("shell", {"command": "sudo apt install"})
        assert result["approved"] is False
        assert any("sudo" in e for e in result["errors"])
