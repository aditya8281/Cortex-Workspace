Last updated: 2026-06-28

# ADR-015: MCP Integration (v1.02 P04)

**Date:** 2026-06-27
**Status:** Accepted
**Deciders:** Cortex Team

---

## Context

CORTEX needs to consume external tools from MCP-compatible servers. Without MCP, the system is limited to its built-in tool set. MCP enables interoperability with any MCP server — filesystem access, database queries, API integrations, custom tools — without implementing them natively.

## Decision

Implement MCP integration with five core components:

### 1. MCP Server Discovery and Lifecycle
- `MCPServerDiscovery` class manages server lifecycle
- Servers configured via YAML or programmatic API
- Health monitoring every 30 seconds
- Automatic restart on failure (max 3 retries)
- Graceful shutdown on daemon stop
- Server states: discovered, starting, running, healthy, unhealthy, restarting, stopped, failed

### 2. Tool Wrapping
- `MCPToolWrapper` translates MCP tools to OpenAI function-calling format
- Namespaced tool names: `mcp_{server}_{tool}` to prevent collisions
- Description prefix: `[MCP:{server}]` for provenance
- Result translation: MCP content array → Cortex dict/JSON
- Error handling: transport exceptions → `{"error": "..."}` response

### 3. Transport Layers
- `MCPTransport` ABC defines `send_request()` and `receive_events()`
- `StdioTransport` for local servers via subprocess stdin/stdout
- `SSETransport` for remote servers via HTTP POST + Server-Sent Events
- Request/response correlation via JSON-RPC `id` field
- Timeout handling (30s default for stdio)

### 4. Configuration Management
- `MCPConfigManager` with three configuration levels:
  - System-level: `mcp_servers.yaml` in CORTEX_ROOT
  - User-level: per-user allowlist/denylist
  - Session-level: temporary tool restrictions
- Allowlist takes priority over denylist when both present
- PyYAML dependency for config parsing

### 5. MCP Tool Search
- `MCPToolSearch` for RAG-based tool selection
- Embeds tool descriptions for vector similarity search
- Falls back to keyword search when embeddings unavailable
- Configurable `top_k` (default: 10)
- Cosine similarity for vector ranking

## Consequences

**Positive:**
- CORTEX can consume tools from any MCP-compatible server
- Clean separation: discovery, wrapper, transport, config, search
- Health monitoring with automatic restart
- Per-user tool filtering for security
- RAG-based tool selection scales to many MCP servers

**Negative:**
- New dependency: PyYAML for config parsing
- aiohttp dependency for SSE transport (optional, only needed for remote servers)
- Subprocess management for stdio transport adds complexity

**Mitigations:**
- PyYAML is a common, stable dependency
- aiohttp is only imported when SSE transport is used
- Subprocess handling follows asyncio best practices with proper cleanup

## References

- MCP Protocol Specification: https://spec.modelcontextprotocol.io
- Constitution Section 4.6: Agent Architecture
- Constitution Section 10.2: Tools Have Schemas
- Constitution Section 3.5: Plugin Boundaries Early
