# Phase 3: Unified Search & Agents

**Goal:** Unified search across all data types (memories, code, tasks, vault) and the beginning of the agent system — a planner agent that can break tasks into subtasks and delegate to specialized agents.

**Depends on:** Phase 2 (indexing + knowledge graph), Phase 0-B (service abstraction)

---

## Architecture

```
┌─────────────────────────────────────────────────┐
│                  FRONTEND                       │
│  GlobalSearch ── SearchResults ── AgentChat     │
└──────────────┬──────────────────────────────────┘
               │
┌──────────────▼──────────────────────────────────┐
│                 API LAYER                       │
│  /api/v1/search/unified   /api/v1/agents/       │
│  /api/v1/agents/chat      /api/v1/agents/runs   │
└──────────────┬──────────────────────────────────┘
               │
┌──────────────▼──────────────────────────────────┐
│              SERVICES                           │
│  UnifiedSearch ── PlannerAgent                 │
│  ExecutorAgent ── AgentRunManager              │
│  FeedbackCollector                             │
└──────────────┬──────────────────────────────────┘
               │
┌──────────────▼──────────────────────────────────┐
│              DATA LAYER                         │
│  PostgreSQL (agents, runs, steps, feedback)     │
│  Qdrant (code + memory embeddings)              │
└────────────────────────────────────────────────┘
```

---

## Task 1: Agent Database Schema

### 1.1 Agent Models

**Create:** `backend/app/models/agent.py`

```python
from sqlalchemy import Column, Integer, String, Text, JSON, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base

class Agent(Base):
    __tablename__ = "agents"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    system_prompt = Column(Text, nullable=False)
    model_id = Column(String(100), nullable=False)
    tools = Column(JSON, nullable=True)  # List of tool names this agent can use
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)
    
    runs = relationship("AgentRun", back_populates="agent")

class AgentRun(Base):
    __tablename__ = "agent_runs"
    
    id = Column(Integer, primary_key=True)
    agent_id = Column(Integer, ForeignKey("agents.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    input = Column(Text, nullable=False)
    status = Column(String(20), nullable=False, default="pending")  # pending, running, completed, failed
    output = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    
    agent = relationship("Agent", back_populates="runs")
    steps = relationship("AgentStep", back_populates="run")
    feedback = relationship("AgentFeedback", back_populates="run")

class AgentStep(Base):
    __tablename__ = "agent_steps"
    
    id = Column(Integer, primary_key=True)
    run_id = Column(Integer, ForeignKey("agent_runs.id", ondelete="CASCADE"), nullable=False)
    step_number = Column(Integer, nullable=False)
    thought = Column(Text, nullable=True)
    action = Column(String(100), nullable=False)
    action_input = Column(JSON, nullable=True)
    observation = Column(Text, nullable=True)
    status = Column(String(20), nullable=False, default="pending")
    created_at = Column(DateTime, nullable=False)
    
    run = relationship("AgentRun", back_populates="steps")

class AgentFeedback(Base):
    __tablename__ = "agent_feedback"
    
    id = Column(Integer, primary_key=True)
    run_id = Column(Integer, ForeignKey("agent_runs.id", ondelete="CASCADE"), nullable=False)
    rating = Column(Integer, nullable=False)  # 1-5
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False)
    
    run = relationship("AgentRun", back_populates="feedback")
```

---

## Task 2: Planner Agent

**Create:** `backend/app/agents/planner.py`

```python
from typing import Any
from app.agents.base import BaseAgent, AgentMessage
from app.services.llm.provider import LLMProvider

class PlannerAgent(BaseAgent):
    """Plans tasks and delegates to specialized agents."""
    
    def __init__(self, llm: LLMProvider):
        super().__init__(llm)
        self.system_prompt = """You are a planner agent. Break down user tasks into subtasks.
        For each subtask, specify:
        1. The goal
        2. Which agent should handle it (executor, researcher, reviewer)
        3. Dependencies on other subtasks
        4. Expected output
        
        Always output as JSON array of subtasks."""
    
    async def plan(self, task: str) -> list[dict]:
        response = await self.llm.chat(
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": task},
            ],
            tools=[],  # No tools needed for planning
            config=None,
        )
        return self._parse_plan(response[0])
    
    def _parse_plan(self, text: str) -> list[dict]:
        """Parse LLM response into structured plan."""
        import json
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return [{"goal": text, "agent": "executor", "dependencies": []}]
```

---

## Task 3: Executor Agent

**Create:** `backend/app/agents/executor.py`

```python
from app.agents.base import BaseAgent
from app.services.llm.provider import LLMProvider
from app.services.search import UnifiedSearch

class ExecutorAgent(BaseAgent):
    """Executes tasks using available tools."""
    
    def __init__(self, llm: LLMProvider, search: UnifiedSearch):
        super().__init__(llm)
        self.search = search
        self.tools = {
            "search": self._search_tool,
            "read_file": self._read_file_tool,
            "write_file": self._write_file_tool,
        }
    
    async def execute(self, task: str, context: dict | None = None) -> str:
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": task},
        ]
        
        if context:
            messages.append({"role": "user", "content": f"Context: {context}"})
        
        # Agent loop: think -> act -> observe -> repeat
        for _ in range(10):  # Max 10 iterations
            response = await self.llm.chat(messages, self._tool_schemas(), None)
            text, tool_calls = response
            
            if not tool_calls:
                return text
            
            for call in tool_calls:
                tool_name = call["name"]
                tool_input = call["arguments"]
                
                if tool_name in self.tools:
                    observation = await self.tools[tool_name](tool_input)
                    messages.append({"role": "assistant", "content": text, "tool_calls": [call]})
                    messages.append({"role": "tool", "content": str(observation)})
        
        return "Task completed with max iterations"
    
    async def _search_tool(self, query: str) -> list[dict]:
        return await self.search.search(query)
    
    async def _read_file_tool(self, path: str) -> str:
        from pathlib import Path
        return Path(path).read_text(errors="replace")
    
    async def _write_file_tool(self, params: dict) -> str:
        from pathlib import Path
        Path(params["path"]).write_text(params["content"])
        return "File written successfully"
```

---

## Task 4: Agent Run Manager

**Create:** `backend/app/agents/run_manager.py`

```python
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.agent import AgentRun, AgentStep
from app.agents.planner import PlannerAgent
from app.agents.executor import ExecutorAgent

class AgentRunManager:
    def __init__(self, db: Session, planner: PlannerAgent, executor: ExecutorAgent):
        self._db = db
        self._planner = planner
        self._executor = executor
    
    async def run(self, agent_id: int, user_id: int, input_text: str) -> AgentRun:
        agent = self._db.query(Agent).get(agent_id)
        run = AgentRun(
            agent_id=agent_id,
            user_id=user_id,
            input=input_text,
            status="running",
            created_at=datetime.utcnow(),
        )
        self._db.add(run)
        self._db.commit()
        self._db.refresh(run)
        
        try:
            # Plan
            plan = await self._planner.plan(input_text)
            
            # Execute each step
            for i, step_plan in enumerate(plan):
                step = AgentStep(
                    run_id=run.id,
                    step_number=i + 1,
                    thought=step_plan.get("thought", ""),
                    action=step_plan.get("agent", "executor"),
                    action_input=step_plan,
                    status="running",
                    created_at=datetime.utcnow(),
                )
                self._db.add(step)
                self._db.commit()
                
                result = await self._executor.execute(
                    step_plan["goal"],
                    context={"previous_steps": plan[:i]}
                )
                
                step.observation = result
                step.status = "completed"
                self._db.commit()
            
            run.status = "completed"
            run.output = plan[-1].get("goal", "") if plan else "Done"
            run.completed_at = datetime.utcnow()
            self._db.commit()
            
        except Exception as e:
            run.status = "failed"
            run.output = str(e)
            self._db.commit()
        
        return run
```

---

## Task 5: Agent API

**Create:** `backend/app/api/v1/agents.py`

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.agent import Agent, AgentRun

router = APIRouter(prefix="/api/v1/agents", tags=["agents"])

@router.get("/")
async def list_agents(db: Session = Depends(get_db)):
    return db.query(Agent).all()

@router.post("/runs")
async def create_run(agent_id: int, input: str, db: Session = Depends(get_db)):
    manager = AgentRunManager(db, ...)
    run = await manager.run(agent_id, current_user_id, input)
    return run

@router.get("/runs/{run_id}")
async def get_run(run_id: int, db: Session = Depends(get_db)):
    return db.query(AgentRun).get(run_id)

@router.get("/runs/{run_id}/steps")
async def get_run_steps(run_id: int, db: Session = Depends(get_db)):
    return db.query(AgentStep).filter_by(run_id=run_id).order_by(AgentStep.step_number).all()

@router.post("/runs/{run_id}/feedback")
async def add_feedback(run_id: int, rating: int, comment: str | None = None, db: Session = Depends(get_db)):
    feedback = AgentFeedback(run_id=run_id, rating=rating, comment=comment, created_at=datetime.utcnow())
    db.add(feedback)
    db.commit()
    return {"status": "ok"}
```

---

## Task 6: Frontend Components

### 6.1 AgentChat Component

**Create:** `frontend/components/agent/AgentChat.tsx`

```typescript
"use client";
import { useState } from "react";

interface Message {
  role: "user" | "assistant";
  content: string;
}

export function AgentChat({ agentId }: { agentId: number }) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  
  const sendMessage = async () => {
    if (!input.trim()) return;
    
    const userMessage = { role: "user" as const, content: input };
    setMessages([...messages, userMessage]);
    setInput("");
    setLoading(true);
    
    try {
      const res = await fetch("/api/v1/agents/runs", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ agent_id: agentId, input }),
      });
      const run = await res.json();
      
      setMessages(prev => [...prev, { role: "assistant", content: run.output }]);
    } catch (error) {
      console.error("Agent error:", error);
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <div className="flex flex-col h-full">
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((msg, i) => (
          <div key={i} className={`p-3 rounded-lg ${
            msg.role === "user" 
              ? "bg-cortex-accent/20 ml-8" 
              : "bg-cortex-bg-secondary mr-8"
          }`}>
            {msg.content}
          </div>
        ))}
        {loading && (
          <div className="p-3 rounded-lg bg-cortex-bg-secondary mr-8 animate-pulse">
            Thinking...
          </div>
        )}
      </div>
      
      <div className="p-4 border-t border-cortex-border">
        <div className="flex gap-2">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && sendMessage()}
            placeholder="Ask the agent..."
            className="flex-1 px-3 py-2 rounded-lg bg-cortex-bg-secondary border border-cortex-border"
          />
          <button
            onClick={sendMessage}
            disabled={loading}
            className="px-4 py-2 rounded-lg bg-cortex-accent text-white"
          >
            Send
          </button>
        </div>
      </div>
    </div>
  );
}
```

### 6.2 SearchResults Enhancements

Update `SearchResults.tsx` to show:
- Code results with file path, name, and graph context
- Memory results with content preview
- Task results (from future phases)
- Vault results (from future phases)

---

## Verification Checklist

```bash
# Backend
PYTHONPATH=. pytest tests/test_planner.py -v
PYTHONPATH=. pytest tests/test_executor.py -v
PYTHONPATH=. pytest tests/test_agent_runs.py -v

# Frontend
cd frontend && npx tsc --noEmit
cd frontend && npx next lint
```

---

## Exit Criteria

- [ ] Agent tables created with proper migrations
- [ ] Planner agent creates structured plans from tasks
- [ ] Executor agent uses tools to complete tasks
- [ ] Agent run manager orchestrates planner + executor
- [ ] Agent API endpoints functional
- [ ] AgentChat UI component works
- [ ] SearchResults displays enriched results
- [ ] All tests pass
