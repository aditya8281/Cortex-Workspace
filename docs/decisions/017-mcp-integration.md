Last updated: 2026-06-28

# ADR-017: MCP Integration

**Status:** Proposed
**Date:** 2026-06-24
**Deciders:** Adi + Claude Code
**Phase:** V3 Phase 3

## Context

Cortex has zero MCP (Model Context Protocol) support. All reference repos (Continue, reference architecture, Strands) have MCP — it's table stakes for AI tool interoperability. MCP enables connecting to external tool servers and exposing Cortex tools to other agents.

## Decision

Start with MCP client only. Defer MCP server to later.

- **MCP Client:** Connect to external MCP servers to use their tools (filesystem, web, databases, etc.)
- **MCP Server (deferred):** Expose Cortex tools (memory search, vault, graph) to external agents

## Consequences

### Positive
- Access to external tool ecosystem immediately
- Foundation for server mode later

### Negative
- Client-only means Cortex tools aren't available to other agents yet
- MCP protocol may evolve

## Related

- V3 Phase 3 plan
