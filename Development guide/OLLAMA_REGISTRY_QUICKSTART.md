# Ollama Model Registry - Quick Start Guide

## For Users

### 1. Access the Model Discovery Interface

Navigate to: `http://localhost:3000/models/discover` (or your Cortex domain)

### 2. Explore Models Tab

**Search for a model**:
- Type in the search box (e.g., "llama", "mistral", "code")
- Results appear instantly as you type
- Models ranked by relevance

**Filter by capabilities**:
- Click capability tags to filter: chat, coding, vision, etc
- Mix and match multiple filters
- Or filter by size: small (<10B), medium (10-50B), large (>50B)

**View model details**:
- Click a model card to see full metadata
- See description, capabilities, parameters, quantization
- Verify it's what you need

### 3. Pull (Download) a Model

1. Click **[Pull Model]** button on any card
2. Download starts in background
3. See progress bar with percentage
4. Button becomes [Installed] when done
5. Model is now available locally in Ollama

### 4. View Installed Models

- Click **Installed** tab
- See all downloaded models
- Know which models are ready to use

### 5. Get Recommendations

- Click **Recommended** tab
- Select a task: chat, coding, vision, reasoning, fast, embedding
- See models ranked best for that task
- Pull recommended models

## For Developers

### Backend Integration

#### Check if Model Exists in Registry
```python
from backend.app.services.ollama_registry import OllamaRegistryService
from sqlalchemy.orm import Session

def get_model(db: Session, model_id: str):
    model = OllamaRegistryService.get_model(db, model_id)
    if not model:
        raise ValueError(f"Model {model_id} not found")
    return model
```

#### Get Models by Capability
```python
chat_models = OllamaRegistryService.list_by_capability(db, "coding")
for model in chat_models:
    print(f"{model['display_name']}: {model['model_id']}")
```

#### Get Recommendations for Task
```python
# Backend side
models = OllamaRegistryService.search_models(
    db,
    query="",
    capability="coding",
    size="small",  # Fast models preferred
    limit=5
)
```

#### Trigger Model Download
```python
from backend.app.services.ollama_registry import OllamaDownloadService

# Start download
progress_id = await OllamaDownloadService.start_download(db, "llama3")

# Background task will execute: ollama pull llama3
# Frontend can poll: GET /registry/downloads/{progress_id}
```

### Frontend Integration

#### Use the Registry Hook
```typescript
import { useOllamaRegistry } from '@/hooks/useOllamaRegistry';

function MyComponent() {
  const registry = useOllamaRegistry();
  
  // Get all models
  const { data } = registry.useAllModels();
  
  // Search models
  const { data: searchResults } = registry.useSearchModels("chat", "chat");
  
  // Get installed
  const { data: installed } = registry.useInstalledModels();
  
  // Pull model
  const pullMutation = registry.usePullModel();
  const handlePull = async (modelId) => {
    const result = await pullMutation.mutateAsync(modelId);
    // result.progress_id can be used to track progress
  };
  
  return (
    // Your UI
  );
}
```

#### Track Download Progress
```typescript
const { data: progress } = useDownloadProgress(progressId);

// progress.status: "queued" | "downloading" | "extracting" | "complete" | "failed"
// progress.progress_percent: 0-100
// progress.error_message: Error if failed
```

#### Get Task Recommendations
```typescript
const { data } = useRecommendations("coding");
// Returns models best for coding task, sorted by relevance
```

## API Endpoints Reference

### Discovery
```
GET /api/v1/registry/models
Get all models with full metadata

GET /api/v1/registry/models/search?q=llama&capability=chat&size=small
Search and filter models

GET /api/v1/registry/models/by-capability/chat
Get models with specific capability

GET /api/v1/registry/recommendations?task=coding
Get recommended models for task
```

### Management
```
GET /api/v1/registry/models/installed
Get locally installed models only

GET /api/v1/registry/models/{model_id}
Get single model details

POST /api/v1/registry/models/{model_id}/pull
Start downloading a model
Returns: { progress_id: int }

GET /api/v1/registry/downloads/{progress_id}
Check download progress
```

### Admin
```
GET /api/v1/registry/sync?force_refresh=false
Sync Ollama library
force_refresh=true: Ignore cache, re-scrape
```

## Common Scenarios

### Scenario 1: User Wants to Chat with AI

1. Go to Cortex Chat → Models dropdown is empty
2. Click "Browse Models" → Redirects to /models/discover
3. On **Recommended** tab, select task "chat"
4. See recommended chat models: llama3, mistral, neural-chat, etc
5. Click [Pull Model] on "Llama 3"
6. Wait for download to complete
7. Go back to Chat → Model dropdown now shows "llama3"
8. Start chatting

### Scenario 2: Developer Wants Code Generation

1. Visit /models/discover → **Explore Models**
2. Click [coding] capability filter
3. Click [small] size (for fast inference)
4. See: deepseek-coder, codeqwen, dolphin-mixtral
5. Pull "deepseek-coder"
6. Use in backend: `model = ModelRegistry.get_model(db, "deepseek-coder")`
7. Execute coding task with selected model

### Scenario 3: Admin Syncs Registry

1. Click [Sync] button
2. System fetches ollama.com/library (if cache stale)
3. Scrapes model metadata
4. Updates database
5. Frontend refreshes with latest models
6. Users see 47 available models

### Scenario 4: Check Model Status

```bash
# See all installed models
curl http://localhost:8000/api/v1/registry/models/installed

# Get specific model details
curl http://localhost:8000/api/v1/registry/models/llama3

# Search with filters
curl "http://localhost:8000/api/v1/registry/models/search?q=code&size=small"

# Get recommendations
curl "http://localhost:8000/api/v1/registry/recommendations?task=reasoning"
```

## Database Schema Overview

### ollama_registry_models
Stores all available models from Ollama library

Key columns:
- `model_id` (unique): "llama3", "mistral", etc
- `family`: "llama", "mistral", etc
- `capabilities` (JSON): ["chat", "reasoning"]
- `is_installed` (bool): Locally available?
- `last_synced_at`: Cache freshness

Query examples:
```sql
-- All installed models
SELECT * FROM ollama_registry_models WHERE is_installed = true;

-- All chat models
SELECT * FROM ollama_registry_models 
WHERE capabilities LIKE '%"chat"%';

-- Models by size
SELECT * FROM ollama_registry_models 
WHERE parameters LIKE '7B';

-- Most recently synced
SELECT * FROM ollama_registry_models 
ORDER BY last_synced_at DESC LIMIT 10;
```

### ollama_download_progress
Tracks active and recent downloads

Key columns:
- `model_id`: Which model
- `status`: "queued" → "downloading" → "extracting" → "complete"
- `progress_percent`: 0-100
- `error_message`: Failure reason

Query examples:
```sql
-- Active downloads
SELECT * FROM ollama_download_progress 
WHERE status NOT IN ('complete', 'failed');

-- Failed downloads (to debug)
SELECT * FROM ollama_download_progress 
WHERE status = 'failed';

-- Download history
SELECT * FROM ollama_download_progress 
ORDER BY completed_at DESC LIMIT 20;
```

## Troubleshooting

### Models Not Showing in UI

**Problem**: Visit /models/discover, see empty list

**Solutions**:
1. Run sync: Click [Sync] button at top
2. Check database: `SELECT COUNT(*) FROM ollama_registry_models;`
3. Check logs: Look for "Scraped X models from Ollama library"
4. Verify network: Is ollama.com/library reachable?

### Can't Pull Model

**Problem**: Click [Pull Model], nothing happens

**Solutions**:
1. Check Ollama installed: `ollama --version`
2. Check Ollama running: `ollama list`
3. Check disk space: `df -h`
4. Check logs for error_message: `SELECT error_message FROM ollama_download_progress`

### Wrong Model Metadata

**Problem**: Model description or parameters are incorrect

**Solutions**:
1. Force sync: `GET /registry/sync?force_refresh=true`
2. Wait 24h for cache to expire automatically
3. Report issue: ollama.com/library might have changed

### Slow Search

**Problem**: Search takes >1 second

**Solutions**:
1. Check database indexes: `PRAGMA index_list(ollama_registry_models);`
2. Check model count: `SELECT COUNT(*) FROM ollama_registry_models;`
3. If >10k models, consider pagination

## Advanced Usage

### Custom Model Tags

After pulling a model manually via CLI, mark it as installed:
```bash
curl -X POST http://localhost:8000/api/v1/registry/models/llama3/mark-installed
```

### Search with Multiple Filters

```bash
# Chat models, small size, with reasoning capability
curl "http://localhost:8000/api/v1/registry/models/search?q=chat&capability=reasoning&size=small"
```

### Monitor Download Progress

```bash
# Start download
RESULT=$(curl -X POST http://localhost:8000/api/v1/registry/models/llama3/pull)
PROGRESS_ID=$(echo $RESULT | jq .progress_id)

# Poll progress every second
while true; do
  curl http://localhost:8000/api/v1/registry/downloads/$PROGRESS_ID | jq '.progress'
  sleep 1
done
```

### Export Model Catalog

```bash
# Get all models as JSON
curl http://localhost:8000/api/v1/registry/models | jq '.models' > models.json

# Get capabilities breakdown
curl http://localhost:8000/api/v1/registry/models/by-capability/chat | jq '.total'
```

## Performance Tips

1. **First Load**: Click [Sync] to populate database (one-time cost)
2. **Search**: Start typing after 2-3 characters (debounced)
3. **Download**: Large models (70B) can take 10-30 minutes
4. **Caching**: Searches cached for 5 minutes, installed models for 1 minute
5. **Browser Cache**: Clear if UI doesn't update after model pull

## Next Steps

- Read [OLLAMA_REGISTRY.md](OLLAMA_REGISTRY.md) for technical details
- Check API docs at: /docs (FastAPI auto-docs)
- Explore [ModelDiscoveryPage.tsx](../frontend/src/pages/ModelDiscoveryPage.tsx) source code
- Review [ollama_registry.py](../backend/app/services/ollama_registry.py) service implementation
