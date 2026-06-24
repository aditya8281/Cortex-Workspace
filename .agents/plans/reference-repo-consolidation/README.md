# Reference Repository Consolidation

**Date:** 2026-06-25

## Batches

| Batch | Repos | Domain |
|-------|-------|--------|
| **Batch 1** | Mem0, Graphiti | Memory, knowledge graphs, entities, relationships, temporal knowledge, retrieval, consolidation |
| **Batch 2** | LlamaIndex, sist2, turbovec | Indexing, retrieval, chunking, search, ranking, incremental indexing, vector storage, embeddings |
| **Batch 3** | Open WebUI, AnythingLLM, ollama-catalog | Platform architecture, providers, models, settings, plugins, local-first, desktop, multi-surface |
| **Batch 4** | Continue, Odysseus, Strands Tools | Agent architecture, orchestration, execution engines, workflows, tool systems, tool registries, planning, context gathering, repository intelligence, automation, command systems, CLI |

## Batch 1 Files (Memory & Knowledge Graphs)

| File | Contents |
|------|----------|
| `architecture-findings.md` | Architecture, subsystems, abstractions, service boundaries (Mem0, Graphiti) |
| `memory-model-findings.md` | Memory representation, storage, consolidation, evolution patterns |
| `graph-model-findings.md` | Graph model, temporal knowledge, entity extraction, traversal |
| `retrieval-findings.md` | Retrieval context construction, hybrid search, reranking |

## Batch 2 Files (Indexing & Retrieval)

| File | Contents |
|------|----------|
| `batch2-indexing-retrieval-findings.md` | LlamaIndex composable RAG, sist2 file search, turbovec quantized vectors |

## Batch 3 Files (Platform Architecture)

| File | Contents |
|------|----------|
| `batch3-platform-architecture-findings.md` | Open WebUI 6-layer plugins, AnythingLLM triple abstraction, ollama-catalog metadata |

## Batch 4 Files (Agent, Orchestration & Tool Systems)

| File | Contents |
|------|----------|
| `batch4-agent-orchestration-findings.md` | Continue 18-tool agent, Odysseus 30+ tool platform, Strands 47-tool library, @tool decorator, swarm, workflow DAG, MCP integration, context compaction, CLI architecture |

## Cross-Batch Integration Files

| File | Contents |
|------|----------|
| `cortex-gap-analysis.md` | **All 4 batches** — consolidated gap analysis against Cortex |
| `recommendations.md` | **All 4 batches** — ADOPT/ADAPT/MERGE/REPLACE/DEFER/REJECT classifications |
| `phase-impact-analysis.md` | **All 4 batches** — impact on daemon-first transition + parallel workstreams |
| `action-items.md` | **All 4 batches** — concrete next steps, ordered by priority |

## Batch Coverage

| Domain | Batch 1 | Batch 2 | Batch 3 | Batch 4 |
|--------|---------|---------|---------|---------|
| Memory consolidation | ✅ Primary | ❌ | ❌ | ❌ |
| Knowledge graphs | ✅ Primary | ❌ | ❌ | ❌ |
| Entity extraction | ✅ Primary | ❌ | ❌ | ❌ |
| Temporal knowledge | ✅ Primary | ❌ | ❌ | ❌ |
| Retrieval pipelines | ✅ Primary | ✅ Primary | ❌ | ❌ |
| Chunking strategies | ❌ | ✅ Primary | ❌ | ❌ |
| Vector storage | ❌ | ✅ Primary | ❌ | ❌ |
| Incremental indexing | ❌ | ✅ Primary | ❌ | ❌ |
| Search scoring | ❌ | ✅ Primary | ❌ | ❌ |
| Provider architecture | ❌ | ❌ | ✅ Primary | ❌ |
| Model management | ❌ | ❌ | ✅ Primary | ❌ |
| Settings/config | ❌ | ❌ | ✅ Primary | ❌ |
| Plugin/extension | ❌ | ❌ | ✅ Primary | ❌ |
| Desktop readiness | ❌ | ❌ | ✅ Primary | ❌ |
| Local-first patterns | ❌ | ✅ Secondary | ✅ Primary | ❌ |
| Agent architecture | ❌ | ❌ | ❌ | ✅ Primary |
| Tool systems | ❌ | ❌ | ❌ | ✅ Primary |
| Orchestration/workflow | ❌ | ❌ | ❌ | ✅ Primary |
| CLI architecture | ❌ | ❌ | ❌ | ✅ Primary |
| Context gathering | ❌ | ❌ | ❌ | ✅ Primary |
| Context compaction | ❌ | ❌ | ❌ | ✅ Primary |
| Event bus/automation | ❌ | ❌ | ❌ | ✅ Primary |
| Prompt security | ❌ | ❌ | ❌ | ✅ Primary |
| MCP integration | ❌ | ❌ | ✅ Secondary | ✅ Primary |
