# backend/app/state/registry.py

from threading import RLock
from .models import SystemState


class StateRegistry:
    """
    In-memory fast state holder (OS-like RAM layer)
    """

    def __init__(self):
        self._lock = RLock()
        self._state = SystemState()

    # -----------------------------
    # READ STATE
    # -----------------------------
    def get_state(self) -> SystemState:
        with self._lock:
            return self._state

    # -----------------------------
    # UPDATE STATE (partial safe update)
    # -----------------------------
    def update(self, updater_fn):
        """
        updater_fn(state) -> modifies state in-place
        """
        with self._lock:
            updater_fn(self._state)

    # -----------------------------
    # REPLACE STATE (rare use)
    # -----------------------------
    def replace(self, new_state: SystemState):
        with self._lock:
            self._state = new_state