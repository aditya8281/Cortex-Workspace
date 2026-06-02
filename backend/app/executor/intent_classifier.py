from backend.app.executor.schemas import IntentType


class IntentClassifier:

    def classify(self, query: str) -> IntentType:
        q = query.lower()

        if any(word in q for word in ["file", "pdf", "document"]):
            return IntentType.TOOL

        if any(word in q for word in ["bug", "error", "repo", "system"]):
            return IntentType.SYSTEM

        return IntentType.CHAT