import time
from dataclasses import dataclass, field
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


class ExecutionTracer:

    def __init__(self):
        self.traces: dict[str, StepTrace] = {}

    # -------------------------------------------------
    # STEP START
    # -------------------------------------------------
    def start(self, step_id: str, step_type: str, name: str | None):

        self.traces[step_id] = StepTrace(
            step_id=step_id,
            step_type=step_type,
            name=name,
            start_time=time.time(),
            status="running"
        )

    # -------------------------------------------------
    # STEP END
    # -------------------------------------------------
    def end(self, step_id: str, result: Any = None, error: str | None = None):

        trace = self.traces.get(step_id)
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