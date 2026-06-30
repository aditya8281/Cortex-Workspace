# Models Page Redesign — Spec

**Date:** 2026-06-30
**Scope:** Backend enrichment fixes + new API endpoints + frontend Browse/Installed/Detail redesign

---

## Problem

Current models page shows 751+ models as a flat grid of cards. Data quality is poor:
- Context length always shows 4096 (hardcoded, never parsed)
- Variants never populated in list API — cards show zero size/quant info
- License never ingested — always null
- quality_score scale mismatch (DB 0-100, frontend reads as 0-1 → "9000%")
- 27 embedding models classified as "chat" — no embedding support
- Family not in list API — can't group client-side
- 15+ DB columns exist but never populated

Power users need: context window, embedding dimensions, variant comparison, family grouping, accurate metadata.

---

## Approach

**Backend:** Fix enrichment pipeline + add 2 new endpoints (lazy-load families + variants)
**Frontend:** Family-first accordion layout with expandable variant rows, separate embedding section

---

## Backend Changes

### 1. Enrichment Fixes (`ollama_catalog.py`)

**Parse `num_ctx`:**
- During enrichment, regex `num_ctx[=:](\d+)` from Ollama `parameters` blob
- Store as `context_length` in enrichment dict
- Falls back to null if not found

**Detect embedding models:**
- Name pattern match: contains "embed", "bert", "bge", "gte", "e5", "instructor"
- Capability detection: set `"embedding"` capability when detected
- Overrides normal `["completion"]` → `["chat"]` normalization

**Parse embedding dimensions:**
- From parameters blob: regex for `dim`, `embedding_dim`, `hidden_size`, `n_embd`
- Fallback to known mapping:
  ```
  nomic-bert: 768
  nomic-bert-moe: 768
  bge-m3: 1024
  bge-large: 1024
  bge-base: 768
  bge-small: 384
  qwen3-embedding: 1024 (or from params)
  all-minilm: 384
  mxbai-embed: 1024
  snowflake-arctic: 1024
  ```
- Store as `embedding_dim` in enrichment dict

### 2. DB Migration

**New columns on `model_catalog`:**
```python
embedding_dim = Column(Integer, nullable=True)
pooling_type = Column(String(20), nullable=True)  # "cls", "mean", "last"
```

### 3. Ingestion Fixes (`model_catalog.py`)

Pipe fields that enrichment already produces but ingestion ignores:
```python
model.license = m.get("license")
model.architecture = m.get("architecture")
model.context_length_default = m.get("context_length")  # from parsed num_ctx
model.embedding_dim = m.get("embedding_dim")
model.pooling_type = m.get("pooling_type")

# Auto-assign recommended_use_cases
if "code" in capabilities:
    model.recommended_use_cases = ["code generation", "programming assistance"]
if "vision" in capabilities:
    model.recommended_use_cases = ["image understanding", "visual Q&A"]
if "embedding" in capabilities:
    model.recommended_use_cases = ["semantic search", "RAG", "text embeddings"]
else:
    model.recommended_use_cases = ["general chat", "Q&A"]
```

### 4. API Schema Fixes

**`ModelCatalogEntry` (list API) — add missing fields:**
```python
class ModelCatalogEntry(BaseModel):
    # ... existing fields ...
    family: str | None = None          # NEW — needed for client-side grouping
    parameter_size: str | None = None  # NEW — human-readable "8B"
    quantization: str | None = None    # NEW — "Q4_K_M"
    embedding_dim: int | None = None   # NEW — for embedding models
```

**Fix quality_score scale:**
```python
# In variant serialization:
quality_score = v.quality_score / 100.0 if v.quality_score else None
```

### 5. New Endpoint: `GET /models/families`

Groups all models by family. Returns summary for each family + separate embedding families.

```python
class FamilyVariant(BaseModel):
    model_id: str
    parameter_count: float | None
    size_gb: float | None
    size_bytes: int | None
    quantization: str | None
    context_length: int | None
    downloaded: bool
    license: str | None

class FamilySummary(BaseModel):
    family: str
    display_name: str
    model_count: int
    capabilities: list[str]
    default_variant: FamilyVariant  # largest param count, smallest quant
    context_range: list[int]        # [min, max]
    param_range: list[float]        # [min, max]
    license: str | None
    embedding_dim: int | None       # null for non-embedding families

class ModelFamiliesResponse(BaseModel):
    families: list[FamilySummary]
    embedding_families: list[FamilySummary]
    total_families: int
    total_models: int
```

**Logic:**
1. Query all models from `model_catalog` (or enriched catalog JSON)
2. Group by `family`
3. For each family: compute param_range, context_range, collect capabilities, pick default_variant
4. Separate embedding families (where any variant has `embedding` capability)
5. Default variant = highest param_count, lowest size_bytes (best quality per param)

### 6. New Endpoint: `GET /models/families/{family}/variants`

Returns all variants for a specific family.

```python
class FamilyVariantsResponse(BaseModel):
    family: str
    display_name: str
    variants: list[FamilyVariant]
```

**Logic:**
1. Query all models matching family
2. Sort by: parameter_count desc, size_bytes asc
3. Return with download status per variant

---

## Frontend Changes

### Types Updates

**Add to `ModelCatalogEntry`:**
```typescript
family: string | null;
parameter_size: string | null;
quantization: string | null;
embedding_dim: number | null;
```

**Add to `ModelDetail`:**
```typescript
downloaded: boolean;
```

**New types:**
```typescript
interface FamilyVariant {
  model_id: string;
  parameter_count: number | null;
  size_gb: number | null;
  size_bytes: number | null;
  quantization: string | null;
  context_length: number | null;
  downloaded: boolean;
  license: string | null;
}

interface FamilySummary {
  family: string;
  display_name: string;
  model_count: number;
  capabilities: string[];
  default_variant: FamilyVariant;
  context_range: [number, number];
  param_range: [number, number];
  license: string | null;
  embedding_dim: number | null;
}

interface ModelFamiliesResponse {
  families: FamilySummary[];
  embedding_families: FamilySummary[];
  total_families: number;
  total_models: number;
}

interface FamilyVariantsResponse {
  family: string;
  display_name: string;
  variants: FamilyVariant[];
}
```

### Browse View Redesign

**Layout:**
```
[Filter Bar: search | capability chips (chat/code/vision/embedding) | size filter | sort]
[Recommended Section: top 4 cards for hardware]
[Families Grid]
  Family Cards (collapsed → expanded)
[Embedding Models Section: separate, only if embedding families exist]
```

**Family Card (collapsed):**
- Header: family display_name, variant count, param range, context range, license badge
- Default variant inline: name, params, size, quantization, RAM fit bar
- Capability badges
- Actions: Download, View Details, Compare checkbox

**Family Card (expanded):**
- Same header
- Variant rows sorted by: param_count desc, size_bytes asc
- Each row: name, params, size, quant, ctx, RAM fit, download/installed badge
- Installed variants show "Installed" badge instead of download button

**Embedding Section:**
- Separate row of cards
- Each shows: name, dimensions (e.g. "768 dim"), context length, size, download status
- No RAM fit (tiny models)

### Installed View Redesign

Same family-first layout but:
- Only shows families with ≥1 downloaded variant
- Variant rows show: last used timestamp, usage count, Open Chat / Delete actions
- No download buttons — replaced with management actions
- Storage summary bar at top

### Detail Modal Redesign

**Chat model detail:**
- Header: name, author/provider, license, variant count
- Overview: param range, context range, architecture, capabilities
- Description
- Recommended use cases badges
- Sortable variant table (by size/params/quant)
- Per-row: name, params, size, quant, ctx, RAM fit, installed badge, download button
- Actions: bulk download, use in chat, set default

**Embedding model detail:**
- Header: name, author, license
- Overview: dimensions, context, pooling type, architecture
- Use cases badges
- Variant table: name, size, quant, status
- No RAM fit bars

---

## Schema Mismatches to Fix During Implementation

| Layer | Field | Issue | Fix |
|---|---|---|---|
| DB → API list | `family` | Not in Pydantic schema | Add `family: str` to `ModelCatalogEntry` |
| DB → API list | `parameter_size` | Not returned | Add to `ModelCatalogEntry` |
| DB → API list | `quantization` | Not returned | Add to `ModelCatalogEntry` |
| DB → API list | `embedding_dim` | No column | New column + add to schema |
| DB → API detail | `license` | Never ingested | Pipe from enrichment |
| DB → API detail | `architecture` | Never ingested | Pipe from enrichment |
| DB → API detail | `context_length_default` | Hardcoded 4096 | Parse from parameters blob |
| DB → API variants | `quality_score` | 0-100 scale | Normalize to 0-1 in API |
| API → TS | `ModelCatalogEntry` | Missing `family`, `parameter_size`, `quantization` | Add to TS type |
| API → TS | `ModelDetail` | Missing `downloaded` | Add to TS type |
| TS → Component | `ModelSearchResult` | Uses `name` instead of `model_id` | Fix field name |
| TS → Component | `ModelWithFit.variants` | Expects objects, list API returns `string[]` | Fix after new family endpoints |
| Enrichment | embedding models | All classified as "chat" | Detect + set "embedding" capability |
| Frontend | `quality_score` | Treated as 0-1, displayed as "9000%" | Divide by 100 |

---

## Dependency Analysis

**Backend deps (no new packages needed):**
- All changes are internal pipeline/API — no new pip packages
- New migration needed for `embedding_dim` + `pooling_type` columns

**Frontend deps (no new packages needed):**
- Accordion/expandable: pure CSS + React state — no new component library
- Family grouping: client-side `Array.reduce()` — no state management library needed

**Migration risk:**
- New columns are nullable — safe, no data loss
- Enrichment re-parse will update `context_length_default` from 4096 to real values
- No column renames or deletions

---

## Scope

**In scope:**
- Backend enrichment fixes (num_ctx, license, architecture, embedding detection)
- DB migration (2 new columns)
- 2 new API endpoints (families, family variants)
- API schema fixes (add missing fields, fix quality_score)
- Frontend Browse view redesign (family accordion)
- Frontend Installed view redesign (same layout + management)
- Frontend Detail modal redesign (variant table)
- Embedding models section
- All schema mismatch fixes

**Out of scope (Phase 2):**
- Benchmarks data population
- Popularity/trending scoring
- Download progress integration in new layout (reuse existing)
- Search integration with new family view
- Virtualized list (773 models is fine without it)

---

## Testing

- Backend: pytest for new endpoints, enrichment parsing, ingestion fixes
- Frontend: Vitest for new components, type compatibility
- Integration: curl tests for new API response shapes
- Browser: Playwright for accordion expand/collapse, variant display
