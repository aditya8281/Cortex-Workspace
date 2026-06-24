# V4 Phase 1: Task Scheduler + Housekeeping

**Duration estimate:** 7-10 days
**Dependencies:** V3 complete (desktop shell, embedded DBs, TUI)
**Risk:** Medium — scheduler reliability, housekeeping task ordering

---

## Goals

Build task scheduler with cron, event, and webhook triggers. Implement 7 housekeeping tasks (memory decay, embedding refresh, graph cleanup, staleness detection, index compaction, log rotation, health check). Make Cortex self-maintaining.

## Deliverables

1. Task scheduler (cron, event, webhook triggers)
2. 7 housekeeping tasks
3. Task queue management (ARQ-based)
4. Task history and logging
5. Scheduler UI in settings
6. Cron expression parser
7. Event-driven task triggers
8. Webhook trigger endpoints

## Architectural Changes

```
BEFORE:
  Background tasks = ad-hoc ARQ tasks (embed, index, build_graph)
  Maintenance = manual or none

AFTER:
  Background tasks = scheduled + event-driven + webhook-triggered
  Maintenance = automated housekeeping (7 tasks)
  Scheduler = cron expressions + event triggers + HTTP webhooks
  Monitoring = task history, run times, failure tracking
```

## Backend Changes

### New Files

| File | Purpose |
|------|---------|
| `backend/app/services/scheduler/__init__.py` | Scheduler package |
| `backend/app/services/scheduler/engine.py` | Scheduler engine (cron parser + event listener) |
| `backend/app/services/scheduler/triggers.py` | Trigger types (cron, event, webhook) |
| `backend/app/services/scheduler/task_registry.py` | Task registration + metadata |
| `backend/app/services/scheduler/history.py` | Task run history + logging |
| `backend/app/services/housekeeping/__init__.py` | Housekeeping package |
| `backend/app/services/housekeeping/memory_decay.py` | Gradual confidence decay |
| `backend/app/services/housekeeping/embedding_refresh.py` | Re-embed stale content |
| `backend/app/services/housekeeping/graph_cleanup.py` | Orphan node/edge removal |
| `backend/app/services/housekeeping/staleness.py` | Detect stale memories |
| `backend/app/services/housekeeping/index_compaction.py` | Compact vector indices |
| `backend/app/services/housekeeping/log_rotation.py` | Rotate + archive logs |
| `backend/app/services/housekeeping/health_check.py` | System health verification |
| `backend/app/models/scheduled_task.py` | ScheduledTask SQLAlchemy model |
| `backend/app/models/task_history.py` | TaskHistory SQLAlchemy model |
| `backend/app/api/v1/scheduler.py` | Scheduler management API |
| `migrations/versions/d00000000006_scheduler.py` | Scheduler tables migration |

### Scheduler Engine

```python
class SchedulerEngine:
    """Task scheduler with cron, event, and webhook triggers."""

    def __init__(self, event_bus: EventBus, task_queue: ARQRedisSettings):
        self.cron_tasks: dict[str, CronTask] = {}
        self.event_triggers: dict[str, list[EventHandler]] = {}
        self.webhook_routes: dict[str, WebhookHandler] = {}

    async def start(self) -> None:
        """Start scheduler, register event listeners."""
        for event_type, handlers in self.event_triggers.items():
            self.event_bus.subscribe(event_type, handlers)

    async def tick(self) -> None:
        """Called every minute. Check cron triggers."""
        now = datetime.utcnow()
        for task_id, cron_task in self.cron_tasks.items():
            if cron_task.should_run(now):
                await self._enqueue(task_id)

    def register_cron(self, task_id: str, expression: str, handler: Callable) -> None:
        """Register a cron-triggered task."""
        self.cron_tasks[task_id] = CronTask(expression, handler)

    def register_event(self, event_type: str, handler: Callable) -> None:
        """Register an event-triggered task."""
        self.event_triggers.setdefault(event_type, []).append(handler)

    def register_webhook(self, path: str, handler: Callable) -> None:
        """Register a webhook-triggered task."""
        self.webhook_routes[path] = handler
```

### Housekeeping Tasks

| Task | Schedule | Description |
|------|----------|-------------|
| Memory Decay | Daily 2am | Reduce confidence of unused memories |
| Embedding Refresh | Weekly Sunday 3am | Re-embed content with updated models |
| Graph Cleanup | Daily 3am | Remove orphan nodes/edges |
| Staleness Detection | Daily 4am | Flag memories not accessed in 90+ days |
| Index Compaction | Weekly Sunday 4am | Merge fragmented vector indices |
| Log Rotation | Daily 1am | Archive logs older than 30 days |
| Health Check | Every 15min | Verify all services healthy |

### Task History

```python
class TaskHistory(Base):
    __tablename__ = "task_history"

    id = Column(Integer, primary_key=True)
    task_id = Column(String, nullable=False, index=True)
    task_type = Column(String, nullable=False)  # cron, event, webhook
    status = Column(String, nullable=False)  # pending, running, completed, failed
    started_at = Column(DateTime, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    duration_ms = Column(Integer, nullable=True)
    error = Column(Text, nullable=True)
    metadata_ = Column("metadata", JSON, nullable=True)
```

### Migration

`d00000000006_scheduler.py` creates:
- scheduled_tasks table (id, name, task_type, schedule, handler, enabled, metadata)
- task_history table (above)

## Frontend Changes

| Page | Change |
|------|--------|
| Settings | New "Scheduler" section |
| Settings | Task list with enable/disable toggles |
| Settings | Task run history (last 50 runs per task) |
| Settings | Cron expression editor with preview |
| Settings | Manual "Run Now" button per task |
| Dashboard | System health card (from health_check task) |

### Scheduler Settings UI

```
┌─────────────────────────────────────────────────┐
│ Task Scheduler                                  │
├─────────────────────────────────────────────────┤
│                                                 │
│ 🧠 Memory Decay         Daily 2:00am    [ON] ▶│
│    Last run: 2h ago    Duration: 1.2s   ✅     │
│                                                 │
│ 🔤 Embedding Refresh    Weekly Sun 3am  [ON] ▶│
│    Last run: 5d ago    Duration: 45s   ✅      │
│                                                 │
│ 🔗 Graph Cleanup        Daily 3:00am    [ON] ▶│
│    Last run: 1h ago    Duration: 0.8s   ✅     │
│                                                 │
│ ⏰ Staleness Detection  Daily 4:00am    [ON] ▶│
│    Last run: 50m ago   Duration: 2.1s   ✅     │
│                                                 │
│ 📦 Index Compaction     Weekly Sun 4am  [ON] ▶│
│    Last run: 5d ago    Duration: 12s   ✅      │
│                                                 │
│ 📋 Log Rotation         Daily 1:00am    [ON] ▶│
│    Last run: 3h ago    Duration: 0.3s   ✅     │
│                                                 │
│ ❤️  Health Check         Every 15min     [ON] ▶│
│    Last run: 2m ago    Duration: 0.1s   ✅     │
│                                                 │
│ [+ Add Custom Task]                             │
└─────────────────────────────────────────────────┘
```

## Memory Changes

Memory Decay task implements gradual confidence reduction:
- Memories not accessed in 30 days: confidence × 0.9
- Memories not accessed in 60 days: confidence × 0.8
- Memories not accessed in 90 days: confidence × 0.7
- Memories with confidence < 0.1: archive (don't delete)

Embedding Refresh task re-embeds content when:
- Embedding model version changes
- Content was modified after last embed
- Embedding is older than 90 days

## Retrieval Changes

No changes.

## Agent Changes

No changes.

## Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Scheduler reliability | Medium | High | Persistent schedule in DB. Restart recovers state. |
| Housekeeping task conflicts | Low | Medium | Mutex locks per task. Don't run same task concurrently. |
| Memory decay too aggressive | Medium | High | Conservative decay rates. Configurable per-user. |
| Embedding refresh cost | Medium | Medium | Only re-embed stale content. Rate limiting. |
| Task history bloat | Low | Low | Auto-purge history older than 90 days. |

## Exit Criteria

- [ ] Scheduler starts on app startup
- [ ] Cron tasks run at scheduled times
- [ ] Event-triggered tasks fire on correct events
- [ ] Webhook triggers work via HTTP endpoint
- [ ] 7 housekeeping tasks run on schedule
- [ ] Task history recorded correctly
- [ ] Settings UI shows task status + history
- [ ] Manual "Run Now" works for each task
- [ ] Memory decay reduces confidence correctly
- [ ] All V1-V3 tests pass
- [ ] New scheduler + housekeeping tests
- [ ] `make lint` + `make format` clean
