from typing import Optional

from .registry import StateRegistry
from .events import EventBus
from .store import StateStore
from .models import SystemEvent


class StateManager:
    """
    Single entry point for ALL system state operations.
    Now execution-aware for replay system.
    """

    def __init__(self):
        self.registry = StateRegistry()
        self.events = EventBus()
        self.store = StateStore()

        # -----------------------------
        # CURRENT EXECUTION CONTEXT
        # -----------------------------
        self._current_execution_id: Optional[str] = None

    # -------------------------------------------------
    # EXECUTION CONTEXT CONTROL
    # -------------------------------------------------
    def set_execution_id(self, execution_id: str):
        """
        Called by GraphRunner at execution start
        """
        self._current_execution_id = execution_id

    def clear_execution_id(self):
        """
        Called at execution end
        """
        self._current_execution_id = None

    def get_execution_id(self) -> Optional[str]:
        return self._current_execution_id

    # -----------------------------
    # READ STATE
    # -----------------------------
    def get_state(self):
        return self.registry.get_state()

    # -----------------------------
    # UPDATE STATE
    # -----------------------------
    def update_state(self, updater_fn):
        self.registry.update(updater_fn)

    # -----------------------------
    # EMIT EVENT (EXECUTION-AWARE)
    # -----------------------------
    def emit_event(self, event: SystemEvent):
        self.events.emit(event)

        # 🔥 CRITICAL FIX: attach execution_id
        self.store.save_event(
            event,
            execution_id=self._current_execution_id
        )

    # -----------------------------
    # SNAPSHOT SYSTEM STATE
    # -----------------------------
    def snapshot(self):
        state = self.registry.get_state()
        self.store.save_snapshot(state)