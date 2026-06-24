# Batch 3 — Platform Architecture Findings

**Date:** 2026-06-25
**Repos:** Open WebUI, AnythingLLM, ollama-catalog
**Focus:** Workspace, provider, model management, settings, plugin/extension systems, local-first, deployment, desktop, multi-surface

---

## Open WebUI — The Mature Web Platform

### Architecture Summary

FastAPI backend + SvelteKit frontend. 118KB monolith `main.py`, 26 ORM models, 30+ API routers.

**Key pattern:** Single FastAPI app with inline router mounting. No microservices.

### Provider Architecture

No formal abstract base class. Each provider is a separate file in `utils/`:
- `utils/ollama.py` — Model listing, chat, streaming, pull/push, embeddings
- `utils/openai.py` — Chat completions, model listing, embeddings
- `utils/anthropic.py` — Messages API, streaming

**Multi-provider model aggregation:** Merges models from Ollama + OpenAI + custom endpoints + user-defined functions + pipelines into a unified list.

**Provider configuration:**
```python
OLLAMA_BASE_URL          # Default: http://localhost:11434
OLLAMA_API_BASE_URLS     # Multi-instance support
OPENAI_API_BASE_URLS     # List of base URLs
OPENAI_API_KEYS          # List of API keys
```

**Key insight:** Provider switching is env-var-driven, not interface-based. Each provider handles its own config parsing.

### Model Management

Models are resolved through a pipeline:
```
User selects model → resolve_model() →
  1. Check user-defined models table
  2. Check Ollama local models
  3. Check OpenAI API models
  4. Check custom endpoint models
  5. Check function-defined models
  → Route to appropriate provider client
```

**ORM Model:** `Model` with `id, user_id, base_model_id, name, meta, access_control`

**Operations:** List, get, create, update, delete, pull from Ollama, list tags.

### Settings Architecture (3-tier)

**Tier 1: Environment Variables** (`env.py` — ~1072 lines)
- Immutable at runtime for most values
- Covers: paths, database, auth, providers, RAG, Redis, timeouts, features

**Tier 2: Persistent Config** (`config.py` — ~4000 lines)
```python
class PersistentConfig:
    """Config value that syncs between memory and database"""
class AppConfig:
    WEBUI_NAME, WEBUI_FAVICON_URL, DEFAULT_MODELS
    OLLAMA_API_BASE_URLS, OPENAI_API_BASE_URLS
    ENABLE_RAG_HYBRID_SEARCH, RAG_TOP_K
    # ... hundreds more
```

**Tier 3: User Settings** — Per-user overrides stored in `users.settings` JSON column.

**Key insight:** `PersistentConfig` pattern — env vars set defaults, DB stores runtime changes, user overrides per-user. Clean separation.

### Plugin/Extension System (6 layers!)

| Layer | Purpose | Example |
|-------|---------|---------|
| **Functions** | User-uploaded Python files, define models/filters/actions | Custom model endpoint |
| **Tools** | Code-execution tools callable by LLMs | Calculator, web search |
| **Skills** | Template-based prompts (PROMPT or PIPELINE type) | Code review prompt |
| **Pipelines** | Multi-step processing chains | RAG pipeline, summarization |
| **Filters** | Pre/post-processing hooks for messages | Content filter, translation |
| **Actions** | Event-driven triggers | Auto-summarize on chat end |

**Loading:** Dynamic `importlib` loading from DB-stored source code. Frontmatter for requirements.

**Key insight:** 6 distinct extension layers is the most mature open-source extensibility system for LLM platforms.

### Local-First Architecture

- **Default:** Connects to Ollama at localhost:11434
- **SQLite default** — no external database needed
- **No cloud required** — runs entirely on local hardware
- **Minimal deps:** Python + Node.js + Ollama = 3 processes

### Desktop Suitability

**NOT desktop-ready.** Web-only, no native shell, no system tray, 3+ processes. But the architecture (SQLite + single port + Ollama) is appropriate for desktop wrapping.

### What Cortex Can Learn

1. **PersistentConfig pattern** — Env → DB → User overrides. Clean configuration hierarchy.
2. **6-layer plugin architecture** — Functions, tools, skills, pipelines, filters, actions. Most mature extensibility.
3. **Multi-provider model aggregation** — Unified model list from multiple backends.
4. **OpenAI-compatible API** — Expose Cortex capabilities via standard API.
5. **Workspace-level provider overrides** — Each workspace can use different LLM/embedding.

---

## AnythingLLM — The Triple Abstraction Champion

### Architecture Summary

Node.js monorepo: Express backend + Next.js frontend + Python collector. 35 LLM providers, 15 embedding engines, 10 vector DBs.

**Key pattern:** Convention-based provider interfaces (no formal base class, but consistent method signatures).

### Provider Architecture (Triple Abstraction)

**LLM Providers (35):**
```
anthropic, apipie, azureOpenAi, bedrock, cerebras, cohere,
deepseek, dockerModelRunner, fireworksAi, foundry, gemini,
genericOpenAi, giteeai, groq, koboldCPP, lemonade, liteLLM,
lmStudio, localAi, minimax, mistral, moonshotAi, novita,
nvidiaNim, ollama, openAi, openRouter, perplexity, ppio,
privatemode, sambanova, textGenWebUI, togetherAi, xai, zai
```

**Each provider implements:**
- `constructor(embedder, modelPreference)` — SDK init
- `streamGetChatCompletion()` / `getChatCompletion()` — inference
- `promptWindowLimit()` — context window size
- `isValidChatCompletionModel()` — model validation

**Embedding Engines (15):** azureOpenAi, cohere, gemini, genericOpenAi, lemonade, liteLLM, lmstudio, localAi, mistral, native, ollama, openAi, openRouter, voyageAi

**Vector DBs (10):** astra, chroma, chromacloud, lance, milvus, pgvector, pinecone, qdrant, weaviate, zilliz

**Key insight:** Convention-based interface (no ABC) but consistent method signatures across all providers. Each provider is a self-contained directory.

### Model Management

**Model resolution flow:**
```
SystemSettings (global default) → Workspace (override) → ModelRouter (dynamic rules) → Provider
```

**Dynamic Model Router:** Rules-based routing per workspace:
1. Calculated rules (always evaluated, free)
2. LLM-based rules (uses cached LLM calls)
3. Sticky route (previous model stays if not expired)
4. Default model (workspace/system default)

**Context Window Finder:** Fetches context window sizes from LiteLLM's remote JSON, caches locally for 3 days. Falls back to hardcoded map.

**Key insight:** Dynamic model routing is a powerful pattern — route different queries to different models based on rules.

### Settings Architecture (2-tier)

**System Settings:** Key-value pairs in SQLite `system_settings` table. Protected fields for critical config.

**Workspace Settings:** ~30+ fields per workspace including:
- `chatProvider` / `chatModel` — per-workspace LLM override
- `agentProvider` / `agentModel` — agent-specific LLM
- `topN`, `similarityThreshold`, `vectorSearchMode` — retrieval settings
- `chatMode` (automatic/query/chat)
- `router_id` — links to model router

**Key insight:** Workspace-level provider overrides enable per-project customization.

### Plugin/Extension System

**Agent Skills:** Whitelist-based, managed per model.
**Agent Flows:** No-code visual flow builder.
**MCP Compatibility:** Connects to external MCP servers via hypervisor pattern.
**Extensions:** GitHub/GitLab repo sync.
**Community Hub:** Marketplace for importing/exporting agent flows, prompts, commands.
**Slash Commands:** Chat commands + user-defined custom commands.
**Embeddable Widgets:** Standalone React widget for website integration.

**Key insight:** MCP hypervisor pattern — AnythingLLM can connect to external tool servers and manage their lifecycle.

### Collector Architecture

**Separate Python (Flask) microservice** for document ingestion:
```
Files → hotdir/ → Collector watches → processes → outputs text chunks → Server indexes into vector DB
```

**Extension system:** GitHub/GitLab repo sync via collector extensions.

**Key insight:** Separating ingestion from the main server allows independent scaling and language choice (Python for document parsing).

### Desktop Suitability

**Downloads exist** (Mac/Win/Linux) but NO Electron/Tauri in repo. Likely uses bundled binary approach. SQLite is excellent for desktop. Local-first by design.

### What Cortex Can Learn

1. **Triple abstraction layer** — LLM + Embedding + VectorDB, each independently switchable. Clean separation.
2. **Dynamic model routing** — Rules-based routing per workspace. Route different queries to different models.
3. **Context Window Finder** — Remote JSON + cache + fallback. Avoids hardcoding model capabilities.
4. **MCP hypervisor pattern** — Connect to external tool servers, manage their lifecycle.
5. **Collector proxy pattern** — Separate ingestion service. Clean separation of concerns.
6. **Community Hub** — Marketplace for sharing extensions, prompts, flows.

---

## ollama-catalog — Model Metadata Aggregator

### What It Is

A discovery and cataloging tool that aggregates metadata for **773+ Ollama models** without downloading weights. Probes OCI registry, cloud API, and local instance.

**Key insight:** Model metadata is valuable independent of model weights. Catalog enables informed model selection.

### Data Model

| Field | Type | Purpose |
|-------|------|---------|
| `name` | string | `model:tag` identifier |
| `source` | string | cloud / local / registry |
| `size_bytes` | int | Download size |
| `family` | string | Architecture family (llama, qwen2, deepseek2) |
| `parameter_size` | string | 7B, 70B, 671B |
| `quantization_level` | string | Q4_K_M, Q8_0, F16 |
| `capabilities` | list | completion, thinking, tools, vision |
| `projector_size` | int | Vision projector size |
| `also_available_on` | list | Cross-source availability |

### Capability Detection

| Capability | Detection Pattern |
|-----------|-------------------|
| Tools | `{{ .Tools }}`, `[AVAILABLE_TOOLS]`, `"tool_calls"` |
| Vision | `{{ .Images }}`, `image_url` |
| Thinking | `{{ .ThinkingEnabled }}`, `<thinking>` |
| Completion | Default capability (always present) |

### What Cortex Can Learn

1. **Model metadata as first-class concept** — Track family, parameter count, quantization, capabilities independent of weights.
2. **Capability detection from templates** — Automatically detect what a model can do.
3. **Cross-source availability** — Know if a model is available locally, in registry, or in cloud.
4. **Size-aware model management** — Track download size, disk usage, VRAM requirements.

---

## Cortex Current Platform Architecture

### Provider System

**Current state:** `llm_manager` singleton with basic provider switching. No formal abstraction layer.

**LLM Manager:** Configures provider from env vars (`LLM_PROVIDER`). Supports: auto, openai, anthropic, ollama, lmstudio, mock.

**Embedding Service:** Three-tier fallback (ONNX → Ollama → Mock). Not pluggable — hardcoded tiers.

**Vector DB:** Qdrant-only. No abstraction for swapping.

**Key gap:** No formal provider abstraction. Each provider is handled inline, not via interface.

### Model Management

**Current state:** `ModelCatalog` + `ModelVariant` + `Provider` + `Quantization` models in PostgreSQL.

**What exists:**
- Model metadata storage (name, family, parameters, quantization)
- Provider tracking
- Download management
- Installation status

**What's missing:**
- No capability detection
- No model routing (which query → which model)
- No context window tracking
- No dynamic model switching per workspace/project

### Settings Architecture

**Current state:** Pydantic `Settings` class loaded from env vars. No runtime-mutable config. No per-user overrides.

**What exists:**
- `config.py` with env-var-based settings
- Database-backed settings (via `settings` router)

**What's missing:**
- No PersistentConfig pattern (env → DB → user)
- No per-workspace settings
- No per-user preference overrides
- No runtime config UI

### Plugin/Extension System

**Current state:** None. No extensibility mechanism.

**What exists:**
- Skills in `.agents/skills/` (file-based, not runtime-loadable)
- Agent system (basic)

**What's missing:**
- No function/tool/skill runtime loading
- No pipeline system
- No filter/action hooks
- No MCP integration
- No community marketplace

### Desktop Suitability

**Current state:** FastAPI backend only. No desktop shell. No system tray. No native notifications.

**What exists:**
- FastAPI server (localhost:8000)
- Next.js frontend (localhost:3000)
- Docker Compose for services

**What's missing:**
- No Tauri/Electron shell
- No system tray integration
- No auto-start
- No native file association
- No offline-first packaging

---

## Comparative Platform Analysis

| Dimension | Open WebUI | AnythingLLM | Cortex |
|-----------|-----------|-------------|--------|
| **Provider abstraction** | File-per-provider, no ABC | Convention-based, no ABC | Inline handling, no ABC |
| **Provider count** | 3 (Ollama, OpenAI, Anthropic) | 35+ LLM, 15 embedding, 10 vector | 4 LLM, 1 embedding, 1 vector |
| **Model routing** | Single model per workspace | Dynamic rules-based routing | None |
| **Settings tiers** | 3 (env → DB → user) | 2 (system → workspace) | 1 (env only) |
| **Plugin layers** | 6 (functions, tools, skills, pipelines, filters, actions) | 5 (skills, flows, MCP, extensions, hub) | 0 |
| **Local-first** | Yes (SQLite + Ollama) | Yes (SQLite + local LLM) | Partial (PostgreSQL + Qdrant) |
| **Desktop readiness** | Web-only | Web-only (downloads exist) | Web-only |
| **Workspace concept** | Not explicit | Yes (primary org unit) | repo_id scoping |
| **MCP support** | No | Yes (hypervisor) | No |
| **Community marketplace** | No | Yes (Community Hub) | No |
| **OpenAI-compatible API** | Yes | Yes | No |
| **CLI** | No | No | Scaffolded (15 stubs) |
| **Multi-surface** | Web + API + WebSocket | Web + API + Widget | Web + API |

---

## Key Findings for Cortex's Daemon-First Architecture

### 1. Provider Abstraction is the #1 Platform Gap

**Current:** Cortex handles LLM providers inline in `llm_manager`. No formal interface. Adding a new provider requires modifying core code.

**Reference:** Open WebUI (file-per-provider), AnythingLLM (directory-per-provider with convention).

**Recommendation:** Create a formal `LLMProvider` Protocol (PEP 544) with standard methods: `generate()`, `stream()`, `context_window()`, `list_models()`. Each provider in its own module. Register via factory.

### 2. Model Routing is a Daemon-Mode Superpower

**Current:** Cortex uses one model for everything. No routing.

**Reference:** AnythingLLM's `AnythingLLMModelRouter` — rules-based routing per workspace.

**Daemon opportunity:** Cortex daemon can route queries to different models based on:
- Task type (code → CodeLlama, chat → Llama, analysis → GPT-4)
- Context window requirements
- Latency requirements
- User preference

### 3. Settings Architecture Needs Three Tiers

**Current:** Env vars only. No runtime config. No per-user.

**Reference:** Open WebUI's PersistentConfig (env → DB → user).

**Daemon opportunity:** 
- Tier 1: Env vars (immutable)
- Tier 2: Daemon config (runtime-mutable, stored in PostgreSQL)
- Tier 3: Per-user preferences (stored in user profile)

### 4. Plugin Architecture Should Be Layered

**Current:** No extensibility mechanism.

**Reference:** Open WebUI's 6 layers. AnythingLLM's 5 layers + MCP.

**Daemon opportunity:** Start with 3 layers for daemon mode:
- **Providers:** LLM, embedding, vector store (formal interfaces)
- **Tools:** Function-calling tools (MCP-compatible)
- **Pipelines:** Processing chains (indexing, consolidation, retrieval)

### 5. MCP Integration is Table Stakes

**Current:** No MCP support.

**Reference:** AnythingLLM's MCP hypervisor pattern.

**Daemon opportunity:** Cortex daemon can act as MCP server (expose tools) AND client (connect to external tools). This is the standard for tool interop.

### 6. Workspace/Project Scoping is Missing

**Current:** `repo_id` scoping is the only organizational unit.

**Reference:** AnythingLLM's Workspace concept (30+ settings per workspace, per-workspace model overrides).

**Daemon opportunity:** Cortex's "vault" concept can become the workspace equivalent. Each vault gets its own:
- Model configuration
- Indexing rules
- Retrieval settings
- Memory scope
- Plugin configuration

### 7. Local-First Means SQLite for Desktop

**Current:** PostgreSQL required.

**Reference:** Open WebUI (SQLite default), AnythingLLM (SQLite via Prisma).

**Daemon opportunity:** For desktop mode, SQLite is the right choice. PostgreSQL for server/power-user mode. The service abstraction layer (Phase 2) enables this swap.

### 8. OpenAI-Compatible API Enables Ecosystem Integration

**Current:** Custom REST API only.

**Reference:** Open WebUI (`/v1/chat/completions`), AnythingLLM (`/v1/openai`).

**Daemon opportunity:** Expose Cortex capabilities via OpenAI-compatible API. This enables integration with any tool that speaks OpenAI protocol (Continue, Cursor, etc.).
