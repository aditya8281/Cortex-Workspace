from typing import Dict, List, Optional


class MemoryRepository:
    """
    Long-term and episodic memory repository for user interactions.
    """

    def __init__(self):
        # Maps user_id -> list of memory dicts {"query": str, "response": str}
        self._memories: Dict[int, List[Dict[str, str]]] = {}

    def add(self, user_id: int, query: str, response: str) -> None:
        """Store a user memory record."""
        if user_id not in self._memories:
            self._memories[user_id] = []
        self._memories[user_id].append({"query": query, "response": response})

    def search(self, user_id: int, query: str) -> Optional[str]:
        """Search similar memories for a user. Returns the matching response or None."""
        user_memories = self._memories.get(user_id, [])
        query_lower = query.lower()

        # Simple keyword match over stored memory queries
        for mem in reversed(user_memories):
            # Match any significant word (>3 chars) from the query in the memory query
            words = [word for word in query_lower.split() if len(word) > 3]
            if words and any(word in mem["query"].lower() for word in words):
                return f"[Memory Recall]: You previously asked about '{mem['query']}'. Context: {mem['response']}"

        return None
