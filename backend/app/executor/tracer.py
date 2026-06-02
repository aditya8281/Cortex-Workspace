import uuid
import time
from dataclasses import dataclass
from typing import Any

@dataclass
class StepTrace:
    step_id: str
    step_type: str
    name: str | None

    start_time: float = 0
    end_time: float = 0
    duration: float = 0

    status: str = "pending"  # running | success | failed
    result_size: int = 0
    error: str | None = None
    
@dataclass
class ExecutionSession:
    execution_id: str
    created_at: float = time.time()
    traces: dict[str, Any] = None

    def __post_init__(self):
        if self.traces is None:
            self.traces = {}


class ExecutionTracer:

    def __init__(self):
        self.sessions: dict[str, ExecutionSession] = {}

    # -------------------------------------------------
    # STEP START
    # -------------------------------------------------
    def start(self, execution_id: str, step_id: str, step_type: str, name: str | None):

        session = self.sessions.get(execution_id)
        if not session:
            return

        session.traces[step_id] = StepTrace(
            step_id=step_id,
            step_type=step_type,
            name=name,
            start_time=time.time(),
            status="running"
        )

    # -------------------------------------------------
    # STEP END
    # -------------------------------------------------
    def end(self, execution_id: str, step_id: str, result: Any = None, error: str | None = None):

        session = self.sessions.get(execution_id)
        if not session:
            return

        trace = session.traces.get(step_id)
        if not trace:
            return

        trace.end_time = time.time()
        trace.duration = trace.end_time - trace.start_time

        if error:
            trace.status = "failed"
            trace.error = error
        else:
            trace.status = "success"
            trace.result_size = len(str(result)) if result else 0

    # -------------------------------------------------
    # FULL REPORT
    # -------------------------------------------------
    def report(self):
        return {
            step_id: vars(trace)
            for step_id, trace in self.traces.items()
        }
    
    def create_session(self) -> str:
        execution_id = str(uuid.uuid4())

        self.sessions[execution_id] = ExecutionSession(
            execution_id=execution_id
        )

        return execution_id
    
    def get_session(self, execution_id: str):
        session = self.sessions.get(execution_id)
        if not session:
            return None

        return {
            "execution_id": execution_id,
            "created_at": session.created_at,
            "traces": {
                step_id: vars(trace)
                for step_id, trace in session.traces.items()
            }
        }