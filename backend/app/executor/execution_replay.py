from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List

from backend.app.state.store import StateStore


class ExecutionReplayEngine:
    def __init__(self):
        self.store = StateStore()

    def list_executions(self, limit: int = 50) -> List[Dict[str, Any]]:
        items = []

        for item in self.store.list_executions(limit=limit):
            execution_id = item["execution_id"]
            data = self.load_execution(execution_id)

            items.append(
                {
                    "execution_id": execution_id,
                    "status": data["status"],
                    "summary": data["summary"],
                    "last_timestamp": item.get("last_timestamp"),
                    "event_count": item.get("event_count", 0),
                }
            )

        return items

    def load_execution(self, execution_id: str) -> Dict[str, Any]:
        events = self.store.get_events_by_execution(execution_id)

        if not events:
            return {
                "execution_id": execution_id,
                "exists": False,
                "status": "not_found",
                "events": [],
                "timeline": [],
                "summary": {},
            }

        return {
            "execution_id": execution_id,
            "exists": True,
            "status": self._derive_status(events),
            "events": events,
            "timeline": self._build_timeline(events),
            "summary": self._build_summary(events),
        }

    def replay_step_by_step(self, execution_id: str) -> List[Dict[str, Any]]:
        data = self.load_execution(execution_id)

        if not data["exists"]:
            return []

        return [
            {
                "step": step["index"],
                "action": step["human_readable"],
                "raw": step,
            }
            for step in data["timeline"]
        ]

    def get_tool_usage(self, execution_id: str) -> Dict[str, List[Dict[str, Any]]]:
        data = self.load_execution(execution_id)

        tools: Dict[str, List[Dict[str, Any]]] = {}

        if not data["exists"]:
            return tools

        for event in data["events"]:
            payload = event.get("payload", {})
            tool_name = payload.get("tool")

            if not tool_name and payload.get("type") == "tool":
                tool_name = payload.get("name")

            if not tool_name:
                continue

            tools.setdefault(tool_name, []).append(event)

        return tools

    def _build_timeline(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        timeline = []

        for index, event in enumerate(events):
            timeline.append(
                {
                    "index": index,
                    "type": event.get("type"),
                    "timestamp": event.get("timestamp"),
                    "source": event.get("source"),
                    "payload": event.get("payload", {}),
                    "human_readable": self._humanize(event),
                }
            )

        return timeline

    def _build_summary(self, events: List[Dict[str, Any]]) -> Dict[str, Any]:
        tools_used: list[str] = []
        step_ids: set[str] = set()
        error_count = 0
        started_at = self._parse_timestamp(events[0].get("timestamp")) if events else None
        completion_event = self._get_completion_event(events)
        completed_at = self._parse_timestamp(completion_event.get("timestamp")) if completion_event else None

        for event in events:
            payload = event.get("payload", {})

            tool_name = payload.get("tool")
            if not tool_name and payload.get("type") == "tool":
                tool_name = payload.get("name")

            if tool_name:
                tools_used.append(tool_name)

            step_id = payload.get("step_id")
            if step_id:
                step_ids.add(step_id)

            status = str(payload.get("status", "")).lower()
            if status in {"failed", "step_failed", "error"}:
                error_count += 1

        duration_ms = None
        if started_at and completed_at:
            duration_ms = int((completed_at - started_at).total_seconds() * 1000)

        return {
            "total_events": len(events),
            "steps_executed": len(step_ids),
            "tools_used": sorted(set(tools_used)),
            "error_count": error_count,
            "started_at": started_at.isoformat() if started_at else None,
            "completed_at": completed_at.isoformat() if completed_at else None,
            "duration_ms": duration_ms,
        }

    def _derive_status(self, events: List[Dict[str, Any]]) -> str:
        final_event = self._get_completion_event(events)

        if final_event:
            status = str(final_event.get("payload", {}).get("status", "")).lower()
            if status in {"success", "failed", "running"}:
                return status

        for event in events:
            payload = event.get("payload", {})
            status = str(payload.get("status", "")).lower()
            if status in {"failed", "step_failed", "error"}:
                return "failed"

        if events:
            return "running"

        return "unknown"

    def _get_completion_event(self, events: List[Dict[str, Any]]) -> Dict[str, Any] | None:
        for event in reversed(events):
            payload = event.get("payload", {})
            if event.get("type") == "EXECUTION_COMPLETED" or payload.get("stage") == "graph_execution_end":
                return event

        return None

    def _humanize(self, event: Dict[str, Any]) -> str:
        payload = event.get("payload", {})
        stage = str(payload.get("stage", "")).lower()
        event_type = str(event.get("type", "")).upper()

        if stage == "graph_execution_start":
            return f"Graph execution started with {payload.get('steps', '?')} steps"

        if stage == "step_start":
            return f"Step started: {payload.get('name')} ({payload.get('type')})"

        if stage == "step_completed":
            return f"Step completed: {payload.get('name')} ({payload.get('status', 'unknown')})"

        if stage == "step_failed":
            return f"Step failed: {payload.get('name')}"

        if event_type == "EXECUTION_COMPLETED":
            return f"Execution completed with status: {payload.get('status', 'unknown')}"

        if payload.get("tool"):
            return f"Tool executed: {payload.get('tool')}"

        if payload.get("query") and stage == "execution_start":
            return "Execution started"

        return f"Event: {event_type}"

    def _parse_timestamp(self, value: str | None) -> datetime | None:
        if not value:
            return None

        try:
            return datetime.fromisoformat(value)
        except ValueError:
            return None
