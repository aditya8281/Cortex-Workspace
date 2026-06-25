"""Tests for @tool decorator and ToolRegistry."""

from __future__ import annotations

from backend.app.agents.tools.registry import Tool, ToolRegistry, tool, get_tool_registry


class TestToolRegistry:
    def setup_method(self):
        self.reg = ToolRegistry()

    def test_register_and_get(self):
        t = Tool(name="test", description="A test tool", handler=lambda: "ok")
        self.reg.register(t)
        assert self.reg.get("test") is t

    def test_get_missing_returns_none(self):
        assert self.reg.get("nonexistent") is None

    def test_list_tools(self):
        self.reg.register(Tool(name="a", description="Tool A", handler=lambda: ""))
        self.reg.register(Tool(name="b", description="Tool B", handler=lambda: ""))
        listing = self.reg.list_tools()
        assert listing == {"a": "Tool A", "b": "Tool B"}

    def test_get_all(self):
        t1 = Tool(name="a", description="Tool A", handler=lambda: "")
        t2 = Tool(name="b", description="Tool B", handler=lambda: "")
        self.reg.register(t1)
        self.reg.register(t2)
        all_tools = self.reg.get_all()
        assert len(all_tools) == 2
        assert t1 in all_tools
        assert t2 in all_tools

    def test_schemas_for_all(self):
        self.reg.register(Tool(name="a", description="Tool A", handler=lambda: "", schema={"s": 1}))
        self.reg.register(Tool(name="b", description="Tool B", handler=lambda: "", schema={"s": 2}))
        schemas = self.reg.schemas_for()
        assert len(schemas) == 2

    def test_schemas_for_filtered(self):
        self.reg.register(Tool(name="a", description="Tool A", handler=lambda: "", schema={"s": 1}))
        self.reg.register(Tool(name="b", description="Tool B", handler=lambda: "", schema={"s": 2}))
        schemas = self.reg.schemas_for(names=["a"])
        assert len(schemas) == 1
        assert schemas[0]["s"] == 1

    def test_remove(self):
        self.reg.register(Tool(name="a", description="Tool A", handler=lambda: ""))
        self.reg.remove("a")
        assert self.reg.get("a") is None

    def test_remove_nonexistent(self):
        self.reg.remove("nonexistent")  # should not raise

    def test_clear(self):
        self.reg.register(Tool(name="a", description="Tool A", handler=lambda: ""))
        self.reg.register(Tool(name="b", description="Tool B", handler=lambda: ""))
        self.reg.clear()
        assert self.reg.count == 0

    def test_count(self):
        assert self.reg.count == 0
        self.reg.register(Tool(name="a", description="Tool A", handler=lambda: ""))
        assert self.reg.count == 1

    def test_register_overwrites(self):
        t1 = Tool(name="a", description="First", handler=lambda: "one")
        t2 = Tool(name="a", description="Second", handler=lambda: "two")
        self.reg.register(t1)
        self.reg.register(t2)
        assert self.reg.get("a").description == "Second"


class TestToolDecorator:
    def test_tool_decorator_registers(self):
        registry = get_tool_registry()
        # Clean up any pre-existing tools for this test
        existing = [t.name for t in registry.get_all()]

        @tool(name="_test_my_fn", description="A test function")
        async def _test_my_fn(query: str, limit: int = 10) -> str:
            """A test function.

            Args:
                query: The search query
                limit: Max results
            """
            return f"Results for {query}"

        try:
            registered = registry.get("_test_my_fn")
            assert registered is not None
            assert registered.name == "_test_my_fn"
            assert registered.description == "A test function"
            # Should have auto-generated schema
            assert registered.schema != {}
            assert registered.schema["function"]["name"] == "_test_my_fn"
        finally:
            registry.remove("_test_my_fn")
            # Restore pre-existing tools
            for name in ["_test_my_fn"]:
                pass

    def test_tool_auto_schema_false(self):
        registry = get_tool_registry()

        @tool(name="_test_no_schema", description="No schema tool", auto_schema=False)
        async def _test_no_schema(x: str) -> str:
            return x

        try:
            registered = registry.get("_test_no_schema")
            assert registered is not None
            assert registered.schema == {}
        finally:
            registry.remove("_test_no_schema")

    def test_tool_name_defaults_to_func_name(self):
        registry = get_tool_registry()

        @tool()
        async def my_default_name() -> str:
            """Default name tool."""
            return "ok"

        try:
            assert registry.get("my_default_name") is not None
        finally:
            registry.remove("my_default_name")

    def test_tool_wrapper_preserves_functionality(self):
        @tool(name="_test_wrapper")
        async def _test_wrapper(x: str) -> str:
            """Test wrapper."""
            return f"got:{x}"

        import asyncio

        try:
            result = asyncio.run(_test_wrapper(x="hello"))
            assert result == "got:hello"
        finally:
            get_tool_registry().remove("_test_wrapper")

    def test_tool_requires_approval_flag(self):
        registry = get_tool_registry()

        @tool(name="_test_approval", description="Approval needed", requires_approval=True)
        async def _test_approval(x: str) -> str:
            return x

        try:
            t = registry.get("_test_approval")
            assert t is not None
            assert t.requires_approval is True
        finally:
            registry.remove("_test_approval")


class TestSingletonRegistry:
    def test_get_tool_registry_returns_same(self):
        r1 = get_tool_registry()
        r2 = get_tool_registry()
        assert r1 is r2
