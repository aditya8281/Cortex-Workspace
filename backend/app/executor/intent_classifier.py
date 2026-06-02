from backend.app.executor.schemas import (
    IntentType,
    IntentDecision,
    IntentConfidence,
)


class IntentClassifier:

    def classify(self, query: str) -> IntentDecision:
        q = query.lower()

        keywords = []

        # TOOL INTENT
        if any(word in q for word in ["file", "pdf", "document"]):
            keywords = ["file", "pdf", "document"]

            return IntentDecision(
                intent=IntentType.TOOL,
                confidence=0.85,
                confidence_level=IntentConfidence.HIGH,
                subtype="file_search",
                keywords=keywords,
                requires_tools=True,
            )

        # SYSTEM INTENT
        if any(word in q for word in ["bug", "error", "repo", "system"]):
            keywords = ["bug", "error", "repo", "system"]

            return IntentDecision(
                intent=IntentType.SYSTEM,
                confidence=0.80,
                confidence_level=IntentConfidence.HIGH,
                subtype="system_scan",
                keywords=keywords,
                requires_tools=True,
            )

        # RAG INTENT
        if any(word in q for word in ["code", "class", "function", "authentication", "router", "endpoint"]):
            keywords = ["code", "architecture"]

            return IntentDecision(
                intent=IntentType.RAG,
                confidence=0.78,
                confidence_level=IntentConfidence.MEDIUM,
                subtype="repo_rag",
                keywords=keywords,
                requires_tools=True,
            )

        # CHAT FALLBACK
        return IntentDecision(
            intent=IntentType.CHAT,
            confidence=0.60,
            confidence_level=IntentConfidence.MEDIUM,
            subtype=None,
            keywords=[],
            requires_tools=False,
        )