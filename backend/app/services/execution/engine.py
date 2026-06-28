"""Core execution engine — runs tools with full lifecycle tracking."""

from __future__ import annotations

import time
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from backend.app.models.execution.tool_execution import ToolExecution
from backend.app.services.execution.action_verifier import ActionVerifier
from backend.app.services.execution.tool_registry import (
    ToolNotFoundError,
    ToolRegistry,
    ToolValidationError,
)


class ExecutionEngine:
    """Tool execution with verification, recording, retry, and stats."""

    def __init__(self, db: Session, tool_registry: ToolRegistry) -> None:
        self.db = db
        self.registry = tool_registry
        self.verifier = ActionVerifier()

    def execute_tool(
        self,
        user_id: int,
        tool_name: str,
        params: dict[str, Any],
        auto_verify: bool = True,
        confirmed: bool = False,
        workflow_id: int | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> ToolExecution:
        start_time = time.time()

        # Verify
        verification_result = None
        if auto_verify:
            verification_result = self.verifier.verify(tool_name, params, {"user_id": user_id})
            if not verification_result["approved"]:
                execution = ToolExecution(
                    user_id=user_id,
                    tool_name=tool_name,
                    parameters=params,
                    status="blocked",
                    error_message=f"Action verification failed: {'; '.join(verification_result['errors'])}",
                    verification_result=verification_result,
                    started_at=datetime.utcnow(),
                    completed_at=datetime.utcnow(),
                    duration_ms=0,
                    workflow_id=workflow_id,
                    meta=metadata,
                )
                self.db.add(execution)
                self.db.commit()
                self.db.refresh(execution)
                return execution

        # Create record
        execution = ToolExecution(
            user_id=user_id,
            tool_name=tool_name,
            parameters=params,
            status="running",
            started_at=datetime.utcnow(),
            verification_result=verification_result,
            workflow_id=workflow_id,
            meta=metadata,
        )
        self.db.add(execution)
        self.db.commit()
        self.db.refresh(execution)

        # Execute
        try:
            result = self.registry.execute_sync(tool_name, params, confirmed=confirmed)
            execution.result = result
            execution.status = "success"
        except ToolValidationError as e:
            execution.status = "failed"
            execution.error_type = "ToolValidationError"
            execution.error_message = str(e)
        except ToolNotFoundError as e:
            execution.status = "failed"
            execution.error_type = "ToolNotFoundError"
            execution.error_message = str(e)
        except PermissionError as e:
            execution.status = "failed"
            execution.error_type = "PermissionError"
            execution.error_message = str(e)
        except TimeoutError as e:
            execution.status = "timeout"
            execution.error_type = "TimeoutError"
            execution.error_message = str(e)
        except Exception as e:
            execution.status = "failed"
            execution.error_type = type(e).__name__
            execution.error_message = str(e)

        # Record timing
        end_time = time.time()
        execution.completed_at = datetime.utcnow()
        execution.duration_ms = int((end_time - start_time) * 1000)

        self.db.commit()
        self.db.refresh(execution)
        return execution

    def execute_with_retry(
        self,
        user_id: int,
        tool_name: str,
        params: dict[str, Any],
        max_retries: int = 3,
    ) -> ToolExecution:
        last_execution = None
        for attempt in range(max_retries + 1):
            execution = self.execute_tool(
                user_id=user_id,
                tool_name=tool_name,
                params=params,
                auto_verify=True,
                metadata={"retry_attempt": attempt, "max_retries": max_retries},
            )
            if execution.status == "success":
                return execution
            last_execution = execution
        return last_execution  # type: ignore[return-value]

    def get_execution(self, execution_id: int) -> ToolExecution | None:
        return self.db.query(ToolExecution).filter(ToolExecution.id == execution_id).first()

    def get_user_executions(
        self,
        user_id: int,
        tool_name: str | None = None,
        status: str | None = None,
        limit: int = 50,
    ) -> list[ToolExecution]:
        query = self.db.query(ToolExecution).filter(ToolExecution.user_id == user_id)
        if tool_name:
            query = query.filter(ToolExecution.tool_name == tool_name)
        if status:
            query = query.filter(ToolExecution.status == status)
        return query.order_by(ToolExecution.started_at.desc()).limit(limit).all()

    def get_execution_stats(self, user_id: int) -> dict[str, Any]:
        executions = self.get_user_executions(user_id, limit=1000)
        total = len(executions)
        successful = sum(1 for e in executions if e.status == "success")
        failed = sum(1 for e in executions if e.status == "failed")
        blocked = sum(1 for e in executions if e.status == "blocked")
        timeout = sum(1 for e in executions if e.status == "timeout")
        durations = [e.duration_ms for e in executions if e.duration_ms is not None]
        avg_duration = sum(durations) // len(durations) if durations else 0
        tool_counts: dict[str, int] = {}
        for e in executions:
            tool_counts[e.tool_name] = tool_counts.get(e.tool_name, 0) + 1
        return {
            "total": total,
            "successful": successful,
            "failed": failed,
            "blocked": blocked,
            "timeout": timeout,
            "success_rate": (successful / total * 100) if total > 0 else 0,
            "average_duration_ms": avg_duration,
            "tool_breakdown": tool_counts,
        }
