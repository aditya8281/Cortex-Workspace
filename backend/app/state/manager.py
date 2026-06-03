# backend/app/state/manager.py

from .registry import StateRegistry
from .events import EventBus
from .store import StateStore
from .models import SystemEvent


class StateManager:
    """
    Single entry point for ALL system state operations.
    """

    def __init__(self):
        self.registry = StateRegistry()
        self.events = EventBus()
        self.store = StateStore()

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
    # EMIT EVENT (selective logging)
    # -----------------------------
    def emit_event(self, event: SystemEvent):
        self.events.emit(event)
        self.store.save_event(event)

    # -----------------------------
    # SNAPSHOT SYSTEM STATE
    # -----------------------------
    def snapshot(self):
        state = self.registry.get_state()
        self.store.save_snapshot(state)