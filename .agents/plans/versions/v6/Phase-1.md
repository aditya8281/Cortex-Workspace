# V6 Phase 1: Plugin Marketplace + Workflow DAGs

**Duration estimate:** 10-14 days
**Dependencies:** V5 complete (workspace, all integrations)
**Risk:** HIGH — marketplace complexity, workflow engine reliability

---

## Goals

Build plugin marketplace for community-contributed plugins. Build visual workflow editor for multi-step agent workflows (DAGs). Enable power users to create, share, and execute complex automation pipelines.

## Deliverables

1. Plugin marketplace (browse, install, rate, review)
2. Plugin publishing pipeline (validate, version, distribute)
3. Visual workflow editor (drag-and-drop DAG builder)
4. Workflow execution engine (DAG runner with error handling)
5. Workflow templates (pre-built common workflows)
6. Workflow sharing (export/import workflows)
7. Plugin dependency management
8. Plugin sandboxing (security isolation)

## Architectural Changes

```
BEFORE:
  Plugins = local filesystem scan (~/.cortex/plugins/)
  Workflows = none (agent loop only)

AFTER:
  Plugins = marketplace + local + community ratings
  Workflows = visual DAG editor + execution engine
  Plugin ecosystem = publish, discover, install, rate
  Workflow ecosystem = create, share, import, execute
```

## Backend Changes

### New Files

| File | Purpose |
|------|---------|
| `backend/app/services/marketplace/__init__.py` | Marketplace package |
| `backend/app/services/marketplace/registry.py` | Plugin registry (remote + local) |
| `backend/app/services/marketplace/publisher.py` | Plugin publishing pipeline |
| `backend/app/services/marketplace/validator.py` | Plugin validation + security check |
| `backend/app/services/marketplace/sandbox.py` | Plugin sandboxing (resource limits) |
| `backend/app/services/marketplace/ratings.py` | Rating + review system |
| `backend/app/services/workflows/__init__.py` | Workflows package |
| `backend/app/services/workflows/engine.py` | DAG execution engine |
| `backend/app/services/workflows/definitions.py` | Workflow definition models |
| `backend/app/services/workflows/templates.py` | Pre-built workflow templates |
| `backend/app/services/workflows/sharing.py` | Workflow export/import |
| `backend/app/services/workflows/scheduler.py` | Workflow scheduling integration |
| `backend/app/models/plugin.py` | Plugin metadata model |
| `backend/app/models/plugin_review.py` | Plugin reviews model |
| `backend/app/models/workflow.py` | Workflow + WorkflowRun models |
| `backend/app/models/workflow_step.py` | Workflow step models |
| `backend/app/api/v1/marketplace.py` | Marketplace API |
| `backend/app/api/v1/workflows.py` | Workflow API |
| `migrations/versions/d00000000012_marketplace_workflows.py` | Marketplace + workflows tables |

### Plugin Marketplace

```python
class PluginRegistry:
    """Unified plugin registry: local + remote marketplace."""

    def __init__(self, marketplace_url: str, local_dir: Path):
        self.marketplace_url = marketplace_url
        self.local_dir = local_dir

    async def search(self, query: str, category: str = None) -> list[PluginInfo]:
        """Search marketplace + local plugins."""
        remote = await self._search_marketplace(query, category)
        local = self._search_local(query, category)
        return self._merge_results(remote, local)

    async def install(self, plugin_id: str, version: str = "latest") -> Plugin:
        """Install plugin from marketplace."""
        # 1. Download from marketplace
        # 2. Validate (security check, dependency check)
        # 3. Install to local directory
        # 4. Register in database
        ...

    async def publish(self, plugin: Plugin, package: bytes) -> str:
        """Publish plugin to marketplace."""
        # 1. Validate plugin manifest
        # 2. Run security audit
        # 3. Sign plugin package
        # 4. Upload to marketplace
        ...

class PluginSandbox:
    """Resource limits for plugin execution."""

    def __init__(self, max_memory_mb: int = 256, max_cpu_s: float = 10, max_network_requests: int = 100):
        self.max_memory_mb = max_memory_mb
        self.max_cpu_s = max_cpu_s
        self.max_network_requests = max_network_requests

    async def execute(self, plugin: Plugin, func: str, **kwargs) -> Any:
        """Execute plugin function with resource limits."""
        ...
```

### Workflow DAG Engine

```python
class WorkflowDefinition(BaseModel):
    """Visual workflow definition (DAG)."""
    id: str
    name: str
    description: str
    nodes: list[WorkflowNode]      # Steps in the workflow
    edges: list[WorkflowEdge]      # Dependencies between steps
    variables: dict[str, Any]      # User-configurable variables
    metadata: dict[str, Any]       # Tags, author, version

class WorkflowNode(BaseModel):
    """A single step in the workflow."""
    id: str
    type: str  # "agent", "tool", "condition", "transform", "output"
    config: dict[str, Any]  # Step-specific configuration
    position: dict[str, float]  # Visual position (x, y)

class WorkflowEdge(BaseModel):
    """Dependency between two nodes."""
    source: str
    target: str
    condition: str | None = None  # Conditional execution

class WorkflowEngine:
    """Execute workflow DAGs."""

    async def execute(self, workflow: WorkflowDefinition, inputs: dict) -> WorkflowResult:
        """Execute workflow in topological order."""
        # 1. Validate DAG (no cycles, all dependencies satisfied)
        # 2. Topological sort
        # 3. Execute each node in order
        # 4. Pass outputs between nodes
        # 5. Handle errors (retry, skip, abort)
        # 6. Return final output
        ...

    async def _execute_node(self, node: WorkflowNode, context: WorkflowContext) -> Any:
        """Execute a single workflow node."""
        match node.type:
            case "agent":
                return await self._run_agent(node.config, context)
            case "tool":
                return await self._run_tool(node.config, context)
            case "condition":
                return await self._evaluate_condition(node.config, context)
            case "transform":
                return await self._transform_data(node.config, context)
            case "output":
                return await self._format_output(node.config, context)
```

### Pre-built Templates

```python
WORKFLOW_TEMPLATES = {
    "daily_briefing": {
        "name": "Daily Morning Briefing",
        "description": "Check email, calendar, tasks, and provide morning summary",
        "nodes": [
            {"id": "email", "type": "tool", "config": {"tool": "read_email", "query": "newer_than:1d"}},
            {"id": "calendar", "type": "tool", "config": {"tool": "check_calendar", "date": "today"}},
            {"id": "tasks", "type": "tool", "config": {"tool": "list_tasks", "view": "today"}},
            {"id": "summarize", "type": "agent", "config": {"prompt": "Create a morning briefing from the above data"}},
            {"id": "output", "type": "output", "config": {"format": "markdown"}},
        ],
        "edges": [
            {"source": "email", "target": "summarize"},
            {"source": "calendar", "target": "summarize"},
            {"source": "tasks", "target": "summarize"},
            {"source": "summarize", "target": "output"},
        ],
    },
    "research_and_report": {
        "name": "Research and Report",
        "description": "Deep research on a topic, generate report, save as note",
        "nodes": [
            {"id": "input", "type": "input", "config": {"variable": "topic"}},
            {"id": "research", "type": "tool", "config": {"tool": "research", "question": "{{topic}}"}},
            {"id": "note", "type": "tool", "config": {"tool": "create_note", "title": "Research: {{topic}}", "content": "{{research.output}}"}},
            {"id": "task", "type": "tool", "config": {"tool": "create_task", "title": "Review research: {{topic}}", "priority": "medium"}},
        ],
        "edges": [
            {"source": "input", "target": "research"},
            {"source": "research", "target": "note"},
            {"source": "research", "target": "task"},
        ],
    },
    "email_triage": {
        "name": "Email Triage",
        "description": "Categorize emails, create tasks for action items, draft replies",
        "nodes": [
            {"id": "emails", "type": "tool", "config": {"tool": "read_email", "query": "newer_than:1d is:unread"}},
            {"id": "categorize", "type": "agent", "config": {"prompt": "Categorize emails: urgent, action_needed, info, newsletter"}},
            {"id": "urgent", "type": "condition", "config": {"check": "categorize.output contains 'urgent'"}},
            {"id": "task", "type": "tool", "config": {"tool": "create_task", "title": "Handle urgent email: {{email.subject}}", "priority": "high"}},
            {"id": "draft", "type": "agent", "config": {"prompt": "Draft reply for this email: {{email.body}}"}},
        ],
        "edges": [
            {"source": "emails", "target": "categorize"},
            {"source": "categorize", "target": "urgent"},
            {"source": "urgent", "target": "task", "condition": "urgent"},
            {"source": "emails", "target": "draft"},
        ],
    },
}
```

### Migration

`d00000000012_marketplace_workflows.py` creates:
- plugins table (id, name, author, version, description, category, manifest_json, package_hash, installed_at, enabled, rating, downloads)
- plugin_reviews table (id, plugin_id, user_id, rating, review, created_at)
- workflows table (id, user_id, name, description, definition_json, enabled, last_run, run_count, created_at, updated_at)
- workflow_runs table (id, workflow_id, status, inputs_json, outputs_json, started_at, completed_at, duration_ms, error)
- workflow_steps table (id, run_id, node_id, status, output_json, started_at, completed_at, duration_ms, error)

## Frontend Changes

| Page | Change |
|------|--------|
| New: /marketplace | Plugin marketplace browser |
| New: /workflows | Workflow list + editor |
| New: /workflows/[id] | Visual workflow editor (canvas) |
| Settings | Plugin management (installed, enabled) |
| Agent | Workflow tools available |

### /marketplace — Plugin Marketplace

```
┌─────────────────────────────────────────────────┐
│ 🧩 Plugin Marketplace                           │
├─────────────────────────────────────────────────┤
│ 🔍 Search plugins...                            │
│ Categories: [All] [AI] [Productivity] [Dev] [Data]│
│                                                 │
│ ⭐ Top Rated                                    │
│ ┌──────────────┐ ┌──────────────┐ ┌───────────┐│
│ │ 📊 Analytics │ │ 🔗 Slack     │ │ 📧 Email  ││
│ │ v2.1 | ⭐4.8 │ │ v1.3 | ⭐4.6 │ │ v1.0|⭐4.5││
│ │ 1.2K installs│ │ 890 installs │ │ 567 inst. ││
│ │ [Install]    │ │ [Installed ✓]│ │ [Install] ││
│ └──────────────┘ └──────────────┘ └───────────┘│
│                                                 │
│ 🆕 New Releases                                 │
│ ┌──────────────┐ ┌──────────────┐ ┌───────────┐│
│ │ 🤖 ChatGPT   │ │ 📊 Grafana   │ │ 🔐 Auth   ││
│ │ v1.0 | ⭐4.2 │ │ v1.1 | ⭐4.4 │ │ v1.0|⭐4.3││
│ │ 234 installs │ │ 456 installs │ │ 123 inst. ││
│ │ [Install]    │ │ [Install]    │ │ [Install] ││
│ └──────────────┘ └──────────────┘ └───────────┘│
│                                                 │
│ 📦 Installed (3)                                │
│ Slack Integration v1.3  [Configure] [Disable]  │
│ Analytics Dashboard v2.1 [Configure] [Disable]  │
│ GitHub Integration v1.0 [Configure] [Disable]   │
└─────────────────────────────────────────────────┘
```

### /workflows — Workflow Editor

```
┌─────────────────────────────────────────────────┐
│ 🔀 Workflows                     [+ New Workflow]│
├─────────────────────────────────────────────────┤
│                                                 │
│ 📋 Daily Morning Briefing          Enabled  ✅  │
│    Last run: 2h ago | Runs: 45 | Avg: 12s      │
│    [Edit] [Run Now] [Disable] [Delete]         │
│                                                 │
│ 📋 Email Triage                    Enabled  ✅  │
│    Last run: 1d ago | Runs: 30 | Avg: 8s       │
│    [Edit] [Run Now] [Disable] [Delete]         │
│                                                 │
│ 📋 Research and Report             Disabled ⬜  │
│    Last run: 5d ago | Runs: 12 | Avg: 45s      │
│    [Edit] [Run Now] [Enable] [Delete]          │
│                                                 │
│ [+ New Workflow] [📂 Import Workflow]            │
│                                                 │
│ Templates:                                      │
│ 📋 Daily Briefing | 📋 Email Triage | 📋 Research│
└─────────────────────────────────────────────────┘
```

### /workflows/[id] — Visual Workflow Editor

```
┌─────────────────────────────────────────────────┐
│ 🔀 Daily Morning Briefing — Workflow Editor     │
├─────────────────────────────────────────────────┤
│                                                 │
│  ┌──────────┐     ┌──────────┐     ┌─────────┐ │
│  │ 📧 Email │────▶│ 🤖 Agent │────▶│ 📤 Output│ │
│  └──────────┘     └──────────┘     └─────────┘ │
│                        ▲                        │
│  ┌──────────┐          │                        │
│  │ 📅 Cal   │──────────┘                        │
│  └──────────┘                                   │
│                                                 │
│  ┌──────────┐          │                        │
│  │ ✅ Tasks │──────────┘                        │
│  └──────────┘                                   │
│                                                 │
│ ─────────────────────────────────────────────── │
│ Node Properties (click a node to edit)          │
│                                                 │
│ [Save] [Run Test] [Schedule] [Export]           │
└─────────────────────────────────────────────────┘
```

Canvas features:
- Drag-and-drop node creation from palette
- Connect nodes by dragging edges
- Node configuration panel (right side)
- Zoom/pan navigation
- Mini-map for large workflows
- Color-coded by node type
- Error indicators on failed runs

## Memory Changes

No changes.

## Retrieval Changes

No changes.

## Agent Changes

Agent gains workflow execution capability. Can trigger workflows programmatically. Workflow results feed into agent context.

## Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Plugin security | High | Critical | Sandboxing. Security audit. Code review for published plugins. |
| Workflow engine bugs | Medium | High | Comprehensive testing. Error handling. Rollback capability. |
| Marketplace abuse | Medium | Medium | Rate limiting. Moderation. Reputation system. |
| Visual editor complexity | High | Medium | Start with simple DAG editor. Add features incrementally. |
| Plugin compatibility | Medium | Medium | Version pinning. Dependency resolution. Compatibility matrix. |

## Exit Criteria

- [ ] Plugin marketplace browse/search/install works
- [ ] Plugin publishing pipeline works
- [ ] Plugin sandboxing works
- [ ] Visual workflow editor renders DAGs
- [ ] Workflow execution engine runs DAGs
- [ ] Workflow templates work
- [ ] Workflow sharing (export/import) works
- [ ] Plugin ratings/reviews work
- [ ] All V1-V5 tests pass
- [ ] New marketplace + workflow tests
- [ ] `make lint` + `make format` clean
