# Models Page Redesign — "Focused Intelligence"

**Date:** 2026-06-22
**Status:** Draft
**Approves:** Direction A — Focused Intelligence (scroll-based, calm hierarchy)

---

## 1. Problem Statement

The current Models page (927-line `ModelsPage.tsx`) tries to show everything at once — hardware, recommendations, catalog, search, filters — with no clear visual hierarchy. Key issues:

- **Information overload**: Three distinct sections compete for attention on a single scrolling page
- **Broken features**: Compare tray/modal exist but are completely unwired. `reasoning` and `fast` filter options match zero models
- **Lossy data conversion**: Recommendations are converted to fake `ModelInfo` objects with stubbed fields (`provider: ""`, `architecture: ""`)
- **No clear user journey**: Is this a store? A dashboard? A settings page?
- **Hidden variant selection**: Quantization variants are buried in dropdowns
- **Invisible installed models**: Users must scroll to the bottom to see what's on disk

## 2. Design Goals

1. **Calm hierarchy**: One page, clear visual flow top-to-bottom. No tabs, no panels, no density
2. **Recommendations lead**: Hardware-aware "best for your machine" is the hero
3. **Technical depth**: Inline variant chips, fit scores with visual bars, performance metrics visible
4. **Both discovery and management**: Browse/download new models AND see installed models as co-equal concerns
5. **Downloads are separate**: Download queue/progress lives on a separate `/downloads` page or modal

## 3. Target User

Technical power user who understands quantization (Q4/Q5/Q6/Q8), VRAM requirements, GGUF format, and tokens/second. Wants full information visible without hunting through dropdowns.

## 4. Layout Structure

```
┌─────────────────────────────────────────────────────────┐
│  1. Hardware Bar (compact, always visible)              │
├─────────────────────────────────────────────────────────┤
│  2. Top Picks Carousel — "Best for your machine"       │
│     (Netflix-style, auto-rotate, 10 cards, arrows)     │
├─────────────────────────────────────────────────────────┤
│  3. Workload Columns — Chat / Code / Vision            │
│     (top 3 per category)                                │
├─────────────────────────────────────────────────────────┤
│  4. Catalog Table — search, filter, sort               │
│     (dense table with inline fit scores)                │
├─────────────────────────────────────────────────────────┤
│  5. Installed Bar — summary + expandable list          │
│     (persistent bottom section)                         │
└─────────────────────────────────────────────────────────┘
```

### 4.1 Hardware Bar

- **Position**: Top of page, below sidebar
- **Style**: `glass-panel`, `rounded-xl`, subtle border
- **Content**: GPU name + VRAM, RAM used/total with fill bar, Disk free, CUDA/Metal badge
- **Behavior**: Always visible, never scrolls away (sticky). Shows pulsing download indicator when active downloads exist.
- **Data source**: `modelsApi.recommendedEnhanced()` → `hardware` field

### 4.2 Top Picks Carousel — "Best for your machine"

- **Position**: Below hardware bar
- **Style**: Full-width horizontal carousel inside a `glass-panel` container
- **Behavior**:
  - Shows **top 10 recommendations** ranked by hardware fit score
  - **Auto-rotates** every 5 seconds (pauses on hover, pauses when tab is hidden)
  - **Left/right arrow buttons** for manual navigation (circular glass buttons)
  - **Dot indicators** at bottom showing current position
  - Smooth horizontal slide animation (framer-motion)
  - First card is always the #1 pick (slightly larger, accent glow border)

- **Card content** (each card in carousel, ~320px wide):
  - Rank badge (#1, #2, etc.)
  - Fit score (large, accent-colored, e.g., "82%")
  - Model name + quantization (e.g., "Llama 3.1 8B · Q5_K_M")
  - Meta: provider, type, parameter count
  - Specs: speed (t/s), disk size, VRAM required
  - Fit bar (visual gradient bar)
  - Description: italic quote (1-2 lines, truncated)
  - **Inline variant chips**: Q4/Q5/Q6/Q8 (only for the active/focused card)
  - Actions: "Download" button + "Details →" link

- **Data source**: `modelsApi.recommendedEnhanced()` → top 10 recommendations across all workloads, sorted by score descending
- **Navigation**: "Details →" navigates to `/models/{id}` (full detail page)
- **Responsive**: On mobile (< md), show 1 card at a time with swipe support

### 4.3 Workload Columns

- **Position**: Below hero card
- **Style**: 3-column responsive grid (`grid-cols-1 md:grid-cols-3`)
- **Content**: One column per workload (Chat, Code, Vision). Each column:
  - Header: icon (emoji in accent/10 bg) + workload title
  - Top 3 models: name, variant + size, fit % (color-coded), speed (t/s), download button
- **Data source**: `modelsApi.recommendedEnhanced()` → `workloads` field
- **Empty state**: If a workload has no recommendations, show "+ N more available" link

### 4.4 Catalog Table

- **Position**: Below workload columns
- **Style**: Full-width table inside a `glass-panel` card
- **Toolbar**: Search input (debounced 250ms) + type filter pills + size filter pills
- **Table columns**: Model (name), Type (color-coded badge), Params, Size, VRAM, Fit (number + mini bar), Download button
- **Pagination**: Bottom of table, showing "Showing X-Y of Z models" + page buttons
- **Filters**:
  - Type: All, Chat, Code, Vision, Embed (only actual `model_type` values — remove broken `reasoning`/`fast`)
  - Size: All, ≤3B, 3-8B, 8-14B, 14B+
- **Row click**: Navigates to `/models/{id}` (detail page)
- **Download button**: Starts download with default variant. If model has 1 variant, auto-selects it
- **Data source**: `modelsApi.list()` → `models` array

### 4.5 Installed Bar

- **Position**: Bottom of page
- **Style**: Collapsible bar inside a `glass-panel` card
- **Collapsed state**: Shows count badge ("3 models"), storage used ("16.7 GB"), and "Manage →" link
- **Expanded state**: List of installed models with:
  - Name + variant (e.g., "Llama 3.1 8B · Q5_K_M")
  - Size + last used time + request count
  - "Chat" button (navigates to chat with that model)
  - Delete button (with confirmation)
- **Data source**: `modelsApi.installed()` + `modelsApi.usageStats()`

## 5. Component Decomposition

Break the current 927-line monolith into focused components:

| Component | Responsibility | Approx lines |
|---|---|---|
| `ModelsPage` | Orchestrator: data fetching, state, layout | ~150 |
| `HardwareBar` | Compact hardware display + download indicator | ~80 |
| `TopPicksCarousel` | Netflix-style carousel, auto-rotate, 10 cards | ~180 |
| `PickCard` | Individual carousel card (fit score, variants, actions) | ~100 |
| `WorkloadTabs` | 3-column workload recommendations | ~100 |
| `CatalogTable` | Search, filter, table, pagination | ~200 |
| `InstalledBar` | Collapsible installed models list | ~80 |

Total: ~810 lines (vs current 927), but each component is focused and testable.

## 6. Data Flow

### On mount:
1. `modelsApi.recommendedEnhanced()` → hardware + workloads (for carousel, workload columns)
2. `modelsApi.list()` → full catalog (for table)
3. `modelsApi.installed()` → installed models (for installed bar)

### Carousel auto-rotation:
- `useEffect` with `setInterval(5000)` — advances active card index
- Pauses on `mouseenter` / `visibilitychange` (hidden tab)
- Resets timer on manual arrow click
- Wraps around: card 10 → card 1

### On search input (debounced 250ms):
- Client-side filtering of `allModels` (no API call needed for basic search)

### On download:
- `modelsApi.download(modelName, variant)` → starts download
- WebSocket `/ws/models` listens for progress updates
- When complete, re-fetch catalog + installed

### On variant chip click (hero card):
- Updates local state to show selected variant's specs
- Download button uses selected variant

## 7. Fixes Applied During Redesign

| Issue | Fix |
|---|---|
| `reasoning`/`fast` filter options match nothing | Remove from filter pills. Only use actual `model_type` values |
| Compare tray/modal unwired | Remove entirely. Compare is a separate `/models/compare` page |
| Lossy `recommendationToModelInfo()` conversion | Carousel uses raw `ModelRecommendation` data directly |
| Download progress keying inconsistency | Standardize on model name as key throughout |
| `onAddToCompare` never passed to ModelCard | Removed — compare is separate page |
| NeuralNetwork intensity mismatch (`low` vs `medium`) | Use `"medium"` per DESIGN.md |
| Single hero card only shows 1 pick | Netflix carousel shows top 10 with auto-rotation |

## 7a. Carousel Interaction Patterns

- **Auto-rotation**: Every 5 seconds, slides to next card. Pauses on hover and when tab is hidden (Page Visibility API)
- **Manual navigation**: Left/right arrow buttons (circular, glass-panel style, 40px). Arrow keys also work (keyboard accessibility)
- **Dot indicators**: Small dots below carousel showing position. Clickable to jump to specific card
- **Card focus**: Active card gets accent glow border + slightly larger scale (1.02). Inactive cards are slightly dimmed (opacity 0.7)
- **Variant chips**: Only visible on the active card. Other cards show a compact summary
- **Download action**: Clicking "Download" on any card starts download with that card's default variant. If user wants a different variant, they must click "Details →" to go to the detail page
- **Responsive**: On mobile (< 768px), shows 1 card at a time with touch swipe support (framer-motion `drag`)

## 8. Responsive Behavior

| Breakpoint | Layout |
|---|---|
| `xl` (1280px+) | Full layout as mockup |
| `md` (768-1279px) | Workload columns: 2-col. Table: scrollable horizontally |
| `< md` (mobile) | All sections stack vertically. Workload columns: 1-col. Installed bar: always expanded |

## 9. Testing Strategy

- Unit test each sub-component in isolation
- Integration test: verify data flows from API → component → UI
- Visual regression: compare mockup screenshots before/after
- Accessibility: keyboard navigation through variant chips, filter pills, table rows

## 10. Out of Scope

- Compare feature (separate page, not part of this redesign)
- Download queue/progress (separate `/downloads` page)
- Model detail page (already exists at `/models/{id}`)
- Settings page changes
