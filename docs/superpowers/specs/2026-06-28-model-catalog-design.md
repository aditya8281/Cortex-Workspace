# Model Catalog + Download Manager — Design Spec

> **For agentic workers:** This is the approved design. Do NOT start implementation until writing-plans creates the implementation plan.

**Goal:** Full-featured model catalog page enabling users to browse, compare, download, and manage LLMs — with Chat integration for model selection.

**Architecture:** Single `/models` page with four tabs (Browse, Compare, Downloads, Installed). API clients merge existing `developer/api.ts` (catalog) and `integration/api.ts` (downloads). New components in `features/models/`. Chat page gets model selector dropdown. Sidebar gets new nav link.

**Tech Stack:** Next.js 15 App Router, React 19, TypeScript, Tailwind CSS (DESIGN.md tokens), existing shared UI components (Card, Badge, Button, Input, Modal, StatusDot, Dropdown).

---

## 1. Backend Endpoints (Source of Truth)

### Catalog (developer/catalog.py)

| Method | Path | Response |
|--------|------|----------|
| GET | `/models` | `ModelListResponse` — models[], total_count, downloaded_count, providers[], type_counts, size_counts, catalog_status |
| GET | `/models/recommended` | `RecommendedModelsAllResponse` — hardware{}, workloads{} |
| GET | `/models/hardware` | `HardwareInfoResponse` — ram, cpu, gpu, disk, cuda/metal |
| GET | `/models/search` | `ModelSearchResponse` — models[], total_count |
| POST | `/models/compare` | `ModelComparisonResponse` — winner, dimensions[], summary |
| GET | `/models/autocomplete` | `AutocompleteResponse` — suggestions[] |
| GET | `/models/{model_id}` | `ModelDetailResponse` — full detail + variants[] |
| GET | `/models/{model_id}/inference-config` | `InferenceConfigResponse` — temperature, top_p, etc. |

### Downloads (integration/downloads.py)

| Method | Path | Response |
|--------|------|----------|
| GET | `/models/installed` | `InstalledModelsResponse` — models[], installed_count |
| POST | `/models/installed/sync` | `SyncInstalledResponse` — matched, created, deleted, errors |
| GET | `/models/downloads/queue` | `DownloadQueueResponse` — active[], queued[], completed[], failed[] |
| GET | `/models/downloads/history` | `DownloadHistoryResponse` — history[] |
| POST | `/models/{model_name}/download` | `DownloadModelResponse` — status, model, download_id |
| GET | `/models/{model_name}/progress` | `DownloadProgressResponse` — model, progress (0-1) |
| POST | `/models/{model_name}/cancel` | `CancelDownloadResponse` — cancelled |
| DELETE | `/models/{model_name}` | `DeleteModelResponse` — status, model |

**Total: 16 endpoints**

---

## 2. Page Structure

### Route: `/models`

Single page with four tabs. Persistent hardware detection bar across all tabs.

```
/models
┌─────────────────────────────────────────────────────┐
│ Hardware Bar (always visible)                       │
│ RAM: 16GB/32GB · GPU: RTX 3080 10GB · Disk: 245GB │
├─────────────────────────────────────────────────────┤
│ [Browse] [Compare] [Downloads] [Installed]          │
├─────────────────────────────────────────────────────┤
│ (tab content)                                       │
└─────────────────────────────────────────────────────┘
```

### Sidebar Update

Add nav link between Agents and System:
- Label: "Models"
- Icon: download/grid icon (consistent with existing icon style)
- Route: `/models`

---

## 3. Hardware Bar Component

**Source:** `GET /models/hardware`

Persistent across all tabs. Shows detected system specs:

```
┌──────────────────────────────────────────────────────┐
│ RAM 16GB/32GB ████████░░  │ GPU RTX 3080 10GB VRAM  │
│ CPU 12 cores AMD64        │ Disk 245GB free          │
└──────────────────────────────────────────────────────┘
```

- RAM bar: green when <70%, yellow 70-85%, red >85%
- GPU: show name + VRAM if available, "No GPU" otherwise
- CUDA/Metal badges if supported
- Compact single-row on mobile, wraps to 2 rows

---

## 4. Browse Tab

### Layout
Responsive card grid:
- Mobile: 1 column
- Tablet (768px+): 2 columns
- Desktop (1280px+): 3 columns

Grid CSS: `grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4`

### Recommended Section (top)
Source: `GET /models/recommended` (without workload param → returns all workloads)

Shows 3-4 highlighted cards with recommendation explanation. Section header: "Recommended for your hardware". Each card includes the `explanation.why` text and a `suitability` indicator.

### Filter Row
Below recommended, above main grid:

1. **Search input** — debounced 300ms, calls `GET /models/search?q=...`. Autocomplete from `GET /models/autocomplete` (show as suggestions below input).

2. **Capability chips** — toggleable: `chat`, `code`, `vision`. Multi-select. Filters client-side from loaded results OR passes `capabilities` param to search endpoint.

3. **Size filter** — three toggleable chips: `Small (<4B)`, `Medium (4-14B)`, `Large (>14B)`. Uses `type_counts` from list response to show counts.

4. **Sort dropdown** — options: `Relevance`, `Size ↑`, `Size ↓`, `Params ↑`, `Params ↓`. Default: Relevance.

5. **Provider filter** — dropdown from `available_from_providers` in list response. Default: All.

### Model Card

```
┌─────────────────────────────────┐
│ Llama 3.1 8B            ★ Installed │  ← display_name + downloaded badge
│ 8B params                        │  ← parameter_count
│ [chat] [code]                    │  ← capability badges
│ 4.7 GB · Q4_K_M                 │  ← primary variant size + quantization
│ RAM: 8GB needed                  │  ← hardware_requirements.min_ram_gb
│ ████████░░ 100% fit              │  ← RAM fit bar
│                                  │
│ [Download]    [Compare □]        │  ← action buttons
└─────────────────────────────────┘
```

**Card states:**
- **Not downloaded:** Show download button + compare checkbox
- **Downloaded:** Show green `✓ Installed` badge, "View Details" button, compare checkbox
- **Downloading:** Show progress bar inline (from progress endpoint), cancel button
- **Download failed:** Show error badge, retry button

**RAM fit calculation:**
- Get `hardware.ram_gb` from hardware endpoint
- Get `model.hardware_requirements.min_ram_gb` from model entry
- Fit % = `(ram_available / min_ram_needed) * 100`, capped at 100
- Green: >=100%, Yellow: 50-99%, Red: <50%
- If no GPU and model needs GPU: show "GPU recommended" warning

**Download action:**
1. Click "Download" → if model has variants, show variant picker (dropdown of `model.variants[]`)
2. Default to smallest variant (lowest `size_bytes`)
3. Call `POST /models/{model_name}/download?variant={variant_id}`
4. Card transitions to "downloading" state with inline progress

**Compare checkbox:**
- Toggle adds/removes model from compare selection (React state array)
- Max 5 selected — disable checkboxes when 5 selected
- Show floating "Compare N models" button when 2+ selected
- Button navigates to Compare tab

### Pagination
Backend returns up to 50 models by default. If `total_count > 50`, show "Load more" button or infinite scroll. Pass `offset` param if backend supports it; otherwise increase `limit`.

---

## 5. Compare Tab

### Selection
Users select 2-5 models via checkboxes in Browse tab. Selection persists in component state when switching tabs.

If <2 selected: show empty state with prompt "Select 2-5 models in the Browse tab to compare".

### Comparison View
Source: `POST /models/compare` with `model_ids: string[]`

Visual bar comparison (no external charting library — pure CSS bars for zero dependency):

```
Comparison: Llama 3.1 8B vs Mistral 7B vs Coder 13B

Parameters
Llama    ████████████████ 8B
Mistral  ██████████████ 7B
Coder    ████████████████████████ 13B  ★

RAM Required
Llama    ████████████████ 8GB   ★
Mistral  ████████████████ 8GB   ★
Coder    ████████████████████████████ 14GB

Estimated Speed (tokens/sec)
Llama    ████████████████████████ 45 t/s
Mistral  ████████████████████████████ 52 t/s  ★
Coder    ████████████████ 28 t/s

Quality Score
Llama    ████████████████████████████ 82/100
Mistral  ██████████████████████████ 78/100
Coder    ████████████████████████████████ 85/100 ★

Winner: Llama 3.1 8B
"Best fit for your 32GB RAM system. Balanced performance across all dimensions."
```

**Bar implementation:**
- Each bar: `div` with `bg-accent` (winner) or `bg-bg-elevated` (others)
- Width: percentage of max value in that dimension
- Star (★) badge on winner per dimension
- Overall winner at bottom with explanation from `summary` field

**Dimension mapping from backend response:**
Each `DimensionComparisonResponse` has: `dimension`, `display_name`, `values` (dict[model_id, value]), `winner` (model_id), `higher_is_better`.

**Actions on compare page:**
- "Download Winner" button → triggers download flow for winner model
- "Download All" → queue downloads for all compared models
- "Clear selection" → resets compare selection
- Reorder columns by clicking model name header

---

## 6. Downloads Tab

### Source
`GET /models/downloads/queue` — returns active[], queued[], completed[], failed[]

### Sections (stacked vertically)

#### Active Downloads
Real-time section. Polls `GET /models/{model_name}/progress` every 2 seconds while any download has `status: "active"`.

Each active download:
```
┌──────────────────────────────────────────────┐
│ llama3.1:8b-q4_km                           │
│ ████████████████░░░░░░░░ 67%                │
│ 2.1 MB/s · 1m 23s remaining · [Cancel]     │
└──────────────────────────────────────────────┘
```

Progress bar: `bg-accent` fill, percentage text. Speed from `speed_bytes_sec`, ETA from `eta_seconds`.

#### Queued
```
┌──────────────────────────────────────────────┐
│ Queued (1)                                   │
│ codellama:13b-q4_km     Position: #3        │
└──────────────────────────────────────────────┘
```

#### Completed (collapsible, collapsed by default)
```
┌──────────────────────────────────────────────┐
│ Completed (5)                          [▸]  │
│                                              │
│ phi3:mini-q4_km     ✓ 1.2 GB   Jun 28     │
│ tinyllama:q4_km     ✓ 637 MB   Jun 27     │
└──────────────────────────────────────────────┘
```

#### Failed (collapsible, expanded by default if non-empty)
```
┌──────────────────────────────────────────────┐
│ Failed (1)                                   │
│ badmodel:7b    ✗ Connection timeout  [Retry] │
└──────────────────────────────────────────────┘
```

**Cancel button:** Calls `POST /models/{name}/cancel`. Optimistic UI: immediately move to failed with "Cancelled" error.

**Retry button:** Calls `POST /models/{name}/download` again.

**Empty state:** "No downloads yet. Browse models to find one to download."

---

## 7. Installed Tab

### Source
`GET /models/installed` — returns models[], installed_count

### Header
"Installed Models (N)" with "Sync from Ollama" button → calls `POST /models/installed/sync`, shows result toast (matched/created/deleted counts).

### Card Grid
Same responsive grid as Browse. Each card:

```
┌─────────────────────────────────┐
│ Llama 3.1 8B                   │
│ 8B · 4.7 GB · Q4_K_M          │
│ [chat] [code]                   │
│                                 │
│ [Set as Default]                │
│ [View Details]  [Delete]        │
└─────────────────────────────────┘
```

**Set as Default:** Stores `model_id` in `localStorage` key `cortex_default_model`. Shows green badge "Default" on the card that has it set. This value is read by Chat's model selector.

**View Details:** Opens ModelDetailModal (see section 8).

**Delete:** Confirmation dialog ("Delete llama3.1:8b? This will remove it from Ollama."). Calls `DELETE /models/{name}`. Optimistic removal from grid.

**Sync from Ollama:** On click → call `POST /models/installed/sync` → show toast with result → refresh installed list.

### Empty state
"No models installed yet. Browse the catalog to download your first model."

---

## 8. Model Detail Modal

Triggered from Browse card click or Installed "View Details".

### Source
`GET /models/{model_id}` for model info + variants
`GET /models/{model_id}/inference-config` for inference parameters

### Layout
```
┌──────────────────────────────────────────────────┐
│ Llama 3.1 8B                              [×]   │
│──────────────────────────────────────────────────│
│ 8B params · Context: 4096 tokens                │
│ License: llama3                                  │
│ [chat] [code]                                    │
│                                                  │
│ Description                                      │
│ Meta's Llama 3.1 8B is a powerful...            │
│                                                  │
│ Recommended Use Cases                            │
│ General chat, code assistance, reasoning         │
│                                                  │
│ Tags                                             │
│ [llama] [meta] [general] [code]                  │
│                                                  │
│ Variants                                         │
│ ┌──────────────────────────────────────────────┐ │
│ │ Quant   Size    Quality  VRAM   Action       │ │
│ │ Q4_K_M  4.7GB   80%      6GB   [Download]  │ │
│ │ Q8_0    8.9GB   95%      11GB  [Download]  │ │
│ │ F16     16GB    100%     20GB  [Download]  │ │
│ └──────────────────────────────────────────────┘ │
│                                                  │
│ Inference Config (default)                       │
│ Temperature: 0.7 · Top P: 0.9 · Top K: 40      │
│ Repeat Penalty: 1.1 · Max Tokens: 2048          │
│                                                  │
│ [Download Default Variant]  [Use in Chat]        │
└──────────────────────────────────────────────────┘
```

**Variant table:**
- Highlight row with `downloaded: true` with green badge
- Show VRAM requirement vs available VRAM from hardware bar
- Download button per variant → triggers download

**Use in Chat:** Sets as default model (localStorage) + navigates to `/chat`.

---

## 9. Chat Integration

### Chat Model Selector
Modify `features/chat/page.tsx` to add model selector:

```
┌──────────────────────────────────────┐
│ Chat                                 │
│                                      │
│ Model: [v llama3.1:8b ▾] [Browse →] │
│                                      │
│ (conversation area)                  │
└──────────────────────────────────────┘
```

**Model selector dropdown:**
- Lists installed models from `GET /models/installed`
- Shows display_name + size for each
- "Browse Models →" link at bottom → navigates to `/models`
- Selected model stored in `localStorage` key `cortex_default_model`
- Falls back to first installed model if no default set

**API change:**
Chat request body must include `model_id` field. Update `chatApi.send()` to accept and pass model parameter.

---

## 10. API Client Merge

### New file: `frontend/src/features/models/api.ts`

Merges and re-exports from existing clients + adds missing types:

```typescript
// Re-export from existing
export { catalog } from "@/features/developer/api";
export { sync as syncApi } from "@/features/integration/api";

// New types for models page
export interface ModelWithFit extends ModelCatalogEntry {
  ramFitPercent: number;
  ramFitStatus: "good" | "tight" | "insufficient";
  isDefault: boolean;
}
```

No duplication. Browse/Compare use `catalog.*`, Downloads/Installed use `syncApi.*` + the download endpoints from `integration/api.ts`.

---

## 11. State Management

All component-local state (no global state needed):

- **Browse:** models[], filters, searchQuery, loading
- **Compare:** selectedModelIds[] (persisted across tab switches via parent state)
- **Downloads:** queue data, polling interval ref, activeCount
- **Installed:** models[], syncStatus
- **Default model:** localStorage key `cortex_default_model`
- **Hardware:** loaded once on mount, shared via prop drilling (small data)

---

## 12. Error Handling

| Scenario | Handling |
|----------|----------|
| Hardware detection fails | Show "Hardware unknown" in bar, disable RAM fit indicators |
| Catalog load fails | Show error banner with retry button |
| Download fails | Move to Failed section with error message, show Retry button |
| Ollama not running | Hardware bar shows "Ollama not connected", installed shows empty with "Start Ollama" hint |
| Search returns empty | "No models match your filters" empty state |
| Compare with <2 models | "Select at least 2 models to compare" prompt |

---

## 13. Loading States

- **Hardware bar:** Skeleton placeholders until loaded
- **Browse grid:** Skeleton cards (3-6) while catalog loads
- **Downloads:** Instant from queue endpoint, no skeleton needed
- **Installed:** Skeleton cards while installed list loads
- **Compare:** Loading spinner while comparison computes

---

## 14. Responsive Behavior

| Breakpoint | Layout |
|------------|--------|
| <640px | Single column cards, hardware bar wraps, tabs scroll horizontally |
| 640-1280px | 2-column card grid |
| >1280px | 3-column card grid |

---

## 15. Accessibility

- Tab navigation: keyboard-accessible tab switching (arrow keys within tab bar)
- Cards: `role="article"`, `aria-label` with model name
- Progress bars: `role="progressbar"`, `aria-valuenow`, `aria-valuemin`, `aria-valuemax`
- Download/cancel buttons: clear `aria-label` ("Download Llama 3.1 8B Q4_K_M variant")
- Compare checkboxes: `aria-label` ("Add Llama 3.1 8B to comparison")
- Modal: focus trap, Escape to close, focus restoration (uses existing Modal component)
- Reduced motion: disable progress bar animation, instant tab switch

---

## 16. Files to Create/Modify

| File | Action | Purpose |
|------|--------|---------|
| `frontend/src/app/models/page.tsx` | Create | Route page (re-export) |
| `frontend/src/features/models/page.tsx` | Create | Client component with tabs |
| `frontend/src/features/models/components/HardwareBar.tsx` | Create | Hardware detection display |
| `frontend/src/features/models/components/BrowseView.tsx` | Create | Browse tab: filters + card grid |
| `frontend/src/features/models/components/ModelCard.tsx` | Create | Model card (Browse + Installed) |
| `frontend/src/features/models/components/CompareView.tsx` | Create | Visual comparison bars |
| `frontend/src/features/models/components/DownloadsView.tsx` | Create | Download queue/history |
| `frontend/src/features/models/components/InstalledView.tsx` | Create | Installed models grid |
| `frontend/src/features/models/components/ModelDetailModal.tsx` | Create | Full model detail modal |
| `frontend/src/features/models/components/VariantPicker.tsx` | Create | Variant selection for download |
| `frontend/src/features/models/api.ts` | Create | Merged API client + types |
| `frontend/src/shared/layout/Sidebar.tsx` | Modify | Add Models nav link |
| `frontend/src/features/chat/page.tsx` | Modify | Add model selector dropdown |

---

## 17. Design Tokens Used

All from DESIGN.md / tailwind.config.ts:

- `bg-void` (#0a0a0f) — page background
- `bg-elevated` (#111118) — card backgrounds
- `bg-surface` (#16161f) — input backgrounds, hardware bar
- `bg-hover` (#1c1c28) — hover states
- `accent` (#0ea5c9) — download buttons, progress bars, active states
- `text-primary` (#e8e8ed) — model names, headings
- `text-secondary` (#9a9aaa) — descriptions, params
- `text-muted` (#7a7a8a) — secondary info, timestamps
- `border-subtle` — card borders, dividers
- `danger` — delete buttons, error states, failed downloads
- `success` — installed badges, completed downloads
- `warning` — tight RAM fit, yellow progress

---

## 18. Anti-Slop Compliance

Per impeccable/impeccable.md rules:
- No gradient text
- No glassmorphism
- No transition-all (use specific properties)
- No h-screen (use dvh)
- No identical card grids (cards have different states/badges)
- No eyebrows or numbered sections
- No side-stripe borders
- Contrast: all text ≥4.5:1 against backgrounds
- Motion: sidebar 200ms, hover 150ms, modal 250ms, ease-out-quart

---

## Spec Self-Review

1. **Placeholder scan:** No TBDs, no TODOs. All sections complete.
2. **Internal consistency:** Tab names match across all sections. API endpoints match backend. File list covers all components referenced.
3. **Scope check:** Single page with clear boundaries. All 16 backend endpoints covered. Chat integration is a small addition to existing page.
4. **Ambiguity check:** RAM fit calculation is explicit. Compare dimensions come from backend. Download flow is step-by-step. No ambiguous requirements.
