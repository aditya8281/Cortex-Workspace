"""Tests for Event, EventType, EventBus."""

import pytest

from backend.app.core.event_bus import EventBus
from backend.app.core.events import Event, EventDomain, EventType


@pytest.fixture
def bus():
    return EventBus()


@pytest.mark.asyncio
async def test_publish_subscribe(bus):
    """Event should reach registered handler."""
    received = []

    async def handler(event: Event):
        received.append(event)

    bus.subscribe(EventType.MEMORY_CREATED, handler)

    event = Event(
        type=EventType.MEMORY_CREATED,
        source="test",
        data={"memory_id": 1},
    )
    await bus.publish(event)

    assert len(received) == 1
    assert received[0].type == EventType.MEMORY_CREATED
    assert received[0].data["memory_id"] == 1


@pytest.mark.asyncio
async def test_multiple_handlers(bus):
    """Multiple handlers should all receive the event."""
    results = {"a": False, "b": False}

    async def handler_a(event):
        results["a"] = True

    async def handler_b(event):
        results["b"] = True

    bus.subscribe(EventType.MEMORY_CREATED, handler_a)
    bus.subscribe(EventType.MEMORY_CREATED, handler_b)

    await bus.publish(Event(type=EventType.MEMORY_CREATED, source="test", data={}))

    assert results["a"] is True
    assert results["b"] is True


@pytest.mark.asyncio
async def test_handler_error_isolation(bus):
    """Failing handler should not prevent other handlers from executing."""
    results = {"good": False}

    async def failing_handler(event):
        raise RuntimeError("handler failed")

    async def good_handler(event):
        results["good"] = True

    bus.subscribe(EventType.MEMORY_CREATED, failing_handler)
    bus.subscribe(EventType.MEMORY_CREATED, good_handler)

    await bus.publish(Event(type=EventType.MEMORY_CREATED, source="test", data={}))

    assert results["good"] is True  # Good handler still executed
    assert bus._error_count == 1  # Error was counted


@pytest.mark.asyncio
async def test_unsubscribe(bus):
    """Unsubscribed handler should not receive events."""
    received = []

    async def handler(event):
        received.append(event)

    bus.subscribe(EventType.MEMORY_CREATED, handler)
    await bus.publish(Event(type=EventType.MEMORY_CREATED, source="test", data={}))
    assert len(received) == 1

    bus.unsubscribe(EventType.MEMORY_CREATED, handler)
    await bus.publish(Event(type=EventType.MEMORY_CREATED, source="test", data={}))
    assert len(received) == 1  # No new event received


@pytest.mark.asyncio
async def test_no_handler_no_error(bus):
    """Publishing with no handlers should not raise."""
    await bus.publish(Event(type=EventType.MEMORY_CREATED, source="test", data={}))


def test_event_domain_extraction():
    """Event domain should be extracted from event type."""
    event = Event(type=EventType.MEMORY_CREATED, source="test", data={})
    assert event.domain == EventDomain.MEMORY

    event = Event(type=EventType.TASK_STARTED, source="test", data={})
    assert event.domain == EventDomain.EXECUTION

    event = Event(type=EventType.MODEL_LOADED, source="test", data={})
    assert event.domain == EventDomain.INTELLIGENCE


def test_event_serialization():
    """Events should serialize and deserialize correctly."""
    event = Event(
        type=EventType.MEMORY_CREATED,
        source="test",
        data={"key": "value"},
        user_id=42,
    )
    event.event_id = "test-uuid"

    d = event.to_dict()
    restored = Event.from_dict(d)

    assert restored.type == event.type
    assert restored.source == event.source
    assert restored.data == event.data
    assert restored.user_id == event.user_id
    assert restored.event_id == event.event_id


def test_get_stats(bus):
    """Stats should reflect handler registration."""

    async def handler(event):
        pass

    bus.subscribe(EventType.MEMORY_CREATED, handler)
    stats = bus.get_stats()
    assert stats["handler_count_by_type"]["memory.created"] == 1


@pytest.mark.asyncio
async def test_start_stop(bus):
    """Bus should track started state."""
    assert bus._started is False
    await bus.start()
    assert bus._started is True
    await bus.stop()
    assert bus._started is False
