# V4 Phase 3: Deep Research Engine + Integration Testing

**Duration estimate:** 7-10 days
**Dependencies:** V4 Phase 1 (scheduler), V4 Phase 2 (sessions, MCP server)
**Risk:** Medium — research engine quality, multi-source aggregation

---

## Goals

Build deep research engine for multi-step web research with HTML report generation. Add integration testing across all V4 systems (scheduler + webhooks + sessions + MCP server). Polish automation features. Final hardening.

## Deliverables

1. Deep research engine (multi-step web research)
2. Research report generation (HTML + Markdown)
3. Research session integration (research within sessions)
4. Research scheduling (recurring research tasks)
5. Integration test suite for V4
6. Performance benchmarks
7. Error handling and recovery

## Architectural Changes

```
BEFORE:
  Research = manual (user searches, reads, summarizes)

AFTER:
  Research = automated multi-step pipeline:
    1. Decompose research question into sub-queries
    2. Execute sub-queries (web search + content extraction)
    3. Synthesize findings across sources
    4. Identify gaps → generate follow-up queries
    5. Iterate until comprehensive or budget exhausted
    6. Generate structured report (HTML + Markdown)
```

## Backend Changes

### New Files

| File | Purpose |
|------|---------|
| `backend/app/services/research/__init__.py` | Research engine package |
| `backend/app/services/research/engine.py` | Main research orchestrator |
| `backend/app/services/research/decomposer.py` | Question decomposition (LLM) |
| `backend/app/services/research/collector.py` | Web search + content extraction |
| `backend/app/services/research/synthesizer.py` | Multi-source synthesis (LLM) |
| `backend/app/services/research/gap_detector.py` | Follow-up query generation |
| `backend/app/services/research/reporter.py` | HTML + Markdown report generation |
| `backend/app/services/research/budget.py` | Research budget management (tokens, time, sources) |
| `backend/app/models/research.py` | ResearchSession + ResearchReport models |
| `backend/app/api/v1/research.py` | Research API endpoints |
| `migrations/versions/d00000000008_research.py` | Research tables migration |

### Research Engine Pipeline

```python
class ResearchEngine:
    """Multi-step deep research with synthesis and reporting."""

    async def research(
        self,
        question: str,
        session_id: str | None = None,
        budget: ResearchBudget | None = None,
    ) -> ResearchReport:
        """
        Execute deep research pipeline.

        1. Decompose question into sub-queries
        2. For each sub-query: search + extract
        3. Synthesize findings
        4. Detect gaps → generate follow-ups
        5. Repeat until budget exhausted or comprehensive
        6. Generate report
        """
        budget = budget or ResearchBudget(max_queries=20, max_tokens=100_000, max_time_s=300)

        # Phase 1: Decompose
        sub_queries = await self.decomposer.decompose(question)

        all_findings = []
        iteration = 0

        while budget.has_remaining(iteration):
            # Phase 2: Collect
            for query in sub_queries:
                if not budget.has_remaining(iteration):
                    break
                results = await self.collector.collect(query)
                all_findings.extend(results)
                budget.consume(iteration, tokens_used=len(str(results)))

            # Phase 3: Synthesize
            synthesis = await self.synthesizer.synthesize(question, all_findings)

            # Phase 4: Gap detection
            gaps = await self.gap_detector.detect(question, synthesis)
            if not gaps or not budget.has_remaining(iteration + 1):
                break

            sub_queries = gaps
            iteration += 1

        # Phase 5: Report
        report = await self.reporter.generate(question, synthesis, all_findings)

        # Store in session if provided
        if session_id:
            await self._store_report(session_id, report)

        return report
```

### Research Budget

```python
@dataclass
class ResearchBudget:
    max_queries: int = 20         # Maximum search queries
    max_tokens: int = 100_000     # Maximum LLM tokens consumed
    max_time_s: int = 300         # Maximum time in seconds
    max_sources: int = 50         # Maximum unique sources

    def has_remaining(self, iteration: int) -> bool:
        return (self.queries_used < self.max_queries and
                self.tokens_used < self.max_tokens and
                self.time_used < self.max_time_s)

    def consume(self, iteration: int, tokens_used: int) -> None:
        self.queries_used += 1
        self.tokens_used += tokens_used
        ...
```

### Report Generation

HTML report structure:
```html
<html>
  <body>
    <h1>Research: {question}</h1>
    <div class="meta">
      <span>Sources: {count}</span>
      <span>Date: {date}</span>
      <span>Queries: {queries_used}</span>
    </div>
    <div class="executive-summary">
      {executive_summary}
    </div>
    <div class="findings">
      {findings_by_topic}
    </div>
    <div class="sources">
      {source_list_with_links}
    </div>
    <div class="methodology">
      {methodology_description}
    </div>
  </body>
</html>
```

### Migration

`d00000000008_research.py` creates:
- research_sessions table (id, user_id, question, status, budget_used, created_at, completed_at)
- research_reports table (id, session_id, question, summary, findings_json, sources_json, html_path, markdown_path, created_at)

## Frontend Changes

| Page | Change |
|------|--------|
| Dashboard | New "Research" quick action |
| Agent | "Research this" button on agent responses |
| Settings | Research budget configuration |
| New page: /research | Research session list + new research form |

### Research Page

```
┌─────────────────────────────────────────────────┐
│ Deep Research                                    │
├─────────────────────────────────────────────────┤
│                                                 │
│ [What would you like to research?]              │
│ ┌─────────────────────────────────────────────┐ │
│ │ Compare memory architectures across mem0,   │ │
│ │ graphiti, and zep...                        │ │
│ └─────────────────────────────────────────────┘ │
│                                                 │
│ Budget: Queries [20▼] Tokens [100k▼] Time [5m▼]│
│                                                 │
│ [Start Research]                                │
│                                                 │
│ ─────────────────────────────────────────────── │
│ Previous Research                               │
│                                                 │
│ 📊 Memory Architecture Comparison   2h ago  ✅ │
│    15 sources | 12 queries | 45s               │
│                                                 │
│ 📊 Local LLM Performance Benchmarks 1d ago  ✅ │
│    23 sources | 18 queries | 2m 12s            │
│                                                 │
│ 📊 Security Best Practices Audit    3d ago  ✅ │
│    8 sources | 6 queries | 45s                  │
└─────────────────────────────────────────────────┘
```

## Memory Changes

Research reports can be stored as memories. Key findings from research automatically extracted and stored in long-term memory with high confidence (sourced from multiple web sources).

## Retrieval Changes

Research findings indexed into vector store for future retrieval. Research reports become searchable content.

## Agent Changes

Agent gains "research" tool:
```python
@tool("research", "Deep multi-step web research with report generation")
async def research_tool(
    question: str,
    max_queries: int = 20,
    max_time_s: int = 300,
) -> str:
    """Execute deep research and return structured report."""
    engine = get_research_engine()
    report = await engine.research(
        question=question,
        budget=ResearchBudget(max_queries=max_queries, max_time_s=max_time_s),
    )
    return report.markdown
```

Agent can initiate research as part of larger tasks. Research results feed back into agent context.

## Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Research quality inconsistency | Medium | High | LLM-based decomposition + synthesis. Quality prompts. |
| Web search rate limiting | High | Medium | Respect rate limits. Cache results. Exponential backoff. |
| Budget overrun | Low | Medium | Hard budget limits. Time-based kill switch. |
| Source credibility | Medium | Medium | Multi-source verification. Flag single-source claims. |
| Research cost (LLM tokens) | Medium | Medium | Configurable budget. Show cost before starting. |

## Exit Criteria

- [ ] Research engine decomposes questions into sub-queries
- [ ] Web search + content extraction works
- [ ] Multi-source synthesis produces quality findings
- [ ] Gap detection generates relevant follow-ups
- [ ] HTML + Markdown reports generated
- [ ] Research budget limits enforced
- [ ] Research sessions persist and are resumable
- [ ] Agent can use research tool
- [ ] Research results indexed in vector store
- [ ] All V1-V4 tests pass
- [ ] New research engine tests
- [ ] `make lint` + `make format` clean
