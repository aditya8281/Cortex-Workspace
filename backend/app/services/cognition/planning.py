"""DAG-based task planning service with dependency resolution."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from backend.app.models.cognition.task_plan import TaskPlan

logger = logging.getLogger(__name__)

# Step decomposition templates keyed by goal keyword.
DEFAULT_STEP_TEMPLATES: dict[str, list[dict[str, Any]]] = {
    "analyze": [
        {"step": 0, "description": "Gather requirements and context", "status": "pending", "depends_on": []},
        {
            "step": 1,
            "description": "Analyze available data and identify patterns",
            "status": "pending",
            "depends_on": [0],
        },
        {"step": 2, "description": "Formulate conclusions and recommendations", "status": "pending", "depends_on": [1]},
    ],
    "build": [
        {
            "step": 0,
            "description": "Design architecture and plan implementation",
            "status": "pending",
            "depends_on": [],
        },
        {"step": 1, "description": "Implement core functionality", "status": "pending", "depends_on": [0]},
        {"step": 2, "description": "Write tests for the implementation", "status": "pending", "depends_on": [1]},
        {"step": 3, "description": "Review and refactor code", "status": "pending", "depends_on": [2]},
    ],
    "research": [
        {"step": 0, "description": "Define research questions and scope", "status": "pending", "depends_on": []},
        {"step": 1, "description": "Gather information from relevant sources", "status": "pending", "depends_on": [0]},
        {"step": 2, "description": "Analyze findings and synthesize insights", "status": "pending", "depends_on": [1]},
        {"step": 3, "description": "Document results and conclusions", "status": "pending", "depends_on": [2]},
    ],
    "debug": [
        {"step": 0, "description": "Reproduce the issue and gather logs", "status": "pending", "depends_on": []},
        {"step": 1, "description": "Identify root cause through analysis", "status": "pending", "depends_on": [0]},
        {"step": 2, "description": "Implement fix for the identified issue", "status": "pending", "depends_on": [1]},
        {"step": 3, "description": "Verify the fix and run regression tests", "status": "pending", "depends_on": [2]},
    ],
}


class TaskPlanningService:
    """DAG-based task planning service.

    Manages goal decomposition, dependency resolution, cycle detection,
    step execution, and confidence estimation.
    """

    def __init__(self, db: Session) -> None:
        self.db = db

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def create_plan(
        self,
        user_id: int,
        goal: str,
        steps: list[dict[str, Any]] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> TaskPlan:
        """Create a plan, auto-decomposing if *steps* is not provided."""
        if steps is None:
            steps = self.decompose_task(goal)

        if self._has_cycle(steps):
            raise ValueError("Task plan contains a cycle in step dependencies")

        confidence = self._estimate_confidence(steps)

        plan = TaskPlan(
            user_id=user_id,
            goal=goal,
            steps=steps,
            status="active",
            confidence=confidence,
            meta=metadata or {},
            current_step=0,
        )
        self.db.add(plan)
        self.db.commit()
        self.db.refresh(plan)
        return plan

    def decompose_task(self, goal: str) -> list[dict[str, Any]]:
        """Template-based decomposition matching goal keywords."""
        goal_lower = goal.lower()
        for keyword, template in DEFAULT_STEP_TEMPLATES.items():
            if keyword in goal_lower:
                return [dict(step) for step in template]

        # Default 3-step template for any unrecognised goal.
        return [
            {"step": 0, "description": f"Plan and prepare for: {goal}", "status": "pending", "depends_on": []},
            {"step": 1, "description": f"Execute the plan for: {goal}", "status": "pending", "depends_on": [0]},
            {
                "step": 2,
                "description": f"Review and finalize results for: {goal}",
                "status": "pending",
                "depends_on": [1],
            },
        ]

    def execute_step(
        self,
        plan_id: int,
        step_index: int,
        result: dict[str, Any] | None = None,
        error: str | None = None,
    ) -> TaskPlan:
        """Execute a step after validating dependencies are met."""
        plan = self._get_plan_or_raise(plan_id)
        if plan.status != "active":
            raise ValueError(f"Cannot execute step on plan with status '{plan.status}'")

        steps = list(plan.steps)
        if step_index < 0 or step_index >= len(steps):
            raise ValueError(f"Step index {step_index} out of range")

        step = dict(steps[step_index])
        if step["status"] != "pending":
            raise ValueError(f"Step {step_index} is already '{step['status']}'")

        # Validate dependencies
        deps = step.get("depends_on", []) or []
        for dep_idx in deps:
            dep_step = steps[dep_idx]
            if dep_step["status"] not in ("completed", "skipped"):
                raise ValueError(
                    f"Dependency step {dep_idx} is not completed or skipped (status: {dep_step['status']})"
                )

        # Execute
        step["status"] = "completed" if error is None else "failed"
        if result is not None:
            step["result"] = result
        if error is not None:
            step["error"] = error
        steps[step_index] = step
        plan.steps = steps
        plan.current_step = max(plan.current_step, step_index + 1)
        plan.updated_at = datetime.now(timezone.utc)

        self.db.commit()
        self.db.refresh(plan)
        return plan

    def skip_step(self, plan_id: int, step_index: int, reason: str | None = None) -> TaskPlan:
        """Mark a step as skipped."""
        plan = self._get_plan_or_raise(plan_id)
        if plan.status != "active":
            raise ValueError(f"Cannot skip step on plan with status '{plan.status}'")

        steps = list(plan.steps)
        if step_index < 0 or step_index >= len(steps):
            raise ValueError(f"Step index {step_index} out of range")

        step = dict(steps[step_index])
        step["status"] = "skipped"
        if reason:
            step["error"] = reason
        steps[step_index] = step
        plan.steps = steps
        plan.updated_at = datetime.now(timezone.utc)

        self.db.commit()
        self.db.refresh(plan)
        return plan

    def get_plan(self, plan_id: int) -> TaskPlan | None:
        """Get a plan by ID."""
        return self.db.query(TaskPlan).filter(TaskPlan.id == plan_id).first()

    def get_user_plans(
        self,
        user_id: int,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[TaskPlan]:
        """Return all plans for a user, optionally filtered by status."""
        query = self.db.query(TaskPlan).filter(TaskPlan.user_id == user_id)
        if status:
            query = query.filter(TaskPlan.status == status)
        query = query.order_by(TaskPlan.created_at.desc()).limit(limit).offset(offset)
        return query.all()

    def cancel_plan(self, plan_id: int) -> TaskPlan:
        """Cancel an active plan."""
        plan = self._get_plan_or_raise(plan_id)
        if plan.status in ("completed", "cancelled"):
            raise ValueError(f"Cannot cancel plan with status '{plan.status}'")
        plan.status = "cancelled"
        plan.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(plan)
        return plan

    def get_next_executable_steps(self, plan_id: int) -> list[int]:
        """Return the indices of steps whose dependencies are satisfied."""
        plan = self._get_plan_or_raise(plan_id)
        steps = plan.steps
        executable: list[int] = []
        for i, step in enumerate(steps):
            if step.get("status") != "pending":
                continue
            deps = step.get("depends_on", []) or []
            if all(steps[d].get("status") in ("completed", "skipped") for d in deps):
                executable.append(i)
        return executable

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_plan_or_raise(self, plan_id: int) -> TaskPlan:
        plan = self.db.query(TaskPlan).filter(TaskPlan.id == plan_id).first()
        if plan is None:
            raise ValueError(f"Plan {plan_id} not found")
        return plan

    def _has_cycle(self, steps: list[dict[str, Any]]) -> bool:
        """DFS-based cycle detection on the dependency graph.

        Each edge *i* -> *d* means step *i* depends on step *d*.
        """
        n = len(steps)
        adj: list[list[int]] = [[] for _ in range(n)]
        for i, step in enumerate(steps):
            deps = step.get("depends_on", []) or []
            for d in deps:
                if 0 <= d < n:
                    adj[i].append(d)

        WHITE, GRAY, BLACK = 0, 1, 2
        color = [WHITE] * n

        def dfs(u: int) -> bool:
            color[u] = GRAY
            for v in adj[u]:
                if color[v] == GRAY:
                    return True
                if color[v] == WHITE and dfs(v):
                    return True
            color[u] = BLACK
            return False

        return any(color[i] == WHITE and dfs(i) for i in range(n))

    def _estimate_confidence(self, steps: list[dict[str, Any]]) -> float:
        """Estimate confidence based on step count, tool usage, dependency depth."""
        if not steps:
            return 1.0

        n = len(steps)
        # More steps = slightly lower confidence
        step_factor = max(0.5, 1.0 - (n - 1) * 0.05)

        # Tool usage increases confidence
        tools_count = sum(1 for s in steps if s.get("tool"))
        tool_factor = min(1.0, 0.8 + tools_count * 0.05)

        # Deeper dependency chain = more complex = lower confidence
        max_depth = self._max_dependency_depth(steps)
        depth_penalty = max(0.7, 1.0 - max_depth * 0.1)

        confidence = step_factor * tool_factor * depth_penalty
        return round(min(1.0, max(0.1, confidence)), 2)

    def _max_dependency_depth(self, steps: list[dict[str, Any]]) -> int:
        """Compute the longest dependency chain depth using memoised DFS."""
        n = len(steps)
        depth: list[int] = [0] * n
        adj: list[list[int]] = [[] for _ in range(n)]
        for i, step in enumerate(steps):
            deps = step.get("depends_on", []) or []
            for d in deps:
                if 0 <= d < n:
                    adj[i].append(d)

        visited = [False] * n

        def dfs(u: int) -> int:
            if visited[u]:
                return depth[u]
            visited[u] = True
            max_d = 0
            for v in adj[u]:
                max_d = max(max_d, dfs(v) + 1)
            depth[u] = max_d
            return depth[u]

        max_depth = 0
        for i in range(n):
            max_depth = max(max_depth, dfs(i))
        return max_depth
