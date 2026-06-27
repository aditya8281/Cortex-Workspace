"""Transparency service — explainable AI decisions."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class DecisionFactor:
    """A single factor in a decision."""

    key: str
    value: Any
    weight: float = 1.0
    description: str | None = None


@dataclass
class DecisionExplanation:
    """Structured explanation of an automated decision."""

    decision_type: str
    reasoning: str
    factors: list[DecisionFactor]
    confidence: float
    alternatives_considered: list[str]
    recommendation: str
    risk_level: str
    audit_trail: list[str] = field(default_factory=list)


class TransparencyService:
    """Provides explainable decisions for automated Cortex reasoning.

    Every automated decision should be explainable through this service.
    """

    DECISION_TEMPLATES: dict[str, dict[str, Any]] = {
        "memory_retrieval": {
            "description": "Retrieved relevant memories based on query similarity",
            "factors": ["query_similarity", "recency", "relevance_score", "access_frequency"],
            "alternatives": ["semantic_search", "keyword_match", "graph_traversal"],
        },
        "hypothesis_scoring": {
            "description": "Scored hypothesis based on evidence balance and novelty",
            "factors": ["evidence_count", "evidence_quality", "novelty", "historical_accuracy"],
            "alternatives": ["simple_majority_vote", "weighted_average", "bayesian_update"],
        },
        "tool_selection": {
            "description": "Selected tool based on task requirements and past performance",
            "factors": ["tool_capability", "past_success_rate", "resource_requirements", "user_preferences"],
            "alternatives": ["alternative_tool_a", "alternative_tool_b", "manual_intervention"],
        },
        "error_analysis": {
            "description": "Analyzed error to determine root cause and resolution",
            "factors": ["error_type", "stack_trace", "historical_patterns", "context"],
            "alternatives": ["retry", "escalate", "skip", "alternative_approach"],
        },
        "access_decision": {
            "description": "Evaluated access request against policies and consent",
            "factors": ["user_role", "resource_owner", "consent_state", "policy_match"],
            "alternatives": ["deny", "request_consent", "escalate_to_admin"],
        },
    }

    def explain_decision(self, decision_type: str, context: dict[str, Any]) -> dict[str, Any]:
        """Generate a structured explanation for an automated decision."""
        template = self.DECISION_TEMPLATES.get(decision_type, {})
        factors = self._extract_factors(decision_type, context)
        confidence = context.get("confidence", 0.5)
        alternatives = template.get("alternatives", [])

        explanation = DecisionExplanation(
            decision_type=decision_type,
            reasoning=self._generate_reasoning(decision_type, context, template),
            factors=factors,
            confidence=confidence,
            alternatives_considered=alternatives,
            recommendation=self._generate_recommendation(confidence),
            risk_level=self._assess_risk_level(confidence, context),
            audit_trail=context.get("audit_trail", []),
        )
        return asdict(explanation)

    def _extract_factors(self, decision_type: str, context: dict[str, Any]) -> list[DecisionFactor]:
        """Extract decision factors from context."""
        template = self.DECISION_TEMPLATES.get(decision_type, {})
        factor_keys = template.get("factors", [])
        factors: list[DecisionFactor] = []

        for key in factor_keys:
            value = context.get(key, "N/A")
            weight = context.get(f"{key}_weight", 1.0)
            factors.append(
                DecisionFactor(
                    key=key,
                    value=value,
                    weight=weight,
                    description=f"Weight of {key} in decision: {weight}",
                )
            )

        # Extra context factors not in template
        skip_keys = set(factor_keys) | {"confidence", "audit_trail"}
        for key, value in context.items():
            if key not in skip_keys and not key.endswith("_weight"):
                factors.append(
                    DecisionFactor(
                        key=key,
                        value=value,
                        weight=0.5,
                        description=f"Additional context: {key}",
                    )
                )
        return factors

    def _generate_reasoning(self, decision_type: str, context: dict[str, Any], template: dict[str, Any]) -> str:
        """Generate human-readable reasoning."""
        description = template.get("description", f"Decision of type '{decision_type}'")
        factor_count = len(template.get("factors", []))
        confidence = context.get("confidence", 0.5)
        ctx_keys = list(context.keys())[:5]
        return (
            f"{description}. "
            f"Evaluated {factor_count} factors with overall confidence of {confidence:.0%}. "
            f"Context keys: {', '.join(ctx_keys)}."
        )

    def _generate_recommendation(self, confidence: float) -> str:
        if confidence > 0.8:
            return "Proceed with high confidence. Decision is well-supported by evidence."
        if confidence > 0.6:
            return "Proceed with verification. Decision is supported but could benefit from additional evidence."
        if confidence > 0.4:
            return "Verify with user before proceeding. Confidence is moderate."
        return "Seek additional information or user input. Confidence is low."

    def _assess_risk_level(self, confidence: float, context: dict[str, Any]) -> str:  # noqa: ARG002
        if confidence < 0.4:
            return "high"
        if confidence < 0.7:
            return "medium"
        return "low"
