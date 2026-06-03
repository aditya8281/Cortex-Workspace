from typing import Dict, List, Any, Optional
from backend.app.state.store import StateStore


class ExecutionReplayEngine:
    """
    Reconstructs and replays a full AI execution from event logs.
    This is the debugging kernel of Cortex.
    """

    def __init__(self):
        self.store = StateStore()

    # -------------------------------------------------
    # LOAD FULL EXECUTION TRACE
    # -------------------------------------------------
    def load_execution(self, execution_id: str) -> Dict[str, Any]:

        events = self.store.get_events_by_execution(execution_id)

        if not events:
            return {
                "execution_id": execution_id,
                "status": "not_found",
                "events": []
            }

        return {
            "execution_id": execution_id,
            "status": "ok",
            "events": events,
            "timeline": self._build_timeline(events),
            "summary": self._build_summary(events)
        }

    # -------------------------------------------------
    # TIMELINE BUILDER (CORE DEBUG VIEW)
    # -------------------------------------------------
    def _build_timeline(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:

        timeline = []

        for i, event in enumerate(events):

            timeline.append({
                "index": i,
                "type": event["type"],
                "timestamp": event["timestamp"],
                "source": event["source"],
                "payload": event["payload"],
                "human_readable": self._humanize(event)
            })

        return timeline

    # -------------------------------------------------
    # HUMAN READABLE DEBUG VIEW
    # -------------------------------------------------
    def _humanize(self, event: Dict[str, Any]) -> str:

        event_type = event.get("type")
        payload = event.get("payload", {})

        if "graph_execution_start" in str(payload.get("stage", "")):
            return f"Graph execution started with {payload.get('steps', '?')} steps"

        if "step_start" in str(payload.get("stage", "")):
            return f"Step started: {payload.get('name')} ({payload.get('type')})"

        if event_type == "execution_completed":
            return f"Execution completed with status: {payload.get('status')}"

        if "tool" in payload:
            return f"Tool executed: {payload.get('tool')}"

        return f"Event: {event_type}"

    # -------------------------------------------------
    # SUMMARY BUILDER (HIGH LEVEL DEBUG VIEW)
    # -------------------------------------------------
    def _build_summary(self, events: List[Dict[str, Any]]) -> Dict[str, Any]:

        tools_used = []
        steps = 0
        errors = 0

        for e in events:

            payload = e.get("payload", {})

            if "tool" in payload:
                tools_used.append(payload.get("tool"))

            if "step_id" in payload:
                steps += 1

            if payload.get("status") in ["failed", "step_failed"]:
                errors += 1

        return {
            "total_events": len(events),
            "steps_executed": steps,
            "tools_used": list(set(tools_used)),
            "error_count": errors
        }

    # -------------------------------------------------
    # STEP-BY-STEP REPLAY (DEBUG MODE)
    # -------------------------------------------------
    def replay_step_by_step(self, execution_id: str) -> List[Dict[str, Any]]:

        data = self.load_execution(execution_id)

        if data["status"] != "ok":
            return []

        replay = []

        for step in data["timeline"]:
            replay.append({
                "step": step["index"],
                "action": step["human_readable"],
                "raw": step
            })

        return replay

    # -------------------------------------------------
    # FIND TOOL USAGE
    # -------------------------------------------------
    def get_tool_usage(self, execution_id: str) -> Dict[str, List[Dict[str, Any]]]:

        data = self.load_execution(execution_id)

        tools = {}

        for event in data["events"]:

            payload = event.get("payload", {})

            tool = payload.get("tool")

            if tool:
                if tool not in tools:
                    tools[tool] = []

                tools[tool].append(event)

        return tools