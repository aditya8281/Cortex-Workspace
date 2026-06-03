from typing import List

from .models import SystemEvent


class EventBus:
    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self.events: List[SystemEvent] = []

    def emit(self, event: SystemEvent) -> None:
        self.events.append(event)

        if len(self.events) > self.max_size:
            self.events.pop(0)

    def get_events(self, limit: int = 100):
        return self.events[-limit:]
