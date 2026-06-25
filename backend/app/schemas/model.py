"""Model endpoint schemas."""

from __future__ import annotations

from pydantic import BaseModel


class ModelProviderInfo(BaseModel):
    name: str
    size_bytes: int
    context_length: int
    capabilities: list[str]


class ModelCatalogEntry(BaseModel):
    name: str
    display_name: str
    provider: str
    model_type: str
    parameter_count: float | None = None
    size_bytes: int | None = None
    context_length: int | None = None
    capabilities: list[str]
    description: str
    downloaded: bool
    variants: list[str] = []
    hardware_requirements: dict


class CatalogSourceStatusResponse(BaseModel):
    cloud: str = "pending"
    local: str = "pending"
    registry: str = "pending"
    last_updated: str = ""
    from_fallback: bool = False
    errors: dict[str, str] = {}


class ModelListResponse(BaseModel):
    models: list[ModelCatalogEntry]
    total_count: int
    downloaded_count: int
    available_from_providers: list[ModelProviderInfo]
    type_counts: dict[str, int] = {}
    size_counts: dict[str, int] = {}
    catalog_status: CatalogSourceStatusResponse | None = None


class RecommendationVariant(BaseModel):
    quantization: str | None = None
    size_gb: float | None = None
    vram_required_gb: float | None = None
    quality_score: float | None = None


class RecommendationPerformance(BaseModel):
    tokens_per_second: float | None = None
    prompt_eval_tps: float | None = None
    memory_usage_gb: float | None = None
    vram_usage_gb: float | None = None
    quantization_quality: str | None = None
    quality_notes: str | None = None
    speed_rating: str | None = None
    fit_rating: str | None = None
    context_length_max: int | None = None


class RecommendationExplanation(BaseModel):
    why: str | None = None
    tradeoff: str | None = None
    suitability: str | None = None


class ModelRecommendation(BaseModel):
    model_id: str
    display_name: str
    family: str
    parameter_count: float | None = None
    capabilities: list[str]
    description: str | None = None
    score: float
    variant: RecommendationVariant | None = None
    performance: RecommendationPerformance | None = None
    explanation: RecommendationExplanation | None = None


class WorkloadRecommendations(BaseModel):
    label: str
    description: str
    recommendations: list[ModelRecommendation]


class RecommendedModelsSingleResponse(BaseModel):
    hardware: dict
    workload: str
    recommendations: list[ModelRecommendation]


class RecommendedModelsAllResponse(BaseModel):
    hardware: dict
    workloads: dict[str, WorkloadRecommendations]


class HardwareInfoResponse(BaseModel):
    ram_gb: float = 0.0
    ram_available_gb: float = 0.0
    ram_percent: float = 0.0
    cpu_count: int = 0
    cpu_threads: int = 0
    cpu_freq_mhz: float = 0.0
    cpu_arch: str = ""
    gpu: dict = {}
    disk_free_gb: float = 0.0
    supports_cuda: bool = False
    supports_metal: bool = False


class LLMHealthResponse(BaseModel):
    status: str = "unknown"
    latency_ms: float = 0.0
    error: str | None = None


class LLMMetricsResponse(BaseModel):
    total_requests: int = 0
    total_tokens: int = 0
    avg_latency: float = 0.0


class UsageStatsResponse(BaseModel):
    total_requests: int = 0
    avg_latency: float = 0.0
    total_tokens: int = 0


class DownloadModelResponse(BaseModel):
    status: str
    model: str
    variant: str | None = None
    download_id: str | None = None


class DownloadProgressResponse(BaseModel):
    model: str
    progress: float


class DownloadJobInfo(BaseModel):
    job_id: str
    model_id: str
    status: str
    progress: float
    speed_bytes_sec: float | None = None
    downloaded_bytes: int
    total_bytes: int
    eta_seconds: float | None = None
    queue_position: int | None = None
    error: str | None = None


class DownloadQueueResponse(BaseModel):
    active: list[DownloadJobInfo]
    queued: list[DownloadJobInfo]
    completed: list[DownloadJobInfo]
    failed: list[DownloadJobInfo]


class DownloadHistoryItem(BaseModel):
    job_id: str
    model_id: str
    status: str
    progress: float
    downloaded_bytes: int
    total_bytes: int
    error: str | None = None
    completed_at: float | None = None
    created_at: float | None = None


class DownloadHistoryResponse(BaseModel):
    history: list[DownloadHistoryItem]


class CancelDownloadResponse(BaseModel):
    cancelled: bool


class DeleteModelResponse(BaseModel):
    status: str
    model: str


class InstalledVariant(BaseModel):
    variant_id: str
    quantization: str
    size_bytes: int
    size_gb: float
    downloaded: bool
    parameter_count: float | None = None
    quality_score: float = 90.0


class InstalledModel(BaseModel):
    model_id: str
    display_name: str
    family: str
    parameter_count: float | None = None
    capabilities: list[str]
    variants: list[InstalledVariant]


class InstalledModelsResponse(BaseModel):
    models: list[InstalledModel]
    installed_count: int


class SyncInstalledResponse(BaseModel):
    """Response for Ollama model sync."""

    matched: int = 0
    created: int = 0
    deleted: int = 0
    errors: list[str] = []


class ModelSearchResult(BaseModel):
    model_id: str
    display_name: str
    family: str
    provider: str
    parameter_count: float | None = None
    architecture: str | None = None
    context_length: int | None = None
    capabilities: list[str]
    description: str | None = None
    tags: list[str]


class ModelSearchResponse(BaseModel):
    models: list[ModelSearchResult]
    total_count: int


class ModelVariantInfo(BaseModel):
    variant_id: str
    quantization: str
    quantization_level: str | None = None
    parameter_count: float | None = None
    size_bytes: int | None = None
    size_gb: float | None = None
    vram_required_gb: float | None = None
    quality_score: float | None = None
    downloaded: bool | None = None
    ollama_tag: str | None = None


class ModelDetailResponse(BaseModel):
    model_id: str
    display_name: str
    family: str
    parameter_count: float | None = None
    architecture: str | None = None
    context_length_default: int | None = None
    context_length_max: int | None = None
    capabilities: list[str]
    license: str | None = None
    recommended_use_cases: list[str]
    description: str | None = None
    tags: list[str]
    benchmarks: dict | None = None
    variants: list[ModelVariantInfo]


class CatalogueRefreshResponse(BaseModel):
    status: str
    models_added: int


class ModelUpdate(BaseModel):
    model_id: str
    display_name: str
    installed_version: str | None = None
    available_version: str | None = None
    update_type: str  # "version", "tag", "new"


class ModelUpdatesResponse(BaseModel):
    updates: list[ModelUpdate]


class StorageUsageResponse(BaseModel):
    total_disk_gb: float
    used_disk_gb: float
    free_disk_gb: float
    models_total_gb: float
    models: list[dict]
    cache_gb: float


class SyncTriggerResponse(BaseModel):
    job_id: str
    status: str
    models_discovered: int
    models_added: int
    models_updated: int
    error_message: str | None = None


class SyncStatusListResponse(BaseModel):
    jobs: list[dict]


class AutocompleteResponse(BaseModel):
    suggestions: list[str]


class DimensionComparisonResponse(BaseModel):
    dimension: str
    display_name: str
    values: dict[str, float]
    winner: str
    higher_is_better: bool


class ModelComparisonResponse(BaseModel):
    winner_model: str
    dimension_wins: dict[str, str]
    dimensions: list[DimensionComparisonResponse]
    summary: str


class ModelSettingsResponse(BaseModel):
    inference_backend: str = "auto"
    huggingface_token: str | None = None
    auto_download: bool = True
    max_concurrent_downloads: int = 2


class ModelSettingsUpdate(BaseModel):
    inference_backend: str | None = None
    huggingface_token: str | None = None
    auto_download: bool | None = None
    max_concurrent_downloads: int | None = None


class InferenceConfigResponse(BaseModel):
    model_id: str
    context_length: int | None = None
    temperature: float = 0.7
    top_p: float = 0.9
    top_k: int = 40
    repeat_penalty: float = 1.1
    seed: int = -1
    num_predict: int = 2048
    num_ctx: int | None = None
    image_resolution: int | None = None
