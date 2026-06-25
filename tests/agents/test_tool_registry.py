"""Tests for @tool decorator and ToolRegistry."""

from __future__ import annotations

from backend.app.agents.tools.registry import Tool, ToolRegistry, get_tool_registry, tool


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


class TestToolDecoratorSync:
    """Tests for @tool decorator behavior with sync vs async functions."""

    def test_decorated_sync_function_stays_callable_sync(self):
        """A sync function wrapped with @tool should remain directly callable
        without `await`, returning the value — not a coroutine.
        """
        registry = get_tool_registry()

        @tool(name="_test_sync_direct", description="Sync test")
        def sync_tool(x: str) -> str:
            """Sync test.

            Args:
                x: Input string
            """
            return f"got:{x}"

        try:
            # Direct sync call should work and return value, not coroutine
            result = sync_tool(x="hello")
            assert result == "got:hello", f"Expected 'got:hello', got {result!r}"
            # Verify it's registered with handler being the original function
            registered = registry.get("_test_sync_direct")
            assert registered is not None
        finally:
            registry.remove("_test_sync_direct")

    def test_sync_tool_works_in_async_context(self):
        """Sync tools can be called directly from async functions."""
        registry = get_tool_registry()

        @tool(name="_test_sync_await2", description="Sync await test")
        def sync_tool(x: str) -> str:
            """Sync await test.

            Args:
                x: Input string
            """
            return f"res:{x}"

        try:

            async def caller():
                # Sync tool returns value directly (no await needed)
                return sync_tool(x="test")

            import asyncio

            result = asyncio.run(caller())
            assert result == "res:test"
        finally:
            registry.remove("_test_sync_await2")


class TestToolRegistrySync:
    """Additional ToolRegistry regression tests."""

    def test_register_with_empty_schema_listeds(self):
        """Tool with empty schema is included in list_tools but excluded from schemas_for."""
        reg = ToolRegistry()
        reg.register(Tool(name="no_schema", description="No schema", handler=lambda: "", schema={}))
        reg.register(Tool(name="with_schema", description="Has schema", handler=lambda: "", schema={"s": 1}))

        listing = reg.list_tools()
        assert "no_schema" in listing
        assert "with_schema" in listing

        schemas = reg.schemas_for()
        assert len(schemas) == 1  # only with_schema
        assert schemas[0]["s"] == 1


class TestSingletonRegistry:
    def test_get_tool_registry_returns_same(self):
        r1 = get_tool_registry()
        r2 = get_tool_registry()
        assert r1 is r2


class TestToolRegistryExecute:
    """ToolRegistry.execute() — tool execution dispatch."""

    def setup_method(self):
        self.reg = ToolRegistry()

    def test_execute_sync_tool(self):
        def my_tool(query: str) -> str:
            return f"result:{query}"

        self.reg.register(Tool(name="my_tool", description="A tool", handler=my_tool))

        import asyncio

        result = asyncio.run(self.reg.execute("my_tool", query="hello"))
        assert result == "result:hello"

    def test_execute_async_tool(self):
        async def my_async_tool(x: int) -> str:
            return f"got:{x}"

        self.reg.register(Tool(name="my_async_tool", description="Async tool", handler=my_async_tool))

        import asyncio

        result = asyncio.run(self.reg.execute("my_async_tool", x=42))
        assert result == "got:42"

    def test_execute_unknown_tool(self):
        import asyncio

        try:
            asyncio.run(self.reg.execute("nonexistent"))
            raise AssertionError("Should have raised")
        except ValueError as e:
            assert "nonexistent" in str(e)

    def test_execute_none_result_coerced_to_string(self):
        def returns_none() -> None:
            return None

        self.reg.register(Tool(name="returns_none", description="Returns none", handler=returns_none))

        import asyncio

        result = asyncio.run(self.reg.execute("returns_none"))
        assert result == ""

    def test_execute_int_result_coerced_to_string(self):
        def returns_int() -> int:
            return 42

        self.reg.register(Tool(name="returns_int", description="Returns int", handler=returns_int))

        import asyncio

        result = asyncio.run(self.reg.execute("returns_int"))
        assert result == "42"

    def test_execute_tool_preserves_handler_registration(self):
        """Calling execute doesn't remove the tool from registry."""

        def my_tool() -> str:
            return "ok"

        self.reg.register(Tool(name="persistent", description="Persistent tool", handler=my_tool))

        import asyncio

        asyncio.run(self.reg.execute("persistent"))
        assert self.reg.get("persistent") is not None
