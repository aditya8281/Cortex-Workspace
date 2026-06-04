from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class BaseAgent(ABC):
    """
    Abstract base class for all Cortex agents.
    Defines capabilities, query-specific confidence assessment, and execution interface.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique identifier name of the agent."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Brief description of what this agent does."""
        pass

    @property
    @abstractmethod
    def capabilities(self) -> List[str]:
        """List of task capabilities this agent can handle (e.g. ['coding', 'file_search'])."""
        pass

    @abstractmethod
    def confidence(self, query: str, context: Optional[str] = None) -> float:
        """
        Assess how confident this agent is in handling the given query.
        Returns a float between 0.0 (completely unqualified) and 1.0 (perfect match).
        """
        pass

    @abstractmethod
    async def execute(
        self,
        query: str,
        context: Optional[str] = None,
        history: Optional[List[Dict[str, str]]] = None,
        **kwargs: Any
    ) -> Dict[str, Any]:
        """
        Execute agent tasks and return a structured dictionary:
        {
            "result": str,
            "confidence": float,
            "reasoning_summary": str
        }
        """
        pass
