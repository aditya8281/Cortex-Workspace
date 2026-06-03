from threading import RLock

from .models import SystemState


class StateRegistry:
    def __init__(self):
        self._lock = RLock()
        self._state = SystemState()

    def get_state(self) -> SystemState:
        with self._lock:
            return self._state

    def update(self, updater_fn):
        with self._lock:
            updater_fn(self._state)

    def replace(self, new_state: SystemState):
        with self._lock:
            self._state = new_state
