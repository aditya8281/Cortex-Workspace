"""Tests for ContextEngineService."""

from __future__ import annotations

import pytest
from sqlalchemy.orm import Session

from backend.app.services.awareness.context_engine import ContextEngineService


class TestContextEngineServiceRules:
    """Tests for context rule CRUD and matching."""

    def test_create_rule(self, db_session: Session) -> None:
        """Creating a rule returns a valid record."""
        svc = ContextEngineService(db_session)
        rule = svc.create_rule(user_id=1, name="test_rule", rule_type="time")
        assert rule.id is not None
        assert rule.name == "test_rule"
        assert rule.rule_type == "time"
        assert rule.enabled  # truthy — SQLite stores booleans as 1
        assert rule.user_id == 1

    def test_create_rule_with_conditions_and_actions(self, db_session: Session) -> None:
        """Creating a rule stores conditions and actions."""
        svc = ContextEngineService(db_session)
        rule = svc.create_rule(
            user_id=1, name="work_hours", rule_type="time", conditions={"hour": 9}, actions={"mode": "focus"}
        )
        assert rule.conditions == {"hour": 9}
        assert rule.actions == {"mode": "focus"}

    def test_create_rule_defaults(self, db_session: Session) -> None:
        """Creating a rule with defaults gets empty conditions/actions and priority 0."""
        svc = ContextEngineService(db_session)
        rule = svc.create_rule(user_id=1, name="r1", rule_type="time")
        assert rule.conditions == {}
        assert rule.actions == {}
        assert rule.priority == 0
        assert rule.hit_count == 0

    def test_get_rules(self, db_session: Session) -> None:
        """Getting rules returns all rules for the user."""
        svc = ContextEngineService(db_session)
        svc.create_rule(user_id=1, name="r1", rule_type="time")
        svc.create_rule(user_id=1, name="r2", rule_type="location")
        rules = svc.get_rules(user_id=1)
        assert len(rules) == 2

    def test_get_rules_empty(self, db_session: Session) -> None:
        """Getting rules with no data returns empty list."""
        svc = ContextEngineService(db_session)
        assert svc.get_rules(user_id=1) == []

    def test_get_rules_by_type(self, db_session: Session) -> None:
        """Getting rules by type returns only matching rules."""
        svc = ContextEngineService(db_session)
        svc.create_rule(user_id=1, name="r1", rule_type="time")
        svc.create_rule(user_id=1, name="r2", rule_type="location")
        rules = svc.get_rules(user_id=1, rule_type="time")
        assert len(rules) == 1
        assert rules[0].rule_type == "time"

    def test_get_rules_user_isolation(self, db_session: Session) -> None:
        """Getting rules is isolated by user_id."""
        svc = ContextEngineService(db_session)
        svc.create_rule(user_id=1, name="r1", rule_type="time")
        svc.create_rule(user_id=2, name="r2", rule_type="time")
        assert len(svc.get_rules(user_id=1)) == 1
        assert len(svc.get_rules(user_id=2)) == 1

    def test_update_rule(self, db_session: Session) -> None:
        """Updating a rule changes the specified fields."""
        svc = ContextEngineService(db_session)
        rule = svc.create_rule(user_id=1, name="r1", rule_type="time")
        updated = svc.update_rule(rule.id, name="r1_updated", priority=10)
        assert updated.name == "r1_updated"
        assert updated.priority == 10

    def test_update_rule_conditions(self, db_session: Session) -> None:
        """Updating a rule changes conditions and actions."""
        svc = ContextEngineService(db_session)
        rule = svc.create_rule(user_id=1, name="r1", rule_type="time")
        updated = svc.update_rule(rule.id, conditions={"new_key": "val"}, actions={"new_action": True})
        assert updated.conditions == {"new_key": "val"}
        assert updated.actions == {"new_action": True}

    def test_update_rule_not_found(self, db_session: Session) -> None:
        """Updating a non-existent rule raises ValueError."""
        svc = ContextEngineService(db_session)
        with pytest.raises(ValueError, match="not found"):
            svc.update_rule(999, name="x")

    def test_delete_rule(self, db_session: Session) -> None:
        """Deleting a rule removes it."""
        svc = ContextEngineService(db_session)
        rule = svc.create_rule(user_id=1, name="r1", rule_type="time")
        svc.delete_rule(rule.id)
        assert svc.get_rules(user_id=1) == []

    def test_delete_rule_not_found(self, db_session: Session) -> None:
        """Deleting a non-existent rule raises ValueError."""
        svc = ContextEngineService(db_session)
        with pytest.raises(ValueError, match="not found"):
            svc.delete_rule(999)

    def test_match_rules(self, db_session: Session) -> None:
        """Matching rules returns rules whose conditions are satisfied."""
        svc = ContextEngineService(db_session)
        svc.create_rule(user_id=1, name="r1", rule_type="time", conditions={"hour": 9})
        matched = svc.match_rules(user_id=1, context={"hour": 9})
        assert len(matched) == 1
        assert matched[0].name == "r1"
        assert matched[0].hit_count == 1

    def test_match_rules_no_match(self, db_session: Session) -> None:
        """Matching rules returns empty list when conditions don't match."""
        svc = ContextEngineService(db_session)
        svc.create_rule(user_id=1, name="r1", rule_type="time", conditions={"hour": 9})
        matched = svc.match_rules(user_id=1, context={"hour": 17})
        assert len(matched) == 0

    def test_match_rules_increments_hit_count(self, db_session: Session) -> None:
        """Matching rules increments hit_count each time."""
        svc = ContextEngineService(db_session)
        svc.create_rule(user_id=1, name="r1", rule_type="time", conditions={"hour": 9})
        svc.match_rules(user_id=1, context={"hour": 9})
        svc.match_rules(user_id=1, context={"hour": 9})
        matched = svc.match_rules(user_id=1, context={"hour": 9})
        assert matched[0].hit_count == 3

    def test_match_rules_disabled_excluded(self, db_session: Session) -> None:
        """Disabled rules are not matched."""
        svc = ContextEngineService(db_session)
        rule = svc.create_rule(user_id=1, name="r1", rule_type="time", conditions={"hour": 9})
        svc.update_rule(rule.id, enabled=False)
        matched = svc.match_rules(user_id=1, context={"hour": 9})
        assert len(matched) == 0

    def test_match_rules_empty_conditions_always_match(self, db_session: Session) -> None:
        """Rules with empty conditions match any context."""
        svc = ContextEngineService(db_session)
        svc.create_rule(user_id=1, name="r1", rule_type="time", conditions={})
        matched = svc.match_rules(user_id=1, context={"anything": "goes"})
        assert len(matched) == 1

    def test_match_rules_partial_context(self, db_session: Session) -> None:
        """Rules match when context contains all required keys."""
        svc = ContextEngineService(db_session)
        svc.create_rule(user_id=1, name="r1", rule_type="time", conditions={"hour": 9, "day": "monday"})
        matched = svc.match_rules(user_id=1, context={"hour": 9, "day": "monday", "extra": True})
        assert len(matched) == 1

    def test_match_rules_partial_mismatch(self, db_session: Session) -> None:
        """Rules don't match when context is missing a required key."""
        svc = ContextEngineService(db_session)
        svc.create_rule(user_id=1, name="r1", rule_type="time", conditions={"hour": 9, "day": "monday"})
        matched = svc.match_rules(user_id=1, context={"hour": 9})
        assert len(matched) == 0


class TestContextEngineServiceState:
    """Tests for context state management."""

    def test_set_and_get_state(self, db_session: Session) -> None:
        """Setting state and getting it back returns the value."""
        svc = ContextEngineService(db_session)
        state = svc.set_state(user_id=1, state_key="current_app", state_value={"name": "code"})
        assert state.id is not None
        assert state.state_key == "current_app"
        retrieved = svc.get_state(user_id=1, state_key="current_app")
        assert retrieved is not None
        assert retrieved.state_value == {"name": "code"}

    def test_set_state_upsert(self, db_session: Session) -> None:
        """Setting state with an existing key updates in place."""
        svc = ContextEngineService(db_session)
        s1 = svc.set_state(user_id=1, state_key="k", state_value={"v": 1})
        s2 = svc.set_state(user_id=1, state_key="k", state_value={"v": 2})
        assert s1.id == s2.id
        assert s2.state_value == {"v": 2}
        assert svc.get_state(user_id=1, state_key="k").state_value == {"v": 2}

    def test_get_state_not_found(self, db_session: Session) -> None:
        """Getting non-existent state returns None."""
        svc = ContextEngineService(db_session)
        assert svc.get_state(user_id=1, state_key="nonexistent") is None

    def test_get_state_user_isolation(self, db_session: Session) -> None:
        """State is isolated by user_id."""
        svc = ContextEngineService(db_session)
        svc.set_state(user_id=1, state_key="k", state_value={"a": 1})
        assert svc.get_state(user_id=1, state_key="k") is not None
        assert svc.get_state(user_id=2, state_key="k") is None

    def test_get_all_states(self, db_session: Session) -> None:
        """Getting all states returns all keys for the user."""
        svc = ContextEngineService(db_session)
        svc.set_state(user_id=1, state_key="a", state_value={})
        svc.set_state(user_id=1, state_key="b", state_value={})
        states = svc.get_all_states(user_id=1)
        assert len(states) == 2

    def test_get_all_states_empty(self, db_session: Session) -> None:
        """Getting all states with no data returns empty list."""
        svc = ContextEngineService(db_session)
        assert svc.get_all_states(user_id=1) == []

    def test_get_all_states_user_isolation(self, db_session: Session) -> None:
        """Getting all states is isolated by user_id."""
        svc = ContextEngineService(db_session)
        svc.set_state(user_id=1, state_key="a", state_value={})
        svc.set_state(user_id=2, state_key="a", state_value={})
        assert len(svc.get_all_states(user_id=1)) == 1
        assert len(svc.get_all_states(user_id=2)) == 1

    def test_set_state_stores_metadata(self, db_session: Session) -> None:
        """Setting state stores source and confidence."""
        svc = ContextEngineService(db_session)
        state = svc.set_state(user_id=1, state_key="k", state_value={}, source="manual", confidence=0.8)
        assert state.source == "manual"
        assert state.confidence == 0.8

    def test_set_state_default_metadata(self, db_session: Session) -> None:
        """Setting state uses default source and confidence."""
        svc = ContextEngineService(db_session)
        state = svc.set_state(user_id=1, state_key="k", state_value={})
        assert state.source == "system"
        assert state.confidence == 1.0


class TestContextEngineServiceEvents:
    """Tests for context event logging."""

    def test_log_event(self, db_session: Session) -> None:
        """Logging an event returns a valid record."""
        svc = ContextEngineService(db_session)
        event = svc.log_event(user_id=1, event_type="app_switch", event_data={"app": "code"})
        assert event.id is not None
        assert event.event_type == "app_switch"
        assert event.event_data == {"app": "code"}
        assert event.user_id == 1

    def test_log_event_defaults(self, db_session: Session) -> None:
        """Logging an event uses default metadata."""
        svc = ContextEngineService(db_session)
        event = svc.log_event(user_id=1, event_type="click")
        assert event.event_data == {}
        assert event.source == "system"
        assert event.relevance_score == 0.0
        assert event.related_rule_id is None

    def test_log_event_with_metadata(self, db_session: Session) -> None:
        """Logging an event with full metadata stores all fields."""
        svc = ContextEngineService(db_session)
        event = svc.log_event(
            user_id=1,
            event_type="app_switch",
            event_data={"app": "code"},
            source="tracker",
            relevance_score=0.9,
            related_rule_id=42,
        )
        assert event.source == "tracker"
        assert event.relevance_score == 0.9
        assert event.related_rule_id == 42

    def test_get_events(self, db_session: Session) -> None:
        """Getting events returns all events for the user."""
        svc = ContextEngineService(db_session)
        svc.log_event(user_id=1, event_type="app_switch")
        svc.log_event(user_id=1, event_type="file_open")
        events = svc.get_events(user_id=1)
        assert len(events) == 2

    def test_get_events_empty(self, db_session: Session) -> None:
        """Getting events with no data returns empty list."""
        svc = ContextEngineService(db_session)
        assert svc.get_events(user_id=1) == []

    def test_get_events_by_type(self, db_session: Session) -> None:
        """Getting events by type returns only matching events."""
        svc = ContextEngineService(db_session)
        svc.log_event(user_id=1, event_type="app_switch")
        svc.log_event(user_id=1, event_type="file_open")
        events = svc.get_events(user_id=1, event_type="app_switch")
        assert len(events) == 1
        assert events[0].event_type == "app_switch"

    def test_get_events_respects_limit(self, db_session: Session) -> None:
        """Getting events respects the limit parameter."""
        svc = ContextEngineService(db_session)
        for _ in range(10):
            svc.log_event(user_id=1, event_type="click")
        events = svc.get_events(user_id=1, limit=3)
        assert len(events) == 3

    def test_get_events_user_isolation(self, db_session: Session) -> None:
        """Getting events is isolated by user_id."""
        svc = ContextEngineService(db_session)
        svc.log_event(user_id=1, event_type="click")
        svc.log_event(user_id=2, event_type="click")
        assert len(svc.get_events(user_id=1)) == 1
        assert len(svc.get_events(user_id=2)) == 1
