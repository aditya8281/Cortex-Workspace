# Phase 6: System Understanding & Learning Loop

> **⚠️ SUPERSEDED:** This plan has been restructured. See `13-PHASE-8-LEARNING-LOOP.md` for the updated plan.

**Goal:** The system develops genuine understanding of your codebase and projects. Long-term memory, learning from corrections, pattern recognition, and proactive assistance.

**Depends on:** Phase 4 (intelligence), Phase 5 (desktop), Phase 2 (knowledge graph)

---

## Architecture

```
┌─────────────────────────────────────────────────┐
│                  FRONTEND                       │
│  MemoryTimeline ── LearningDashboard           │
│  PatternView ── ProactiveSuggestions            │
└──────────────┬──────────────────────────────────┘
               │
┌──────────────▼──────────────────────────────────┐
│                 API LAYER                       │
│  /api/v1/learning/     /api/v1/patterns/        │
│  /api/v1/proactive/    /api/v1/memory/longterm   │
└──────────────┬──────────────────────────────────┘
               │
┌──────────────▼──────────────────────────────────┐
│              SERVICES                           │
│  LearningLoop ── PatternRecognizer              │
│  LongTermMemory ── ProactiveAssistant          │
│  CorrectionTracker ── KnowledgeRefiner         │
└──────────────┬──────────────────────────────────┘
               │
┌──────────────▼──────────────────────────────────┐
│              DATA LAYER                         │
│  PostgreSQL (patterns, corrections, knowledge)  │
│  Qdrant (long-term memory embeddings)           │
│  ChromaDB (pattern embeddings)                  │
└────────────────────────────────────────────────┘
```

---

## Task 1: Long-Term Memory

### 1.1 Long-Term Memory Model

**Create:** `backend/app/models/long_term_memory.py`

```python
from sqlalchemy import Column, Integer, String, Text, JSON, DateTime, Float
from app.core.database import Base

class LongTermMemory(Base):
    __tablename__ = "long_term_memory"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False, index=True)
    memory_type = Column(String(50), nullable=False, index=True)  # fact, preference, pattern, correction
    content = Column(Text, nullable=False)
    context = Column(JSON, nullable=True)  # What triggered this memory
    confidence = Column(Float, default=0.5)  # 0-1, increases with reinforcement
    access_count = Column(Integer, default=0)
    last_accessed = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)
```

### 1.2 Long-Term Memory Service

**Create:** `backend/app/services/long_term_memory.py`

```python
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.long_term_memory import LongTermMemory
from app.services.embedding_service import EmbeddingService
from app.core.vector_db import VectorDB

class LongTermMemoryService:
    def __init__(self, db: Session, embedding: EmbeddingService, vector_db: VectorDB):
        self._db = db
        self._embedding = embedding
        self._vector_db = vector_db
    
    async def store(
        self, user_id: int, memory_type: str, content: str,
        context: dict | None = None, confidence: float = 0.5
    ):
        """Store a new long-term memory."""
        memory = LongTermMemory(
            user_id=user_id,
            memory_type=memory_type,
            content=content,
            context=context,
            confidence=confidence,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        self._db.add(memory)
        self._db.commit()
        self._db.refresh(memory)
        
        # Store embedding for semantic search
        embedding = (await self._embedding.embed_batch([content]))[0]
        await self._vector_db.upsert([{
            "id": f"ltm:{memory.id}",
            "vector": embedding,
            "payload": {
                "memory_id": memory.id,
                "user_id": user_id,
                "memory_type": memory_type,
                "content": content,
            }
        }])
        
        return memory
    
    async def retrieve(
        self, user_id: int, query: str, max_results: int = 5
    ) -> list[dict]:
        """Retrieve relevant long-term memories."""
        embedding = (await self._embedding.embed_batch([query]))[0]
        results = await self._vector_db.search(embedding, max_results=max_results)
        
        memories = []
        for r in results:
            if r["payload"].get("user_id") != user_id:
                continue
            
            memory = self._db.query(LongTermMemory).get(r["payload"]["memory_id"])
            if memory:
                memory.access_count += 1
                memory.last_accessed = datetime.utcnow()
                self._db.commit()
                
                memories.append({
                    "id": memory.id,
                    "type": memory.memory_type,
                    "content": memory.content,
                    "confidence": memory.confidence,
                    "score": r["score"],
                })
        
        return memories
    
    async def reinforce(self, memory_id: int, confidence_boost: float = 0.1):
        """Reinforce a memory (increase confidence)."""
        memory = self._db.query(LongTermMemory).get(memory_id)
        if memory:
            memory.confidence = min(1.0, memory.confidence + confidence_boost)
            memory.access_count += 1
            memory.updated_at = datetime.utcnow()
            self._db.commit()
    
    async def decay(self, user_id: int, decay_rate: float = 0.01):
        """Decay old memories (reduce confidence)."""
        from datetime import timedelta
        cutoff = datetime.utcnow() - timedelta(days=30)
        
        memories = self._db.query(LongTermMemory).filter(
            LongTermMemory.user_id == user_id,
            LongTermMemory.last_accessed < cutoff
        ).all()
        
        for memory in memories:
            memory.confidence = max(0.1, memory.confidence - decay_rate)
            self._db.commit()
```

---

## Task 2: Pattern Recognition

### 2.1 Pattern Model

**Create:** `backend/app/models/pattern.py`

```python
from sqlalchemy import Column, Integer, String, Text, JSON, DateTime, Float
from app.core.database import Base

class Pattern(Base):
    __tablename__ = "patterns"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False, index=True)
    pattern_type = Column(String(50), nullable=False, index=True)  # coding_style, naming, architecture, workflow
    description = Column(Text, nullable=False)
    examples = Column(JSON, nullable=True)  # List of example occurrences
    frequency = Column(Integer, default=1)
    confidence = Column(Float, default=0.5)
    created_at = Column(DateTime, nullable=False)
    last_seen = Column(DateTime, nullable=False)
```

### 2.2 Pattern Recognizer Service

**Create:** `backend/app/services/pattern_recognizer.py`

```python
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.pattern import Pattern
from app.models.agent import AgentRun

class PatternRecognizer:
    def __init__(self, db: Session):
        self._db = db
    
    async def analyze_conversations(self, user_id: int):
        """Analyze recent conversations to identify patterns."""
        runs = self._db.query(AgentRun).filter_by(
            user_id=user_id, status="completed"
        ).order_by(AgentRun.created_at.desc()).limit(100).all()
        
        patterns = []
        
        # Detect coding style patterns
        code_runs = [r for r in runs if "code" in r.input.lower() or "write" in r.input.lower()]
        if len(code_runs) > 5:
            style_pattern = self._detect_coding_style(code_runs)
            if style_pattern:
                patterns.append(style_pattern)
        
        # Detect workflow patterns
        workflow_runs = [r for r in runs if "fix" in r.input.lower() or "debug" in r.input.lower()]
        if len(workflow_runs) > 3:
            workflow_pattern = self._detect_workflow_pattern(workflow_runs)
            if workflow_pattern:
                patterns.append(workflow_pattern)
        
        # Store new patterns
        for pattern_data in patterns:
            existing = self._db.query(Pattern).filter_by(
                user_id=user_id,
                pattern_type=pattern_data["type"],
                description=pattern_data["description"]
            ).first()
            
            if existing:
                existing.frequency += 1
                existing.confidence = min(1.0, existing.confidence + 0.1)
                existing.last_seen = datetime.utcnow()
            else:
                self._db.add(Pattern(
                    user_id=user_id,
                    pattern_type=pattern_data["type"],
                    description=pattern_data["description"],
                    examples=pattern_data.get("examples", []),
                    confidence=0.5,
                    created_at=datetime.utcnow(),
                    last_seen=datetime.utcnow(),
                ))
        
        self._db.commit()
    
    def _detect_coding_style(self, runs: list) -> dict | None:
        """Detect coding style from conversation history."""
        # Analyze input patterns
        inputs = [r.input for r in runs]
        
        # Check for consistent naming conventions
        # Check for consistent code structure preferences
        # Check for preferred libraries/frameworks
        
        return {
            "type": "coding_style",
            "description": "User prefers functional programming style",
            "examples": inputs[:3],
        }
    
    def _detect_workflow_pattern(self, runs: list) -> dict | None:
        """Detect workflow patterns."""
        # Analyze fix/debug patterns
        # Check for test-first vs code-first
        # Check for commit patterns
        
        return {
            "type": "workflow",
            "description": "User typically writes tests after implementation",
            "examples": [r.input for r in runs[:3]],
        }
    
    async def get_patterns(self, user_id: int) -> list[dict]:
        """Get all patterns for a user."""
        patterns = self._db.query(Pattern).filter_by(user_id=user_id).all()
        return [
            {
                "id": p.id,
                "type": p.pattern_type,
                "description": p.description,
                "frequency": p.frequency,
                "confidence": p.confidence,
            }
            for p in patterns
        ]
```

---

## Task 3: Correction Tracker

### 3.1 Correction Model

**Create:** `backend/app/models/correction.py`

```python
from sqlalchemy import Column, Integer, String, Text, JSON, DateTime
from app.core.database import Base

class Correction(Base):
    __tablename__ = "corrections"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False, index=True)
    original_output = Column(Text, nullable=False)
    corrected_output = Column(Text, nullable=False)
    context = Column(JSON, nullable=True)  # What the user asked
    applied = Column(Integer, default=0)  # How many times this correction was applied
    created_at = Column(DateTime, nullable=False)
```

### 3.2 Correction Tracker Service

**Create:** `backend/app/services/correction_tracker.py`

```python
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.correction import Correction

class CorrectionTracker:
    def __init__(self, db: Session):
        self._db = db
    
    async def record_correction(
        self, user_id: int, original: str, corrected: str,
        context: dict | None = None
    ):
        """Record when a user corrects agent output."""
        correction = Correction(
            user_id=user_id,
            original_output=original,
            corrected_output=corrected,
            context=context,
            created_at=datetime.utcnow(),
        )
        self._db.add(correction)
        self._db.commit()
        return correction
    
    async def get_corrections(self, user_id: int, limit: int = 20) -> list[dict]:
        """Get recent corrections."""
        corrections = self._db.query(Correction).filter_by(
            user_id=user_id
        ).order_by(Correction.created_at.desc()).limit(limit).all()
        
        return [
            {
                "id": c.id,
                "original": c.original_output,
                "corrected": c.corrected_output,
                "context": c.context,
                "applied": c.applied,
            }
            for c in corrections
        ]
    
    async def apply_corrections(self, output: str, user_id: int) -> str:
        """Apply learned corrections to new output."""
        corrections = self._db.query(Correction).filter_by(
            user_id=user_id
        ).all()
        
        corrected = output
        for correction in corrections:
            if correction.original_output in corrected:
                corrected = corrected.replace(
                    correction.original_output,
                    correction.corrected_output
                )
                correction.applied += 1
                self._db.commit()
        
        return corrected
```

---

## Task 4: Proactive Assistant

### 4.1 Proactive Suggestion Model

**Create:** `backend/app/models/proactive.py`

```python
from sqlalchemy import Column, Integer, String, Text, JSON, DateTime, Boolean
from app.core.database import Base

class ProactiveSuggestion(Base):
    __tablename__ = "proactive_suggestions"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False, index=True)
    suggestion_type = Column(String(50), nullable=False)  # code_review, optimization, test, documentation
    content = Column(Text, nullable=False)
    context = Column(JSON, nullable=True)
    accepted = Column(Boolean, nullable=True)  # null = pending, true = accepted, false = dismissed
    created_at = Column(DateTime, nullable=False)
```

### 4.2 Proactive Assistant Service

**Create:** `backend/app/services/proactive_assistant.py`

```python
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.proactive import ProactiveSuggestion
from app.models.graph import GraphNode, GraphEdge

class ProactiveAssistant:
    def __init__(self, db: Session):
        self._db = db
    
    async def analyze_for_suggestions(self, user_id: int, repo_id: int | None = None):
        """Analyze workspace and suggest improvements."""
        suggestions = []
        
        # Check for functions without tests
        untested = self._find_untested_functions(repo_id)
        if untested:
            suggestions.append(ProactiveSuggestion(
                user_id=user_id,
                suggestion_type="test",
                content=f"Found {len(untested)} functions without tests",
                context={"functions": untested[:5]},
                created_at=datetime.utcnow(),
            ))
        
        # Check for long functions (complexity)
        complex_funcs = self._find_complex_functions(repo_id)
        if complex_funcs:
            suggestions.append(ProactiveSuggestion(
                user_id=user_id,
                suggestion_type="optimization",
                content=f"Found {len(complex_funcs)} complex functions that could be refactored",
                context={"functions": complex_funcs[:5]},
                created_at=datetime.utcnow(),
            ))
        
        # Check for missing documentation
        undocumented = self._find_undocumented_functions(repo_id)
        if undocumented:
            suggestions.append(ProactiveSuggestion(
                user_id=user_id,
                suggestion_type="documentation",
                content=f"Found {len(undocumented)} functions without documentation",
                context={"functions": undocumented[:5]},
                created_at=datetime.utcnow(),
            ))
        
        self._db.add_all(suggestions)
        self._db.commit()
        return suggestions
    
    def _find_untested_functions(self, repo_id: int | None) -> list[dict]:
        """Find functions that don't have corresponding tests."""
        query = self._db.query(GraphNode).filter_by(node_type="function")
        if repo_id:
            query = query.filter(GraphNode.entry.has(repo_id=repo_id))
        
        functions = query.all()
        untested = []
        
        for func in functions:
            # Check if there's a test file that imports or references this function
            has_test = self._db.query(GraphEdge).filter(
                GraphEdge.target_id == func.id,
                GraphEdge.edge_type == "references",
                GraphEdge.source.has(GraphNode.file_path.like("%test%"))
            ).first()
            
            if not has_test:
                untested.append({
                    "name": func.name,
                    "file": func.file_path,
                    "line": func.start_line,
                })
        
        return untested
    
    def _find_complex_functions(self, repo_id: int | None) -> list[dict]:
        """Find functions with high complexity."""
        query = self._db.query(GraphNode).filter_by(node_type="function")
        if repo_id:
            query = query.filter(GraphNode.entry.has(repo_id=repo_id))
        
        functions = query.all()
        complex_funcs = []
        
        for func in functions:
            # Simple heuristic: check line count
            if func.end_line and func.start_line:
                line_count = func.end_line - func.start_line
                if line_count > 50:  # Functions over 50 lines
                    complex_funcs.append({
                        "name": func.name,
                        "file": func.file_path,
                        "lines": line_count,
                    })
        
        return sorted(complex_funcs, key=lambda x: x["lines"], reverse=True)
    
    def _find_undocumented_functions(self, repo_id: int | None) -> list[dict]:
        """Find functions without docstrings."""
        query = self._db.query(GraphNode).filter_by(node_type="function")
        if repo_id:
            query = query.filter(GraphNode.entry.has(repo_id=repo_id))
        
        functions = query.all()
        undocumented = []
        
        for func in functions:
            # Check if there's a docstring node as first child
            has_doc = self._db.query(GraphEdge).filter(
                GraphEdge.source_id == func.id,
                GraphEdge.edge_type == "contains",
                GraphEdge.target.has(node_type="docstring")
            ).first()
            
            if not has_doc:
                undocumented.append({
                    "name": func.name,
                    "file": func.file_path,
                    "line": func.start_line,
                })
        
        return undocumented
    
    async def get_suggestions(
        self, user_id: int, suggestion_type: str | None = None,
        pending_only: bool = True
    ) -> list[dict]:
        """Get suggestions for a user."""
        query = self._db.query(ProactiveSuggestion).filter_by(user_id=user_id)
        
        if suggestion_type:
            query = query.filter_by(suggestion_type=suggestion_type)
        
        if pending_only:
            query = query.filter_by(accepted=None)
        
        suggestions = query.order_by(
            ProactiveSuggestion.created_at.desc()
        ).limit(20).all()
        
        return [
            {
                "id": s.id,
                "type": s.suggestion_type,
                "content": s.content,
                "context": s.context,
                "created_at": s.created_at.isoformat(),
            }
            for s in suggestions
        ]
    
    async def accept_suggestion(self, suggestion_id: int, accepted: bool):
        """Mark a suggestion as accepted or dismissed."""
        suggestion = self._db.query(ProactiveSuggestion).get(suggestion_id)
        if suggestion:
            suggestion.accepted = accepted
            self._db.commit()
```

---

## Task 5: Learning API

**Create:** `backend/app/api/v1/learning.py`

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.long_term_memory import LongTermMemoryService
from app.services.pattern_recognizer import PatternRecognizer
from app.services.correction_tracker import CorrectionTracker
from app.services.proactive_assistant import ProactiveAssistant

router = APIRouter(prefix="/api/v1/learning", tags=["learning"])

@router.get("/patterns")
async def get_patterns(db: Session = Depends(get_db)):
    recognizer = PatternRecognizer(db)
    return await recognizer.get_patterns(current_user_id)

@router.post("/patterns/analyze")
async def analyze_patterns(db: Session = Depends(get_db)):
    recognizer = PatternRecognizer(db)
    await recognizer.analyze_conversations(current_user_id)
    return {"status": "ok"}

@router.get("/corrections")
async def get_corrections(limit: int = 20, db: Session = Depends(get_db)):
    tracker = CorrectionTracker(db)
    return await tracker.get_corrections(current_user_id, limit)

@router.post("/corrections")
async def record_correction(original: str, corrected: str, db: Session = Depends(get_db)):
    tracker = CorrectionTracker(db)
    return await tracker.record_correction(current_user_id, original, corrected)

@router.get("/suggestions")
async def get_suggestions(type: str | None = None, db: Session = Depends(get_db)):
    assistant = ProactiveAssistant(db)
    return await assistant.get_suggestions(current_user_id, type)

@router.post("/suggestions/analyze")
async def analyze_suggestions(db: Session = Depends(get_db)):
    assistant = ProactiveAssistant(db)
    return await assistant.analyze_for_suggestions(current_user_id)

@router.post("/suggestions/{suggestion_id}/accept")
async def accept_suggestion(suggestion_id: int, accepted: bool, db: Session = Depends(get_db)):
    assistant = ProactiveAssistant(db)
    await assistant.accept_suggestion(suggestion_id, accepted)
    return {"status": "ok"}

@router.get("/longterm")
async def get_longterm_memories(query: str, db: Session = Depends(get_db)):
    ltm = LongTermMemoryService(db, ...)
    return await ltm.retrieve(current_user_id, query)

@router.post("/longterm")
async def store_longterm_memory(content: str, type: str, db: Session = Depends(get_db)):
    ltm = LongTermMemoryService(db, ...)
    return await ltm.store(current_user_id, type, content)
```

---

## Task 6: Frontend Components

### 6.1 LearningDashboard Component

**Create:** `frontend/components/learning/LearningDashboard.tsx`

```typescript
"use client";
import { useEffect, useState } from "react";

interface Pattern {
  id: number;
  type: string;
  description: string;
  frequency: number;
  confidence: number;
}

export function LearningDashboard() {
  const [patterns, setPatterns] = useState<Pattern[]>([]);
  const [corrections, setCorrections] = useState<any[]>([]);
  
  useEffect(() => {
    fetch("/api/v1/learning/patterns").then(r => r.json()).then(setPatterns);
    fetch("/api/v1/learning/corrections").then(r => r.json()).then(setCorrections);
  }, []);
  
  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-cortex-text-primary">Learning Dashboard</h2>
      
      <div>
        <h3 className="text-lg font-semibold text-cortex-text-secondary mb-3">Detected Patterns</h3>
        <div className="space-y-2">
          {patterns.map(p => (
            <div key={p.id} className="p-3 rounded-lg bg-cortex-bg-secondary border border-cortex-border">
              <div className="flex items-center gap-2">
                <span className="px-2 py-0.5 rounded text-xs bg-cortex-accent/20 text-cortex-accent">
                  {p.type}
                </span>
                <span className="text-sm text-cortex-text-muted">
                  Seen {p.frequency} times ({(p.confidence * 100).toFixed(0)}% confident)
                </span>
              </div>
              <p className="mt-2 text-sm text-cortex-text-primary">{p.description}</p>
            </div>
          ))}
        </div>
      </div>
      
      <div>
        <h3 className="text-lg font-semibold text-cortex-text-secondary mb-3">Recent Corrections</h3>
        <div className="space-y-2">
          {corrections.map(c => (
            <div key={c.id} className="p-3 rounded-lg bg-cortex-bg-secondary border border-cortex-border">
              <p className="text-xs text-cortex-text-muted">Original:</p>
              <p className="text-sm text-red-400 line-through">{c.original}</p>
              <p className="text-xs text-cortex-text-muted mt-2">Corrected:</p>
              <p className="text-sm text-green-400">{c.corrected}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
```

### 6.2 ProactiveSuggestions Component

**Create:** `frontend/components/learning/ProactiveSuggestions.tsx`

```typescript
"use client";
import { useEffect, useState } from "react";

interface Suggestion {
  id: number;
  type: string;
  content: string;
  context: any;
}

export function ProactiveSuggestions() {
  const [suggestions, setSuggestions] = useState<Suggestion[]>([]);
  
  useEffect(() => {
    fetch("/api/v1/learning/suggestions").then(r => r.json()).then(setSuggestions);
  }, []);
  
  const handleAccept = async (id: number, accepted: boolean) => {
    await fetch(`/api/v1/learning/suggestions/${id}/accept?accepted=${accepted}`, {
      method: "POST",
    });
    setSuggestions(suggestions.filter(s => s.id !== id));
  };
  
  if (suggestions.length === 0) return null;
  
  return (
    <div className="space-y-3">
      <h3 className="text-lg font-semibold text-cortex-text-primary">Suggestions</h3>
      {suggestions.map(s => (
        <div key={s.id} className="p-3 rounded-lg bg-cortex-bg-secondary border border-cortex-border">
          <div className="flex items-center gap-2 mb-2">
            <span className={`px-2 py-0.5 rounded text-xs ${
              s.type === "test" ? "bg-yellow-500/20 text-yellow-400" :
              s.type === "optimization" ? "bg-blue-500/20 text-blue-400" :
              "bg-green-500/20 text-green-400"
            }`}>
              {s.type}
            </span>
          </div>
          <p className="text-sm text-cortex-text-primary">{s.content}</p>
          <div className="flex gap-2 mt-3">
            <button
              onClick={() => handleAccept(s.id, true)}
              className="px-3 py-1 rounded bg-cortex-accent text-white text-sm"
            >
              Apply
            </button>
            <button
              onClick={() => handleAccept(s.id, false)}
              className="px-3 py-1 rounded bg-cortex-bg-primary text-cortex-text-secondary text-sm"
            >
              Dismiss
            </button>
          </div>
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
PYTHONPATH=. pytest tests/test_long_term_memory.py -v
PYTHONPATH=. pytest tests/test_pattern_recognizer.py -v
PYTHONPATH=. pytest tests/test_correction_tracker.py -v
PYTHONPATH=. pytest tests/test_proactive_assistant.py -v

# Frontend
cd frontend && npx tsc --noEmit
cd frontend && npx next lint
```

---

## Exit Criteria

- [ ] Long-term memory stores and retrieves with semantic search
- [ ] Pattern recognizer identifies coding and workflow patterns
- [ ] Correction tracker records and applies corrections
- [ ] Proactive assistant suggests improvements
- [ ] Learning API endpoints functional
- [ ] LearningDashboard displays patterns and corrections
- [ ] ProactiveSuggestions component shows and handles suggestions
- [ ] All tests pass
