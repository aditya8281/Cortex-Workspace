# Models System Audit

Date: 2026-06-22
Status: Full system design approved — 4 components

---

## System Overview

Four interconnected components:

| Component | Scope | Layer |
|-----------|-------|-------|
| Marketplace | Browse, discover, download | Frontend |
| Download Manager | Queue, progress, history | Frontend + Backend |
| Recommendation Engine | VRAM-centric scoring | Backend |
| Model Catalog | Data layer, discovery, sync | Backend |

---

## Component 1: Marketplace

The user-facing storefront. Browse by task, filter by hardware, download in one click.

### Key Design Decisions
- **VRAM as primary sort** — every card shows VRAM fit %. Models that fit rank higher.
- **Variant chips inline** — each card shows available quantizations with size. Best-fit pre-selected.
- **Status everywhere** — installed badge, downloading indicator, overflow warning. No click-through needed.
- **Natural language search** — "fast code completion under 4GB" parsed to filters.

### Layout
```
┌─────────────────────────────────────────────┐
│ Hardware context bar (GPU, RAM, Disk)       │
├─────────────────────────────────────────────┤
│ Search bar + quick filters (Chat, Code, ...)│
├──────────────────────┬──────────────────────┤
│ Installed (3)        │ Downloading (1)      │
│ Quick access cards   │ Inline progress      │
├──────────────────────┴──────────────────────┤
│ Model Cards (VRAM-centric)                  │
│ - Name, family, params, provider            │
│ - VRAM fit %, disk size, TPS, context       │
│ - Variant chips (Q4_K_M, Q5_K_M, ...)      │
│ - Status badge (installed/download/overflow)│
│ - Download button (one-click best variant)  │
├─────────────────────────────────────────────┤
│ Inline Download Panel (if active)           │
│ - Progress, speed, ETA, cancel              │
│ - "View all downloads →" link               │
└─────────────────────────────────────────────┘
```

---

## Component 2: Download Manager

Queue management, progress tracking, history. Real-time WebSocket updates.

### Key Design Decisions
- **Summary bar** — installed count/size, active, queued, disk free, speed
- **Active downloads** — animated progress bar, speed, ETA, pause/cancel buttons
- **Queue** — numbered positions, estimated times, cancel per item
- **History** — completed with open/delete, failed with retry/dismiss
- **Settings** — auto-download, max concurrent, storage limit

### Architecture
- `DownloadManager` (asyncio Queue + Semaphore) — core queue system
- `_LegacyModelDownloader` — backward-compatible adapter
- WebSocket `/ws/models` — pushes progress every 1s
- State persistence to `download_state.json`
- DB sync via `ModelDownload` table

---

## Component 3: Recommendation Engine

VRAM-centric scoring. 8 workloads. 7-dimension composite score.

### 7-Dimension Scoring (0-100)

| Dimension | Max Points | Logic |
|-----------|-----------|-------|
| VRAM Fit | 30 | excellent(≤60%)=25-30, good(≤85%)=18-24, tight(≤100%)=10-17, overflow=0-9 |
| Quantization Quality | 20 | Q8_0=100, Q6_K=98, Q5_K_M=95, Q4_K_M=90, Q4_K_S=85, Q2_K=75 |
| Expected TPS | 20 | bandwidth / (2 × model_size), capped at 200 |
| Workload Match | 15 | priority_families + preferred_families + capabilities |
| Popularity | 10 | tiered by download count from ModelStatistics |
| Disk Space | 5 | available disk check |
| Recency | 5 | tiered by days since last_updated |

### VRAM-First Variant Selection
1. Sort variants by quality_score DESC
2. Check: estimated_vram ≤ available_vram × 0.9 (10% headroom)
3. Pick first that fits (highest quality)
4. If none fit → pick smallest, mark as "overflow"
5. Apply architecture multiplier (Ada ×0.95, Apple ×0.90, etc.)

### 8 Workload Types
coding, reasoning, agents, vision, embeddings, lightweight, high_quality, rag

### Performance Estimation
- GPU TPS: `min(bandwidth_gbps / (2 × model_size_gb), 200)`
- VRAM: `param_count × bytes_per_param + kv_cache + 0.3GB overhead`
- Architecture multiplier applied post-estimation

---

## Component 4: Model Catalog

Data layer. 12 tables. 3-source discovery pipeline.

### Database Schema (12 tables)

**Core:**
- `model_catalog` — model registry (model_id, family, capabilities, benchmarks, scores)
- `model_variants` — quantization variants (size, VRAM, TPS, quality_score, downloaded)
- `model_downloads` — download history (status, progress, speed, error)
- `model_usage` — inference metrics (tokens, TPS, context_length)

**Reference:**
- `providers` — provider registry (ollama, huggingface, lmstudio, openrouter)
- `capabilities` — 8 capability types
- `quantizations` — 16 quantization levels with quality scores
- `hardware_profiles` — stored hardware specs

**Aggregation:**
- `model_statistics` — download counts, trending, benchmarks (1:1 with catalog)
- `sync_jobs` — sync history
- `provider_models` — models discovered from providers
- `user_model_settings` — per-user preferences

### 3-Source Discovery Pipeline
1. **OCI Registry** — probe manifests, extract template/params/license (no weight downloads)
2. **Cloud API** — ollama.com GET /api/tags + POST /api/show
3. **Local Ollama** — localhost:11434 GET /api/tags + POST /api/show

Dedup by name → Capability detection → Upsert into catalog + variants

### Provider Adapters
- **Ollama** — active: pull/delete/list
- **HuggingFace** — active: GGUF discovery
- **LM Studio** — seeded, no adapter
- **OpenRouter** — seeded, no adapter

---

## API Endpoints (already exist, no backend changes needed)

| Endpoint | Component |
|----------|-----------|
| `GET /models` | Catalog |
| `GET /models/{id}` | Catalog |
| `GET /models/search` | Catalog |
| `GET /models/recommended` | Recommendation Engine |
| `GET /models/hardware` | Recommendation Engine |
| `POST /models/compare` | Recommendation Engine |
| `GET /models/installed` | Catalog |
| `POST /models/{name}/download` | Download Manager |
| `POST /models/{name}/cancel` | Download Manager |
| `GET /models/downloads/queue` | Download Manager |
| `GET /models/downloads/history` | Download Manager |
| `DELETE /models/{name}` | Download Manager |
| `GET /models/storage` | Catalog |
| `POST /models/sync` | Catalog |
| `POST /models/catalogue/refresh` | Catalog |
| `GET /models/autocomplete` | Catalog |
| `WS /ws/models` | Download Manager |

---

## Frontend Changes Required

### Models Page (Direction A — Model Dashboard)
- Restructure layout: installed-first, recommendations compact, catalog with fit scores
- Remove TopPicksCarousel and auto-rotation
- Integrate InstalledBar as primary column
- Add inline download panel
- Populate CatalogTable "Fit" column from recommendation scores
- Add status badges (installed/downloading/available)
- Variant chips from API data (not hardcoded)

### Downloads Page
- Add back-link to Models
- Keep as detailed view for power users
- Consolidate WebSocket handling

### Components to Remove
- `TopPicksCarousel.tsx` — redundant with workload columns
- `PickCard.tsx` — hardcoded quantizations

### Components to Modify
- `CatalogTable.tsx` — add fit scores, status badges
- `InstalledBar.tsx` — redesign as primary column
- `HardwareBar.tsx` — add installed/download counts

### Components to Create
- `InlineDownloadPanel.tsx` — compact download status for Models page
- `ModelCard.tsx` — VRAM-centric card with variant chips

---

## Backend Changes Required

### Minimal
- Move helper functions from routes to services (`_infer_model_type`, `_guess_param_count`, `_estimate_hardware`)
- Consolidate dual download tracking (local state vs downloadQueue API)

### No Changes Needed
- All 20+ API endpoints already exist
- Recommendation engine already VRAM-centric
- Hardware detection already complete
- Download manager already queue-based
- Catalog sync already 3-source pipeline

---

## Files Inventory

### Frontend — Keep
- `ModelsPage.tsx` — restructure
- `HardwareBar.tsx` — modify
- `WorkloadColumns.tsx` — optional, may remove
- `InstalledBar.tsx` — redesign

### Frontend — Remove
- `TopPicksCarousel.tsx`
- `PickCard.tsx`

### Frontend — Create
- `ModelCard.tsx` — VRAM-centric model card
- `InlineDownloadPanel.tsx` — compact download status

### Backend — Keep (no changes)
- `recommendation.py` (525 lines)
- `hardware.py` (359 lines)
- `model_downloader.py` (520 lines)
- `ollama_catalog.py` (578 lines)
- `catalogue.py` (298 lines)
- `model_search.py` (124 lines)
- `model_comparison.py` (197 lines)
- `quantization_db.py` (131 lines)
- `sync_service.py` (210 lines)
- `usage_tracker.py` (65 lines)
- `models.py` routes (927 lines) — minor cleanup only
