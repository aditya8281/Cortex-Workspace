# CORTEX V6: "The Ecosystem"

**Version:** 6
**Date:** 2026-06-25
**Status:** Planned

---

## 1. Goals

V6 transforms CORTEX from a product into a platform. Community plugins, workflow orchestration, advanced graph intelligence, and ecosystem governance make Cortex the foundation for an open AI workspace ecosystem.

This is the version where the community takes Cortex beyond what the core team can build alone. The plugin system matures. The graph becomes truly intelligent. Workflows become composable. The ecosystem becomes self-sustaining.

### Primary Goals

1. **Community plugin marketplace** — Discover, install, rate, and publish plugins
2. **Workflow DAGs** — Visual workflow editor, multi-step agent orchestration
3. **Advanced graph intelligence** — Community detection, multi-hop traversal, graph visualization
4. **Cross-encoder reranking** — GPU-accelerated reranking for search quality
5. **Ecosystem governance** — Plugin security, community standards, effectiveness metrics

### Non-Goals

- This is the final planned version. Beyond V6, the ecosystem evolves through community contribution, not versioned releases.

---

## 2. Scope

### 2.1 Community Plugin Marketplace

| Feature | V6 Implementation |
|---------|-------------------|
| Plugin registry | Central registry of community plugins |
| Discovery | Search, browse, filter by category/rating/popularity |
| Install | One-click install from marketplace |
| Update | Auto-update with version checking |
| Rating | Star ratings + reviews |
| Publishing | Developer portal for plugin submission |
| Security | Plugin scanning, sandboxing options, trust levels |
| Compatibility | Version compatibility checking |

**Scope boundary:** The marketplace is a web UI + CLI command. It connects to a central registry (could be GitHub-based initially). Plugin security starts with scanning, sandboxing deferred.

### 2.2 Workflow DAGs

| Feature | V6 Implementation | Source |
|---------|-------------------|--------|
| Visual editor | Drag-and-drop workflow builder | Strands workflow DAGs pattern |
| Node types | Agent, tool, condition, loop, parallel | Strands |
| Execution | Deterministic execution engine | Strands |
| Persistence | Workflows saved as JSON | Custom |
| Sharing | Export/import workflows | Custom |
| Triggers | Manual, cron, event, webhook | V4 scheduler integration |

**Scope boundary:** Workflows are agent orchestration — multiple agent steps in sequence/parallel with conditions. They are NOT business process automation (use n8n/Make for that via webhooks).

### 2.3 Advanced Graph Intelligence

| Feature | V6 Implementation | Source |
|---------|-------------------|--------|
| Community detection | Identify clusters of related entities | Graphiti pattern (deferred from V2) |
| Multi-hop traversal | Follow entity relationships across multiple hops | Graphiti pattern (deferred from V2) |
| Graph visualization | Interactive graph explorer in desktop shell + web UI | Custom |
| Graph queries | Natural language queries against the graph | Custom |
| Graph metrics | Centrality, clustering coefficient, path length | Custom |

**Scope boundary:** Advanced graph features require the richer entity graph from V2+ memory consolidation and LLM extraction. They are deferred to V6 because they need the data foundation first.

### 2.4 Cross-Encoder Reranking

| Feature | V6 Implementation | Source |
|---------|-------------------|--------|
| Cross-encoder model | GPU-accelerated reranking of search results | Deferred from V2 (D1) |
| Fallback | CPU-based reranking with quality trade-off | Custom |
| Integration | Reranking stage after MMR diversity | Custom |
| Model selection | User chooses reranking model based on GPU availability | Custom |

**Scope boundary:** Cross-encoder reranking requires GPU or API dependency. It is the final retrieval quality improvement. Everything else (RRF, MMR, entity boosting, adaptive normalization) is done by V4.

### 2.5 Ecosystem Governance

| Feature | V6 Implementation |
|---------|-------------------|
| Plugin security scanning | Automated security analysis of plugin code |
| Trust levels | Verified, community, experimental |
| Community standards | Plugin quality guidelines, coding standards |
| Effectiveness metrics | Governance hooks effectiveness measurement |
| ADR automation | Automatic ADR creation for architectural decisions |
| Skill creation workflows | Workflows for creating new skills from reusable patterns |

### 2.6 Additional V6 Capabilities

| Capability | Why |
|-----------|-----|
| UI control tool | Agent can manipulate desktop shell UI |
| Model serving cookbook | Guides for running models locally |
| Multi-agent swarms | Strands-style swarm orchestration for complex tasks |
| Knowledge graph explorer | Interactive graph visualization and query |
| Plugin analytics | Usage statistics for plugin authors |

---

## 3. Success Criteria

### Functional

| Criterion | Measure |
|-----------|---------|
| Plugin marketplace | 10+ community plugins available at launch |
| Workflow DAGs | User can create, save, execute multi-step workflows |
| Graph intelligence | Community detection identifies meaningful entity clusters |
| Cross-encoder | Search quality improves with reranking (measured by NDCG) |
| Ecosystem governance | Plugin security scanning operational |

### Quality

| Criterion | Measure |
|-----------|---------|
| Plugin security | All marketplace plugins pass security scan |
| Workflow reliability | Workflows execute deterministically |
| Graph quality | Community detection precision > 80% |
| Search improvement | Cross-encoder improves NDCG by > 5% |
| Test count | V5 count + new ecosystem tests |

---

## 4. User Impact

### Before V6

- CORTEX is a product built by the core team
- No community contribution path
- No visual workflow editor
- Graph intelligence is basic (code-only, no community detection)
- Search quality has a ceiling (no cross-encoder)

### After V6

- CORTEX is a platform with community plugins
- Visual workflow editor for multi-step agent orchestration
- Advanced graph intelligence (community detection, multi-hop)
- Best-in-class search with cross-encoder reranking
- Self-sustaining ecosystem

### Who Benefits

| User | How |
|------|-----|
| Plugin developers | Marketplace, publishing, analytics |
| Power users | Workflow DAGs, advanced graph queries |
| All users | Cross-encoder improves search quality |
| Community | Open platform, contribution guidelines, governance |

---

## 5. Architecture Impact

### What Changes

```
V5:
  Cortex = product (core team builds everything)

V6:
  Cortex = platform (community extends via plugins)
  Workflows = composable agent orchestration
  Graph = advanced intelligence (community detection, multi-hop)
  Search = cross-encoder reranking
```

### New Components

| Component | Purpose |
|-----------|---------|
| Plugin marketplace | Discovery, install, rating, publishing |
| Workflow engine | DAG execution, persistence, sharing |
| Graph intelligence | Community detection, multi-hop, visualization |
| Cross-encoder service | GPU-accelerated reranking |
| Plugin security scanner | Automated code analysis |
| Governance metrics | Hook effectiveness measurement |

### What Stays

| Component | Why |
|-----------|-----|
| All V1-V5 functionality | Complete workspace with daily productivity tools |
| Plugin system (V2) | Marketplace builds on existing plugin infrastructure |
| Event bus (V2) | Workflows use events |
| MCP (V2+V4) | MCP tools integrated into workflows |
| Scheduler (V4) | Workflows can be scheduled |

---

## 6. UX Impact

### Surfaces

| Surface | V6 Change |
|---------|-----------|
| Desktop shell | New: plugin marketplace, workflow editor, graph explorer |
| CLI | New commands: `cortex plugin search/install/publish`, `cortex workflow create/run`, `cortex graph explore` |
| API | New endpoints: marketplace, workflow CRUD, graph advanced queries |
| Web UI | New pages: plugin marketplace, workflow editor, graph explorer |

### Interaction Model

| Before V6 | After V6 |
|-----------|----------|
| User builds everything manually | Community provides plugins for common tasks |
| Agent executes single tasks | Workflows orchestrate multi-step processes |
| Graph shows code structure | Graph shows entire digital life with communities |
| Search is good | Search is best-in-class with cross-encoder |

---

## 7. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Plugin security vulnerabilities | High | High | Security scanning, trust levels, sandboxing |
| Workflow complexity | Medium | Medium | Start with simple linear workflows. Add complexity iteratively. |
| Cross-encoder performance | Medium | Medium | CPU fallback. Optional GPU acceleration. |
| Community adoption | Medium | High | Good documentation, plugin authoring guide, examples. |
| Graph quality with community detection | Medium | Medium | Tune algorithms against known data sets. |
| Maintenance burden of marketplace | Medium | Medium | Start with GitHub-based registry. Automate where possible. |

---

## 8. Exit Criteria (V6 Complete When)

- [ ] Plugin marketplace: discover, install, rate, publish
- [ ] 10+ community plugins available
- [ ] Workflow DAGs: visual editor, execution engine, persistence
- [ ] Community detection identifies meaningful entity clusters
- [ ] Multi-hop graph traversal works
- [ ] Graph visualization in desktop shell + web UI
- [ ] Cross-encoder reranking operational
- [ ] Search quality improves (NDCG > 5% improvement)
- [ ] Plugin security scanning operational
- [ ] Governance effectiveness metrics operational
- [ ] All V1-V5 tests pass
- [ ] New ecosystem tests
- [ ] Plugin authoring documentation complete
