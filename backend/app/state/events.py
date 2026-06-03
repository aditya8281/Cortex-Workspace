# backend/app/state/events.py

from typing import List
from .models import SystemEvent


class EventBus:
    """
    Lightweight in-memory event collector (selective event sourcing)
    """

    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self.events: List[SystemEvent] = []

    # -----------------------------
    # EMIT EVENT
    # -----------------------------
    def emit(self, event: SystemEvent):
        self.events.append(event)

        if len(self.events) > self.max_size:
            self.events.pop(0)

    # -----------------------------
    # GET EVENTS
    # -----------------------------
    def get_events(self, limit: int = 100):
        return self.events[-limit:]