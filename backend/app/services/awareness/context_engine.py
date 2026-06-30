"""Context engine — manages rules, state, and events for adaptive context awareness."""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from backend.app.models.awareness.context_engine import ContextEvent, ContextRule, ContextState

logger = logging.getLogger(__name__)


class ContextEngineService:
    """Manages context rules, persistent state, and event logging."""

    def __init__(self, db: Session) -> None:
        self.db = db

    # ------------------------------------------------------------------
    # Rules CRUD
    # ------------------------------------------------------------------

    def create_rule(
        self,
        user_id: int,
        name: str,
        rule_type: str,
        description: str | None = None,
        conditions: dict | None = None,
        actions: dict | None = None,
        priority: int = 0,
    ) -> ContextRule:
        """Create a new context rule."""
        rule = ContextRule(
            user_id=user_id,
            name=name,
            rule_type=rule_type,
            description=description,
            conditions=conditions or {},
            actions=actions or {},
            priority=priority,
        )
        self.db.add(rule)
        self.db.commit()
        self.db.refresh(rule)
        logger.info("Created context rule %d (%s)", rule.id, name)
        return rule

    def get_rules(self, user_id: int, rule_type: str | None = None) -> list[ContextRule]:
        """Get rules for a user, optionally filtered by type."""
        q = self.db.query(ContextRule).filter(ContextRule.user_id == user_id)
        if rule_type:
            q = q.filter(ContextRule.rule_type == rule_type)
        return q.order_by(ContextRule.priority.desc()).all()

    def update_rule(self, rule_id: int, **kwargs: object) -> ContextRule:
        """Update fields on an existing rule."""
        rule = self.db.query(ContextRule).filter(ContextRule.id == rule_id).first()
        if not rule:
            raise ValueError(f"Rule {rule_id} not found")
        for k, v in kwargs.items():
            if hasattr(rule, k) and v is not None:
                setattr(rule, k, v)
        self.db.commit()
        self.db.refresh(rule)
        return rule

    def delete_rule(self, rule_id: int) -> None:
        """Delete a context rule."""
        rule = self.db.query(ContextRule).filter(ContextRule.id == rule_id).first()
        if not rule:
            raise ValueError(f"Rule {rule_id} not found")
        self.db.delete(rule)
        self.db.commit()
        logger.info("Deleted context rule %d", rule_id)

    def match_rules(self, user_id: int, context: dict) -> list[ContextRule]:
        """Return enabled rules whose conditions match the given context."""
        rules = (
            self.db.query(ContextRule)
            .filter(ContextRule.user_id == user_id, ContextRule.enabled == True)  # noqa: E712
            .all()
        )
        matched: list[ContextRule] = []
        for rule in rules:
            if self._conditions_match(rule.conditions, context):
                rule.hit_count += 1
                rule.last_hit_at = datetime.now(timezone.utc)
                matched.append(rule)
        if matched:
            self.db.commit()
        return matched

    def _conditions_match(self, conditions: dict, context: dict) -> bool:
        """Check if rule conditions are satisfied by the context."""
        if not conditions:
            return True
        return all(context.get(key) == value for key, value in conditions.items())

    # ------------------------------------------------------------------
    # State management
    # ------------------------------------------------------------------

    def get_state(self, user_id: int, state_key: str) -> ContextState | None:
        """Get a single context state by key."""
        return (
            self.db.query(ContextState)
            .filter(ContextState.user_id == user_id, ContextState.state_key == state_key)
            .first()
        )

    def set_state(
        self,
        user_id: int,
        state_key: str,
        state_value: dict,
        source: str = "system",
        confidence: float = 1.0,
    ) -> ContextState:
        """Create or update a context state entry."""
        state = self.get_state(user_id, state_key)
        if state:
            state.state_value = state_value
            state.source = source
            state.confidence = confidence
        else:
            state = ContextState(
                user_id=user_id,
                state_key=state_key,
                state_value=state_value,
                source=source,
                confidence=confidence,
            )
            self.db.add(state)
        self.db.commit()
        self.db.refresh(state)
        return state

    def get_all_states(self, user_id: int) -> list[ContextState]:
        """Get all context states for a user."""
        return self.db.query(ContextState).filter(ContextState.user_id == user_id).all()

    # ------------------------------------------------------------------
    # Event logging
    # ------------------------------------------------------------------

    def log_event(
        self,
        user_id: int,
        event_type: str,
        event_data: dict | None = None,
        source: str = "system",
        relevance_score: float = 0.0,
        related_rule_id: int | None = None,
    ) -> ContextEvent:
        """Log a context event."""
        event = ContextEvent(
            user_id=user_id,
            event_type=event_type,
            event_data=event_data or {},
            source=source,
            relevance_score=relevance_score,
            related_rule_id=related_rule_id,
        )
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)
        return event

    def get_events(self, user_id: int, event_type: str | None = None, limit: int = 50) -> list[ContextEvent]:
        """Get recent events for a user, optionally filtered by type."""
        q = self.db.query(ContextEvent).filter(ContextEvent.user_id == user_id)
        if event_type:
            q = q.filter(ContextEvent.event_type == event_type)
        return q.order_by(ContextEvent.created_at.desc()).limit(limit).all()
