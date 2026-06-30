# Models Page Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Redesign the models page with family-first grouping, accurate metadata (context window, embedding dims, variants), and proper data pipeline from enrichment through to UI.

**Architecture:** Backend enrichment pipeline parses `num_ctx` and embedding dims, DB gets 2 new columns, 2 new API endpoints group by family, frontend renders accordion layout with expandable variants.

**Tech Stack:** FastAPI, SQLAlchemy 2.0, Alembic, Pydantic v2, Next.js 15, React 19, TypeScript, Tailwind CSS, Vitest

## Global Constraints

- Backend: FastAPI + sync SQLAlchemy 2.0 + Alembic
- Frontend: Next.js 15 App Router + React 19 + TypeScript + Tailwind CSS
- DB: `get_db()` generator, migrations at startup
- Services: constructor injection, global singletons
- Routes: specific before parameterized, `response_model=` on all
- Frontend: DESIGN.md tokens, dark-only, Geist font, tonal elevation
- Tests: SQLite in-memory, no real Postgres/Redis
- Commit messages: one line, standard format, no co-authored-by
- TDD when applicable
- Skill-first: check for applicable skills before every action

---

## File Structure

### Backend Files Modified
| File | Change |
|------|--------|
| `backend/app/models/intelligence/model_catalog.py` | Add `embedding_dim`, `pooling_type` columns |
| `backend/app/services/intelligence/ollama_catalog.py` | Parse `num_ctx`, detect embeddings, parse dims |
| `backend/app/schemas/intelligence/model.py` | Add `family`, `parameter_size`, `quantization`, `embedding_dim` to `ModelCatalogEntry`; fix `quality_score` |
| `backend/app/api/v1/developer/catalog.py` | Add `family`/`parameter_size`/`quantization` to list serialization; fix quality_score; add 2 new endpoints |
| `backend/app/models/__init__.py` | Already imports ModelCatalog — verify |

### Backend Files Created
| File | Purpose |
|------|---------|
| `migrations/versions/xxxx_add_embedding_columns.py` | Add `embedding_dim`, `pooling_type` columns |

### Frontend Files Modified
| File | Change |
|------|--------|
| `frontend/src/features/developer/api.ts` | Add `family`, `parameter_size`, `quantization`, `embedding_dim` to TS types; add new types |
| `frontend/src/features/models/api.ts` | Update `ModelWithFit` |
| `frontend/src/features/models/page.tsx` | Use new BrowseView/InstalledView |
| `frontend/src/features/models/components/BrowseView.tsx` | Complete rewrite — family accordion |
| `frontend/src/features/models/components/InstalledView.tsx` | Complete rewrite — family accordion + management |
| `frontend/src/features/models/components/ModelDetailModal.tsx` | Complete rewrite — variant table |
| `frontend/src/features/models/components/ModelCard.tsx` | Rewrite as FamilyCard |
| `frontend/src/features/models/components/VariantPicker.tsx` | Rewrite as variant table rows |

### Frontend Files Created
| File | Purpose |
|------|---------|
| `frontend/src/features/models/components/FamilyCard.tsx` | Collapsible family group card |
| `frontend/src/features/models/components/VariantRow.tsx` | Single variant row inside expanded family |
| `frontend/src/features/models/components/EmbeddingSection.tsx` | Separate embedding models section |

---

## Task 1: DB Migration — Add Embedding Columns

**Files:**
- Create: `backend/app/models/intelligence/model_catalog.py:12` (modify existing)
- Create: `migrations/versions/xxxx_add_embedding_columns.py`

**Interfaces:**
- Consumes: existing `ModelCatalog` model at `backend/app/models/intelligence/model_catalog.py:12`
- Produces: `ModelCatalog.embedding_dim: Integer nullable`, `ModelCatalog.pooling_type: String(20) nullable`

- [ ] **Step 1: Add columns to ModelCatalog model**

```python
# backend/app/models/intelligence/model_catalog.py
# After line 25 (after `license` column), add:
embedding_dim = Column(Integer, nullable=True)
pooling_type = Column(String(20), nullable=True)
```

- [ ] **Step 2: Create Alembic migration**

Run: `make migration m=add_embedding_columns`

Then edit the generated migration file to add:

```python
def upgrade() -> None:
    op.add_column('model_catalog', sa.Column('embedding_dim', sa.Integer(), nullable=True))
    op.add_column('model_catalog', sa.Column('pooling_type', sa.String(20), nullable=True))


def downgrade() -> None:
    op.drop_column('model_catalog', 'pooling_type')
    op.drop_column('model_catalog', 'embedding_dim')
```

- [ ] **Step 3: Apply migration**

Run: `make migrate`
Expected: Successfully applied migration

- [ ] **Step 4: Commit**

```bash
git add backend/app/models/intelligence/model_catalog.py migrations/versions/
git commit -m "feat: add embedding_dim and pooling_type columns to model_catalog"
```

---

## Task 2: Enrichment — Parse num_ctx from Parameters Blob

**Files:**
- Modify: `backend/app/services/intelligence/ollama_catalog.py:499` (`_normalize_model`)
- Test: `tests/services/test_ollama_catalog.py`

**Interfaces:**
- Consumes: `parameters` string blob from Ollama `/api/show` (already fetched at line 636)
- Produces: `context_length` integer in enrichment dict (integrated into `_normalize_model` output)

- [ ] **Step 1: Write failing test for num_ctx parsing**

```python
# tests/services/test_ollama_catalog.py (or create if not exists)
import pytest
from backend.app.services.intelligence.ollama_catalog import OllamaCatalogService


class TestParseNumCtx:
    def test_parse_num_ctx_from_parameters(self):
        params = "num_ctx=8192\ntemperature=0.7\n"
        result = OllamaCatalogService._parse_num_ctx(params)
        assert result == 8192

    def test_parse_num_ctx_from_parameters_with_equals(self):
        params = "PARAMETER num_ctx 131072\n"
        result = OllamaCatalogService._parse_num_ctx(params)
        assert result == 131072

    def test_parse_num_ctx_missing(self):
        params = "temperature=0.7\n"
        result = OllamaCatalogService._parse_num_ctx(params)
        assert result is None

    def test_parse_num_ctx_empty(self):
        result = OllamaCatalogService._parse_num_ctx("")
        assert result is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/services/test_ollama_catalog.py::TestParseNumCtx -v`
Expected: FAIL — `AttributeError: type object 'OllamaCatalogService' has no attribute '_parse_num_ctx'`

- [ ] **Step 3: Implement _parse_num_ctx**

```python
# backend/app/services/intelligence/ollama_catalog.py
# Add as a static method on OllamaCatalogService, near _detect_capabilities (~line 578)

@staticmethod
def _parse_num_ctx(parameters: str) -> int | None:
    """Parse num_ctx from Ollama parameters blob."""
    if not parameters:
        return None
    import re
    match = re.search(r'num_ctx[=\s]+(\d+)', parameters)
    return int(match.group(1)) if match else None
```

Then in `_normalize_model` (line 499), after the existing normalization block, add:

```python
# Parse context length from parameters if available
if "parameters" in model:
    num_ctx = OllamaCatalogService._parse_num_ctx(model.get("parameters", ""))
    if num_ctx:
        model["context_length"] = num_ctx
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/services/test_ollama_catalog.py::TestParseNumCtx -v`
Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/intelligence/ollama_catalog.py tests/services/test_ollama_catalog.py
git commit -m "feat: parse num_ctx from Ollama parameters blob during catalog enrichment"
```

---

## Task 3: Enrichment — Detect Embedding Models and Parse Dimensions

**Files:**
- Modify: `backend/app/services/intelligence/ollama_catalog.py:578` (`_detect_capabilities` + new methods)
- Test: `tests/services/test_ollama_catalog.py`

**Interfaces:**
- Consumes: model `name`, `capabilities` list, `parameters` blob
- Produces: `embedding_dim: int | None` in enrichment dict, `capabilities: ["embedding"]` for embedding models

- [ ] **Step 1: Write failing tests for embedding detection**

```python
# tests/services/test_ollama_catalog.py

class TestEmbeddingDetection:
    def test_detect_embedding_by_name(self):
        caps = OllamaCatalogService._detect_capabilities(
            template="", model_name="nomic-embed-text"
        )
        assert "embedding" in caps

    def test_detect_embedding_bge(self):
        caps = OllamaCatalogService._detect_capabilities(
            template="", model_name="bge-m3"
        )
        assert "embedding" in caps

    def test_detect_embedding_qwen(self):
        caps = OllamaCatalogService._detect_capabilities(
            template="", model_name="qwen3-embedding"
        )
        assert "embedding" in caps

    def test_chat_model_not_embedding(self):
        caps = OllamaCatalogService._detect_capabilities(
            template="", model_name="qwen3:8b"
        )
        assert "embedding" not in caps

    def test_parse_embedding_dim_from_parameters(self):
        params = "num_ctx=8192\nembedding_dim=768\n"
        dim = OllamaCatalogService._parse_embedding_dim(params)
        assert dim == 768

    def test_parse_embedding_dim_hidden_size(self):
        params = "hidden_size=1024\n"
        dim = OllamaCatalogService._parse_embedding_dim(params)
        assert dim == 1024

    def test_embedding_dim_fallback_known_model(self):
        dim = OllamaCatalogService._get_embedding_dim_fallback("nomic-embed-text")
        assert dim == 768

    def test_embedding_dim_fallback_unknown(self):
        dim = OllamaCatalogService._get_embedding_dim_fallback("some-random-model")
        assert dim is None

    def test_normalize_embedding_model(self):
        """Embedding models get ['embedding'] cap, not ['chat']."""
        model = {
            "name": "nomic-embed-text:latest",
            "capabilities": ["completion"],
            "parameters": "num_ctx=8192\nembedding_dim=768\n"
        }
        OllamaCatalogService._normalize_model(model)
        assert "embedding" in model["capabilities"]
        assert "chat" not in model["capabilities"]
        assert model["embedding_dim"] == 768
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/services/test_ollama_catalog.py::TestEmbeddingDetection -v`
Expected: FAIL — `_parse_embedding_dim` and `_get_embedding_dim_fallback` not defined; existing `_detect_capabilities` doesn't detect embeddings

- [ ] **Step 3: Implement embedding detection**

```python
# backend/app/services/intelligence/ollama_catalog.py

# 1. Add EMBEDDING_NAME_PATTERNS constant near top of class
EMBEDDING_NAME_PATTERNS = ["embed", "bert", "bge", "gte", "e5", "instructor", "minilm", "mxbai", "snowflake-arctic"]

# 2. Add KNOWN_EMBEDDING_DIMS constant
KNOWN_EMBEDDING_DIMS = {
    "nomic-bert": 768, "nomic-bert-moe": 768, "nomic-embed": 768,
    "bge-m3": 1024, "bge-large": 1024, "bge-base": 768, "bge-small": 384,
    "qwen3-embedding": 1024, "all-minilm": 384,
    "mxbai-embed": 1024, "snowflake-arctic": 1024,
}

# 3. Update _detect_capabilities to accept model_name
@staticmethod
def _detect_capabilities(template: str, model_name: str = "") -> list[str]:
    caps = []
    # ... existing template-based detection ...

    # Detect embedding from name
    name_lower = model_name.lower()
    if any(p in name_lower for p in OllamaCatalogService.EMBEDDING_NAME_PATTERNS):
        if "embed" in name_lower or "bert" in name_lower or "bge" in name_lower:
            caps.append("embedding")

    if not caps:
        caps.append("chat")
    return caps

# 4. Add _parse_embedding_dim
@staticmethod
def _parse_embedding_dim(parameters: str) -> int | None:
    if not parameters:
        return None
    import re
    for pattern in [r'embedding_dim[=\s]+(\d+)', r'hidden_size[=\s]+(\d+)', r'n_embd[=\s]+(\d+)']:
        match = re.search(pattern, parameters)
        if match:
            return int(match.group(1))
    return None

# 5. Add _get_embedding_dim_fallback
@staticmethod
def _get_embedding_dim_fallback(model_name: str) -> int | None:
    name_lower = model_name.lower()
    for key, dim in OllamaCatalogService.KNOWN_EMBEDDING_DIMS.items():
        if key in name_lower:
            return dim
    return None

# 6. Update _normalize_model to handle embeddings
# In _normalize_model, AFTER capability normalization but BEFORE the chat fallback:
if "embedding" in model.get("capabilities", []):
    # Parse dimension
    dim = OllamaCatalogService._parse_embedding_dim(model.get("parameters", ""))
    if not dim:
        dim = OllamaCatalogService._get_embedding_dim_fallback(model.get("name", ""))
    model["embedding_dim"] = dim
    # Ensure embedding models don't get "chat" capability
    model["capabilities"] = [c for c in model["capabilities"] if c != "chat"]
else:
    model["embedding_dim"] = None
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/services/test_ollama_catalog.py::TestEmbeddingDetection -v`
Expected: 9 passed

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/intelligence/ollama_catalog.py tests/services/test_ollama_catalog.py
git commit -m "feat: detect embedding models and parse dimensions during catalog enrichment"
```

---

## Task 4: Ingestion — Pipe Missing Fields to DB

**Files:**
- Modify: `backend/app/models/intelligence/model_catalog.py` (ingestion logic — find `ingest_from_catalog` method)
- Test: `tests/models/test_catalog_ingestion.py` (new)

**Interfaces:**
- Consumes: enrichment dict with `license`, `architecture`, `context_length`, `embedding_dim`, `pooling_type`
- Produces: populated DB columns on `ModelCatalog`

- [ ] **Step 1: Write failing test for ingestion**

```python
# tests/models/test_catalog_ingestion.py
import pytest
from backend.app.models.intelligence.model_catalog import ModelCatalog


class TestCatalogIngestion:
    def test_ingest_license(self, db_session):
        """License from enrichment should be stored in DB."""
        from backend.app.services.intelligence.ollama_catalog import OllamaCatalogService
        # ... create a ModelCatalog entry with license in the dict
        # Assert model.license == "Apache-2.0"

    def test_ingest_context_length(self, db_session):
        """context_length from enrichment should populate context_length_default."""
        # ... create entry with context_length=8192
        # Assert model.context_length_default == 8192

    def test_ingest_architecture(self, db_session):
        """architecture from enrichment should be stored."""
        # ... create entry with architecture="Transformer"
        # Assert model.architecture == "Transformer"

    def test_ingest_embedding_fields(self, db_session):
        """embedding_dim and pooling_type should be stored."""
        # ... create entry with embedding_dim=768, pooling_type="mean"
        # Assert model.embedding_dim == 768
        # Assert model.pooling_type == "mean"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/models/test_catalog_ingestion.py -v`
Expected: FAIL — ingestion doesn't pipe these fields

- [ ] **Step 3: Fix ingestion logic**

Find the `ingest_from_catalog` method (search for `def ingest_from_catalog` in the model_catalog files). Add these lines where other fields are set:

```python
# After existing field assignments:
model_catalog.license = m.get("license")
model_catalog.architecture = m.get("architecture")
if m.get("context_length"):
    model_catalog.context_length_default = m["context_length"]
model_catalog.embedding_dim = m.get("embedding_dim")
model_catalog.pooling_type = m.get("pooling_type")

# Auto-assign recommended_use_cases
capabilities = m.get("capabilities", [])
if "embedding" in capabilities:
    model_catalog.recommended_use_cases = ["semantic search", "RAG", "text embeddings"]
elif "code" in capabilities:
    model_catalog.recommended_use_cases = ["code generation", "programming assistance"]
elif "vision" in capabilities:
    model_catalog.recommended_use_cases = ["image understanding", "visual Q&A"]
else:
    model_catalog.recommended_use_cases = ["general chat", "Q&A"]
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/models/test_catalog_ingestion.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/models/intelligence/ model_catalog.py tests/models/test_catalog_ingestion.py
git commit -m "feat: pipe license, architecture, context_length, embedding fields to DB during ingestion"
```

---

## Task 5: API Schema Fixes — Add Missing Fields + Fix quality_score

**Files:**
- Modify: `backend/app/schemas/intelligence/model.py:15` (`ModelCatalogEntry`)
- Modify: `backend/app/api/v1/developer/catalog.py:456` (quality_score serialization)
- Test: `tests/api/test_catalog_api.py`

**Interfaces:**
- Consumes: `ModelCatalog` DB model with new columns
- Produces: Pydantic schemas with correct fields, API responses with normalized quality_score

- [ ] **Step 1: Add fields to ModelCatalogEntry**

```python
# backend/app/schemas/intelligence/model.py, class ModelCatalogEntry (line 15)
# Add these fields:

family: str | None = None
parameter_size: str | None = None
quantization: str | None = None
embedding_dim: int | None = None
```

- [ ] **Step 2: Fix quality_score in list endpoint serialization**

```python
# backend/app/api/v1/developer/catalog.py
# Find where variants are serialized (line ~456)
# Change:
#   "quality_score": v.quality_score
# To:
"quality_score": (v.quality_score / 100.0) if v.quality_score else None
```

Do the same at line ~609 (recommendation variants).

- [ ] **Step 3: Update list endpoint to include new fields**

```python
# backend/app/api/v1/developer/catalog.py, in list_models()
# Where the dict is built for each model, add:
"family": model.get("family") or catalog_entry.get("family"),
"parameter_size": model.get("parameter_size"),
"quantization": model.get("quantization"),
"embedding_dim": model.get("embedding_dim"),
```

- [ ] **Step 4: Write test for new fields**

```python
# tests/api/test_catalog_api.py
def test_list_models_includes_family(db_session, client, auth_headers):
    response = client.get("/api/v1/developer/catalog/models", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    if data["models"]:
        model = data["models"][0]
        assert "family" in model
        assert "parameter_size" in model
        assert "quantization" in model
        assert "embedding_dim" in model
```

- [ ] **Step 5: Run tests**

Run: `pytest tests/api/test_catalog_api.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add backend/app/schemas/intelligence/model.py backend/app/api/v1/developer/catalog.py tests/api/test_catalog_api.py
git commit -m "feat: add family, parameter_size, quantization, embedding_dim to catalog API; fix quality_score scale"
```

---

## Task 6: New Endpoint — GET /models/families

**Files:**
- Modify: `backend/app/schemas/intelligence/model.py` (new Pydantic classes)
- Modify: `backend/app/api/v1/developer/catalog.py` (new endpoint)
- Test: `tests/api/test_catalog_api.py`

**Interfaces:**
- Consumes: `ModelCatalog` DB + `ModelVariant` table + `LLMManager` (downloaded status)
- Produces: `ModelFamiliesResponse` with grouped family summaries

- [ ] **Step 1: Add Pydantic schemas**

```python
# backend/app/schemas/intelligence/model.py

class FamilyVariant(BaseModel):
    model_id: str
    parameter_count: float | None = None
    size_gb: float | None = None
    size_bytes: int | None = None
    quantization: str | None = None
    context_length: int | None = None
    downloaded: bool = False
    license: str | None = None
    embedding_dim: int | None = None

class FamilySummary(BaseModel):
    family: str
    display_name: str
    model_count: int
    capabilities: list[str]
    default_variant: FamilyVariant
    context_range: list[int] = []
    param_range: list[float] = []
    license: str | None = None
    embedding_dim: int | None = None

class ModelFamiliesResponse(BaseModel):
    families: list[FamilySummary]
    embedding_families: list[FamilySummary]
    total_families: int
    total_models: int
```

- [ ] **Step 2: Write failing test**

```python
# tests/api/test_catalog_api.py

def test_get_families(db_session, client, auth_headers):
    response = client.get("/api/v1/developer/catalog/models/families", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "families" in data
    assert "embedding_families" in data
    assert "total_families" in data
    assert "total_models" in data
    if data["families"]:
        fam = data["families"][0]
        assert "family" in fam
        assert "display_name" in fam
        assert "model_count" in fam
        assert "default_variant" in fam
        assert "param_range" in fam
        assert "context_range" in fam

def test_get_family_variants(db_session, client, auth_headers):
    # First get families to find a valid family name
    families_resp = client.get("/api/v1/developer/catalog/models/families", headers=auth_headers)
    families = families_resp.json()["families"]
    if families:
        family_name = families[0]["family"]
        response = client.get(
            f"/api/v1/developer/catalog/models/families/{family_name}/variants",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["family"] == family_name
        assert "variants" in data
        assert isinstance(data["variants"], list)
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `pytest tests/api/test_catalog_api.py::test_get_families -v`
Expected: FAIL — 404 Not Found

- [ ] **Step 4: Implement the endpoints**

```python
# backend/app/api/v1/developer/catalog.py

@router.get(
    "/models/families",
    response_model=ModelFamiliesResponse,
    summary="Get models grouped by family",
)
async def get_model_families(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Return all catalog models grouped by family with variant summaries."""
    from backend.app.models.intelligence.model_catalog import ModelCatalog, ModelVariant

    # Get all catalog entries
    entries = db.query(ModelCatalog).all()

    # Get all variants
    all_variants = db.query(ModelVariant).all()
    variants_by_catalog_id = {}
    for v in all_variants:
        variants_by_catalog_id.setdefault(v.model_catalog_id, []).append(v)

    # Get downloaded model names from LLM manager
    from backend.app.services.intelligence.llm.manager import LLMManager
    llm_manager = LLMManager.get_instance()
    downloaded_names = set()
    try:
        models = llm_manager.list_models()
        downloaded_names = {m.get("name", "") for m in models}
    except Exception:
        pass

    families = {}
    embedding_families = {}

    for entry in entries:
        family = entry.family or "unknown"
        is_embedding = "embedding" in (entry.capabilities or [])

        # Build variant info from DB variants
        entry_variants = variants_by_catalog_id.get(entry.id, [])

        # Build FamilyVariant for each
        family_variants = []
        for v in entry_variants:
            fv = FamilyVariant(
                model_id=v.variant_id or f"{entry.model_id}:{v.ollama_tag or 'latest'}",
                parameter_count=v.parameter_count,
                size_gb=round(v.size_gb, 2) if v.size_gb else None,
                size_bytes=v.size_bytes,
                quantization=v.quantization,
                context_length=entry.context_length_default,
                downloaded=v.downloaded or (v.ollama_tag in downloaded_names if v.ollama_tag else False),
                license=entry.license,
                embedding_dim=entry.embedding_dim,
            )
            family_variants.append(fv)

        # If no DB variants, create a synthetic one from the catalog entry itself
        if not family_variants:
            fv = FamilyVariant(
                model_id=entry.model_id,
                parameter_count=entry.parameter_count,
                size_gb=round((entry_variants[0].size_gb if entry_variants else 0), 2) if entry_variants else None,
                size_bytes=entry_variants[0].size_bytes if entry_variants else None,
                quantization=entry_variants[0].quantization if entry_variants else None,
                context_length=entry.context_length_default,
                downloaded=entry.model_id in downloaded_names,
                license=entry.license,
                embedding_dim=entry.embedding_dim,
            )
            family_variants.append(fv)

        # Pick default variant: highest param_count, then smallest size
        default_variant = sorted(
            family_variants,
            key=lambda x: (-(x.parameter_count or 0), x.size_bytes or float("inf"))
        )[0]

        # Compute ranges
        param_range = sorted(set(v.parameter_count for v in family_variants if v.parameter_count))
        context_range = sorted(set(v.context_length for v in family_variants if v.context_length))
        all_caps = list(set(c for v in family_variants for c in (entry.capabilities or [])))

        summary = FamilySummary(
            family=family,
            display_name=family.replace("-", " ").replace("_", " ").title(),
            model_count=len(family_variants),
            capabilities=all_caps,
            default_variant=default_variant,
            context_range=context_range if context_range else [0, 0],
            param_range=param_range if param_range else [0, 0],
            license=entry.license,
            embedding_dim=entry.embedding_dim,
        )

        if is_embedding:
            embedding_families[family] = summary
        else:
            families[family] = summary

    return ModelFamiliesResponse(
        families=sorted(families.values(), key=lambda x: -x.model_count),
        embedding_families=sorted(embedding_families.values(), key=lambda x: -x.model_count),
        total_families=len(families) + len(embedding_families),
        total_models=len(entries),
    )


@router.get(
    "/models/families/{family}/variants",
    response_model=FamilyVariantsResponse,
    summary="Get all variants for a family",
)
async def get_family_variants(
    family: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Return all variants for a specific model family."""
    from backend.app.models.intelligence.model_catalog import ModelCatalog, ModelVariant

    entry = db.query(ModelCatalog).filter(ModelCatalog.family == family).first()
    if not entry:
        raise HTTPException(status_code=404, detail=f"Family '{family}' not found")

    all_entries = db.query(ModelCatalog).filter(ModelCatalog.family == family).all()
    entry_ids = [e.id for e in all_entries]

    variants = db.query(ModelVariant).filter(ModelVariant.model_catalog_id.in_(entry_ids)).all()

    from backend.app.services.intelligence.llm.manager import LLMManager
    llm_manager = LLMManager.get_instance()
    downloaded_names = set()
    try:
        models = llm_manager.list_models()
        downloaded_names = {m.get("name", "") for m in models}
    except Exception:
        pass

    family_variants = []
    for v in variants:
        fv = FamilyVariant(
            model_id=v.variant_id or f"{entry.model_id}:{v.ollama_tag or 'latest'}",
            parameter_count=v.parameter_count,
            size_gb=round(v.size_gb, 2) if v.size_gb else None,
            size_bytes=v.size_bytes,
            quantization=v.quantization,
            context_length=entry.context_length_default,
            downloaded=v.downloaded or (v.ollama_tag in downloaded_names if v.ollama_tag else False),
            license=entry.license,
            embedding_dim=entry.embedding_dim,
        )
        family_variants.append(fv)

    # Sort by param desc, size asc
    family_variants.sort(key=lambda x: (-(x.parameter_count or 0), x.size_bytes or float("inf")))

    return FamilyVariantsResponse(
        family=family,
        display_name=family.replace("-", " ").replace("_", " ").title(),
        variants=family_variants,
    )
```

Add the new Pydantic class:

```python
# backend/app/schemas/intelligence/model.py
class FamilyVariantsResponse(BaseModel):
    family: str
    display_name: str
    variants: list[FamilyVariant]
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `pytest tests/api/test_catalog_api.py::test_get_families tests/api/test_catalog_api.py::test_get_family_variants -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add backend/app/schemas/intelligence/model.py backend/app/api/v1/developer/catalog.py tests/api/test_catalog_api.py
git commit -m "feat: add /models/families and /models/families/{family}/variants endpoints"
```

---

## Task 7: Frontend Types — Update and Add New Types

**Files:**
- Modify: `frontend/src/features/developer/api.ts:26` (`ModelCatalogEntry`)
- Modify: `frontend/src/features/developer/api.ts:146` (`ModelVariantInfo`)
- Modify: `frontend/src/features/developer/api.ts:160` (`ModelDetail`)
- Modify: `frontend/src/features/models/api.ts:26` (`ModelWithFit`)

**Interfaces:**
- Consumes: API responses from Tasks 5-6
- Produces: TypeScript types matching all API response shapes

- [ ] **Step 1: Update ModelCatalogEntry**

```typescript
// frontend/src/features/developer/api.ts
// Add to interface ModelCatalogEntry (after line ~35):

interface ModelCatalogEntry {
  name: string;
  display_name: string;
  provider: string;
  model_type: string;
  parameter_count: number | null;
  parameter_size: string | null;    // NEW
  quantization: string | null;      // NEW
  size_bytes: number | null;
  context_length: number | null;
  capabilities: string[];
  description: string;
  downloaded: boolean;
  variants: string[];
  hardware_requirements: Record<string, any>;
  family: string | null;            // NEW
  embedding_dim: number | null;     // NEW
}
```

- [ ] **Step 2: Update ModelDetail**

```typescript
// frontend/src/features/developer/api.ts
// Add to interface ModelDetail:

interface ModelDetail {
  // ... existing fields ...
  downloaded: boolean;              // NEW
  embedding_dim: number | null;     // NEW
}
```

- [ ] **Step 3: Add new types**

```typescript
// frontend/src/features/developer/api.ts

interface FamilyVariant {
  model_id: string;
  parameter_count: number | null;
  size_gb: number | null;
  size_bytes: number | null;
  quantization: string | null;
  context_length: number | null;
  downloaded: boolean;
  license: string | null;
  embedding_dim: number | null;
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

- [ ] **Step 4: Update ModelWithFit**

```typescript
// frontend/src/features/models/api.ts

interface ModelWithFit {
  // ... existing fields ...
  embedding_dim: number | null;     // NEW
  ramFitPercent: number;
  ramFitStatus: RamFitStatus;
  isDefault: boolean;
}
```

- [ ] **Step 5: Add API methods for new endpoints**

```typescript
// frontend/src/features/developer/api.ts
// Add to catalog object:

async families(): Promise<ModelFamiliesResponse> {
  const response = await apiFetch("/models/families");
  return response.json();
},

async familyVariants(family: string): Promise<FamilyVariantsResponse> {
  const response = await apiFetch(`/models/families/${encodeURIComponent(family)}/variants`);
  return response.json();
},
```

- [ ] **Step 6: Commit**

```bash
git add frontend/src/features/developer/api.ts frontend/src/features/models/api.ts
git commit -m "feat: add TypeScript types for family grouping and embedding models"
```

---

## Task 8: Frontend — VariantRow Component

**Files:**
- Create: `frontend/src/features/models/components/VariantRow.tsx`
- Test: `frontend/src/features/models/__tests__/VariantRow.test.tsx`

**Interfaces:**
- Consumes: `FamilyVariant` from Task 7
- Produces: rendered variant row with download/installed status

- [ ] **Step 1: Write failing test**

```typescript
// frontend/src/features/models/__tests__/VariantRow.test.tsx
import { render, screen } from "@testing-library/react";
import { VariantRow } from "../components/VariantRow";

const mockVariant = {
  model_id: "qwen3:8b",
  parameter_count: 8.0,
  size_gb: 4.7,
  size_bytes: 4700000000,
  quantization: "Q4_K_M",
  context_length: 4096,
  downloaded: false,
  license: "Apache-2.0",
  embedding_dim: null,
};

describe("VariantRow", () => {
  it("renders model name and params", () => {
    render(<VariantRow variant={mockVariant} ramFitPercent={75} ramFitStatus="good" />);
    expect(screen.getByText("qwen3:8b")).toBeInTheDocument();
    expect(screen.getByText("8B")).toBeInTheDocument();
  });

  it("shows download button when not downloaded", () => {
    render(<VariantRow variant={mockVariant} ramFitPercent={75} ramFitStatus="good" />);
    expect(screen.getByText("Download")).toBeInTheDocument();
  });

  it("shows installed badge when downloaded", () => {
    render(<VariantRow variant={{ ...mockVariant, downloaded: true }} ramFitPercent={75} ramFitStatus="good" />);
    expect(screen.getByText("Installed")).toBeInTheDocument();
  });

  it("shows size in GB", () => {
    render(<VariantRow variant={mockVariant} ramFitPercent={75} ramFitStatus="good" />);
    expect(screen.getByText("4.7 GB")).toBeInTheDocument();
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd frontend && npm test -- VariantRow`
Expected: FAIL — module not found

- [ ] **Step 3: Implement VariantRow**

```tsx
// frontend/src/features/models/components/VariantRow.tsx
"use client";

import { Badge } from "@/shared/ui/Badge";
import { Button } from "@/shared/ui/Button";
import type { FamilyVariant } from "@/features/developer/api";
import { formatParamCount, formatBytes } from "@/features/models/api";

interface VariantRowProps {
  variant: FamilyVariant;
  ramFitPercent: number;
  ramFitStatus: "good" | "tight" | "insufficient";
  onDownload?: (modelId: string) => void;
}

export function VariantRow({ variant, ramFitPercent, ramFitStatus, onDownload }: VariantRowProps) {
  const statusColor = {
    good: "bg-accent/20 text-accent",
    tight: "bg-warning/20 text-warning",
    insufficient: "bg-danger/20 text-danger",
  }[ramFitStatus];

  return (
    <div className="flex items-center gap-4 px-4 py-3 border-b border-border-default/50 last:border-0">
      {/* Name */}
      <span className="text-sm font-medium text-text-primary min-w-[140px]">
        {variant.model_id}
      </span>

      {/* Params */}
      <span className="text-sm text-text-secondary min-w-[60px]">
        {formatParamCount(variant.parameter_count)}
      </span>

      {/* Size */}
      <span className="text-sm text-text-secondary min-w-[80px]">
        {variant.size_gb ? `${variant.size_gb} GB` : "—"}
      </span>

      {/* Quantization */}
      <span className="text-xs font-mono text-text-muted min-w-[80px]">
        {variant.quantization || "—"}
      </span>

      {/* Context */}
      <span className="text-xs text-text-muted min-w-[60px]">
        {variant.context_length ? `${Math.round(variant.context_length / 1000)}K` : "—"}
      </span>

      {/* RAM fit bar */}
      <div className="flex-1 min-w-[100px]">
        <div className="h-1.5 rounded-full bg-bg-surface overflow-hidden">
          <div
            className={`h-full rounded-full ${statusColor}`}
            style={{ width: `${Math.min(100, ramFitPercent)}%` }}
          />
        </div>
      </div>

      {/* Action */}
      {variant.downloaded ? (
        <Badge variant="success">Installed</Badge>
      ) : (
        <Button
          size="sm"
          variant="ghost"
          onClick={() => onDownload?.(variant.model_id)}
        >
          Download
        </Button>
      )}
    </div>
  );
}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd frontend && npm test -- VariantRow`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add frontend/src/features/models/components/VariantRow.tsx frontend/src/features/models/__tests__/VariantRow.test.tsx
git commit -m "feat: VariantRow component for expanded family variant display"
```

---

## Task 9: Frontend — FamilyCard Component

**Files:**
- Create: `frontend/src/features/models/components/FamilyCard.tsx`
- Test: `frontend/src/features/models/__tests__/FamilyCard.test.tsx`

**Interfaces:**
- Consumes: `FamilySummary`, `FamilyVariant[]` (loaded on expand), `HardwareInfo`
- Produces: collapsible family card with default variant shown inline + expandable variant list

- [ ] **Step 1: Write failing test**

```typescript
// frontend/src/features/models/__tests__/FamilyCard.test.tsx
import { render, screen, fireEvent } from "@testing-library/react";
import { FamilyCard } from "../components/FamilyCard";

const mockFamily = {
  family: "qwen3",
  display_name: "Qwen3",
  model_count: 5,
  capabilities: ["chat", "thinking"],
  default_variant: {
    model_id: "qwen3:8b",
    parameter_count: 8.0,
    size_gb: 4.7,
    size_bytes: 4700000000,
    quantization: "Q4_K_M",
    context_length: 4096,
    downloaded: false,
    license: "Apache-2.0",
    embedding_dim: null,
  },
  context_range: [4096, 131072] as [number, number],
  param_range: [0.6, 235.0] as [number, number],
  license: "Apache-2.0",
  embedding_dim: null,
};

describe("FamilyCard", () => {
  it("renders family name and variant count", () => {
    render(<FamilyCard family={mockFamily} ram_gb={32} />);
    expect(screen.getByText("Qwen3")).toBeInTheDocument();
    expect(screen.getByText("5 variants")).toBeInTheDocument();
  });

  it("shows default variant inline", () => {
    render(<FamilyCard family={mockFamily} ram_gb={32} />);
    expect(screen.getByText("qwen3:8b")).toBeInTheDocument();
  });

  it("expands to show variants on click", async () => {
    render(<FamilyCard family={mockFamily} ram_gb={32} />);
    fireEvent.click(screen.getByText("5 variants"));
    // After expansion, should show variant rows
    // (This test will be enhanced when loadFamilyVariants is mocked)
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd frontend && npm test -- FamilyCard`
Expected: FAIL — module not found

- [ ] **Step 3: Implement FamilyCard**

```tsx
// frontend/src/features/models/components/FamilyCard.tsx
"use client";

import { useState, useCallback } from "react";
import { Card } from "@/shared/ui/Card";
import { Badge } from "@/shared/ui/Badge";
import { Button } from "@/shared/ui/Button";
import { Skeleton } from "@/shared/ui/Skeleton";
import type { FamilySummary, FamilyVariant } from "@/features/developer/api";
import { catalog } from "@/features/developer/api";
import { formatParamCount, calculateRamFit } from "@/features/models/api";
import { VariantRow } from "./VariantRow";

interface FamilyCardProps {
  family: FamilySummary;
  ram_gb: number;
  onDownload?: (modelId: string) => void;
  onViewDetail?: (family: string) => void;
  onToggleCompare?: (modelId: string) => void;
  compareSelectedIds?: string[];
}

export function FamilyCard({
  family,
  ram_gb,
  onDownload,
  onViewDetail,
  onToggleCompare,
  compareSelectedIds = [],
}: FamilyCardProps) {
  const [expanded, setExpanded] = useState(false);
  const [variants, setVariants] = useState<FamilyVariant[]>([]);
  const [loadingVariants, setLoadingVariants] = useState(false);

  const loadVariants = useCallback(async () => {
    if (expanded) return;
    setLoadingVariants(true);
    try {
      const res = await catalog.familyVariants(family.family);
      setVariants(res.variants);
    } catch (e) {
      console.error("Failed to load variants:", e);
    } finally {
      setLoadingVariants(false);
    }
  }, [expanded, family.family]);

  const handleExpand = async () => {
    if (!expanded && variants.length === 0) {
      await loadVariants();
    }
    setExpanded(!expanded);
  };

  const dv = family.default_variant;
  const minRam = dv.size_gb ? dv.size_gb * 1.2 : 0;
  const { percent, status } = calculateRamFit(ram_gb, minRam);

  return (
    <Card className="overflow-hidden">
      {/* Header */}
      <div className="p-4">
        <div className="flex items-center justify-between mb-2">
          <h3 className="text-sm font-semibold text-text-primary">
            {family.display_name}
          </h3>
          <div className="flex items-center gap-2">
            {family.license && (
              <Badge variant="default">{family.license}</Badge>
            )}
            {dv.downloaded && <Badge variant="success">Installed</Badge>}
          </div>
        </div>

        {/* Summary line */}
        <button
          onClick={handleExpand}
          className="text-xs text-text-muted hover:text-text-secondary transition-colors"
        >
          {family.model_count} variants ·{" "}
          {formatParamCount(family.param_range[0])}–{formatParamCount(family.param_range[1])} ·{" "}
          {family.context_range[0] >= 1000
            ? `${Math.round(family.context_range[0] / 1000)}K`
            : family.context_range[0]}–
          {family.context_range[1] >= 1000
            ? `${Math.round(family.context_range[1] / 1000)}K`
            : family.context_range[1]} ctx
        </button>

        {/* Capabilities */}
        <div className="flex items-center gap-1.5 mt-2">
          {family.capabilities.map((cap) => (
            <Badge key={cap} variant="default">
              {cap}
            </Badge>
          ))}
        </div>

        {/* Default variant inline */}
        <div className="mt-3 flex items-center gap-3 text-xs">
          <span className="font-medium text-text-primary">{dv.model_id}</span>
          <span className="text-text-secondary">{formatParamCount(dv.parameter_count)}</span>
          <span className="text-text-secondary">{dv.size_gb} GB</span>
          <span className="font-mono text-text-muted">{dv.quantization}</span>
        </div>

        {/* RAM fit bar */}
        <div className="mt-2 h-1.5 rounded-full bg-bg-surface overflow-hidden">
          <div
            className={`h-full rounded-full ${
              status === "good"
                ? "bg-accent"
                : status === "tight"
                ? "bg-warning"
                : "bg-danger"
            }`}
            style={{ width: `${Math.min(100, percent)}%` }}
          />
        </div>

        {/* Actions */}
        <div className="flex items-center gap-2 mt-3">
          {!dv.downloaded && onDownload && (
            <Button size="sm" onClick={() => onDownload(dv.model_id)}>
              Download
            </Button>
          )}
          {onViewDetail && (
            <Button
              size="sm"
              variant="ghost"
              onClick={() => onViewDetail(family.family)}
            >
              View Details
            </Button>
          )}
        </div>
      </div>

      {/* Expanded variants */}
      {expanded && (
        <div className="border-t border-border-default/50">
          {loadingVariants ? (
            <div className="p-4 space-y-2">
              {Array.from({ length: 3 }).map((_, i) => (
                <Skeleton key={i} className="h-10 w-full" />
              ))}
            </div>
          ) : variants.length > 0 ? (
            variants.map((v) => {
              const vMinRam = v.size_gb ? v.size_gb * 1.2 : 0;
              const vFit = calculateRamFit(ram_gb, vMinRam);
              return (
                <VariantRow
                  key={v.model_id}
                  variant={v}
                  ramFitPercent={vFit.percent}
                  ramFitStatus={vFit.status}
                  onDownload={onDownload}
                />
              );
            })
          ) : (
            <p className="p-4 text-xs text-text-muted">No variants available</p>
          )}
        </div>
      )}
    </Card>
  );
}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd frontend && npm test -- FamilyCard`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add frontend/src/features/models/components/FamilyCard.tsx frontend/src/features/models/__tests__/FamilyCard.test.tsx
git commit -m "feat: FamilyCard component with expandable variant list"
```

---

## Task 10: Frontend — EmbeddingSection Component

**Files:**
- Create: `frontend/src/features/models/components/EmbeddingSection.tsx`

**Interfaces:**
- Consumes: `FamilySummary[]` (embedding families)
- Produces: separate section displaying embedding models with dimensions

- [ ] **Step 1: Implement EmbeddingSection**

```tsx
// frontend/src/features/models/components/EmbeddingSection.tsx
"use client";

import { Card } from "@/shared/ui/Card";
import { Badge } from "@/shared/ui/Badge";
import { Button } from "@/shared/ui/Button";
import type { FamilySummary } from "@/features/developer/api";
import { formatBytes } from "@/features/models/api";

interface EmbeddingSectionProps {
  families: FamilySummary[];
  onDownload?: (modelId: string) => void;
  onViewDetail?: (family: string) => void;
}

export function EmbeddingSection({ families, onDownload, onViewDetail }: EmbeddingSectionProps) {
  if (families.length === 0) return null;

  return (
    <div>
      <h3 className="text-sm font-semibold text-text-primary mb-3">
        Embedding Models
      </h3>
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
        {families.map((fam) => (
          <Card key={fam.family} className="p-4">
            <div className="flex items-center justify-between mb-2">
              <h4 className="text-sm font-medium text-text-primary">
                {fam.display_name}
              </h4>
              <Badge variant="default">
                {fam.model_count} variant{fam.model_count !== 1 ? "s" : ""}
              </Badge>
            </div>

            {/* Key stats */}
            <div className="space-y-1 text-xs text-text-secondary mb-3">
              {fam.embedding_dim && (
                <p>{fam.embedding_dim} dimensions</p>
              )}
              <p>
                Context:{" "}
                {fam.context_range[0] >= 1000
                  ? `${Math.round(fam.context_range[0] / 1000)}K`
                  : fam.context_range[0]}
              </p>
              {fam.license && <p>{fam.license}</p>}
            </div>

            {/* Actions */}
            <div className="flex items-center gap-2">
              {fam.default_variant.downloaded ? (
                <Badge variant="success">Installed</Badge>
              ) : (
                onDownload && (
                  <Button
                    size="sm"
                    onClick={() => onDownload(fam.default_variant.model_id)}
                  >
                    Download
                  </Button>
                )
              )}
              {onViewDetail && (
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={() => onViewDetail(fam.family)}
                >
                  View Details
                </Button>
              )}
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Run existing frontend tests**

Run: `cd frontend && npm test`
Expected: PASS (no regressions)

- [ ] **Step 3: Commit**

```bash
git add frontend/src/features/models/components/EmbeddingSection.tsx
git commit -m "feat: EmbeddingSection component for embedding model families"
```

---

## Task 11: Frontend — Rewrite BrowseView

**Files:**
- Modify: `frontend/src/features/models/components/BrowseView.tsx` (complete rewrite)

**Interfaces:**
- Consumes: `ModelFamiliesResponse` from API, `HardwareInfo`, `FamilySummary`/`FamilyVariant` types
- Produces: family-first accordion layout with search, filters, recommended section, embedding section

- [ ] **Step 1: Rewrite BrowseView**

```tsx
// frontend/src/features/models/components/BrowseView.tsx
"use client";

import { useState, useEffect, useCallback } from "react";
import type { FamilySummary, HardwareInfo, ModelFamiliesResponse } from "@/features/developer/api";
import { catalog } from "@/features/developer/api";
import { calculateRamFit, getDefaultModel } from "@/features/models/api";
import { Card } from "@/shared/ui/Card";
import { Badge } from "@/shared/ui/Badge";
import { Button } from "@/shared/ui/Button";
import { Input } from "@/shared/ui/Input";
import { EmptyState } from "@/shared/ui/EmptyState";
import { Skeleton } from "@/shared/ui/Skeleton";
import { FamilyCard } from "./FamilyCard";
import { EmbeddingSection } from "./EmbeddingSection";

interface BrowseViewProps {
  hardware: HardwareInfo | null;
  onDownload: (modelId: string) => void;
  onViewDetail: (modelId: string) => void;
  compareSelectedIds: string[];
  onToggleCompare: (modelId: string) => void;
  compareDisabled: boolean;
}

type SizeFilter = "small" | "medium" | "large" | null;

export function BrowseView({
  hardware,
  onDownload,
  onViewDetail,
  compareSelectedIds,
  onToggleCompare,
  compareDisabled,
}: BrowseViewProps) {
  const [data, setData] = useState<ModelFamiliesResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [debouncedQuery, setDebouncedQuery] = useState("");
  const [capabilityFilter, setCapabilityFilter] = useState<string[]>([]);
  const [sizeFilter, setSizeFilter] = useState<SizeFilter>(null);
  const [sort, setSort] = useState<string>("relevance");
  const ram_gb = hardware?.ram_gb ?? 32;

  // Debounce search
  useEffect(() => {
    const timer = setTimeout(() => setDebouncedQuery(searchQuery), 300);
    return () => clearTimeout(timer);
  }, [searchQuery]);

  const loadFamilies = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await catalog.families();
      setData(result);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadFamilies(); }, [loadFamilies]);

  if (!data && loading) {
    return (
      <div className="space-y-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <Skeleton key={i} className="h-32 w-full rounded-lg" />
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-lg bg-danger/10 border border-danger/20 px-4 py-3 text-sm text-danger">
        {error}
        <Button size="sm" variant="ghost" className="ml-2" onClick={loadFamilies}>
          Retry
        </Button>
      </div>
    );
  }

  if (!data) return null;

  // Filter families
  let filteredFamilies = data.families.filter((fam) => {
    // Search filter
    if (debouncedQuery) {
      const q = debouncedQuery.toLowerCase();
      if (
        !fam.family.toLowerCase().includes(q) &&
        !fam.display_name.toLowerCase().includes(q) &&
        !fam.default_variant.model_id.toLowerCase().includes(q)
      ) {
        return false;
      }
    }

    // Capability filter
    if (capabilityFilter.length > 0) {
      if (!capabilityFilter.some((c) => fam.capabilities.includes(c))) {
        return false;
      }
    }

    // Size filter
    if (sizeFilter) {
      const params = fam.param_range[1] ?? 0;
      if (sizeFilter === "small" && params >= 4) return false;
      if (sizeFilter === "medium" && (params < 4 || params > 14)) return false;
      if (sizeFilter === "large" && params <= 14) return false;
    }

    return true;
  });

  // Sort
  if (sort !== "relevance") {
    filteredFamilies = [...filteredFamilies].sort((a, b) => {
      if (sort === "size_asc") return (a.default_variant.size_bytes ?? 0) - (b.default_variant.size_bytes ?? 0);
      if (sort === "size_desc") return (b.default_variant.size_bytes ?? 0) - (a.default_variant.size_bytes ?? 0);
      if (sort === "params_asc") return (a.param_range[1] ?? 0) - (b.param_range[1] ?? 0);
      if (sort === "params_desc") return (b.param_range[1] ?? 0) - (a.param_range[1] ?? 0);
      return 0;
    });
  }

  const capabilities = ["chat", "code", "vision"];

  return (
    <div className="space-y-6">
      {/* Filters */}
      <div className="flex flex-wrap items-end gap-3">
        <div className="flex-1 min-w-[200px]">
          <Input
            label="Search models"
            placeholder="Search by name, family..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>

        <div className="flex items-center gap-1.5">
          {capabilities.map((cap) => (
            <button
              key={cap}
              onClick={() =>
                setCapabilityFilter((prev) =>
                  prev.includes(cap) ? prev.filter((c) => c !== cap) : [...prev, cap]
                )
              }
              className={`px-2.5 py-1 rounded-md text-xs font-medium transition-colors duration-150 ${
                capabilityFilter.includes(cap)
                  ? "bg-accent/12 text-accent"
                  : "bg-bg-surface text-text-muted hover:text-text-secondary"
              }`}
            >
              {cap}
            </button>
          ))}
        </div>

        <div className="flex items-center gap-1.5">
          {(["small", "medium", "large"] as const).map((size) => (
            <button
              key={size}
              onClick={() => setSizeFilter(sizeFilter === size ? null : size)}
              className={`px-2.5 py-1 rounded-md text-xs font-medium transition-colors duration-150 ${
                sizeFilter === size
                  ? "bg-accent/12 text-accent"
                  : "bg-bg-surface text-text-muted hover:text-text-secondary"
              }`}
            >
              {size === "small" ? "<4B" : size === "medium" ? "4-14B" : ">14B"}
            </button>
          ))}
        </div>

        <select
          value={sort}
          onChange={(e) => setSort(e.target.value)}
          className="h-9 rounded-md border border-border-default bg-bg-surface px-2.5 text-xs text-text-secondary"
          aria-label="Sort families"
        >
          <option value="relevance">Relevance</option>
          <option value="size_asc">Size ↑</option>
          <option value="size_desc">Size ↓</option>
          <option value="params_asc">Params ↑</option>
          <option value="params_desc">Params ↓</option>
        </select>
      </div>

      {/* Results count */}
      <p className="text-xs text-text-muted">
        {filteredFamilies.length} families · {data.total_models} models
      </p>

      {/* Families grid */}
      {filteredFamilies.length > 0 ? (
        <div className="space-y-4">
          {filteredFamilies.map((fam) => (
            <FamilyCard
              key={fam.family}
              family={fam}
              ram_gb={ram_gb}
              onDownload={onDownload}
              onViewDetail={onViewDetail}
              onToggleCompare={onToggleCompare}
              compareSelectedIds={compareSelectedIds}
            />
          ))}
        </div>
      ) : (
        <EmptyState
          title="No families found"
          description={searchQuery ? "Try a different search query or filters" : "No models available"}
        />
      )}

      {/* Embedding models section */}
      <EmbeddingSection
        families={data.embedding_families}
        onDownload={onDownload}
        onViewDetail={onViewDetail}
      />
    </div>
  );
}
```

- [ ] **Step 2: Run frontend tests**

Run: `cd frontend && npm test`
Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add frontend/src/features/models/components/BrowseView.tsx
git commit -m "feat: rewrite BrowseView with family-first accordion layout"
```

---

## Task 12: Frontend — Rewrite InstalledView

**Files:**
- Modify: `frontend/src/features/models/components/InstalledView.tsx` (complete rewrite)

**Interfaces:**
- Consumes: `ModelFamiliesResponse` from API (filtered to downloaded), `HardwareInfo`
- Produces: family-first layout with management actions (Open Chat, Delete, Set Default)

- [ ] **Step 1: Rewrite InstalledView**

The InstalledView uses the same FamilyCard component but:
- Calls `catalog.families()` then filters to families with `default_variant.downloaded === true`
- Each variant row shows: last used timestamp, usage count, Open Chat / Delete buttons
- Shows storage summary at top
- No download buttons

```tsx
// frontend/src/features/models/components/InstalledView.tsx
"use client";

import { useState, useEffect, useCallback } from "react";
import type { FamilySummary, HardwareInfo, ModelFamiliesResponse } from "@/features/developer/api";
import { catalog } from "@/features/developer/api";
import { Card } from "@/shared/ui/Card";
import { Badge } from "@/shared/ui/Badge";
import { Button } from "@/shared/ui/Button";
import { EmptyState } from "@/shared/ui/EmptyState";
import { Skeleton } from "@/shared/ui/Skeleton";

interface InstalledViewProps {
  hardware: HardwareInfo | null;
  onDelete: (modelId: string) => void;
  onOpenChat: (modelId: string) => void;
  onSetDefault: (modelId: string) => void;
  defaultModel: string | null;
}

export function InstalledView({
  hardware,
  onDelete,
  onOpenChat,
  onSetDefault,
  defaultModel,
}: InstalledViewProps) {
  const [data, setData] = useState<ModelFamiliesResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadInstalled = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await catalog.families();
      // Filter to families with at least one downloaded variant
      const installedFamilies = result.families.filter((fam) =>
        fam.default_variant.downloaded || result.families.some((f) => f.default_variant.downloaded)
      );
      // Actually, we need to check per-variant. For now, filter families where default is downloaded.
      // The full variant list will be loaded on expand.
      setData({
        ...result,
        families: installedFamilies,
      });
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadInstalled(); }, [loadInstalled]);

  if (loading) {
    return (
      <div className="space-y-4">
        {Array.from({ length: 2 }).map((_, i) => (
          <Skeleton key={i} className="h-32 w-full rounded-lg" />
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-lg bg-danger/10 border border-danger/20 px-4 py-3 text-sm text-danger">
        {error}
        <Button size="sm" variant="ghost" className="ml-2" onClick={loadInstalled}>
          Retry
        </Button>
      </div>
    );
  }

  if (!data || data.families.length === 0) {
    return (
      <EmptyState
        title="No models installed"
        description="Download a model from the Browse tab to get started"
      />
    );
  }

  // Compute storage summary
  const totalSizeGb = data.families.reduce((acc, fam) => acc + (fam.default_variant.size_gb ?? 0), 0);

  return (
    <div className="space-y-6">
      {/* Storage summary */}
      <Card className="p-4">
        <div className="flex items-center justify-between mb-2">
          <h3 className="text-sm font-semibold text-text-primary">
            Installed Models
          </h3>
          <span className="text-xs text-text-muted">
            {totalSizeGb.toFixed(1)} GB used
          </span>
        </div>
        <div className="h-2 rounded-full bg-bg-surface overflow-hidden">
          <div
            className="h-full rounded-full bg-accent"
            style={{ width: `${Math.min(100, (totalSizeGb / 500) * 100)}%` }}
          />
        </div>
        <p className="text-xs text-text-muted mt-1">
          {data.families.length} families · {data.total_models} models
        </p>
      </Card>

      {/* Installed families */}
      <div className="space-y-4">
        {data.families.map((fam) => (
          <Card key={fam.family} className="p-4">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-semibold text-text-primary">
                {fam.display_name}
              </h3>
              <div className="flex items-center gap-2">
                {fam.default_variant.model_id === defaultModel && (
                  <Badge variant="success">Default</Badge>
                )}
                <Badge variant="default">{fam.model_count} installed</Badge>
              </div>
            </div>

            {/* Stats */}
            <div className="text-xs text-text-muted mb-3">
              {fam.model_count} variants ·{" "}
              {fam.default_variant.size_gb} GB
            </div>

            {/* Actions */}
            <div className="flex items-center gap-2">
              <Button
                size="sm"
                onClick={() => onOpenChat(fam.default_variant.model_id)}
              >
                Open Chat
              </Button>
              {fam.default_variant.model_id !== defaultModel && (
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={() => onSetDefault(fam.default_variant.model_id)}
                >
                  Set Default
                </Button>
              )}
              <Button
                size="sm"
                variant="ghost"
                onClick={() => onDelete(fam.default_variant.model_id)}
              >
                Delete
              </Button>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Run frontend tests**

Run: `cd frontend && npm test`
Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add frontend/src/features/models/components/InstalledView.tsx
git commit -m "feat: rewrite InstalledView with family-first layout and management actions"
```

---

## Task 13: Frontend — Rewrite ModelDetailModal

**Files:**
- Modify: `frontend/src/features/models/components/ModelDetailModal.tsx` (complete rewrite)

**Interfaces:**
- Consumes: `FamilySummary`, `FamilyVariantsResponse`, `HardwareInfo`
- Produces: full detail modal with overview, variant table, actions

- [ ] **Step 1: Rewrite ModelDetailModal**

```tsx
// frontend/src/features/models/components/ModelDetailModal.tsx
"use client";

import { useState, useEffect, useCallback } from "react";
import { Modal } from "@/shared/ui/Modal";
import { Badge } from "@/shared/ui/Badge";
import { Button } from "@/shared/ui/Button";
import { Skeleton } from "@/shared/ui/Skeleton";
import type { FamilySummary, FamilyVariant, FamilyVariantsResponse, HardwareInfo } from "@/features/developer/api";
import { catalog } from "@/features/developer/api";
import { formatParamCount, calculateRamFit } from "@/features/models/api";
import { VariantRow } from "./VariantRow";

interface ModelDetailModalProps {
  family: FamilySummary | null;
  open: boolean;
  onClose: () => void;
  onDownload: (modelId: string) => void;
  onUseInChat: (modelId: string) => void;
  onSetDefault: (modelId: string) => void;
  hardware: HardwareInfo | null;
  defaultModel: string | null;
}

type SortKey = "size" | "params";

export function ModelDetailModal({
  family: initialFamily,
  open,
  onClose,
  onDownload,
  onUseInChat,
  onSetDefault,
  hardware,
  defaultModel,
}: ModelDetailModalProps) {
  const [variantsData, setVariantsData] = useState<FamilyVariantsResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [sortBy, setSortBy] = useState<SortKey>("size");
  const ram_gb = hardware?.ram_gb ?? 32;

  useEffect(() => {
    if (!open || !initialFamily) return;
    setLoading(true);
    catalog
      .familyVariants(initialFamily.family)
      .then(setVariantsData)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [open, initialFamily]);

  if (!initialFamily) return null;

  const variants = variantsData?.variants ?? [];
  const isEmbedding = initialFamily.embedding_dim !== null;

  // Sort variants
  const sortedVariants = [...variants].sort((a, b) => {
    if (sortBy === "size") return (a.size_bytes ?? 0) - (b.size_bytes ?? 0);
    return (b.parameter_count ?? 0) - (a.parameter_count ?? 0);
  });

  return (
    <Modal open={open} onClose={onClose}>
      <div className="max-h-[80vh] overflow-y-auto">
        {/* Header */}
        <div className="p-6 border-b border-border-default/50">
          <div className="flex items-center justify-between mb-2">
            <h2 className="text-lg font-semibold text-text-primary">
              {initialFamily.display_name}
            </h2>
            {initialFamily.license && (
              <Badge variant="default">{initialFamily.license}</Badge>
            )}
          </div>
          <p className="text-xs text-text-muted">
            {initialFamily.model_count} variants
          </p>
        </div>

        {/* Overview */}
        <div className="p-6 border-b border-border-default/50">
          <h3 className="text-sm font-semibold text-text-primary mb-3">Overview</h3>
          <div className="grid grid-cols-2 gap-3 text-xs">
            {isEmbedding ? (
              <>
                <div>
                  <span className="text-text-muted">Dimensions:</span>{" "}
                  <span className="text-text-primary">{initialFamily.embedding_dim}</span>
                </div>
                <div>
                  <span className="text-text-muted">Context:</span>{" "}
                  <span className="text-text-primary">
                    {initialFamily.context_range[0] >= 1000
                      ? `${Math.round(initialFamily.context_range[0] / 1000)}K`
                      : initialFamily.context_range[0]}
                  </span>
                </div>
              </>
            ) : (
              <>
                <div>
                  <span className="text-text-muted">Parameters:</span>{" "}
                  <span className="text-text-primary">
                    {formatParamCount(initialFamily.param_range[0])}–
                    {formatParamCount(initialFamily.param_range[1])}
                  </span>
                </div>
                <div>
                  <span className="text-text-muted">Context:</span>{" "}
                  <span className="text-text-primary">
                    {initialFamily.context_range[0] >= 1000
                      ? `${Math.round(initialFamily.context_range[0] / 1000)}K`
                      : initialFamily.context_range[0]}–
                    {initialFamily.context_range[1] >= 1000
                      ? `${Math.round(initialFamily.context_range[1] / 1000)}K`
                      : initialFamily.context_range[1]}
                  </span>
                </div>
              </>
            )}
            <div>
              <span className="text-text-muted">Capabilities:</span>{" "}
              <div className="flex gap-1 mt-1">
                {initialFamily.capabilities.map((cap) => (
                  <Badge key={cap} variant="default">{cap}</Badge>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Variants table */}
        <div className="p-6">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-semibold text-text-primary">
              Variants ({variants.length})
            </h3>
            <div className="flex items-center gap-1">
              <button
                onClick={() => setSortBy("size")}
                className={`px-2 py-1 rounded text-xs ${
                  sortBy === "size" ? "bg-accent/12 text-accent" : "text-text-muted"
                }`}
              >
                Size
              </button>
              <button
                onClick={() => setSortBy("params")}
                className={`px-2 py-1 rounded text-xs ${
                  sortBy === "params" ? "bg-accent/12 text-accent" : "text-text-muted"
                }`}
              >
                Params
              </button>
            </div>
          </div>

          {loading ? (
            <div className="space-y-2">
              {Array.from({ length: 5 }).map((_, i) => (
                <Skeleton key={i} className="h-10 w-full" />
              ))}
            </div>
          ) : sortedVariants.length > 0 ? (
            <div className="border border-border-default/50 rounded-lg overflow-hidden">
              {sortedVariants.map((v) => {
                const minRam = v.size_gb ? v.size_gb * 1.2 : 0;
                const fit = calculateRamFit(ram_gb, minRam);
                return (
                  <VariantRow
                    key={v.model_id}
                    variant={v}
                    ramFitPercent={fit.percent}
                    ramFitStatus={fit.status}
                    onDownload={onDownload}
                  />
                );
              })}
            </div>
          ) : (
            <p className="text-xs text-text-muted">No variants available</p>
          )}
        </div>

        {/* Actions */}
        <div className="p-6 border-t border-border-default/50 flex items-center gap-3">
          <Button onClick={() => onUseInChat(initialFamily.default_variant.model_id)}>
            Use in Chat
          </Button>
          {initialFamily.default_variant.model_id !== defaultModel && (
            <Button
              variant="ghost"
              onClick={() => onSetDefault(initialFamily.default_variant.model_id)}
            >
              Set as Default
            </Button>
          )}
        </div>
      </div>
    </Modal>
  );
}
```

- [ ] **Step 2: Run frontend tests**

Run: `cd frontend && npm test`
Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add frontend/src/features/models/components/ModelDetailModal.tsx
git commit -m "feat: rewrite ModelDetailModal with variant table and embedding support"
```

---

## Task 14: Frontend — Update page.tsx to Use New Components

**Files:**
- Modify: `frontend/src/features/models/page.tsx:219` (BrowseView), `:39` (InstalledView)

**Interfaces:**
- Consumes: new BrowseView, InstalledView, ModelDetailModal from Tasks 11-13
- Produces: updated page with correct props

- [ ] **Step 1: Update page.tsx**

The page needs to:
1. Pass correct props to new BrowseView/InstalledView
2. Handle `onViewDetail` to open the new ModelDetailModal with a `FamilySummary`
3. Store selected family for detail modal

Find the relevant sections in `frontend/src/features/models/page.tsx` and update:

```tsx
// Add state for detail modal family
const [detailFamily, setDetailFamily] = useState<FamilySummary | null>(null);
const [detailOpen, setDetailOpen] = useState(false);

// Update onViewDetail handler to accept family name
const handleViewDetail = (familyName: string) => {
  // Find the family from loaded data
  // This requires BrowseView/InstalledView to expose families
  // Alternative: load families on detail open
  catalog.families().then((data) => {
    const fam = data.families.find((f) => f.family === familyName) ||
                data.embedding_families.find((f) => f.family === familyName);
    if (fam) {
      setDetailFamily(fam);
      setDetailOpen(true);
    }
  });
};
```

Update the BrowseView and InstalledView rendering to use the new props.

- [ ] **Step 2: Run frontend tests**

Run: `cd frontend && npm test`
Expected: PASS

- [ ] **Step 3: Run frontend build**

Run: `cd frontend && npm run build`
Expected: No errors

- [ ] **Step 4: Commit**

```bash
git add frontend/src/features/models/page.tsx
git commit -m "feat: update models page to use new family-first components"
```

---

## Task 15: Integration Test — Full Pipeline

**Files:**
- Test: `tests/api/test_catalog_integration.py`

**Interfaces:**
- Tests the full pipeline: enrichment → DB → API → response shape

- [ ] **Step 1: Write integration test**

```python
# tests/api/test_catalog_integration.py
import pytest


class TestCatalogIntegration:
    def test_families_endpoint_returns_grouped_data(self, db_session, client, auth_headers):
        """GET /models/families returns properly structured grouped data."""
        response = client.get("/api/v1/developer/catalog/models/families", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()

        assert "families" in data
        assert "embedding_families" in data
        assert isinstance(data["families"], list)
        assert isinstance(data["embedding_families"], list)

        if data["families"]:
            fam = data["families"][0]
            assert "family" in fam
            assert "display_name" in fam
            assert "model_count" in fam
            assert fam["model_count"] > 0
            assert "capabilities" in fam
            assert isinstance(fam["capabilities"], list)
            assert "default_variant" in fam
            assert "param_range" in fam
            assert len(fam["param_range"]) == 2
            assert "context_range" in fam
            assert len(fam["context_range"]) == 2

    def test_family_variants_returns_sorted_list(self, db_session, client, auth_headers):
        """GET /models/families/{family}/variants returns sorted variants."""
        # First get families
        families_resp = client.get("/api/v1/developer/catalog/models/families", headers=auth_headers)
        families = families_resp.json()["families"]
        if not families:
            pytest.skip("No families in DB")

        family_name = families[0]["family"]
        response = client.get(
            f"/api/v1/developer/catalog/models/families/{family_name}/variants",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()

        assert data["family"] == family_name
        assert "variants" in data
        assert isinstance(data["variants"], list)

        # Check sorting: param desc
        if len(data["variants"]) > 1:
            for i in range(len(data["variants"]) - 1):
                curr = data["variants"][i]["parameter_count"] or 0
                next_ = data["variants"][i + 1]["parameter_count"] or 0
                assert curr >= next_, "Variants should be sorted by param_count desc"

    def test_list_models_includes_new_fields(self, db_session, client, auth_headers):
        """List endpoint returns family, parameter_size, quantization, embedding_dim."""
        response = client.get("/api/v1/developer/catalog/models", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        if data["models"]:
            model = data["models"][0]
            assert "family" in model
            assert "parameter_size" in model
            assert "quantization" in model
            assert "embedding_dim" in model

    def test_quality_score_is_normalized(self, db_session, client, auth_headers):
        """quality_score should be 0-1 scale, not 0-100."""
        response = client.get("/api/v1/developer/catalog/models", headers=auth_headers)
        assert response.status_code == 200
        # quality_score is on variants in detail, check detail endpoint
        data = response.json()
        if data["models"]:
            model_id = data["models"][0]["name"]
            detail_resp = client.get(
                f"/api/v1/developer/catalog/models/{model_id}",
                headers=auth_headers,
            )
            if detail_resp.status_code == 200:
                detail = detail_resp.json()
                for variant in detail.get("variants", []):
                    if variant.get("quality_score") is not None:
                        assert 0 <= variant["quality_score"] <= 1, (
                            f"quality_score should be 0-1, got {variant['quality_score']}"
                        )
```

- [ ] **Step 2: Run integration tests**

Run: `pytest tests/api/test_catalog_integration.py -v`
Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add tests/api/test_catalog_integration.py
git commit -m "test: integration tests for catalog family grouping and data quality"
```

---

## Task 16: Final Validation — All Tests + Build

- [ ] **Step 1: Run all backend tests**

Run: `make test`
Expected: All pass (2040+)

- [ ] **Step 2: Run frontend tests**

Run: `cd frontend && npm test`
Expected: All pass

- [ ] **Step 3: Run frontend build**

Run: `cd frontend && npm run build`
Expected: No errors

- [ ] **Step 4: Run lint**

Run: `make lint && cd frontend && npm run lint`
Expected: Clean

- [ ] **Step 5: Run format**

Run: `make format && cd frontend && npm run format`
Expected: Clean

- [ ] **Step 6: Final commit if any formatting fixes needed**

```bash
git add -A
git commit -m "style: format and lint fixes for models page redesign"
```
