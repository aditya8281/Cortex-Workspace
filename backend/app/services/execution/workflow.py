"""DAG-based workflow orchestrator with dependency resolution."""

from __future__ import annotations

import copy
import re
import time
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from backend.app.models.execution.workflow import Workflow
from backend.app.services.execution.engine import ExecutionEngine


class WorkflowOrchestrator:
    """Multi-step workflow with DAG dependency resolution, conditions, retry."""

    def __init__(self, db: Session, execution_engine: ExecutionEngine) -> None:
        self.db = db
        self.engine = execution_engine

    def create_workflow(
        self,
        user_id: int,
        name: str,
        steps: list[dict[str, Any]],
        description: str | None = None,
    ) -> Workflow:
        for i, step in enumerate(steps):
            if "tool" not in step:
                raise ValueError(f"Step {i} missing 'tool' field")
            step["status"] = step.get("status", "pending")
            step["depends_on"] = step.get("depends_on", [])
            step["max_retries"] = step.get("max_retries", 0)
            step["on_failure"] = step.get("on_failure", "fail")

        if self._has_cycle(steps):
            raise ValueError("Workflow step dependencies contain a cycle")

        for i, step in enumerate(steps):
            for dep in step.get("depends_on", []):
                if dep < 0 or dep >= len(steps):
                    raise ValueError(f"Step {i} depends on invalid index {dep}")

        workflow = Workflow(
            user_id=user_id,
            name=name,
            description=description,
            steps=copy.deepcopy(steps),
            status="idle",
            current_step=0,
            created_at=datetime.utcnow(),
        )
        self.db.add(workflow)
        self.db.commit()
        self.db.refresh(workflow)
        return workflow

    def _save_steps(self, workflow: Workflow, local_steps: list[dict[str, Any]]) -> None:
        """Reassign steps to trigger SQLAlchemy JSON dirty detection."""
        workflow.steps = local_steps
        self.db.commit()

    def run_workflow(self, workflow_id: int) -> Workflow:
        workflow = self.db.query(Workflow).filter(Workflow.id == workflow_id).first()
        if not workflow:
            raise ValueError(f"Workflow {workflow_id} not found")

        workflow.status = "running"
        workflow.last_run = datetime.utcnow()
        start_time = time.time()
        # Working copy — mutations happen here, saved back at commit points
        local_steps = copy.deepcopy(workflow.steps)
        self._save_steps(workflow, local_steps)

        try:
            for i, step in enumerate(local_steps):
                workflow.current_step = i

                # Check dependencies
                deps_ok = True
                for dep_idx in step.get("depends_on", []):
                    if dep_idx < len(local_steps):
                        dep_step = local_steps[dep_idx]
                        if dep_step.get("status") not in ("completed", "success", "skipped"):
                            deps_ok = False
                            break

                if not deps_ok:
                    step["status"] = "failed"
                    step["error"] = "Dependencies not satisfied"
                    workflow.status = "failed"
                    workflow.error_message = f"Step {i}: dependencies not satisfied"
                    self._save_steps(workflow, local_steps)
                    return workflow

                # Check condition
                condition = step.get("condition")
                if condition and not self._evaluate_condition(condition, local_steps, i):
                    step["status"] = "skipped"
                    self._save_steps(workflow, local_steps)
                    continue

                # Resolve params
                params = self._resolve_params(step.get("params", {}), local_steps)

                # Execute with retry
                tool_name = step.get("tool")
                max_retries = step.get("max_retries", 0)
                last_error = None

                for _attempt in range(max_retries + 1):
                    execution = self.engine.execute_tool(
                        user_id=workflow.user_id,
                        tool_name=tool_name,
                        params=params,
                        auto_verify=True,
                        workflow_id=workflow.id,
                        metadata={"workflow_step": i},
                    )
                    step["result"] = execution.result

                    if execution.status == "success":
                        step["status"] = "completed"
                        last_error = None
                        break
                    else:
                        step["status"] = execution.status
                        last_error = execution.error_message
                        step["error"] = last_error

                self._save_steps(workflow, local_steps)

                if step.get("status") != "completed":
                    on_failure = step.get("on_failure", "fail")
                    if on_failure == "skip":
                        step["status"] = "skipped"
                        self._save_steps(workflow, local_steps)
                        continue
                    else:
                        workflow.status = "failed"
                        workflow.error_message = f"Step {i} failed: {last_error}"
                        self.db.commit()
                        return workflow

            # All steps completed
            workflow.status = "completed"
            workflow.last_run_status = "completed"
            workflow.run_count = (workflow.run_count or 0) + 1
            end_time = time.time()
            workflow.total_duration_ms = int((end_time - start_time) * 1000)
            self._save_steps(workflow, local_steps)
            self.db.refresh(workflow)
            return workflow

        except Exception as e:
            workflow.status = "failed"
            workflow.error_message = str(e)
            self.db.commit()
            self.db.refresh(workflow)
            return workflow

    def cancel_workflow(self, workflow_id: int) -> Workflow:
        workflow = self.db.query(Workflow).filter(Workflow.id == workflow_id).first()
        if not workflow:
            raise ValueError(f"Workflow {workflow_id} not found")
        workflow.status = "cancelled"
        workflow.last_run_status = "cancelled"
        self.db.commit()
        self.db.refresh(workflow)
        return workflow

    def get_workflow(self, workflow_id: int) -> Workflow | None:
        return self.db.query(Workflow).filter(Workflow.id == workflow_id).first()

    def get_user_workflows(
        self,
        user_id: int,
        status: str | None = None,
        limit: int = 50,
    ) -> list[Workflow]:
        query = self.db.query(Workflow).filter(Workflow.user_id == user_id)
        if status:
            query = query.filter(Workflow.status == status)
        return query.order_by(Workflow.created_at.desc()).limit(limit).all()

    def duplicate_workflow(self, workflow_id: int, new_name: str) -> Workflow:
        original = self.db.query(Workflow).filter(Workflow.id == workflow_id).first()
        if not original:
            raise ValueError(f"Workflow {workflow_id} not found")
        return self.create_workflow(
            user_id=original.user_id,
            name=new_name,
            steps=[
                {k: v for k, v in step.items() if k not in ("status", "result", "error")} for step in original.steps
            ],
            description=f"Copy of {original.name}",
        )

    def _has_cycle(self, steps: list[dict[str, Any]]) -> bool:
        n = len(steps)
        WHITE, GRAY, BLACK = 0, 1, 2
        color = {i: WHITE for i in range(n)}

        adj: dict[int, list[int]] = {}
        for idx, step in enumerate(steps):
            adj[idx] = step.get("depends_on", [])

        def dfs(node: int) -> bool:
            color[node] = GRAY
            for neighbor in adj.get(node, []):
                if neighbor >= n:
                    continue
                if color[neighbor] == GRAY:
                    return True
                if color[neighbor] == WHITE and dfs(neighbor):
                    return True
            color[node] = BLACK
            return False

        return any(color[i] == WHITE and dfs(i) for i in range(n))

    def _evaluate_condition(
        self,
        condition: dict[str, Any],
        steps: list[dict[str, Any]],
        current_step: int,
    ) -> bool:
        ctype = condition.get("type", "")
        if ctype == "always":
            return True
        elif ctype == "previous_step_success":
            step_idx = condition.get("step_index", current_step - 1)
            if 0 <= step_idx < len(steps):
                return steps[step_idx].get("status") in ("completed", "success")
            return False
        elif ctype == "variable_equals":
            var_name = condition.get("variable", "")
            expected = condition.get("value")
            for i in range(current_step - 1, -1, -1):
                result = steps[i].get("result", {})
                if isinstance(result, dict) and var_name in result:
                    return result[var_name] == expected
            return False
        return True

    def _resolve_params(
        self,
        params: dict[str, Any],
        steps: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Resolve $ref references to previous step results."""
        resolved = {}
        ref_pattern = re.compile(r"^step\.(\d+)\.(result|status)\.(.+)$")

        for key, value in params.items():
            if isinstance(value, dict) and "$ref" in value:
                match = ref_pattern.match(value["$ref"])
                if match:
                    step_idx = int(match.group(1))
                    field = match.group(2)
                    nested_key = match.group(3)
                    if step_idx < len(steps):
                        step = steps[step_idx]
                        if field == "result" and step.get("result"):
                            resolved[key] = step["result"].get(nested_key)
                        elif field == "status":
                            resolved[key] = step.get("status")
                    else:
                        resolved[key] = None
                else:
                    resolved[key] = value
            else:
                resolved[key] = value

        return resolved
