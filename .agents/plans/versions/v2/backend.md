# V2 Backend: The Architecture

## Overview

V2 restructures the backend from a monolithic service layer into a composable, event-driven architecture with protocol-based service abstraction. Three phases: abstraction + event bus → MCP client + plugins → memory consolidation + context providers.

## File Structure (V2 additions)

```
backend/app/
├── core/
│   ├── providers/           # NEW: Protocol interfaces
│   │   ├── __init__.py
│   │   ├── llm.py           # Protocol[LLMProvider]
│   │   ├── embedding.py     # Protocol[EmbeddingProvider]
│   │   ├── vector_store.py  # Protocol[VectorStore]
│   │   ├── cache.py         # Protocol[CacheProvider]
│   │   ├── database.py      # Protocol[DatabaseProvider]
│   │   └── registry.py      # Provider registry + decorator
│   ├── events/              # NEW: Event bus
│   │   ├── __init__.py
│   │   ├── bus.py           # In-process pub/sub
│   │   ├── types.py         # Typed event dataclasses
│   │   └── tracing.py       # Event tracing + metadata
│   ├── config.py            # MODIFIED: add PersistentConfig support
│   ├── vector_db.py         # MODIFIED: implement VectorStore protocol
│   └── redis.py             # MODIFIED: implement CacheProvider protocol
├── services/
│   ├── llm/manager.py       # MODIFIED: implement LLMProvider protocol
│   ├── embedding_service.py # MODIFIED: implement EmbeddingProvider protocol
│   ├── memory/              # NEW: Memory consolidation
│   │   ├── __init__.py
│   │   ├── consolidator.py  # Pipeline orchestrator
│   │   ├── extractor.py     # LLM-based fact extraction
│   │   ├── deduplicator.py  # 3-level dedup
│   │   ├── contradictor.py  # Contradiction detection
│   │   └── bitemporal.py    # Bi-temporal tracking
│   ├── context/             # NEW: Composable context providers
│   │   ├── __init__.py
│   │   ├── provider.py      # Protocol[ContextProvider]
│   │   ├── manager.py       # Budget allocation + composition
│   │   ├── memory_provider.py
│   │   ├── graph_provider.py
│   │   ├── search_provider.py
│   │   ├── vault_provider.py
│   │   └── conversation_provider.py
│   ├── config/              # NEW: Configuration management
│   │   ├── __init__.py
│   │   └── persistent.py    # PersistentConfig hierarchy
│   ├── routing/             # NEW: Model routing
│   │   ├── __init__.py
│   │   └── model_router.py  # Task → model selection
│   └── mcp/                 # NEW: MCP client
│       ├── __init__.py
│       ├── client.py        # MCP protocol client
│       ├── manager.py       # MCP lifecycle management
│       ├── wrapper.py       # MCPTool wrapper
│       └── transports/
│           ├── __init__.py
│           ├── stdio.py     # Stdio transport
│           └── sse.py       # SSE transport
├── plugins/                 # NEW: Plugin system
│   ├── __init__.py
│   ├── loader.py            # Plugin discovery + loading
│   ├── base.py              # Plugin base classes
│   └── registry.py          # Plugin registry
├── models/
│   ├── event_log.py         # NEW: Event log table
│   ├── mcp_server.py        # NEW: MCP server config
│   ├── user_config.py       # NEW: UserConfig + SystemConfig
│   └── routing_rule.py      # NEW: Model routing rules
├── api/v1/
│   ├── mcp.py               # NEW: MCP server management API
│   ├── plugins.py           # NEW: Plugin management API
│   └── config.py            # NEW: Config management API
└── agents/
    └── loop.py              # MODIFIED: use ContextManager + ModelRouter
```

## Phase 1: Service Abstraction + Event Bus

### Protocol Interfaces

5 Protocol interfaces define contracts for all core services:

- **LLMProvider**: chat, stream_chat, embed, list_models, health
- **EmbeddingProvider**: embed, embed_batch, dimensions, health
- **VectorStore**: upsert, search, delete, list_collections, health
- **CacheProvider**: get, set, delete, health
- **DatabaseProvider**: session, health

### Provider Registry

Decorator-based registration:
```python
@register_provider("llm", "ollama")
class OllamaProvider(LLMProvider): ...

@register_provider("llm", "openai")
class OpenAIProvider(LLMProvider): ...
```

Runtime lookup: `get_provider("llm", "ollama")` or `get_default_provider("llm")`.

### Event Bus

In-process pub/sub with typed events:
- FileChanged, MemoryDecayed, IndexComplete
- EntityDiscovered, ConversationArchived
- AgentRunComplete, JobStarted/Completed/Failed

Events logged to PostgreSQL for tracing. No external dependency (no RabbitMQ, no Kafka).

### Migration

Alembic migration `d00000000001_event_log.py` creates event_log table with columns: id, event_type, payload (JSONB), source, created_at, metadata (JSONB).

## Phase 2: MCP Client + Plugin System

### MCP Client

Two transports:
- **Stdio**: for local MCP servers (spawn process, communicate via stdin/stdout)
- **SSE**: for remote MCP servers (HTTP Server-Sent Events)

MCPTool wraps external tools:
```python
class MCPTool:
    name = f"mcp_{server.name}_{tool_name}"
    description = tool_schema["description"]
    schema = tool_schema["inputSchema"]

    async def execute(self, **kwargs) -> str:
        return await self.server.client.call_tool(self.name, kwargs)
```

### Plugin System

3 layers:
- **Providers**: Register new LLM/embedding/vector store providers
- **Tools**: Register new agent tools
- **Pipelines**: Register new processing pipelines (e.g., custom extraction)

Plugin discovery: scan `~/.cortex/plugins/`, each with manifest.json.

### Migration

Alembic migration `d00000000002_mcp_servers.py` creates mcp_servers table.

## Phase 3: Memory Consolidation + Context Providers

### Memory Consolidation Pipeline

Triggered by events (index_complete, conversation_archived):

1. **Extractor** (LLM): conversation/document → structured facts
2. **Deduplicator** (3-level): batch dedup → vector dedup → hash dedup
3. **Contradictor** (LLM): new facts vs existing facts → invalidate contradictions
4. **Merger**: consolidate duplicates, keep highest confidence
5. **Confidence**: assign initial confidence + decay formula

### Context Provider Architecture

Replace monolithic hybrid_retrieval.py:

```python
class ContextProvider(Protocol):
    name: str
    priority: int

    async def gather(self, query: str, token_budget: int) -> list[ContextChunk]: ...
    def token_count(self, chunks: list[ContextChunk]) -> int: ...
```

5 providers: memory, graph, search, vault, conversation. Each independent, token-budgeted. ContextManager allocates budget by priority, composes results.

### PersistentConfig

4-level override chain:
1. Environment variables (highest)
2. Database SystemConfig (admin)
3. Database UserConfig (per-user)
4. Code defaults (lowest)

### Model Routing

Task-specific model selection:
- Agent conversation → user's preferred model
- Memory extraction → cheaper/faster model
- Context compaction → cheaper/faster model
- Embedding → ONNX/Ollama (existing)

### Migrations

- `d00000000003_memory_pipeline.py`: memory pipeline schema changes
- `d00000000004_config_tables.py`: user_config, system_config tables
- `d00000000005_routing_rules.py`: model routing rules table

## Testing Strategy

| Test Category | Count Target | Approach |
|--------------|-------------|----------|
| Protocol compliance | 25+ | Each provider implements protocol correctly |
| Event bus | 20+ | Publish/subscribe, tracing, error handling |
| MCP client | 30+ | Connect, list tools, call tools, error recovery |
| Plugin system | 15+ | Discovery, loading, registration |
| Memory consolidation | 40+ | Extract, dedup, contradict, merge |
| Context providers | 25+ | Each provider, budget allocation, composition |
| Config hierarchy | 15+ | Override chain, per-user, persistence |
| Model routing | 10+ | Task → model selection |
| **Total V2** | **180+** | |

## Performance Targets

- Event bus publish/subscribe: < 1ms per event
- MCP tool call overhead: < 50ms (excluding server processing)
- Memory consolidation: < 30s per conversation
- Context provider gather: < 500ms total
- Config lookup: < 1ms (cached)

## Database Changes

4 new tables across 5 migrations:
- event_log (Phase 1)
- mcp_servers (Phase 2)
- user_config, system_config (Phase 3)
- model_routing_rules (Phase 3)
- long_term_memory modifications: valid_at, invalid_at, extraction_method (Phase 3)
