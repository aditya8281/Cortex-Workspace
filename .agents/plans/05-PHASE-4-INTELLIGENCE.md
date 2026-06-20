# Phase 4: Intelligence

> **⚠️ SUPERSEDED:** This plan has been split into Phase 4A (LLM Integration) and Phase 4B (Smart Indexing). See `08-PHASE-4A-LLM-INTEGRATION.md` and `09-PHASE-4B-SMART-INDEXING.md` for the updated plans.

**Goal:** Context-aware agent responses, workspace understanding, and learning loop. Agents understand your codebase, remember past interactions, and improve over time.

**Depends on:** Phase 3 (unified search + agents), Phase 2 (knowledge graph)

---

## Architecture

```
┌─────────────────────────────────────────────────┐
│                  FRONTEND                       │
│  AgentChat ── ContextPanel ── MemoryTimeline    │
└──────────────┬──────────────────────────────────┘
               │
┌──────────────▼──────────────────────────────────┐
│                 API LAYER                       │
│  /api/v1/agents/chat    /api/v1/memory/history   │
│  /api/v1/agents/context /api/v1/feedback/        │
└──────────────┬──────────────────────────────────┘
               │
┌──────────────▼──────────────────────────────────┐
│              SERVICES                           │
│  ContextBuilder ── ConversationMemory          │
│  LearningLoop ── FeedbackCollector             │
│  WorkspaceUnderstanding                        │
└──────────────┬──────────────────────────────────┘
               │
┌──────────────▼──────────────────────────────────┐
│              DATA LAYER                         │
│  PostgreSQL (conversations, context, feedback)  │
│  Qdrant (conversation embeddings)               │
└────────────────────────────────────────────────┘
```

---

## Task 1: Context Builder

**Create:** `backend/app/services/context_builder.py`

```python
from sqlalchemy.orm import Session
from app.models.graph import GraphNode, GraphEdge
from app.services.cross_file_search import CrossFileSearch

class ContextBuilder:
    """Builds context for agent responses from workspace state."""
    
    def __init__(self, db: Session, search: CrossFileSearch):
        self._db = db
        self._search = search
    
    async def build_context(
        self, user_message: str, repo_id: int | None = None
    ) -> dict:
        """Build context for a user message."""
        # Search for relevant code
        code_results = await self._search.search(user_message, repo_id, max_results=5)
        
        # Get recent conversation context
        recent = await self._get_recent_conversations(limit=5)
        
        # Get workspace state
        workspace = self._get_workspace_state(repo_id)
        
        return {
            "relevant_code": code_results,
            "recent_conversations": recent,
            "workspace_state": workspace,
            "user_message": user_message,
        }
    
    def _get_workspace_state(self, repo_id: int | None) -> dict:
        """Get current workspace state."""
        if repo_id:
            nodes = self._db.query(GraphNode).filter(
                GraphNode.entry.has(repo_id=repo_id)
            ).count()
            edges = self._db.query(GraphEdge).filter(
                GraphEdge.source.has(GraphNode.entry.has(repo_id=repo_id))
            ).count()
            return {"repo_id": repo_id, "nodes": nodes, "edges": edges}
        return {"total_nodes": self._db.query(GraphNode).count()}
    
    async def _get_recent_conversations(self, limit: int) -> list[dict]:
        """Get recent conversation history."""
        from app.models.agent import AgentRun
        runs = self._db.query(AgentRun).order_by(
            AgentRun.created_at.desc()
        ).limit(limit).all()
        return [{"input": r.input, "output": r.output} for r in runs]
```

---

## Task 2: Conversation Memory

**Create:** `backend/app/services/conversation_memory.py`

```python
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.agent import AgentRun
from app.services.embedding_service import EmbeddingService
from app.core.vector_db import VectorDB

class ConversationMemory:
    """Stores and retrieves conversation history with semantic search."""
    
    def __init__(self, db: Session, embedding: EmbeddingService, vector_db: VectorDB):
        self._db = db
        self._embedding = embedding
        self._vector_db = vector_db
    
    async def store_conversation(self, run: AgentRun):
        """Store a conversation for future retrieval."""
        # Embed the conversation
        text = f"User: {run.input}\nAssistant: {run.output}"
        embedding = (await self._embedding.embed_batch([text]))[0]
        
        # Store in Qdrant
        await self._vector_db.upsert([{
            "id": f"conv:{run.id}",
            "vector": embedding,
            "payload": {
                "run_id": run.id,
                "user_id": run.user_id,
                "input": run.input,
                "output": run.output,
                "created_at": run.created_at.isoformat(),
            }
        }])
    
    async def search_conversations(
        self, query: str, user_id: int, max_results: int = 5
    ) -> list[dict]:
        """Search conversation history semantically."""
        embedding = (await self._embedding.embed_batch([query]))[0]
        
        results = await self._vector_db.search(embedding, max_results=max_results)
        
        return [
            {
                "score": r["score"],
                "input": r["payload"]["input"],
                "output": r["payload"]["output"],
                "created_at": r["payload"]["created_at"],
            }
            for r in results
            if r["payload"].get("user_id") == user_id
        ]
```

---

## Task 3: Learning Loop

**Create:** `backend/app/services/learning_loop.py`

```python
from sqlalchemy.orm import Session
from app.models.agent import AgentFeedback, AgentRun
from app.services.conversation_memory import ConversationMemory

class LearningLoop:
    """Learns from feedback to improve agent responses."""
    
    def __init__(self, db: Session, memory: ConversationMemory):
        self._db = db
        self._memory = memory
    
    async def process_feedback(self, run_id: int, rating: int, comment: str | None):
        """Process feedback and update learning."""
        run = self._db.query(AgentRun).get(run_id)
        if not run:
            return
        
        # Store the conversation for learning
        await self._memory.store_conversation(run)
        
        # If low rating, create a learning example
        if rating <= 2:
            await self._create_learning_example(run, rating, comment)
    
    async def _create_learning_example(self, run: AgentRun, rating: int, comment: str | None):
        """Create a learning example from negative feedback."""
        # Store as a negative example for future improvement
        # This can be used to fine-tune prompts or adjust agent behavior
        pass  # Implementation depends on specific learning strategy
    
    async def get_recent_feedback(self, limit: int = 10) -> list[dict]:
        """Get recent feedback for analysis."""
        feedback = self._db.query(AgentFeedback).order_by(
            AgentFeedback.created_at.desc()
        ).limit(limit).all()
        
        return [
            {
                "run_id": f.run_id,
                "rating": f.rating,
                "comment": f.comment,
                "created_at": f.created_at.isoformat(),
            }
            for f in feedback
        ]
```

---

## Task 4: Workspace Understanding

**Create:** `backend/app/services/workspace_understanding.py`

```python
from sqlalchemy.orm import Session
from app.models.graph import GraphNode, GraphEdge
from app.models.knowledge import KnowledgeEntry

class WorkspaceUnderstanding:
    """Understands the structure and relationships in the workspace."""
    
    def __init__(self, db: Session):
        self._db = db
    
    def get_workspace_summary(self, repo_id: int | None = None) -> dict:
        """Get a summary of the workspace."""
        query = self._db.query(GraphNode)
        if repo_id:
            query = query.filter(GraphNode.entry.has(repo_id=repo_id))
        
        nodes = query.all()
        
        # Group by type
        by_type = {}
        for node in nodes:
            by_type.setdefault(node.node_type, []).append(node.name)
        
        # Get key relationships
        key_edges = self._db.query(GraphEdge).filter(
            GraphEdge.edge_type.in_(["calls", "inherits", "imports"])
        ).all()
        
        relationships = {}
        for edge in key_edges:
            source = self._db.query(GraphNode).get(edge.source_id)
            target = self._db.query(GraphNode).get(edge.target_id)
            if source and target:
                relationships.setdefault(edge.edge_type, []).append({
                    "from": source.name,
                    "to": target.name,
                })
        
        return {
            "total_nodes": len(nodes),
            "by_type": {k: len(v) for k, v in by_type.items()},
            "key_relationships": relationships,
        }
    
    def get_file_imports(self, file_path: str) -> list[str]:
        """Get all imports for a file."""
        nodes = self._db.query(GraphNode).filter_by(
            file_path=file_path, node_type="import"
        ).all()
        return [n.name for n in nodes]
    
    def get_call_graph(self, function_name: str, depth: int = 2) -> dict:
        """Get the call graph for a function."""
        node = self._db.query(GraphNode).filter_by(
            name=function_name, node_type="function"
        ).first()
        
        if not node:
            return {}
        
        return self._traverse_calls(node, depth, set())
    
    def _traverse_calls(self, node: GraphNode, depth: int, visited: set) -> dict:
        if depth == 0 or node.id in visited:
            return {"name": node.name, "calls": []}
        
        visited.add(node.id)
        edges = self._db.query(GraphEdge).filter_by(
            source_id=node.id, edge_type="calls"
        ).all()
        
        calls = []
        for edge in edges:
            target = self._db.query(GraphNode).get(edge.target_id)
            if target:
                calls.append(self._traverse_calls(target, depth - 1, visited))
        
        return {"name": node.name, "calls": calls}
```

---

## Task 5: Enhanced Agent with Context

**Update:** `backend/app/agents/executor.py`

Add context building to executor:

```python
class ExecutorAgent(BaseAgent):
    def __init__(self, llm, search, context_builder, conversation_memory):
        super().__init__(llm)
        self.search = search
        self.context_builder = context_builder
        self.conversation_memory = conversation_memory
    
    async def execute(self, task: str, context: dict | None = None) -> str:
        # Build rich context
        rich_context = await self.context_builder.build_context(task)
        
        # Search for relevant past conversations
        past_conversations = await self.conversation_memory.search_conversations(
            task, user_id=context.get("user_id") if context else None
        )
        
        # Include past conversations in context
        if past_conversations:
            rich_context["past_conversations"] = past_conversations[:3]
        
        # Continue with existing execution logic...
```

---

## Task 6: Conversation History API

**Create:** `backend/app/api/v1/conversations.py`

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.conversation_memory import ConversationMemory

router = APIRouter(prefix="/api/v1/conversations", tags=["conversations"])

@router.get("/history")
async def get_history(
    query: str | None = None,
    limit: int = 20,
    db: Session = Depends(get_db),
):
    memory = ConversationMemory(db, ...)
    if query:
        return await memory.search_conversations(query, current_user_id, limit)
    # Return recent conversations
    from app.models.agent import AgentRun
    runs = db.query(AgentRun).filter_by(user_id=current_user_id).order_by(
        AgentRun.created_at.desc()
    ).limit(limit).all()
    return [{"input": r.input, "output": r.output, "created_at": r.created_at} for r in runs]

@router.get("/timeline")
async def get_timeline(db: Session = Depends(get_db)):
    """Get conversation timeline for UI."""
    from app.models.agent import AgentRun
    runs = db.query(AgentRun).filter_by(user_id=current_user_id).order_by(
        AgentRun.created_at.desc()
    ).limit(50).all()
    return [
        {
            "id": r.id,
            "input": r.input,
            "output": r.output,
            "created_at": r.created_at.isoformat(),
            "status": r.status,
        }
        for r in runs
    ]
```

---

## Task 7: Frontend Components

### 7.1 ContextPanel Component

**Create:** `frontend/components/agent/ContextPanel.tsx`

```typescript
"use client";
import { useEffect, useState } from "react";

interface ContextPanelProps {
  agentRunId: number;
}

export function ContextPanel({ agentRunId }: ContextPanelProps) {
  const [context, setContext] = useState<any>(null);
  
  useEffect(() => {
    fetch(`/api/v1/agents/runs/${agentRunId}/context`)
      .then(r => r.json())
      .then(setContext);
  }, [agentRunId]);
  
  if (!context) return null;
  
  return (
    <div className="p-4 space-y-4">
      <h3 className="text-lg font-semibold text-cortex-text-primary">Context</h3>
      
      {context.relevant_code?.length > 0 && (
        <div>
          <h4 className="text-sm font-medium text-cortex-text-secondary mb-2">Relevant Code</h4>
          <div className="space-y-2">
            {context.relevant_code.map((r: any, i: number) => (
              <div key={i} className="p-2 rounded bg-cortex-bg-secondary text-sm">
                <p className="font-mono text-cortex-accent">{r.name}</p>
                <p className="text-cortex-text-muted text-xs">{r.file_path}</p>
              </div>
            ))}
          </div>
        </div>
      )}
      
      {context.past_conversations?.length > 0 && (
        <div>
          <h4 className="text-sm font-medium text-cortex-text-secondary mb-2">Past Conversations</h4>
          <div className="space-y-2">
            {context.past_conversations.map((c: any, i: number) => (
              <div key={i} className="p-2 rounded bg-cortex-bg-secondary text-sm">
                <p className="text-cortex-text-primary">{c.input}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
```

### 7.2 MemoryTimeline Component

**Create:** `frontend/components/memory/MemoryTimeline.tsx`

```typescript
"use client";
import { useEffect, useState } from "react";

interface TimelineEntry {
  id: number;
  input: string;
  output: string;
  created_at: string;
  status: string;
}

export function MemoryTimeline() {
  const [entries, setEntries] = useState<TimelineEntry[]>([]);
  
  useEffect(() => {
    fetch("/api/v1/conversations/timeline")
      .then(r => r.json())
      .then(setEntries);
  }, []);
  
  return (
    <div className="space-y-3">
      {entries.map((entry) => (
        <div key={entry.id} className="p-3 rounded-lg bg-cortex-bg-secondary border border-cortex-border">
          <div className="flex items-center gap-2 mb-2">
            <span className={`px-2 py-0.5 rounded text-xs ${
              entry.status === "completed" ? "bg-green-500/20 text-green-400" : "bg-yellow-500/20 text-yellow-400"
            }`}>
              {entry.status}
            </span>
            <span className="text-xs text-cortex-text-muted">
              {new Date(entry.created_at).toLocaleString()}
            </span>
          </div>
          <p className="text-sm text-cortex-text-primary line-clamp-2">{entry.input}</p>
        </div>
      ))}
    </div>
  );
}
```

---

## Verification Checklist

```bash
# Backend
PYTHONPATH=. pytest tests/test_context_builder.py -v
PYTHONPATH=. pytest tests/test_conversation_memory.py -v
PYTHONPATH=. pytest tests/test_learning_loop.py -v
PYTHONPATH=. pytest tests/test_workspace_understanding.py -v

# Frontend
cd frontend && npx tsc --noEmit
cd frontend && npx next lint
```

---

## Exit Criteria

- [ ] Context builder creates rich context from workspace state
- [ ] Conversation memory stores and retrieves conversations
- [ ] Learning loop processes feedback
- [ ] Workspace understanding provides meaningful summaries
- [ ] Enhanced executor uses context for better responses
- [ ] Conversation history API works
- [ ] ContextPanel displays relevant code and past conversations
- [ ] MemoryTimeline shows conversation history
- [ ] All tests pass
