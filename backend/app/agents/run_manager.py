"""Agent run manager — orchestrates planner + executor runs."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from backend.app.agents.executor import ExecutorAgent
from backend.app.agents.planner import PlannerAgent
from backend.app.models.agent import Agent, AgentFeedback, AgentRun, AgentStep
from backend.app.services.llm.manager import llm_manager

logger = logging.getLogger(__name__)


class AgentRunManager:
    """Manages agent runs: planning, execution, and persistence."""

    def __init__(
        self,
        db: Session,
        planner: PlannerAgent | None = None,
        executor: ExecutorAgent | None = None,
        event_callback: Any | None = None,
    ):
        self.db = db
        self.planner = planner or PlannerAgent(llm_chat=llm_manager.chat)
        self.executor = executor or ExecutorAgent()
        self._event_callback = event_callback

    def create_agent(
        self,
        name: str,
        system_prompt: str,
        user_id: int,
        model_id: str = "local",
        description: str | None = None,
        tools: list[str] | None = None,
    ) -> Agent:
        """Create a new agent definition."""
        agent = Agent(
            name=name,
            description=description,
            system_prompt=system_prompt,
            model_id=model_id,
            user_id=user_id,
            tools_json=json.dumps(tools) if tools else None,
        )
        self.db.add(agent)
        self.db.commit()
        self.db.refresh(agent)
        return agent

    def get_agent(self, agent_id: int, user_id: int | None = None) -> Agent | None:
        """Get an agent by ID, optionally filtered by user."""
        query = self.db.query(Agent).filter(Agent.id == agent_id)
        if user_id is not None:
            query = query.filter(Agent.user_id == user_id)
        return query.first()

    def list_agents(self, user_id: int, active_only: bool = True) -> list[Agent]:
        """List agents for a specific user."""
        query = self.db.query(Agent).filter(Agent.user_id == user_id)
        if active_only:
            query = query.filter(Agent.is_active.is_(True))
        return query.order_by(Agent.name).all()

    def create_run(self, agent_id: int, user_id: int, input_text: str) -> AgentRun:
        """Create a run record (status=pending) without executing."""
        run = AgentRun(
            agent_id=agent_id,
            user_id=user_id,
            input_text=input_text,
            status="pending",
        )
        self.db.add(run)
        self.db.commit()
        self.db.refresh(run)
        return run

    async def _emit(self, event: dict[str, Any]) -> None:
        if self._event_callback:
            await self._event_callback(event)

    async def run_agent(
        self,
        agent_id: int,
        user_id: int,
        input_text: str,
    ) -> AgentRun:
        """Execute an agent run: plan → execute → record."""
        agent = self.get_agent(agent_id)
        if not agent:
            raise ValueError(f"Agent {agent_id} not found")

        # Create run record
        run = self.create_run(agent_id, user_id, input_text)
        run.status = "running"
        self.db.commit()

        try:
            # Attach agent model to executor for model_id/tools_json access
            self.executor._agent = agent

            # Plan the task
            plan = await self.planner.plan(input_text)
            logger.info("Agent %d planned %d steps for run %d", agent_id, len(plan), run.id)

            # Execute each step
            results: list[str] = []
            for i, step_plan in enumerate(plan):
                step = AgentStep(
                    run_id=run.id,
                    step_number=i + 1,
                    thought=step_plan.get("thought", ""),
                    action=step_plan.get("agent", "executor"),
                    action_input_json=json.dumps(step_plan),
                    status="running",
                )
                self.db.add(step)
                self.db.commit()

                try:
                    result = await self.executor.run(
                        step_plan.get("goal", ""),
                        context={"previous_steps": plan[:i], "previous_results": results},
                    )
                    step.observation = result
                    step.status = "completed"
                    results.append(result)
                except Exception as e:
                    step.observation = f"Error: {e}"
                    step.status = "failed"
                    logger.error("Step %d failed: %s", i + 1, e)

                self.db.commit()

                await self._emit(
                    {
                        "type": "step",
                        "step_number": step.step_number,
                        "thought": step.thought or "",
                        "action": step.action or "",
                        "observation": step.observation or "",
                    }
                )

            # Finalize run
            run.status = "completed"
            run.output = results[-1] if results else "No output"
            run.completed_at = datetime.now(timezone.utc)
            self.db.commit()

            await self._emit(
                {
                    "type": "done",
                    "status": "completed",
                    "total_steps": len(plan),
                }
            )

        except Exception as e:
            run.status = "failed"
            run.error = str(e)
            run.completed_at = datetime.now(timezone.utc)
            self.db.commit()
            logger.error("Agent run %d failed: %s", run.id, e)

            await self._emit(
                {
                    "type": "error",
                    "message": str(e),
                }
            )

        self.db.refresh(run)
        return run

    def get_run(self, run_id: int) -> AgentRun | None:
        """Get a run by ID."""
        return self.db.query(AgentRun).filter(AgentRun.id == run_id).first()

    def list_runs(
        self,
        agent_id: int | None = None,
        user_id: int | None = None,
        status: str | None = None,
        limit: int = 20,
    ) -> list[AgentRun]:
        """List runs with optional filters."""
        query = self.db.query(AgentRun)
        if agent_id is not None:
            query = query.filter(AgentRun.agent_id == agent_id)
        if user_id is not None:
            query = query.filter(AgentRun.user_id == user_id)
        if status is not None:
            query = query.filter(AgentRun.status == status)
        return query.order_by(AgentRun.created_at.desc()).limit(limit).all()

    def get_run_steps(self, run_id: int) -> list[AgentStep]:
        """Get all steps for a run, ordered by step number."""
        return self.db.query(AgentStep).filter(AgentStep.run_id == run_id).order_by(AgentStep.step_number).all()

    def add_feedback(
        self,
        run_id: int,
        user_id: int,
        rating: int,
        comment: str | None = None,
    ) -> AgentFeedback:
        """Add feedback for a run."""
        if not 1 <= rating <= 5:
            raise ValueError("Rating must be between 1 and 5")

        feedback = AgentFeedback(
            run_id=run_id,
            user_id=user_id,
            rating=rating,
            comment=comment,
        )
        self.db.add(feedback)
        self.db.commit()
        self.db.refresh(feedback)
        return feedback

    def get_run_feedback(self, run_id: int) -> list[AgentFeedback]:
        """Get all feedback for a run."""
        return (
            self.db.query(AgentFeedback).filter(AgentFeedback.run_id == run_id).order_by(AgentFeedback.created_at).all()
        )

    @staticmethod
    def serialize_run(run: AgentRun) -> dict:
        """Serialize a run for API response."""
        return {
            "id": run.id,
            "agent_id": run.agent_id,
            "user_id": run.user_id,
            "input": run.input_text,
            "status": run.status,
            "output": run.output,
            "error": run.error,
            "created_at": run.created_at.isoformat() if run.created_at else None,
            "completed_at": run.completed_at.isoformat() if run.completed_at else None,
        }

    @staticmethod
    def serialize_step(step: AgentStep) -> dict:
        """Serialize a step for API response."""
        action_input = None
        if step.action_input_json:
            try:
                action_input = json.loads(step.action_input_json)
            except (json.JSONDecodeError, TypeError):
                action_input = step.action_input_json

        return {
            "id": step.id,
            "run_id": step.run_id,
            "step_number": step.step_number,
            "thought": step.thought,
            "action": step.action,
            "action_input": action_input,
            "observation": step.observation,
            "status": step.status,
            "created_at": step.created_at.isoformat() if step.created_at else None,
        }
