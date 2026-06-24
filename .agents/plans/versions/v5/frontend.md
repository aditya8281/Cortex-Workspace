# V5 Frontend: The Workspace

## Overview

V5 is where the frontend becomes a true workspace hub. Email browser, calendar view, task manager, notes editor, document manager, and contacts — all unified under one roof. The dashboard becomes the command center. Cross-tool workflows make Cortex the single place for daily work.

## Information Architecture Changes

```
V4 IA:
  Dashboard | Memory | Graph | Search | Research | Vault | Settings

V5 IA:
  Dashboard (Workspace) | Email | Calendar | Tasks | Notes | Documents | Contacts | Memory | Graph | Search | Research | Vault | Settings
                                                ↑ NEW    ↑ NEW     ↑ NEW       ↑ NEW

  Navigation split:
  ─────────────────────
  🧠 Intelligence:  Memory, Graph, Search, Research
  📋 Workspace:     Email, Calendar, Tasks, Notes, Documents, Contacts
  🗄️ Storage:       Vault
  ⚙️ System:        Settings
  ─────────────────────
```

## New Pages

### /email — Email Browser

```
┌─────────────────────────────────────────────────┐
│ 📧 Email                           [Compose ✉️] │
├─────────────────────────────────────────────────┤
│ Inbox (3) │ Sent │ Drafts │ Archive             │
│                                                 │
│ 🔍 Search emails...                             │
│                                                 │
│ 📩 From: alice@acme.com                         │
│    Subject: Re: API review                      │
│    "The auth middleware looks good, but..."     │
│    2h ago                                   [→]│
│                                                 │
│ 📩 From: bob@acme.com                           │
│    Subject: Sprint planning                     │
│    "Let's sync on Monday about..."              │
│    1d ago                                   [→]│
│                                                 │
│ 📩 From: github.com                             │
│    Subject: PR #42 approved                     │
│    "Your pull request has been merged..."        │
│    2d ago                                   [→]│
└─────────────────────────────────────────────────┘
```

### /calendar — Calendar View

```
┌─────────────────────────────────────────────────┐
│ 📅 Calendar          [Today] [◀ Week ▶] [Month] │
├─────────────────────────────────────────────────┤
│ Mon 23 │ Tue 24 │ Wed 25 │ Thu 26 │ Fri 27     │
│        │        │ 10:00  │        │              │
│        │        │ Standup│        │              │
│        │ 14:00  │        │ 10:00  │              │
│        │ Design │ 16:00  │ Standup│              │
│        │ Review │ 1:1    │        │              │
│        │        │ 17:00  │        │              │
│        │        │ Sync   │        │              │
│                                                 │
│ [+ New Event] [🔗 Import from Email]             │
│                                                 │
│ ─────────────────────────────────────────────── │
│ TODAY                                            │
│ 10:00 Standup (30 min) — with team              │
│ 14:00 Design Review (1 hr) — Alice, Bob         │
│ 16:00 1:1 with Manager (30 min)                 │
│ 17:00 Team Sync (30 min)                        │
└─────────────────────────────────────────────────┘
```

### /tasks — Task Manager

```
┌─────────────────────────────────────────────────┐
│ ✅ Tasks                          [+ New Task]   │
├─────────────────────────────────────────────────┤
│ Views: [Today] [Upcoming] [Overdue] [All]       │
│ Sort: [Priority ▼] [Due Date ▼]                 │
│                                                 │
│ TODAY (3)                                       │
│ 🔴 Fix auth middleware bug              Overdue │
│    Due: yesterday | #bug #auth                  │
│    [Complete] [Edit] [Delegate]                 │
│                                                 │
│ 🟡 Review PR #42                        Today   │
│    Due: today 5pm | #review                    │
│    [Complete] [Edit] [Delegate]                 │
│                                                 │
│ 🟢 Write V5 documentation              Today   │
│    Due: today | #docs                           │
│    [Complete] [Edit] [Delegate]                 │
│                                                 │
│ ─────────────────────────────────────────────── │
│ UPCOMING (5)                                    │
│ 🟢 Sprint planning                    Tomorrow  │
│ 🟡 Update API docs                   Friday     │
│ 🟢 Prepare demo                      Next week  │
│ ...                                             │
└─────────────────────────────────────────────────┘
```

### /notes — Notes Browser + Editor

```
┌─────────────────────────────────────────────────┐
│ 📝 Notes                        [+ New Note]     │
├──────────┬──────────────────────────────────────┤
│ Tags     │ #architecture (12)                    │
│          │ #meeting (8)                          │
│          │ #idea (15)                            │
│          │ #research (6)                         │
│          │                                       │
│ Recent   │                                       │
│ Memory   │ 📝 Memory Architecture Comparison     │
│ Sprint   │ Updated: 2h ago                       │
│ API      │ #architecture #research               │
│          │                                       │
│          │ Comparing [[mem0]], [[graphiti]],     │
│          │ and [[zep]] approaches to persistent  │
│          │ memory...                             │
│          │                                       │
│          │ ## Key Findings                       │
│          │ - mem0 uses...                        │
│          │ - graphiti focuses on...              │
│          │ - zep takes a...                      │
│          │                                       │
│          │ ────────────────────────────────────  │
│          │ Tags: #architecture #research         │
│          │ Links: [[mem0]] [[graphiti]] [[zep]]  │
└──────────┴──────────────────────────────────────┘
```

### /documents — Document Manager

```
┌─────────────────────────────────────────────────┐
│ 📄 Documents                  [📁 Import] [🔗 URL]│
├─────────────────────────────────────────────────┤
│ 🔍 Search documents...                          │
│ Type: [All] [PDF] [DOCX] [Markdown] [Other]     │
│                                                 │
│ 📄 architecture-spec.pdf     2.3MB  45 chunks   │
│    Imported: 3d ago | Tags: #architecture        │
│    Preview: "The system architecture follows..." │
│    [View] [Search] [Delete]                     │
│                                                 │
│ 📄 meeting-notes.docx        156KB  12 chunks   │
│    Imported: 1d ago | Tags: #meeting            │
│    Preview: "Key decisions from Monday..."       │
│    [View] [Search] [Delete]                     │
│                                                 │
│ 📄 api-reference.md          89KB   34 chunks   │
│    Imported: 5d ago | Tags: #docs               │
│    Preview: "## Authentication..."              │
│    [View] [Search] [Delete]                     │
└─────────────────────────────────────────────────┘
```

### /contacts — Contact Manager

```
┌─────────────────────────────────────────────────┐
│ 👥 Contacts                    [+ Add Contact]   │
├─────────────────────────────────────────────────┤
│ 🔍 Search contacts...                           │
│                                                 │
│ 👤 Alice Chen          eng lead @ Acme          │
│    alice@acme.com | 12 emails | 8 meetings     │
│    Last: 2d ago — "Re: API review"              │
│    [View] [Edit]                                │
│                                                 │
│ 👤 Bob Smith           PM @ Acme                │
│    bob@acme.com | 5 emails | 3 meetings        │
│    Last: 1d ago — "Sprint planning"             │
│    [View] [Edit]                                │
│                                                 │
│ 👤 Carol Davis         designer @ Acme          │
│    carol@acme.com | 3 emails | 2 meetings      │
│    Last: 5d ago — "Design mockups"              │
│    [View] [Edit]                                │
│                                                 │
│ [+ Add Contact] [🔗 Import from Email]          │
└─────────────────────────────────────────────────┘
```

## Navigation Redesign

Sidebar becomes categorized:

```
┌──────────┐
│ 🏠 Home  │ ← Workspace dashboard
│ ─────── │
│ 📋 WORKSPACE
│ 📧 Email │
│ 📅 Cal   │
│ ✅ Tasks │
│ 📝 Notes │
│ 📄 Docs  │
│ 👥 People│
│ ─────── │
│ 🧠 INTEL
│ Memory  │
│ Graph   │
│ Search  │
│ Research│
│ ─────── │
│ 🗄️ VAULT │
│ ─────── │
│ ⚙️ Settings│
└──────────┘
```

## Dashboard Redesign — Workspace Hub

The dashboard becomes the command center:
- 6 widgets (Email, Calendar, Tasks, Notes, Documents, Agent)
- Each widget shows summary with "View All" link
- Quick actions bar at top
- Activity timeline at bottom
- Responsive: widgets stack on tablet, hide on mobile (use bottom tabs)

## Design System

No major design system changes. New tokens:
- `--color-email`: Blue for email features
- `--color-calendar`: Green for calendar features
- `--color-task`: Orange for task features
- `--color-note`: Purple for notes features
- `--color-document`: Teal for document features
- `--color-contact`: Pink for contacts features

Each workspace tool gets its own accent color for visual distinction.

## Responsive Behavior

Desktop (1200px+): Full sidebar + 2-column dashboard
Tablet (800-1199px): Collapsible sidebar + stacked dashboard
Mobile (< 800px): Bottom tab bar (Workspace, Intel, Vault, Settings)

## Keyboard Shortcuts

New shortcuts for workspace:
- `Ctrl+E`: Go to Email
- `Ctrl+D`: Go to Calendar (D for Date)
- `Ctrl+T`: Go to Tasks
- `Ctrl+Shift+N`: New Note
- `Ctrl+Shift+T`: New Task
- `Ctrl+Shift+E`: Compose Email
- `Ctrl+Shift+C`: New Calendar Event
