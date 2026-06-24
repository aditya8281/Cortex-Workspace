# V2 Phase 2: MCP Client + Plugin System

**Duration estimate:** 5-7 days
**Dependencies:** V2 Phase 1 complete (service abstractions in place)
**Risk:** Medium — MCP ecosystem still evolving

---

## Goals

Build MCP client that connects to external servers and wraps their tools as native Cortex tools. Define 3-layer plugin architecture (providers, tools, pipelines). Plugin authoring guide. First community-facing extension points.

## Deliverables

1. MCP client (stdio + SSE transports)
2. MCPTool wrapper for external tools
3. MCP server registry (database-backed)
4. 3-layer plugin architecture (providers, tools, pipelines)
5. Plugin discovery (~/.cortex/plugins/)
6. Plugin authoring guide
7. Plugin management CLI commands

## Architectural Changes

```
BEFORE:
  Cortex tools only (5-15 tools)

AFTER:
  Cortex tools + MCP tools (external) = unified tool registry
  Plugin registry: ~/.cortex/plugins/ scanned on startup
  3 layers: providers | tools | pipelines
```

## Backend Changes

### New Files

| File | Purpose |
|------|---------|
| `backend/app/services/mcp/__init__.py` | MCP package init |
| `backend/app/services/mcp/client.py` | MCP client: connect, list tools, call tools |
| `backend/app/services/mcp/manager.py` | MCP lifecycle: start, stop, health, reconnect |
| `backend/app/services/mcp/wrapper.py` | MCPTool: wrap external MCP tool as native Cortex tool |
| `backend/app/services/mcp/transports/stdio.py` | Stdio transport for local MCP servers |
| `backend/app/services/mcp/transports/sse.py` | SSE transport for remote MCP servers |
| `backend/app/models/mcp_server.py` | MCPServer SQLAlchemy model |
| `backend/app/plugins/__init__.py` | Plugin package init |
| `backend/app/plugins/loader.py` | Plugin discovery + lazy loading |
| `backend/app/plugins/base.py` | Plugin base classes for each layer |
| `backend/app/api/v1/mcp.py` | MCP server management API routes |
| `migrations/versions/d00000000002_mcp_servers.py` | MCP server table migration |
| `docs/PLUGIN_GUIDE.md` | Plugin authoring guide |

### MCP Client Design

**MCPTool wrapper:**
```python
class MCPTool:
    """Wraps an external MCP tool as a native Cortex tool."""
    def __init__(self, server: MCPServer, tool_name: str, tool_schema: dict):
        self.server = server
        self.name = f"mcp_{server.name}_{tool_name}"
        self.description = tool_schema["description"]
        self.schema = tool_schema["inputSchema"]

    async def execute(self, **kwargs) -> str:
        return await self.server.client.call_tool(self.name, kwargs)
```

**Plugin loader:**
```python
class PluginLoader:
    """Scans ~/.cortex/plugins/ and loads plugins lazily."""
    def scan(self) -> list[PluginManifest]:
        # Read plugin directories, parse manifests
        ...

    def load(self, plugin_id: str) -> Plugin:
        # Import plugin module, instantiate, register
        ...
```

### Modified Files

| File | Change |
|------|--------|
| `backend/app/agents/tools/registry.py` | Accept MCPTool registrations alongside @tool |
| `backend/app/api/v1/router.py` | Mount MCP routes |
| `cli/src/commands/mcp.ts` | New CLI commands: mcp list, mcp add, mcp remove, mcp status |

## Frontend Changes

| Page | Change |
|------|--------|
| Settings | New "MCP Servers" section: list, add, remove, status |
| Settings | New "Plugins" section: installed plugins, enable/disable |
| Agent | MCP tools appear in tool list alongside native tools |

## Memory Changes

No changes.

## Retrieval Changes

No changes.

## Agent Changes

Agent tool registry now includes MCP tools. When agent needs a tool, it checks: native tools → MCP tools → deny.

## Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| MCP server crashes | High | Medium | Graceful degradation. Failed servers don't block others. |
| MCP tool naming conflicts | Medium | Medium | Namespace: `mcp_{server}_{tool}` |
| Plugin loading failures | Medium | Medium | Catch + log. Don't crash daemon. |

## Exit Criteria

- [ ] MCP client connects to external stdio server
- [ ] MCP client connects to external SSE server
- [ ] External tools appear as native Cortex tools
- [ ] MCP server registry in database
- [ ] Plugin loader scans ~/.cortex/plugins/
- [ ] Plugin authoring guide published
- [ ] CLI: mcp list/add/remove/status works
- [ ] Settings UI shows MCP servers + plugins
- [ ] All V1 + V2 Phase 1 tests pass
- [ ] New MCP + plugin tests
