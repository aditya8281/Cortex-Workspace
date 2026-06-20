# Phase 8: Learning Loop — Full Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Cortex learns from interactions. Pattern recognition, correction tracking, proactive suggestions, and long-term memory with decay.

**Architecture:** Long-term memory with reinforcement/decay, pattern recognizer for coding style, correction tracker, proactive assistant that suggests actions.

**Tech Stack:** Python 3.12+, SQLAlchemy 2.0, Qdrant, Next.js 15

---

## Task 1: Long-Term Memory Model & Service

**Files:**
- Create: `backend/app/models/long_term_memory.py`
- Create: `backend/app/services/long_term_memory.py`
- Create: `migrations/versions/o00000000015_add_long_term_memory.py`

### Step 1: Create LongTermMemory SQLAlchemy Model

**File:** `backend/app/models/long_term_memory.py`

```python
"""Long-term memory model — stores facts, preferences, patterns, corrections."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base


class LongTermMemory(Base):
    """Persistent user memory with confidence-based relevance and decay.

    memory_type values: fact, preference, pattern, correction
    confidence: 0.0–1.0 — increases on reinforcement, decays over time
    access_count: incremented each time the memory is retrieved
    """

    __tablename__ = "long_term_memories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    memory_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    context: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.5)
    embedding_id: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    access_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_accessed: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    __table_args__ = (
        Index("idx_ltm_user_type", "user_id", "memory_type"),
        Index("idx_ltm_confidence", "user_id", "confidence"),
    )
```

### Step 2: Create Alembic Migration

**File:** `migrations/versions/o00000000015_add_long_term_memory.py`

```python
"""Add long_term_memories table.

Revision ID: o00000000015
Revises: n00000000014
Create Date: 2026-06-20 16:00:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "o00000000015"
down_revision: str | None = "n00000000014"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "long_term_memories",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("memory_type", sa.String(32), nullable=False, index=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("context", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="0.5"),
        sa.Column("embedding_id", sa.String(128), nullable=True, index=True),
        sa.Column("access_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_accessed", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_ltm_user_type", "long_term_memories", ["user_id", "memory_type"])
    op.create_index("idx_ltm_confidence", "long_term_memories", ["user_id", "confidence"])


def downgrade() -> None:
    op.drop_index("idx_ltm_confidence", table_name="long_term_memories")
    op.drop_index("idx_ltm_user_type", table_name="long_term_memories")
    op.drop_table("long_term_memories")
```

### Step 3: Create LongTermMemoryService

**File:** `backend/app/services/long_term_memory.py`

```python
"""Long-term memory service — store, retrieve, reinforce, and decay memories."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.app.core.vector_db import VectorDB, get_vector_db
from backend.app.models.long_term_memory import LongTermMemory
from backend.app.services.embedding_service import EmbeddingService, get_embedding_service

logger = logging.getLogger(__name__)

COLLECTION = "cortex_ltm"

# Decay: confidence reduced by this factor per day since last_accessed
DECAY_RATE_PER_DAY = 0.01
# Minimum confidence before a memory is considered stale
MIN_CONFIDENCE = 0.05
# Reinforcement boost per access
REINFORCEMENT_BOOST = 0.05
# Maximum confidence cap
MAX_CONFIDENCE = 1.0


class LongTermMemoryService:
    """Manages long-term memories with semantic search and confidence decay."""

    def __init__(
        self,
        db: Session,
        vector_db: VectorDB | None = None,
        embedding_service: EmbeddingService | None = None,
    ):
        self._db = db
        self._vector_db = vector_db or get_vector_db()
        self._embedder = embedding_service or get_embedding_service()

    def store(
        self,
        user_id: int,
        content: str,
        memory_type: str,
        context: dict | None = None,
        confidence: float = 0.5,
    ) -> LongTermMemory:
        """Store a new long-term memory with vector embedding."""
        embedding_id = self._embedder.compute_embedding_id(f"{memory_type}:{content}")

        memory = LongTermMemory(
            user_id=user_id,
            memory_type=memory_type,
            content=content,
            context=context or {},
            confidence=confidence,
            embedding_id=embedding_id,
        )
        self._db.add(memory)
        self._db.commit()
        self._db.refresh(memory)

        vector = self._embedder.embed_single(content)
        self._vector_db.upsert(
            COLLECTION,
            [
                {
                    "id": embedding_id,
                    "vector": vector,
                    "payload": {
                        "memory_id": memory.id,
                        "user_id": user_id,
                        "memory_type": memory_type,
                    },
                }
            ],
        )
        logger.info("Stored LTM %d (type=%s, confidence=%.2f): %s", memory.id, memory_type, confidence, content[:80])
        return memory

    def retrieve(
        self,
        user_id: int,
        query: str,
        memory_type: str | None = None,
        limit: int = 10,
    ) -> list[dict]:
        """Semantic search over long-term memories, weighted by confidence."""
        query_vector = self._embedder.embed_single(query)

        filter_payload: dict[str, str | int] = {"user_id": user_id}
        if memory_type:
            filter_payload["memory_type"] = memory_type

        results = self._vector_db.search(
            COLLECTION,
            query_vector,
            limit=limit * 2,  # over-fetch to account for confidence weighting
            filter_payload=filter_payload,
        )

        memory_ids = [r["payload"].get("memory_id") for r in results if r.get("payload")]
        valid_ids = [mid for mid in memory_ids if mid is not None]
        if not valid_ids:
            return []

        memories = self._db.query(LongTermMemory).filter(LongTermMemory.id.in_(valid_ids)).all()
        memory_map = {m.id: m for m in memories}

        scored: list[dict] = []
        for r in results:
            mid = r.get("payload", {}).get("memory_id")
            if mid and mid in memory_map:
                m = memory_map[mid]
                # Combine vector similarity with confidence
                combined_score = r["score"] * m.confidence
                scored.append({
                    "memory_id": m.id,
                    "content": m.content,
                    "memory_type": m.memory_type,
                    "context": m.context,
                    "confidence": m.confidence,
                    "access_count": m.access_count,
                    "score": combined_score,
                    "created_at": m.created_at.isoformat() if m.created_at else None,
                })

        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:limit]

    def reinforce(self, memory_id: int) -> LongTermMemory | None:
        """Increase confidence and access count for a memory."""
        memory = self._db.query(LongTermMemory).filter(LongTermMemory.id == memory_id).first()
        if not memory:
            return None

        memory.confidence = min(MAX_CONFIDENCE, memory.confidence + REINFORCEMENT_BOOST)
        memory.access_count += 1
        memory.last_accessed = datetime.now(timezone.utc)
        self._db.commit()
        self._db.refresh(memory)
        logger.info("Reinforced LTM %d -> confidence=%.2f", memory_id, memory.confidence)
        return memory

    def decay(self, user_id: int | None = None) -> int:
        """Reduce confidence of unused memories based on time since last access.

        Returns the number of memories affected.
        """
        now = datetime.now(timezone.utc)
        query = self._db.query(LongTermMemory)
        if user_id is not None:
            query = query.filter(LongTermMemory.user_id == user_id)

        memories = query.all()
        affected = 0

        for m in memories:
            last = m.last_accessed or m.created_at
            if last is None:
                continue

            # Ensure timezone-aware for subtraction
            if last.tzinfo is None:
                last = last.replace(tzinfo=timezone.utc)

            days_since = (now - last).total_seconds() / 86400
            if days_since < 1:
                continue

            decay_amount = DECAY_RATE_PER_DAY * days_since
            new_confidence = max(0.0, m.confidence - decay_amount)

            if new_confidence != m.confidence:
                m.confidence = new_confidence
                affected += 1

        if affected:
            self._db.commit()
            logger.info("Decayed %d long-term memories", affected)

        return affected

    def get_facts(self, user_id: int, limit: int = 50) -> list[LongTermMemory]:
        """Retrieve stored facts for a user, ordered by confidence."""
        return (
            self._db.query(LongTermMemory)
            .filter(LongTermMemory.user_id == user_id, LongTermMemory.memory_type == "fact")
            .order_by(LongTermMemory.confidence.desc())
            .limit(limit)
            .all()
        )

    def get_preferences(self, user_id: int, limit: int = 50) -> list[LongTermMemory]:
        """Retrieve stored preferences for a user, ordered by confidence."""
        return (
            self._db.query(LongTermMemory)
            .filter(LongTermMemory.user_id == user_id, LongTermMemory.memory_type == "preference")
            .order_by(LongTermMemory.confidence.desc())
            .limit(limit)
            .all()
        )

    def get_by_type(
        self,
        user_id: int,
        memory_type: str,
        min_confidence: float = 0.0,
        limit: int = 50,
    ) -> list[LongTermMemory]:
        """Retrieve memories of a specific type above a confidence threshold."""
        return (
            self._db.query(LongTermMemory)
            .filter(
                LongTermMemory.user_id == user_id,
                LongTermMemory.memory_type == memory_type,
                LongTermMemory.confidence >= min_confidence,
            )
            .order_by(LongTermMemory.confidence.desc())
            .limit(limit)
            .all()
        )

    def delete(self, memory_id: int) -> bool:
        """Delete a long-term memory and its vector embedding."""
        memory = self._db.query(LongTermMemory).filter(LongTermMemory.id == memory_id).first()
        if not memory:
            return False

        if memory.embedding_id:
            self._vector_db.delete(COLLECTION, [memory.embedding_id])
        self._db.delete(memory)
        self._db.commit()
        logger.info("Deleted LTM %d", memory_id)
        return True
```

### Step 4: Verify Migration Applies

```bash
cd /home/adi/Desktop/Cortex-Workspace
alembic upgrade head
```

---

## Task 2: Pattern Recognizer

**Files:**
- Create: `backend/app/services/pattern_recognizer.py`

### Step 1: Implement Pattern Detection

**File:** `backend/app/services/pattern_recognizer.py`

```python
"""Pattern recognizer — detects coding style, frameworks, and workflow patterns from history."""

from __future__ import annotations

import logging
import re
from collections import Counter

from sqlalchemy.orm import Session

from backend.app.models.agent import AgentRun, AgentStep
from backend.app.models.long_term_memory import LongTermMemory
from backend.app.services.long_term_memory import LongTermMemoryService

logger = logging.getLogger(__name__)

# Framework keywords to detect in user messages
FRAMEWORK_KEYWORDS = [
    "react", "next.js", "nextjs", "vue", "nuxt", "svelte", "angular",
    "fastapi", "django", "flask", "express", "fastify", "nest",
    "tailwind", "shadcn", "prisma", "drizzle", "sqlalchemy",
    "pytest", "jest", "vitest", "cypress", "playwright",
    "docker", "kubernetes", "terraform", "aws", "gcp", "azure",
]

# Workflow sequence patterns (step action sequences)
WORKFLOW_SEQUENCES: list[tuple[list[str], str]] = [
    (["bash", "bash", "bash"], "test_commit_push"),
    (["file_edit", "bash"], "edit_then_test"),
    (["file_create", "bash"], "create_then_test"),
    (["code_analysis", "file_edit"], "analyze_then_fix"),
]


class PatternRecognizer:
    """Detects user patterns from agent conversation history."""

    def __init__(self, db: Session, ltm_service: LongTermMemoryService | None = None):
        self._db = db
        self._ltm = ltm_service or LongTermMemoryService(db)

    def analyze_and_store(self, user_id: int, run_limit: int = 20) -> list[LongTermMemory]:
        """Analyze recent agent runs for a user and store detected patterns.

        Returns newly created or updated pattern memories.
        """
        patterns: list[LongTermMemory] = []

        # Fetch recent completed runs for this user
        runs = (
            self._db.query(AgentRun)
            .filter(AgentRun.user_id == user_id, AgentRun.status == "completed")
            .order_by(AgentRun.created_at.desc())
            .limit(run_limit)
            .all()
        )

        if not runs:
            return patterns

        # Gather all steps and user inputs
        all_steps: list[AgentStep] = []
        user_inputs: list[str] = []
        for run in runs:
            user_inputs.append(run.input_text)
            steps = (
                self._db.query(AgentStep)
                .filter(AgentStep.run_id == run.id)
                .order_by(AgentStep.step_number)
                .all()
            )
            all_steps.extend(steps)

        # Detect coding style
        style = self._detect_coding_style(all_steps)
        if style:
            p = self._store_pattern(user_id, "coding_style", style)
            if p:
                patterns.append(p)

        # Detect preferred frameworks
        frameworks = self._detect_frameworks(user_inputs)
        if frameworks:
            p = self._store_pattern(user_id, "preferred_frameworks", frameworks)
            if p:
                patterns.append(p)

        # Detect workflow patterns
        workflows = self._detect_workflows(all_steps)
        if workflows:
            p = self._store_pattern(user_id, "workflow_pattern", workflows)
            if p:
                patterns.append(p)

        return patterns

    def _detect_coding_style(self, steps: list[AgentStep]) -> dict | None:
        """Analyze step outputs for naming conventions and indentation style."""
        code_snippets: list[str] = []

        for step in steps:
            if step.observation and len(step.observation) > 50:
                code_snippets.append(step.observation)
            if step.action_input_json:
                code_snippets.append(step.action_input_json)

        if not code_snippets:
            return None

        combined = "\n".join(code_snippets)

        # Naming convention detection
        camel_case_count = len(re.findall(r"\b[a-z][a-zA-Z0-9]*[A-Z][a-zA-Z0-9]*\b", combined))
        snake_case_count = len(re.findall(r"\b[a-z]+_[a-z]+[a-z_]*\b", combined))

        if camel_case_count + snake_case_count == 0:
            naming = "unknown"
        elif camel_case_count > snake_case_count * 2:
            naming = "camelCase"
        elif snake_case_count > camel_case_count * 2:
            naming = "snake_case"
        else:
            naming = "mixed"

        # Indentation detection
        indent_2 = len(re.findall(r"\n  \S", combined))
        indent_4 = len(re.findall(r"\n    \S", combined))
        indent_style = "2_spaces" if indent_2 > indent_4 * 2 else ("4_spaces" if indent_4 > indent_2 * 2 else "mixed")

        return {
            "naming_convention": naming,
            "indentation": indent_style,
            "camel_case_count": camel_case_count,
            "snake_case_count": snake_case_count,
            "samples_analyzed": len(code_snippets),
        }

    def _detect_frameworks(self, user_inputs: list[str]) -> dict | None:
        """Count framework mentions in user messages."""
        combined = " ".join(user_inputs).lower()
        counts: Counter[str] = Counter()

        for kw in FRAMEWORK_KEYWORDS:
            if kw in combined:
                counts[kw] += 1

        if not counts:
            return None

        top = counts.most_common(10)
        return {
            "frameworks": {k: v for k, v in top},
            "total_messages": len(user_inputs),
        }

    def _detect_workflows(self, steps: list[AgentStep]) -> dict | None:
        """Detect recurring step-action sequences (e.g., test→commit→push)."""
        if len(steps) < 3:
            return None

        actions = [s.action.lower() for s in steps]
        sequence_counts: Counter[str] = Counter()

        for pattern, name in WORKFLOW_SEQUENCES:
            for i in range(len(actions) - len(pattern) + 1):
                if actions[i : i + len(pattern)] == pattern:
                    sequence_counts[name] += 1

        if not sequence_counts:
            return None

        return {
            "detected_sequences": dict(sequence_counts),
            "total_steps": len(steps),
        }

    def _store_pattern(self, user_id: int, pattern_key: str, data: dict) -> LongTermMemory | None:
        """Store or update a pattern memory. Updates existing if found."""
        content = f"{pattern_key}: {json.dumps(data, sort_keys=True)}"

        # Check for existing pattern of this type
        existing = (
            self._db.query(LongTermMemory)
            .filter(
                LongTermMemory.user_id == user_id,
                LongTermMemory.memory_type == "pattern",
                LongTermMemory.content.startswith(f"{pattern_key}:"),
            )
            .first()
        )

        if existing:
            existing.content = content
            existing.context = data
            existing.confidence = min(1.0, existing.confidence + 0.1)
            self._db.commit()
            self._db.refresh(existing)
            logger.info("Updated pattern LTM %d for user %d: %s", existing.id, user_id, pattern_key)
            return existing

        memory = self._ltm.store(
            user_id=user_id,
            content=content,
            memory_type="pattern",
            context=data,
            confidence=0.6,
        )
        logger.info("Stored new pattern LTM %d for user %d: %s", memory.id, user_id, pattern_key)
        return memory


# json is needed by _store_pattern
import json  # noqa: E402
```

---

## Task 3: Correction Tracker

**Files:**
- Create: `backend/app/services/correction_tracker.py`

### Step 1: Implement Correction Detection and Storage

**File:** `backend/app/services/correction_tracker.py`

```python
"""Correction tracker — detects and stores user corrections, injects them into prompts."""

from __future__ import annotations

import logging
import re

from sqlalchemy.orm import Session

from backend.app.models.agent import AgentRun
from backend.app.models.long_term_memory import LongTermMemory
from backend.app.services.long_term_memory import LongTermMemoryService

logger = logging.getLogger(__name__)

# Keywords that signal a correction when following an agent response
CORRECTION_SIGNALS = re.compile(
    r"\b(no|wrong|actually|instead|correct|fix|not what i meant|that's incorrect|"
    r"i meant|i wanted|i asked for|not quite|try again|not this|change it)\b",
    re.IGNORECASE,
)

# Keywords that signal approval (not a correction)
APPROVAL_SIGNALS = re.compile(
    r"\b(thanks|thank you|perfect|great|awesome|exactly|spot on|nice|good|works|"
    r"excellent|that's it|you got it|well done)\b",
    re.IGNORECASE,
)


class CorrectionTracker:
    """Detects user corrections and injects correction context into agent prompts."""

    def __init__(self, db: Session, ltm_service: LongTermMemoryService | None = None):
        self._db = db
        self._ltm = ltm_service or LongTermMemoryService(db)

    def detect_and_record(self, user_id: int, run_id: int) -> LongTermMemory | None:
        """Check if the user's latest message is a correction of the prior agent response.

        A correction is detected when:
        1. There's a prior completed run for this user
        2. The current run's input contains correction signals
        3. The current run's input does NOT predominantly contain approval signals

        If a correction is detected, it's stored as a LongTermMemory entry.
        """
        # Get the current run
        current_run = self._db.query(AgentRun).filter(AgentRun.id == run_id).first()
        if not current_run:
            return None

        # Get the previous completed run
        prev_run = (
            self._db.query(AgentRun)
            .filter(
                AgentRun.user_id == user_id,
                AgentRun.status == "completed",
                AgentRun.id < run_id,
            )
            .order_by(AgentRun.created_at.desc())
            .first()
        )

        if not prev_run:
            return None

        user_message = current_run.input_text.strip()
        if not user_message:
            return None

        # Check for correction signals
        correction_matches = CORRECTION_SIGNALS.findall(user_message)
        approval_matches = APPROVAL_SIGNALS.findall(user_message)

        # Must have correction signals and not be predominantly approval
        if not correction_matches:
            return None

        if len(approval_matches) > len(correction_matches):
            return None

        # Extract the correction context
        correction_content = self._extract_correction(prev_run, current_run)

        # Store as correction memory
        memory = self._ltm.store(
            user_id=user_id,
            content=correction_content,
            memory_type="correction",
            context={
                "original_agent_output": (prev_run.output or "")[:500],
                "user_correction": user_message,
                "trigger_run_id": run_id,
                "original_run_id": prev_run.id,
                "correction_signals": correction_matches,
            },
            confidence=0.7,
        )

        logger.info(
            "Recorded correction LTM %d for user %d (run %d -> %d): %s",
            memory.id, user_id, prev_run.id, run_id, correction_content[:100],
        )
        return memory

    def _extract_correction(self, prev_run: AgentRun, current_run: AgentRun) -> str:
        """Build a human-readable correction string."""
        agent_output_preview = (prev_run.output or "")[:300]
        return (
            f"User corrected agent after this output:\n"
            f"Agent said: {agent_output_preview}\n"
            f"User said: {current_run.input_text}"
        )

    def get_corrections_for_prompt(
        self,
        user_id: int,
        limit: int = 5,
        min_confidence: float = 0.3,
    ) -> str:
        """Retrieve recent high-confidence corrections to inject into agent system prompt.

        Returns a formatted string suitable for inclusion in a system prompt,
        or empty string if no corrections exist.
        """
        corrections = self._ltm.get_by_type(
            user_id=user_id,
            memory_type="correction",
            min_confidence=min_confidence,
            limit=limit,
        )

        if not corrections:
            return ""

        lines = ["## User Corrections (avoid repeating these mistakes)"]
        for c in corrections:
            user_correction = c.context.get("user_correction", "")
            lines.append(f"- {user_correction}")
            # Reinforce the correction since it's being used
            self._ltm.reinforce(c.id)

        return "\n".join(lines)

    def get_all_corrections(
        self,
        user_id: int,
        limit: int = 50,
    ) -> list[dict]:
        """List all corrections for a user (for UI display)."""
        corrections = (
            self._db.query(LongTermMemory)
            .filter(
                LongTermMemory.user_id == user_id,
                LongTermMemory.memory_type == "correction",
            )
            .order_by(LongTermMemory.created_at.desc())
            .limit(limit)
            .all()
        )

        return [
            {
                "id": c.id,
                "content": c.content,
                "context": c.context,
                "confidence": c.confidence,
                "access_count": c.access_count,
                "created_at": c.created_at.isoformat() if c.created_at else None,
            }
            for c in corrections
        ]
```

---

## Task 4: Proactive Assistant API & UI

**Files:**
- Create: `backend/app/api/v1/proactive.py`
- Create: `frontend/src/shared/components/ProactiveSuggestions.tsx`
- Edit: `frontend/src/shared/auth/cortexApi.ts` (add API function)
- Edit: `frontend/src/shared/types.ts` (add types)
- Edit: `backend/app/api/router.py` (register router)
- Edit: `frontend/src/shared/layout/DashboardShell.tsx` (add widget)

### Step 1: Create Proactive Suggestions API

**File:** `backend/app/api/v1/proactive.py`

```python
"""Proactive suggestions API — workspace-aware action suggestions."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.app.core.db import get_current_user, get_db
from backend.app.models.user import User
from backend.app.services.long_term_memory import LongTermMemoryService
from backend.app.services.correction_tracker import CorrectionTracker
from backend.app.services.pattern_recognizer import PatternRecognizer

router = APIRouter()


class Suggestion(BaseModel):
    id: str
    category: str
    title: str
    description: str
    confidence: float
    action_label: str | None = None
    action_url: str | None = None


class ProactiveResponse(BaseModel):
    suggestions: list[Suggestion]
    patterns_detected: int
    corrections_learned: int


@router.get("/proactive/suggestions", response_model=ProactiveResponse)
def get_proactive_suggestions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate proactive suggestions based on user patterns and corrections."""
    ltm = LongTermMemoryService(db)
    tracker = CorrectionTracker(db, ltm)
    recognizer = PatternRecognizer(db, ltm)

    suggestions: list[Suggestion] = []

    # 1. Check for recent corrections — suggest avoiding repeated mistakes
    corrections = tracker.get_all_corrections(current_user.id, limit=5)
    if corrections:
        suggestions.append(
            Suggestion(
                id="correction_summary",
                category="learning",
                title=f"{len(corrections)} corrections learned",
                description="I've learned from your recent corrections. I'll avoid repeating these patterns.",
                confidence=0.9,
                action_label="View corrections",
                action_url="/memory?type=correction",
            )
        )

    # 2. Check detected patterns — suggest based on coding style
    patterns = ltm.get_by_type(current_user.id, "pattern", min_confidence=0.3, limit=10)
    for p in patterns:
        ctx = p.context or {}
        if p.content.startswith("coding_style:"):
            naming = ctx.get("naming_convention", "unknown")
            indent = ctx.get("indentation", "unknown")
            suggestions.append(
                Suggestion(
                    id=f"pattern_style_{p.id}",
                    category="style",
                    title=f"Coding style detected: {naming}, {indent}",
                    description=f"Based on your code, I detect {naming} naming with {indent} indentation.",
                    confidence=p.confidence,
                )
            )
        elif p.content.startswith("preferred_frameworks:"):
            fw = ctx.get("frameworks", {})
            top_fw = list(fw.keys())[:3]
            if top_fw:
                suggestions.append(
                    Suggestion(
                        id=f"pattern_fw_{p.id}",
                        category="tools",
                        title=f"Preferred frameworks: {', '.join(top_fw)}",
                        description=f"Based on your messages, you frequently use {', '.join(top_fw)}.",
                        confidence=p.confidence,
                    )
                )

    # 3. Suggest running pattern analysis if enough runs exist
    from backend.app.models.agent import AgentRun

    run_count = (
        db.query(AgentRun)
        .filter(AgentRun.user_id == current_user.id, AgentRun.status == "completed")
        .count()
    )

    if run_count >= 5 and not patterns:
        suggestions.append(
            Suggestion(
                id="suggest_analyze",
                category="learning",
                title="Analyze your coding patterns",
                description=f"You have {run_count} completed sessions. Let me analyze your coding style.",
                confidence=0.7,
                action_label="Analyze now",
                action_url="/settings/patterns",
            )
        )

    # 4. Low-confidence memories — suggest reinforcement
    low_conf = ltm.get_by_type(current_user.id, "fact", min_confidence=0.0, limit=100)
    stale = [m for m in low_conf if m.confidence < 0.2]
    if stale:
        suggestions.append(
            Suggestion(
                id="stale_memories",
                category="memory",
                title=f"{len(stale)} memories fading",
                description="Some stored facts have low confidence. Interact to reinforce them.",
                confidence=0.6,
                action_label="View memories",
                action_url="/memory",
            )
        )

    # Limit total suggestions
    suggestions = sorted(suggestions, key=lambda s: s.confidence, reverse=True)[:8]

    return ProactiveResponse(
        suggestions=suggestions,
        patterns_detected=len(patterns),
        corrections_learned=len(corrections),
    )
```

### Step 2: Register the Router

**Edit:** `backend/app/api/router.py`

```python
from fastapi import APIRouter

from backend.app.api.metrics import router as metrics_router
from backend.app.api.v1.agents import router as agents_router
from backend.app.api.v1.github import router as github_router
from backend.app.api.v1.health import router as health_router
from backend.app.api.v1.notifications import router as notifications_router
from backend.app.api.v1.proactive import router as proactive_router
from backend.app.api.v1.profile import router as profile_router
from backend.app.api.v1.repository import router as repository_router
from backend.app.api.v1.search import router as search_router
from backend.app.api.v1.system import router as system_router
from backend.app.api.v1.users import router as users_router
from backend.app.api.v1.vault import router as vault_router

api_router = APIRouter()

api_router.include_router(health_router, tags=["Health"])

api_router.include_router(users_router, tags=["Users"])

api_router.include_router(profile_router, prefix="/me/profile", tags=["Profile"])

api_router.include_router(github_router, prefix="/me/github", tags=["GitHub"])

api_router.include_router(vault_router, prefix="/me/vault", tags=["Vault"])

api_router.include_router(metrics_router, tags=["Metrics"])

api_router.include_router(notifications_router, prefix="/notifications", tags=["Notifications"])

api_router.include_router(system_router, tags=["System"])

api_router.include_router(search_router, tags=["Search"])

api_router.include_router(repository_router, tags=["Repository"])

api_router.include_router(agents_router, tags=["Agents"])

api_router.include_router(proactive_router, tags=["Proactive"])
```

### Step 3: Add TypeScript Types

**Edit:** `frontend/src/shared/types.ts` — append to end of file:

```typescript
// ── Proactive Suggestions ─────────────────────────────────────────

export interface ProactiveSuggestion {
  id: string;
  category: string;
  title: string;
  description: string;
  confidence: number;
  action_label?: string | null;
  action_url?: string | null;
}

export interface ProactiveSuggestionsResponse {
  suggestions: ProactiveSuggestion[];
  patterns_detected: number;
  corrections_learned: number;
}
```

### Step 4: Add API Client Function

**Edit:** `frontend/src/shared/auth/cortexApi.ts` — add after the last exported function:

```typescript
// ── Proactive Suggestions ────────────────────────────────────────

export async function apiGetProactiveSuggestions(): Promise<ProactiveSuggestionsResponse> {
  return apiFetch<ProactiveSuggestionsResponse>("/api/v1/proactive/suggestions");
}
```

Also add the type import at the top of `cortexApi.ts`:

```typescript
import type {
  // ... existing types ...
  ProactiveSuggestionsResponse,
} from "../types";
```

### Step 5: Create ProactiveSuggestions Component

**File:** `frontend/src/shared/components/ProactiveSuggestions.tsx`

```tsx
"use client";

import { useState, useEffect, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Lightbulb, Brain, AlertTriangle, Palette, X, RefreshCw } from "lucide-react";
import { apiGetProactiveSuggestions } from "../auth/cortexApi";
import type { ProactiveSuggestion } from "../types";
import { cn } from "../../lib/utils";

const CATEGORY_ICONS: Record<string, typeof Lightbulb> = {
  learning: Brain,
  style: Palette,
  tools: AlertTriangle,
  memory: Brain,
};

const CATEGORY_COLORS: Record<string, string> = {
  learning: "text-cyan-400",
  style: "text-violet-400",
  tools: "text-amber-400",
  memory: "text-rose-400",
};

interface ProactiveSuggestionsProps {
  className?: string;
}

export default function ProactiveSuggestions({ className }: ProactiveSuggestionsProps) {
  const [suggestions, setSuggestions] = useState<ProactiveSuggestion[]>([]);
  const [loading, setLoading] = useState(true);
  const [dismissed, setDismissed] = useState<Set<string>>(new Set());

  const fetchSuggestions = useCallback(async () => {
    setLoading(true);
    try {
      const data = await apiGetProactiveSuggestions();
      setSuggestions(data.suggestions);
    } catch {
      setSuggestions([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchSuggestions();
  }, [fetchSuggestions]);

  const dismiss = (id: string) => {
    setDismissed((prev) => new Set(prev).add(id));
  };

  const visible = suggestions.filter((s) => !dismissed.has(s.id));

  if (loading) {
    return (
      <div className={cn("rounded-xl border border-border-subtle bg-bg-elevated/50 p-4", className)}>
        <div className="flex items-center gap-2 text-text-muted text-sm">
          <RefreshCw className="h-4 w-4 animate-spin" />
          <span>Loading suggestions...</span>
        </div>
      </div>
    );
  }

  if (visible.length === 0) {
    return null;
  }

  return (
    <div className={cn("rounded-xl border border-border-subtle bg-bg-elevated/50 overflow-hidden", className)}>
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-border-subtle">
        <div className="flex items-center gap-2">
          <Lightbulb className="h-4 w-4 text-accent" />
          <span className="text-sm font-medium text-text">Suggestions</span>
        </div>
        <button
          onClick={fetchSuggestions}
          className="p-1 rounded-md hover:bg-bg-hover text-text-muted hover:text-text-secondary transition-colors"
          aria-label="Refresh suggestions"
        >
          <RefreshCw className="h-3.5 w-3.5" />
        </button>
      </div>

      {/* Suggestions list */}
      <div className="divide-y divide-border-subtle">
        <AnimatePresence mode="popLayout">
          {visible.map((s) => {
            const Icon = CATEGORY_ICONS[s.category] || Lightbulb;
            const colorClass = CATEGORY_COLORS[s.category] || "text-accent";
            return (
              <motion.div
                key={s.id}
                layout
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: "auto" }}
                exit={{ opacity: 0, height: 0 }}
                className="px-4 py-3 flex items-start gap-3 group"
              >
                <Icon className={cn("h-4 w-4 mt-0.5 shrink-0", colorClass)} />
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-text font-medium leading-tight">{s.title}</p>
                  <p className="text-xs text-text-muted mt-1 leading-relaxed">{s.description}</p>
                  {s.action_label && s.action_url && (
                    <a
                      href={s.action_url}
                      className="inline-block mt-2 text-xs font-medium text-accent hover:text-accent/80 transition-colors"
                    >
                      {s.action_label} &rarr;
                    </a>
                  )}
                </div>
                <button
                  onClick={() => dismiss(s.id)}
                  className="p-1 rounded-md opacity-0 group-hover:opacity-100 hover:bg-bg-hover text-text-muted hover:text-text-secondary transition-all"
                  aria-label="Dismiss suggestion"
                >
                  <X className="h-3 w-3" />
                </button>
              </motion.div>
            );
          })}
        </AnimatePresence>
      </div>
    </div>
  );
}
```

### Step 6: Integrate into DashboardShell

**Edit:** `frontend/src/shared/layout/DashboardShell.tsx`

Add import at the top (after existing imports):

```typescript
import ProactiveSuggestions from "../components/ProactiveSuggestions";
```

Add the widget inside the sidebar, after the Status Bar section and before the User Card section (around line 250 in the desktop sidebar). Insert before the `/* User Card */` comment:

```tsx
          {/* Proactive Suggestions */}
          <div className="px-3 pb-2">
            <ProactiveSuggestions />
          </div>
```

Also add the same widget inside the tablet sidebar, after its Status Bar section and before its User Card section (around line 415). Insert before the closing `</motion.aside>`:

```tsx
          {/* Proactive Suggestions */}
          <div className="px-3 pb-2">
            <ProactiveSuggestions />
          </div>
```

---

## Exit Criteria

- [ ] `LongTermMemory` model stores facts, preferences, patterns, corrections with confidence 0–1
- [ ] Migration `o00000000015` creates the `long_term_memories` table and applies cleanly
- [ ] `LongTermMemoryService` supports store, retrieve (semantic via Qdrant), reinforce, decay, get_facts, get_preferences
- [ ] `PatternRecognizer` detects coding style (naming, indentation), preferred frameworks, workflow sequences from AgentRun/AgentStep history
- [ ] `CorrectionTracker` detects "no/wrong/actually/instead" signals, records corrections, injects them into prompts
- [ ] `GET /proactive/suggestions` returns category-based suggestions
- [ ] `ProactiveSuggestions.tsx` renders sidebar widget with dismiss/refresh
- [ ] All code compiles and builds clean (`next build` passes, no Python import errors)
- [ ] Alembic migration runs without errors: `alembic upgrade head`
