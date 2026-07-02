"""UserWorkspace — filesystem-based per-user data storage.

The central brain (Postgres) holds auth + pointers only.
ALL user-specific data lives in {storage_root}/ as JSON/JSONL files.

This service is the single point of entry for reading/writing user data.
Every other service (conversations, memory, agents) delegates here.

File layout:
    {storage_root}/
    ├── conversations/
    │   ├── index.json        # conversation metadata list
    │   └── {id}.jsonl        # append-only message log
    ├── memory/
    │   ├── long_term.json    # long-term memories
    │   └── summaries.json    # conversation summaries
    ├── agents/
    │   ├── config.json       # agent definitions
    │   └── runs/
    │       └── {id}.jsonl    # run history
    ├── knowledge/
    │   └── entries.json      # knowledge entries
    ├── vault/                # already exists
    └── workspace/            # already exists
"""

from __future__ import annotations

import json
import logging
import os
import tempfile
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class UserWorkspace:
    """Filesystem-based storage for all user-specific data.

    Usage:
        ws = UserWorkspace("/home/adi/CortexStorage/adi")
        ws.conversations.save_message(conv_id, "user", "hello")
        msgs = ws.conversations.get_messages(conv_id)
    """

    def __init__(self, storage_root: str | Path):
        self._root = Path(storage_root)
        self._conversations = ConversationStore(self._root / "conversations")
        self._memory = MemoryStore(self._root / "memory")
        self._agents = AgentStore(self._root / "agents")
        self._knowledge = KnowledgeStore(self._root / "knowledge")

    @property
    def root(self) -> Path:
        return self._root

    @property
    def conversations(self) -> ConversationStore:
        return self._conversations

    @property
    def memory(self) -> MemoryStore:
        return self._memory

    @property
    def agents(self) -> AgentStore:
        return self._agents

    @property
    def knowledge(self) -> KnowledgeStore:
        return self._knowledge

    def ensure_dirs(self) -> None:
        """Create all required directories if they don't exist."""
        for subdir in [
            "conversations", "memory", "agents/runs", "knowledge",
            "vault", "workspace", "profile", "exports",
        ]:
            (self._root / subdir).mkdir(parents=True, exist_ok=True)

    def disk_usage(self) -> dict[str, int]:
        """Return disk usage in bytes per subdirectory."""
        usage: dict[str, int] = {}
        if not self._root.exists():
            return usage
        for item in self._root.iterdir():
            if item.is_dir():
                total = sum(f.stat().st_size for f in item.rglob("*") if f.is_file())
                usage[item.name] = total
        return usage


# ── File locking ────────────────────────────────────────────────────

@contextmanager
def _file_lock(path: Path):
    """Simple file lock using fcntl. Prevents concurrent corruption."""
    import fcntl
    lock_path = path.with_suffix(path.suffix + ".lock")
    lock_path.touch(exist_ok=True)
    fd = open(lock_path, "r+")
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
        yield
    finally:
        fcntl.flock(fd, fcntl.LOCK_UN)
        fd.close()


def _atomic_write(path: Path, content: str) -> None:
    """Write to temp file then rename — prevents partial writes."""
    dir_path = path.parent
    dir_path.mkdir(parents=True, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(dir=dir_path, suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as f:
            f.write(content)
        os.replace(tmp_path, path)
    except Exception:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


def _read_json(path: Path, default: Any = None) -> Any:
    """Read a JSON file, returning default if missing/corrupt."""
    if not path.exists():
        return default if default is not None else []
    try:
        with open(path) as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError) as exc:
        logger.warning("Failed to read %s: %s — using default", path, exc)
        return default if default is not None else []


# ── Conversation Store ──────────────────────────────────────────────

class ConversationStore:
    """Filesystem-based conversation storage.

    index.json: [{id, title, created_at, updated_at, model_used, message_count, total_tokens}]
    {id}.jsonl: append-only lines of {role, content, thinking_content, tokens, timestamp}
    """

    def __init__(self, base_dir: Path):
        self._dir = base_dir
        self._dir.mkdir(parents=True, exist_ok=True)
        self._index_path = self._dir / "index.json"

    def _msg_path(self, conv_id: int) -> Path:
        return self._dir / f"{conv_id}.jsonl"

    # ── Index operations ────────────────────────────────────────

    def _load_index(self) -> list[dict]:
        return _read_json(self._index_path, [])

    def _save_index(self, index: list[dict]) -> None:
        _atomic_write(self._index_path, json.dumps(index, indent=2))

    def index_entry(self, conv_id: int, title: str = "New Conversation",
                    model_used: str | None = None, **extra) -> dict:
        """Create or update an entry in conversations/index.json."""
        with _file_lock(self._index_path):
            index = self._load_index()
            existing = next((e for e in index if e["id"] == conv_id), None)
            now = time.time()
            if existing:
                existing["updated_at"] = now
                if title and title != "New Conversation":
                    existing["title"] = title
                if model_used:
                    existing["model_used"] = model_used
                existing.update(extra)
            else:
                entry = {
                    "id": conv_id,
                    "title": title,
                    "created_at": now,
                    "updated_at": now,
                    "model_used": model_used,
                    "message_count": 0,
                    "total_tokens": 0,
                    **extra,
                }
                index.append(entry)
            self._save_index(index)
            return existing or entry

    def update_index(self, conv_id: int, **fields) -> dict | None:
        """Update specific fields in index for a conversation."""
        with _file_lock(self._index_path):
            index = self._load_index()
            entry = next((e for e in index if e["id"] == conv_id), None)
            if not entry:
                return None
            entry.update(fields)
            entry["updated_at"] = time.time()
            self._save_index(index)
            return entry

    def remove_from_index(self, conv_id: int) -> bool:
        """Remove a conversation from the index and delete its message file."""
        with _file_lock(self._index_path):
            index = self._load_index()
            before = len(index)
            index = [e for e in index if e["id"] != conv_id]
            if len(index) < before:
                self._save_index(index)
                msg_file = self._msg_path(conv_id)
                if msg_file.exists():
                    msg_file.unlink()
                return True
            return False

    def list_conversations(self, limit: int = 50, offset: int = 0) -> list[dict]:
        """List conversations from index, sorted by updated_at descending."""
        index = self._load_index()
        index.sort(key=lambda e: e.get("updated_at", 0), reverse=True)
        return index[offset:offset + limit]

    def get_index_entry(self, conv_id: int) -> dict | None:
        """Get a single conversation's index entry."""
        index = self._load_index()
        return next((e for e in index if e["id"] == conv_id), None)

    # ── Message operations ──────────────────────────────────────

    def append_message(self, conv_id: int, role: str, content: str,
                       tokens: int = 0, thinking_content: str | None = None,
                       **extra) -> dict:
        """Append a message to a conversation's JSONL file."""
        msg = {
            "role": role,
            "content": content,
            "tokens": tokens,
            "timestamp": time.time(),
        }
        if thinking_content:
            msg["thinking_content"] = thinking_content
        msg.update(extra)

        msg_file = self._msg_path(conv_id)
        with _file_lock(msg_file):
            with open(msg_file, "a") as f:
                f.write(json.dumps(msg) + "\n")

        # Update index counters
        with _file_lock(self._index_path):
            index = self._load_index()
            entry = next((e for e in index if e["id"] == conv_id), None)
            if entry:
                entry["message_count"] = entry.get("message_count", 0) + 1
                entry["total_tokens"] = entry.get("total_tokens", 0) + tokens
                entry["updated_at"] = time.time()
                self._save_index(index)

        return msg

    def get_messages(self, conv_id: int, limit: int = 500) -> list[dict]:
        """Read all messages from a conversation's JSONL file."""
        msg_file = self._msg_path(conv_id)
        if not msg_file.exists():
            return []
        messages = []
        try:
            with open(msg_file) as f:
                for line in f:
                    line = line.strip()
                    if line:
                        messages.append(json.loads(line))
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("Failed to read messages for conv %d: %s", conv_id, exc)
        if limit:
            messages = messages[-limit:]
        return messages

    def get_context_messages(self, conv_id: int, max_tokens: int = 28000) -> list[dict]:
        """Get messages that fit within token budget, keeping most recent."""
        all_msgs = self.get_messages(conv_id, limit=0)
        if not all_msgs:
            return []
        total = 0
        kept = []
        for msg in reversed(all_msgs):
            msg_tokens = msg.get("tokens", 0)
            if total + msg_tokens > max_tokens:
                break
            kept.append(msg)
            total += msg_tokens
        kept.reverse()
        return kept

    def delete_conversation(self, conv_id: int) -> bool:
        """Delete a conversation's message file and remove from index."""
        msg_file = self._msg_path(conv_id)
        if msg_file.exists():
            msg_file.unlink()
        lock_file = msg_file.with_suffix(msg_file.suffix + ".lock")
        if lock_file.exists():
            lock_file.unlink()
        return self.remove_from_index(conv_id)


# ── Memory Store ────────────────────────────────────────────────────

class MemoryStore:
    """Filesystem-based memory storage.

    long_term.json: [{id, category, title, content, confidence, source, created_at}]
    summaries.json: [{conv_id, summary, created_at}]
    """

    def __init__(self, base_dir: Path):
        self._dir = base_dir
        self._dir.mkdir(parents=True, exist_ok=True)
        self._ltm_path = self._dir / "long_term.json"
        self._summaries_path = self._dir / "summaries.json"

    # ── Long-term memories ──────────────────────────────────────

    def load_memories(self) -> list[dict]:
        return _read_json(self._ltm_path, [])

    def save_memories(self, memories: list[dict]) -> None:
        _atomic_write(self._ltm_path, json.dumps(memories, indent=2, default=str))

    def add_memory(self, category: str, title: str, content: str,
                   confidence: float = 0.5, source: str = "",
                   source_id: int | None = None) -> dict:
        """Add a new memory entry."""
        memories = self.load_memories()
        # Assign next ID
        max_id = max((m.get("id", 0) for m in memories), default=0)
        entry = {
            "id": max_id + 1,
            "category": category,
            "title": title[:50],
            "content": content[:200],
            "confidence": confidence,
            "source": source,
            "source_id": source_id,
            "access_count": 0,
            "created_at": time.time(),
        }
        memories.append(entry)
        self.save_memories(memories)
        return entry

    def update_memory(self, memory_id: int, **fields) -> dict | None:
        memories = self.load_memories()
        entry = next((m for m in memories if m["id"] == memory_id), None)
        if entry:
            entry.update(fields)
            self.save_memories(memories)
        return entry

    def search_memories(self, query: str = "", min_confidence: float = 0.0,
                        limit: int = 15) -> list[dict]:
        """Search memories by keyword and confidence."""
        memories = self.load_memories()
        results = [m for m in memories if m.get("confidence", 0) >= min_confidence]
        if query:
            query_lower = query.lower()
            scored = []
            for m in results:
                text = f"{m.get('title', '')} {m.get('content', '')}".lower()
                # Simple keyword scoring
                score = sum(1 for word in query_lower.split() if word in text)
                if score > 0:
                    scored.append((score, m))
            scored.sort(key=lambda x: (-x[0], -x[1].get("confidence", 0)))
            results = [m for _, m in scored]
        else:
            results.sort(key=lambda m: -m.get("confidence", 0))
        return results[:limit]

    def reinforce_memory(self, memory_id: int, amount: float = 0.01) -> None:
        """Gently boost confidence for accessed memories."""
        memories = self.load_memories()
        for m in memories:
            if m["id"] == memory_id:
                m["confidence"] = min(1.0, m.get("confidence", 0.5) + amount)
                m["access_count"] = m.get("access_count", 0) + 1
                break
        self.save_memories(memories)

    def delete_memory(self, memory_id: int) -> bool:
        memories = self.load_memories()
        before = len(memories)
        memories = [m for m in memories if m["id"] != memory_id]
        if len(memories) < before:
            self.save_memories(memories)
            return True
        return False

    # ── Summaries ───────────────────────────────────────────────

    def add_summary(self, conv_id: int, summary: str) -> dict:
        summaries = _read_json(self._summaries_path, [])
        entry = {"conv_id": conv_id, "summary": summary, "created_at": time.time()}
        summaries.append(entry)
        _atomic_write(self._summaries_path, json.dumps(summaries, indent=2))
        return entry

    def get_summaries(self, limit: int = 20) -> list[dict]:
        summaries = _read_json(self._summaries_path, [])
        return summaries[-limit:]


# ── Agent Store ─────────────────────────────────────────────────────

class AgentStore:
    """Filesystem-based agent configuration and run history."""

    def __init__(self, base_dir: Path):
        self._dir = base_dir
        self._dir.mkdir(parents=True, exist_ok=True)
        self._runs_dir = self._dir / "runs"
        self._runs_dir.mkdir(exist_ok=True)
        self._config_path = self._dir / "config.json"

    def load_config(self) -> dict:
        return _read_json(self._config_path, {"agents": []})

    def save_config(self, config: dict) -> None:
        _atomic_write(self._config_path, json.dumps(config, indent=2, default=str))

    def append_run(self, run_id: int, agent_name: str, status: str,
                   result: str = "", **meta) -> dict:
        entry = {
            "run_id": run_id,
            "agent_name": agent_name,
            "status": status,
            "result": result,
            "timestamp": time.time(),
            **meta,
        }
        run_file = self._runs_dir / f"{run_id}.jsonl"
        with open(run_file, "a") as f:
            f.write(json.dumps(entry) + "\n")
        return entry

    def get_runs(self, limit: int = 50) -> list[dict]:
        runs = []
        for f in sorted(self._runs_dir.glob("*.jsonl"), reverse=True)[:limit]:
            try:
                with open(f) as fh:
                    for line in fh:
                        if line.strip():
                            runs.append(json.loads(line.strip()))
            except (json.JSONDecodeError, OSError):
                pass
        runs.sort(key=lambda r: r.get("timestamp", 0), reverse=True)
        return runs[:limit]


# ── Knowledge Store ─────────────────────────────────────────────────

class KnowledgeStore:
    """Filesystem-based knowledge entries."""

    def __init__(self, base_dir: Path):
        self._dir = base_dir
        self._dir.mkdir(parents=True, exist_ok=True)
        self._entries_path = self._dir / "entries.json"

    def load_entries(self) -> list[dict]:
        return _read_json(self._entries_path, [])

    def add_entry(self, title: str, content: str, category: str = "general",
                  **extra) -> dict:
        entries = self.load_entries()
        max_id = max((e.get("id", 0) for e in entries), default=0)
        entry = {
            "id": max_id + 1,
            "title": title,
            "content": content,
            "category": category,
            "created_at": time.time(),
            **extra,
        }
        entries.append(entry)
        _atomic_write(self._entries_path, json.dumps(entries, indent=2))
        return entry

    def search_entries(self, query: str, limit: int = 10) -> list[dict]:
        entries = self.load_entries()
        if not query:
            return entries[:limit]
        q = query.lower()
        scored = []
        for e in entries:
            text = f"{e.get('title', '')} {e.get('content', '')}".lower()
            score = sum(1 for word in q.split() if word in text)
            if score > 0:
                scored.append((score, e))
        scored.sort(key=lambda x: -x[0])
        return [e for _, e in scored[:limit]]
