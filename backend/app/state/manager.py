from typing import Optional

from .events import EventBus
from .registry import StateRegistry
from .store import StateStore
from .models import SystemEvent


class StateManager:
    def __init__(self):
        self.registry = StateRegistry()
        self.events = EventBus()
        self.store = StateStore()
        self._current_execution_id: Optional[str] = None

    def set_execution_id(self, execution_id: str) -> None:
        self._current_execution_id = execution_id

    def clear_execution_id(self) -> None:
        self._current_execution_id = None

    def get_execution_id(self) -> Optional[str]:
        return self._current_execution_id

    def get_state(self):
        return self.registry.get_state()

    def update_state(self, updater_fn):
        self.registry.update(updater_fn)

    def emit_event(
        self,
        event: SystemEvent,
        execution_id: Optional[str] = None
    ) -> None:
        self.events.emit(event)
        self.store.save_event(
            event,
            execution_id=execution_id or self._current_execution_id,
        )

    def snapshot(self) -> None:
        state = self.registry.get_state()
        self.store.save_snapshot(state)

    def get_events(self, execution_id: str):
        return self.store.get_events_by_execution(execution_id)

    def list_executions(self, limit: int = 50):
        return self.store.list_executions(limit=limit)
