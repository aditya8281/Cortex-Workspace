from typing import Dict, List, Optional, Any
from backend.app.agent.base import BaseAgent

class AgentRegistry:
    def __init__(self):
        self._agents: Dict[str, BaseAgent] = {}

    def register(self, agent: BaseAgent) -> None:
        """Register a new agent in the registry."""
        self._agents[agent.name] = agent

    def unregister(self, name: str) -> Optional[BaseAgent]:
        """Unregister an agent by name from the registry."""
        return self._agents.pop(name, None)

    def get(self, name: str) -> Optional[BaseAgent]:
        """Get an agent by name."""
        return self._agents.get(name)

    def discover_agents(self) -> List[BaseAgent]:
        """List all currently registered agents."""
        return list(self._agents.values())

    def route_request(self, query: str, context: Optional[str] = None) -> tuple[BaseAgent, float]:
        """
        Route the request to the agent with the highest confidence score.
        Returns a tuple of (best_agent, confidence_score).
        """
        agents = self.discover_agents()
        if not agents:
            raise ValueError("No agents registered in the AgentRegistry.")

        best_agent = None
        best_score = -1.0

        for agent in agents:
            try:
                score = agent.confidence(query, context)
            except Exception:
                score = 0.0
            
            if score > best_score:
                best_score = score
                best_agent = agent

        # Fallback to the first agent if all confidence scores are identical/zero
        if best_agent is None:
            best_agent = agents[0]
            best_score = 0.0

        return best_agent, best_score
