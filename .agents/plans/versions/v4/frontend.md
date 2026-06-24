# V4 Frontend: The Automaton

## Overview

V4 frontend adds management UIs for automation features (scheduler, sessions, webhooks, MCP server, research). The research page is the first major new feature page since V1. Sessions reshape how conversations work. The app starts to feel like a command center.

## Information Architecture Changes

```
V3 IA:
  Dashboard | Memory | Graph | Search | Vault | Settings

V4 IA:
  Dashboard | Memory | Graph | Search | Research | Vault | Settings
                                                    ↑ NEW
  Sessions: integrated into Agent/Conversation flow
  Scheduler: in Settings
  Webhooks: in Settings
  MCP Server: in Settings
```

## New Pages

### /research — Deep Research

Full-page research interface:
- Research question input (large textarea)
- Budget configuration (queries, tokens, time)
- Real-time progress (current phase, queries executed, tokens used)
- Results display (executive summary, findings, sources)
- Previous research sessions list
- Export (HTML, Markdown, PDF)

### /research/[id] — Research Report

Individual research report view:
- Executive summary
- Findings organized by topic
- Source list with links and credibility indicators
- Methodology section
- Raw data (expandable)
- Share/export options

## Modified Pages

### Agent/Conversation → Session-Aware

Conversations gain session context:
- Session selector in header (switch between active sessions)
- "New Session" / "Resume Session" options
- Session metadata panel (accumulated context, decisions, facts)
- Session archive option

### Settings → Expanded

```
Settings
├── General
├── Providers
├── MCP Servers (client)
├── MCP Server (server)  ← NEW
├── Plugins
├── Webhooks             ← NEW
├── Scheduler            ← NEW (from V4 Phase 1)
├── Sessions             ← NEW
├── Research             ← NEW
├── Preferences
├── Routing
├── Backup
├── Performance
└── About
```

## New Components

### ResearchProgress

Real-time research progress indicator:
```
┌─────────────────────────────────────────────────┐
│ 🔍 Researching: "Compare memory architectures"  │
│                                                 │
│ Phase: Synthesizing findings                    │
│ ████████████░░░░░░░░  60%                       │
│                                                 │
│ Queries: 12/20  │  Tokens: 45K/100K  │  2m 15s  │
│ Sources: 18 found                             │
└─────────────────────────────────────────────────┘
```

### SessionSelector

Dropdown in conversation header:
```
┌──────────────────────────┐
│ 📁 Active Sessions       │
│ ──────────────────────── │
│ • Research: mem0 vs zep  │ ← current
│ • Debug auth bug          │
│ • Planning V5 features    │
│ ──────────────────────── │
│ [+ New Session]           │
│ [View All Sessions]       │
└──────────────────────────┘
```

### WebhookCard

Individual webhook configuration:
```
┌─────────────────────────────────────────────────┐
│ 📡 GitHub Push                                 │
│ Path: /webhooks/github                         │
│ Events: push, pull_request                     │
│ Status: 🟢 Active | Last: 5m ago              │
│ Secret: ●●●●●●●● [Show] [Regenerate]          │
│ [Test] [Edit] [Disable] [Delete]              │
└─────────────────────────────────────────────────┘
```

### SchedulerTaskCard

Individual task configuration:
```
┌─────────────────────────────────────────────────┐
│ 🧠 Memory Decay                                │
│ Schedule: Daily at 2:00 AM                     │
│ Status: ✅ Last run: 2h ago (1.2s)            │
│ History: 28/30 runs successful                 │
│ [Run Now] [Edit Schedule] [View History]       │
└─────────────────────────────────────────────────┘
```

## Navigation Changes

Main nav gains Research:
```
┌──────────┐
│ Dashboard│
│ Memory   │
│ Graph    │
│ Search   │
│ Research │ ← NEW
│ Vault    │
│ ──────── │
│ Settings │
└──────────┘
```

## Design System

No major changes. New tokens:
- `--color-research`: Accent color for research features (deep blue)
- `--color-session-active`: Green for active sessions
- `--color-session-archived`: Gray for archived sessions

## Responsive Behavior

Research page: full-width on desktop, stacked on tablet/mobile. Progress indicator sticky on scroll.
