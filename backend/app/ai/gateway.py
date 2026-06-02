from backend.app.ai.llm_router import LLMRouter
from backend.app.ai.memory.repository import MemoryRepository
from backend.app.agent.file_search import FileSearchAgent
from backend.app.agent.system_scanner import SystemScanner


class AIGateway:
    def __init__(self):
        self.llm = LLMRouter()
        self.memory = MemoryRepository()
        self.file_agent = FileSearchAgent()
        self.system_agent = SystemScanner()

    async def route(self, query: str, user_id: int = None) -> str:
        query_lower = query.lower()

        if "file" in query_lower or "pdf" in query_lower:
            return self.file_agent.search(query)

        if "bug" in query_lower or "error" in query_lower or "repo" in query_lower:
            return self.system_agent.scan(query)

        if user_id:
            memory = self.memory.search(user_id, query)
            if memory:
                return memory

        response = await self.llm.generate(query)

        if user_id and response:
            self.memory.add(user_id, query, response)

        return response