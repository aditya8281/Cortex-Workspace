# V5 Phase 2: Tasks + Notes + Documents

**Duration estimate:** 10-14 days
**Dependencies:** V5 Phase 1 (email, calendar integrations)
**Risk:** Medium — task management complexity, document processing variety

---

## Goals

Build task management system (create, track, prioritize, remind). Build notes system (markdown notes with embedding). Build document management (import, parse, index, search). All integrated with agent — Cortex can create tasks, take notes, manage documents.

## Deliverables

1. Task management system (CRUD, priorities, due dates, reminders)
2. Notes system (markdown, embedding, search)
3. Document management (import, parse, index)
4. Agent tools: create_task, list_tasks, complete_task, create_note, search_notes, import_document
5. Task-calendar integration (tasks with due dates → calendar events)
6. Note-email integration (email content → note)
7. Document-agent integration (agent reads documents for context)

## Architectural Changes

```
BEFORE:
  Cortex = memory, graph, search, vault, email, calendar
  Tasks = external (Todoist, Apple Reminders, etc.)
  Notes = external (Notion, Obsidian, etc.)
  Documents = vault files (manual import)

AFTER:
  Cortex = all above + tasks + notes + documents
  Tasks = built-in, agent-accessible, calendar-integrated
  Notes = built-in markdown notes with vector search
  Documents = parsed, indexed, searchable, agent-readable
```

## Backend Changes

### New Files

| File | Purpose |
|------|---------|
| `backend/app/services/tasks/__init__.py` | Tasks package |
| `backend/app/services/tasks/manager.py` | Task CRUD + lifecycle |
| `backend/app/services/tasks/reminder.py` | Reminder system (scheduler-integrated) |
| `backend/app/services/tasks/views.py` | Task views (today, upcoming, overdue) |
| `backend/app/services/notes/__init__.py` | Notes package |
| `backend/app/services/notes/manager.py` | Note CRUD + lifecycle |
| `backend/app/services/notes/parser.py` | Markdown parser + frontmatter |
| `backend/app/services/notes/linker.py` | Wiki-link resolution ([[note]]) |
| `backend/app/services/documents/__init__.py` | Documents package |
| `backend/app/services/documents/manager.py` | Document lifecycle |
| `backend/app/services/documents/parser.py` | Multi-format parsing (PDF, DOCX, MD, TXT, HTML) |
| `backend/app/services/documents/chunker.py` | Smart chunking for large documents |
| `backend/app/services/documents/indexer.py` | Document → vector + fulltext index |
| `backend/app/models/task.py` | Task SQLAlchemy model |
| `backend/app/models/note.py` | Note SQLAlchemy model |
| `backend/app/models/document.py` | Document + DocumentChunk models |
| `backend/app/api/v1/tasks.py` | Task management API |
| `backend/app/api/v1/notes.py` | Notes API |
| `backend/app/api/v1/documents.py` | Document management API |
| `migrations/versions/d00000000010_tasks_notes_docs.py` | Tasks + notes + documents migration |

### Task System

```python
class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String, default="pending")  # pending, in_progress, completed, cancelled
    priority = Column(String, default="medium")  # low, medium, high, urgent
    due_date = Column(DateTime, nullable=True)
    reminder_at = Column(DateTime, nullable=True)
    tags = Column(JSON, default=list)
    source = Column(String, nullable=True)  # "agent", "user", "email", "calendar"
    parent_id = Column(Integer, ForeignKey("tasks.id"), nullable=True)  # subtasks
    created_at = Column(DateTime, default=func.now())
    completed_at = Column(DateTime, nullable=True)

class TaskManager:
    async def create(self, user_id: int, **kwargs) -> Task: ...
    async def list(self, user_id: int, view: str = "all") -> list[Task]: ...
    async def update(self, task_id: int, **kwargs) -> Task: ...
    async def complete(self, task_id: int) -> Task: ...
    async def get_overdue(self, user_id: int) -> list[Task]: ...
    async def get_today(self, user_id: int) -> list[Task]: ...
```

### Notes System

```python
class Note(Base):
    __tablename__ = "notes"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)  # Markdown
    tags = Column(JSON, default=list)
    source = Column(String, nullable=True)  # "user", "agent", "email", "research"
    embedding_id = Column(String, nullable=True)  # Vector store reference
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

class NoteManager:
    async def create(self, user_id: int, title: str, content: str, tags: list[str] = None) -> Note: ...
    async def list(self, user_id: int, tag: str = None) -> list[Note]: ...
    async def search(self, user_id: int, query: str) -> list[Note]: ...
    async def get_links(self, note_id: int) -> list[Note]: ...  # [[wiki-links]]
    async def update(self, note_id: int, **kwargs) -> Note: ...
    async def delete(self, note_id: int) -> None: ...
```

### Document Management

```python
class DocumentManager:
    PARSERS = {
        ".pdf": PDFParser,
        ".docx": DocxParser,
        ".md": MarkdownParser,
        ".txt": TextParser,
        ".html": HTMLParser,
        ".csv": CSVParser,
    }

    async def import_file(self, user_id: int, file_path: Path) -> Document:
        """Parse, chunk, index a document."""
        parser = self.PARSERS[file_path.suffix]()
        content = await parser.parse(file_path)
        chunks = await self.chunker.chunk(content)
        doc = await self._store_document(user_id, file_path, content)
        await self.indexer.index(doc, chunks)
        return doc

    async def search(self, user_id: int, query: str) -> list[DocumentResult]:
        """Search documents by vector + fulltext."""
        ...
```

### Agent Tools

```python
@tool("create_task", "Create a new task")
async def create_task_tool(title: str, description: str = "", due_date: str = "",
                           priority: str = "medium", tags: str = "") -> str:
    """Create a task with optional due date and priority."""
    ...

@tool("list_tasks", "List tasks")
async def list_tasks_tool(view: str = "all", status: str = "") -> str:
    """List tasks by view (today, upcoming, overdue, all)."""
    ...

@tool("complete_task", "Mark a task as completed")
async def complete_task_tool(task_id: int) -> str:
    """Mark task as completed."""
    ...

@tool("create_note", "Create a markdown note")
async def create_note_tool(title: str, content: str, tags: str = "") -> str:
    """Create a note with markdown content."""
    ...

@tool("search_notes", "Search notes")
async def search_notes_tool(query: str) -> str:
    """Search notes by content."""
    ...

@tool("import_document", "Import a document for indexing", requires_approval=True)
async def import_document_tool(file_path: str) -> str:
    """Import and index a document."""
    ...
```

### Migration

`d00000000010_tasks_notes_docs.py` creates:
- tasks table
- notes table
- documents table (id, user_id, filename, file_path, content_type, size_bytes, chunk_count, embedding_ids, metadata, created_at)
- document_chunks table (id, document_id, chunk_index, content, embedding_id, metadata)

## Frontend Changes

| Page | Change |
|------|--------|
| Dashboard | Tasks widget (today's tasks, overdue count) |
| Dashboard | Notes widget (recent notes) |
| New: /tasks | Task management page |
| New: /notes | Notes browser |
| New: /documents | Document manager |
| Navigation | Add Tasks, Notes, Documents to sidebar |

### /tasks — Task Management

```
┌─────────────────────────────────────────────────┐
│ Tasks                                            │
├─────────────────────────────────────────────────┤
│ Views: [Today] [Upcoming] [Overdue] [All]       │
│                                                 │
│ TODAY (3)                                       │
│ ┌─────────────────────────────────────────────┐ │
│ │ 🔴 Fix auth middleware bug          Overdue │ │
│ │    Due: yesterday                          │ │
│ │    Tags: #bug #auth                        │ │
│ └─────────────────────────────────────────────┘ │
│ ┌─────────────────────────────────────────────┐ │
│ │ 🟡 Review PR #42                    Today   │ │
│ │    Due: today 5pm                          │ │
│ │    Tags: #review                           │ │
│ └─────────────────────────────────────────────┘ │
│ ┌─────────────────────────────────────────────┐ │
│ │ 🟢 Write V5 docs                   Today   │ │
│ │    Due: today                               │ │
│ │    Tags: #docs                              │ │
│ └─────────────────────────────────────────────┘ │
│                                                 │
│ [+ New Task]                                    │
└─────────────────────────────────────────────────┘
```

### /notes — Notes Browser

```
┌─────────────────────────────────────────────────┐
│ Notes                                            │
├─────────────────────────────────────────────────┤
│ 🔍 Search notes...                              │
│ Tags: [All] [#architecture] [#meeting] [#idea]  │
│                                                 │
│ ┌─────────────────────────────────────────────┐ │
│ │ Memory Architecture Comparison              │ │
│ │ Updated: 2h ago | Tags: #architecture       │ │
│ │ Compare mem0, graphiti, zep approaches...   │ │
│ └─────────────────────────────────────────────┘ │
│ ┌─────────────────────────────────────────────┐ │
│ │ Sprint Planning Notes                       │ │
│ │ Updated: 1d ago | Tags: #meeting            │ │
│ │ Key decisions from Monday planning...        │ │
│ └─────────────────────────────────────────────┘ │
│                                                 │
│ [+ New Note]                                    │
└─────────────────────────────────────────────────┘
```

### /documents — Document Manager

```
┌─────────────────────────────────────────────────┐
│ Documents                                        │
├─────────────────────────────────────────────────┤
│ 🔍 Search documents...                          │
│                                                 │
│ 📄 architecture-spec.pdf     2.3MB  45 chunks  │
│    Imported: 3d ago | Indexed: ✅               │
│                                                 │
│ 📄 meeting-notes.docx        156KB  12 chunks  │
│    Imported: 1d ago | Indexed: ✅               │
│                                                 │
│ 📄 api-reference.md          89KB   34 chunks  │
│    Imported: 5d ago | Indexed: ✅               │
│                                                 │
│ [📁 Import Document] [🔗 Import URL]            │
└─────────────────────────────────────────────────┘
```

## Memory Changes

Notes can be stored as memories with high confidence (user-authored). Task completions tracked as memory events. Document key facts extracted and stored.

## Retrieval Changes

Notes, tasks, and documents added to context providers. Search includes all content types.

## Agent Changes

Agent gains 6 new tools (create_task, list_tasks, complete_task, create_note, search_notes, import_document). Agent can proactively create tasks from conversations.

## Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Document parser failures | High | Medium | Graceful fallback. Log errors. Support common formats first. |
| Task-reminder reliability | Medium | High | Scheduler-based. Persistent reminders. Desktop notifications. |
| Wiki-link resolution complexity | Low | Medium | Simple [[title]] matching first. Fuzzy match later. |
| Document chunk quality | Medium | Medium | Smart chunking. Overlap. Test with real documents. |

## Exit Criteria

- [ ] Task CRUD works (create, read, update, delete, complete)
- [ ] Task views work (today, upcoming, overdue, all)
- [ ] Task reminders fire via scheduler + desktop notification
- [ ] Notes CRUD works (create, read, update, delete)
- [ ] Note search works (vector search)
- [ ] Wiki-link resolution works ([[note]] links)
- [ ] Document import works (PDF, DOCX, MD, TXT, HTML)
- [ ] Document chunking works
- [ ] Document search works (vector + fulltext)
- [ ] Agent tools work for all 6 new tools
- [ ] All V1-V5 Phase 1 tests pass
- [ ] New tasks/notes/documents tests
- [ ] `make lint` + `make format` clean
