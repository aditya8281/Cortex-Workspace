# V2 Frontend: The Architecture

## Overview

V2 frontend changes are focused and incremental — adding management UIs for the new backend capabilities (MCP servers, plugins, providers, config). No major redesign. V3 is the desktop redesign.

## Information Architecture Changes

```
V1 IA:
  Dashboard | Memory | Graph | Search | Vault | Settings

V2 IA:
  Dashboard | Memory | Graph | Search | Vault | Settings
                                                  ├── Providers (NEW)
                                                  ├── MCP Servers (NEW)
                                                  ├── Plugins (NEW)
                                                  ├── Preferences (NEW)
                                                  └── Routing (NEW)
```

Settings page expands from 3 sections to 8 sections. New sidebar navigation within Settings.

## New Pages/Sections

### Settings → Providers

Shows registered LLM, embedding, vector store, and cache providers.

- Provider name, type, status (green/yellow/red health indicator)
- Default provider selection per type
- Provider configuration (endpoint URLs, API keys, model names)
- Health check button per provider

### Settings → MCP Servers

List of configured MCP servers.

- Server name, transport type (stdio/SSE), status
- Add server form (name, transport, command/URL, args)
- Server health status (connected/disconnected/error)
- Available tools per server (expandable)
- Remove server button

### Settings → Plugins

Installed plugins list.

- Plugin name, version, author, status (enabled/disabled)
- Plugin details (description, capabilities)
- Enable/disable toggle
- Plugin configuration (if plugin has settings)

### Settings → Preferences

PersistentConfig UI.

- User preferences organized by category
- Each preference: name, description, current value, default value
- Edit preference with type-appropriate input (text, number, select, toggle)
- Reset to default button
- Show override source (env, system, user, default)

### Settings → Routing

Model routing rules.

- Task type → model mapping table
- Edit routing: select task type, select model
- Test routing: input task type, see which model would be selected
- Show model health/status for each routed model

## Component Changes

| Component | Change |
|-----------|--------|
| SettingsLayout | New sidebar navigation for settings sections |
| ProviderCard | New: provider info with health indicator |
| MCPServerCard | New: server info with status + tool list |
| PluginCard | New: plugin info with enable/disable |
| ConfigEditor | New: preference editing with type-appropriate inputs |
| RoutingTable | New: task→model mapping editor |

## Navigation Changes

Settings page gains internal navigation:
```
┌─────────────────────────────────────────────┐
│ Settings                                     │
├──────────┬──────────────────────────────────┤
│ General  │ General Settings                 │
│ Providers│ [LLM] [Embedding] [Vector] [Cache]│
│ MCP      │ [Server list]                    │
│ Plugins  │ [Plugin list]                    │
│ Config   │ [Preference editor]              │
│ Routing  │ [Task→Model table]               │
│ About    │ Version, license, diagnostics     │
└──────────┴──────────────────────────────────┘
```

## Memory Page Changes

- Add consolidation status panel (last run, facts extracted, duplicates removed)
- Show bi-temporal on memory items: valid_from / valid_until dates
- Visual indicator for invalidated memories (contradicted by newer facts)

## No Major Changes

- Dashboard: no changes
- Graph: no changes
- Search: no changes
- Vault: no changes
- Navigation: no changes (Settings expands, not the main nav)

## Design System

No design system changes. Uses existing tokens, components, patterns.

## Responsive Behavior

Settings sidebar collapses to horizontal tabs on tablet/mobile. Same pattern as existing DashboardShell sidebar collapse.
