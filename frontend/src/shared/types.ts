/** Shared TypeScript types for the Cortex frontend. */

// ── User ──────────────────────────────────────────────────────────

export interface User {
  id: number;
  username: string | null;
  full_name: string;
  role: "user" | "admin";
  nickname: string;
  bio: string | null;
  description: string | null;
  profile_photo: string | null;
  handles: Record<string, unknown> | null;
  storage_root: string | null;
  github_username: string | null;
  data_path?: string | null;
  personal_storage_path?: string | null;
  preferences: Record<string, unknown> | null;
  created_at?: string | null;
  updated_at?: string | null;
  programming_languages?: string[];
  frameworks?: string[];
  current_projects?: { name: string; description?: string }[];
  contribution_style?: string | null;
  social_links?: { twitter?: string; linkedin?: string; website?: string };
}

// ── Auth ──────────────────────────────────────────────────────────

export interface TokenResponse {
  access_token: string;
  token_type: string;
  refresh_token?: string | null;
  user?: User | null;
}

export interface UsernameCheckResponse {
  available: boolean;
  message: string;
}

// ── Profile ───────────────────────────────────────────────────────

export interface ProfileUpdate {
  full_name?: string;
  nickname?: string;
  bio?: string;
  description?: string;
  programming_languages?: string[];
  frameworks?: string[];
  current_projects?: { name: string; description: string }[];
  contribution_style?: string;
  social_links?: { twitter?: string; linkedin?: string; website?: string };
  preferences?: Record<string, unknown>;
}

// ── GitHub ────────────────────────────────────────────────────────

export interface GitHubStatus {
  connected: boolean;
  github_username: string | null;
}

// ── Vault ─────────────────────────────────────────────────────────

export interface VaultStatus {
  locked: boolean;
  has_vault_password: boolean;
}

export interface VaultFileEntry {
  name: string;
  path: string;
  is_dir: boolean;
  size: number;
  modified?: number;
  created?: number;
  favorite?: boolean;
  tags?: string[];
}

export interface VaultUploadResult {
  name: string;
  path: string;
  size: number;
}

export interface VaultSearchResult {
  name: string;
  path: string;
  is_dir: boolean;
  score: number;
}

export interface VaultSearchResponse {
  results: VaultSearchResult[];
}

// ── Knowledge ─────────────────────────────────────────────────────

export interface KnowledgeHealth {
  status: string;
  documents_indexed: number;
  total_chunks: number;
  graph_nodes: number;
  graph_edges: number;
  repos_indexed: number;
  code_chunks: number;
}

export interface KnowledgeStats {
  documents_by_type: Record<string, number>;
  chunks_by_language: Record<string, number>;
  avg_chunks_per_document: number;
  graph_edge_types: Record<string, number>;
}

// ── Memory ────────────────────────────────────────────────────────

export interface MemoryEntry {
  id: number;
  user_id: number | null;
  category: string;
  title: string;
  content: string;
  source_path: string | null;
  tags: string[];
  embedding_id: string | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface MemorySearchResult {
  score: number;
  entry: MemoryEntry | null;
}

export interface MemoryListResponse {
  count: number;
  total?: number;
  offset?: number;
  limit?: number;
  categories: Record<string, number>;
  entries: MemoryEntry[];
}

export interface MemorySearchResponse {
  query: string;
  results: MemorySearchResult[];
}

// ── Long-Term Memory ────────────────────────────────────────────

export interface LongTermMemory {
  id: number;
  category: "preference" | "pattern" | "correction" | "fact" | "context";
  title: string;
  content: string;
  confidence: number;
  access_count: number;
  source: string | null;
  created_at: string | null;
}

export interface MemoryStats {
  total: number;
  active: number;
  by_category: Record<string, number>;
  avg_confidence: number;
}

// ── System ──────────────────────────────────────────────────────

export interface SystemProcess {
  pid: number;
  name: string;
  cpu: number;
  memory: number;
  status: string;
}

export interface SystemMetrics {
  cpu_percent: number;
  ram_total_gb: number;
  ram_used_gb: number;
  ram_percent: number;
  gpu_name: string;
  gpu_type: string;
  gpu_percent: number | null;
  disk_total_gb: number;
  disk_used_gb: number;
  disk_percent: number;
  processes: SystemProcess[];
}

export interface SystemLog {
  timestamp: string;
  level: string;
  logger: string;
  message: string;
  request_id: string;
  module: string;
  pathname: string;
  lineno: number;
}

export interface SystemLogsResponse {
  logs: SystemLog[];
  total: number;
}

// ── Notifications ───────────────────────────────────────────────

export interface Notification {
  id: number;
  user_id: number;
  type: string;
  title: string;
  message: string;
  read: boolean;
  created_at: string | null;
}

export interface NotificationListResponse {
  notifications: Notification[];
  total: number;
  unread_count: number;
}

// ── Search ─────────────────────────────────────────────────────

export interface SearchResult {
  content: string;
  source: string;
  score: number;
  file_path: string;
  document_id: number;
  language: string;
  chunk_type: string;
}

export interface SearchResponse {
  query: string;
  total: number;
  results: SearchResult[];
}

export interface SearchAnswerResponse {
  query: string;
  answer: string;
  results: SearchResult[];
}

// ── Repository ────────────────────────────────────────────────

export interface Repository {
  id: number;
  user_id: number | null;
  repo_path: string;
  repo_name: string;
  primary_language: string | null;
  total_files: number;
  total_chunks: number;
  last_indexed_at: string | null;
  status: string;
  created_at: string | null;
  updated_at: string | null;
}

export interface RepoListResponse {
  repos: Repository[];
}

export interface RepoStatus {
  repo_id: number;
  status: string;
  total_files: number;
  total_chunks: number;
  indexed_files: number;
  indexed: number;
  pending: number;
  errors: number;
  last_indexed_at: string | null;
}

export interface IndexResult {
  status: string;
  files_scanned: number;
  files_indexed: number;
  files_skipped: number;
  chunks_created: number;
}

// ── Graph ─────────────────────────────────────────────────────

export interface GraphNode {
  id: number;
  name: string;
  node_type: string;
  file_path: string;
  language: string | null;
  qualified_name?: string | null;
  start_line?: number | null;
  end_line?: number | null;
}

export interface GraphEdge {
  id: number;
  source_id: number;
  target_id: number;
  edge_type: string;
  weight: number;
}

export interface GraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export interface NodeContext {
  node: GraphNode;
  calls: { id: number; name: string; file_path: string }[];
  called_by: { id: number; name: string; file_path: string }[];
  imports: { id: number; name: string; file_path: string }[];
  imported_by: { id: number; name: string; file_path: string }[];
  inherits: { id: number; name: string; file_path: string }[];
  contains: { id: number; name: string; node_type: string }[];
}

// ── Agents ─────────────────────────────────────────────────────

export interface Agent {
  id: number;
  name: string;
  description: string | null;
  system_prompt: string;
  model_id: string;
  tools: string[];
  is_active: boolean;
  created_at: string | null;
  updated_at: string | null;
}

export interface AgentRun {
  id: number;
  agent_id: number;
  user_id: number;
  input: string;
  status: "pending" | "running" | "completed" | "failed";
  output: string | null;
  error: string | null;
  created_at: string | null;
  completed_at: string | null;
}

export interface AgentStep {
  id: number;
  run_id: number;
  step_number: number;
  thought: string | null;
  action: string;
  action_input: Record<string, unknown> | null;
  observation: string | null;
  status: string;
  created_at: string | null;
}

export interface AgentFeedback {
  id: number;
  rating: number;
  comment: string | null;
  created_at: string | null;
}

export interface AgentListResponse {
  agents: Agent[];
}

export interface RunListResponse {
  runs: AgentRun[];
}

export interface RunDetailResponse {
  run: AgentRun;
  steps: AgentStep[];
}

// ── Models ────────────────────────────────────────────────────────

export interface ModelInfo {
  model_id: string;
  name: string;
  display_name: string;
  description: string;
  provider: string;
  model_type: "chat" | "code" | "vision" | "embedding";
  parameter_count: string;
  context_length: number;
  capabilities: string[];
  hardware_requirements: {
    min_ram_gb: number;
    recommended_ram_gb: number;
    min_vram_gb: number;
    recommended_vram_gb: number;
  } | null;
  recommended?: boolean;
  downloaded?: boolean;
  size_bytes?: number;
  variants?: string[];
  family: string;
  architecture: string;
  license: string;
}

export interface HardwareInfo {
  ram_gb: number;
  ram_available_gb: number;
  ram_percent: number;
  cpu_count: number;
  cpu_threads: number;
  cpu_freq_mhz: number;
  cpu_arch: string;
  gpu: {
    available: boolean;
    name: string | null;
    type: string;
    vram_gb: number;
    vram_available_gb: number;
    memory_bandwidth_gbps: number | null;
    compute_capability: string | null;
    arch: string | null;
  };
  disk_free_gb: number;
  supports_cuda: boolean;
  supports_metal: boolean;
}

export interface ModelListResponse {
  models: ModelInfo[];
  total_count: number;
  downloaded_count: number;
  available_from_providers: { name: string; size_bytes: number; context_length: number; capabilities: string[] }[];
  type_counts: Record<string, number>;
  size_counts: Record<string, number>;
}

export interface RecommendedModelsResponse {
  hardware: HardwareInfo;
  recommended: ModelInfo[];
}

export interface DownloadProgressResponse {
  model: string;
  progress: number;
}

export interface DownloadResult {
  status: string;
  model: string;
  variant: string | null;
  download_id: string | null;
}

// ── Enhanced Models ──────────────────────────────────────────────

export interface HardwareProfile {
  ram_gb: number;
  ram_available_gb: number;
  ram_percent: number;
  cpu_count: number;
  cpu_threads: number;
  cpu_freq_mhz: number;
  cpu_arch: string;
  gpu: {
    available: boolean;
    name: string | null;
    type: string;
    vram_gb: number;
    vram_available_gb: number;
    memory_bandwidth_gbps: number | null;
    compute_capability: string | null;
    arch: string | null;
  };
  disk_free_gb: number;
  supports_cuda: boolean;
  supports_metal: boolean;
}

export interface PerformanceEstimate {
  tokens_per_second: number | null;
  prompt_eval_tps: number | null;
  memory_usage_gb: number;
  vram_usage_gb: number;
  quantization_quality: string;
  quality_notes: string;
  speed_rating: string;
  fit_rating: string;
  context_length_max: number;
}

export interface ModelRecommendation {
  model_id: string;
  display_name: string;
  family: string;
  parameter_count: string;
  capabilities: string[];
  description: string;
  score: number;
  variant: {
    quantization: string;
    size_gb: number;
    vram_required_gb: number;
    quality_score: number;
  } | null;
  performance: PerformanceEstimate | null;
  explanation: {
    why: string;
    tradeoff: string;
    suitability: string;
  } | null;
}

export interface WorkloadRecommendations {
  label: string;
  description: string;
  recommendations: ModelRecommendation[];
}

export interface RecommendedModelsResponseEnhanced {
  hardware: HardwareProfile;
  workloads: Record<string, WorkloadRecommendations>;
}

export interface DownloadJob {
  job_id: string;
  model_id: string;
  status: "queued" | "downloading" | "completed" | "failed" | "cancelled" | "paused";
  progress: number;
  speed_bytes_sec: number | null;
  downloaded_bytes: number;
  total_bytes: number;
  eta_seconds: number | null;
  queue_position: number | null;
  error: string | null;
}

export interface DownloadQueueResponse {
  active: DownloadJob[];
  queued: DownloadJob[];
  completed: DownloadJob[];
  failed: DownloadJob[];
}

export interface StorageUsage {
  total_disk_gb: number;
  used_disk_gb: number;
  free_disk_gb: number;
  models_total_gb: number;
  models: ModelStorageEntry[];
  cache_gb: number;
}

export interface ModelStorageEntry {
  model_id: string;
  variant_id: string;
  size_gb: number;
  last_used: string | null;
  usage_count: number;
}

export interface ModelCatalogEntry {
  id: number;
  model_id: string;
  family: string;
  display_name: string;
  provider: string;
  parameter_count: number;
  architecture: string | null;
  context_length_default: number;
  context_length_max: number | null;
  capabilities: string[];
  license: string | null;
  recommended_use_cases: string[];
  description: string;
  tags: string[];
  variants: ModelVariantInfo[];
}

export interface ModelVariantInfo {
  id: number;
  variant_id: string;
  quantization: string;
  quantization_level: string;
  parameter_count: number;
  size_bytes: number;
  size_gb: number;
  vram_required_gb: number;
  ram_required_gb: number;
  quality_score: number;
  downloaded: boolean;
  ollama_tag: string | null;
}

// ── Model Search / Comparison / Sync ───────────────────────

export interface ModelSearchResult {
  models: ModelInfo[];
  total_count: number;
}

export interface DimensionComparison {
  dimension: string;
  display_name: string;
  values: Record<string, number>;
  winner: string;
  higher_is_better: boolean;
}

export interface ModelComparisonResult {
  winner_model: string;
  dimension_wins: Record<string, string>;
  dimensions: DimensionComparison[];
  summary: string;
}

export interface ModelUsageStats {
  total_requests: number;
  avg_latency: number;
  total_tokens: number;
}

export interface DeleteModelResponse {
  status: string;
  model: string;
}

export interface SyncJob {
  id: number;
  sync_type: string;
  status: string;
  models_discovered: number;
  models_added: number;
  models_updated: number;
  error_message: string | null;
  started_at: string | null;
  completed_at: string | null;
  created_at: string | null;
}

// ── Model Settings ───────────────────────────────────────────

export interface ModelSettings {
  inference_backend: string;
  huggingface_token: string | null;
  auto_download: boolean;
  max_concurrent_downloads: number;
}

export type UserSettings = ModelSettings;

export interface ModelUpdate {
  model_id: string;
  display_name: string;
  installed_version: string | null;
  available_version: string | null;
  update_type: string;
}

export interface ModelUpdatesResponse {
  updates: ModelUpdate[];
}

// ── Indexing Config ───────────────────────────────────────────

export interface IndexingConfig {
  id: number;
  name: string;
  include_paths: string[];
  exclude_paths: string[];
  include_patterns: string[];
  exclude_patterns: string[];
  max_file_size_bytes: number;
  follow_symlinks: boolean;
  sync_enabled: boolean;
  sync_interval_seconds: number;
  priority: number;
}

export interface IndexingConfigPayload {
  name?: string;
  include_paths?: string[];
  exclude_paths?: string[];
  include_patterns?: string[];
  exclude_patterns?: string[];
  max_file_size_bytes?: number;
  follow_symlinks?: boolean;
  sync_enabled?: boolean;
  sync_interval_seconds?: number;
  priority?: number;
}

export interface IndexingPreview {
  total_files: number;
  will_index: number;
  excluded_by_directory: number;
  excluded_by_pattern: number;
  excluded_by_size: number;
}

export interface IndexingStatus {
  watching_count: number;
  pending_changes: number;
  indexed_files: number;
  errors: number;
  watched_paths: string[];
}

// ── Conversations ──────────────────────────────────────────────────

export interface Conversation {
  id: number;
  title: string;
  repo_id: number | null;
  model_used: string | null;
  message_count: number;
  total_tokens: number;
  created_at: string | null;
  updated_at: string | null;
}

export interface ConversationMessage {
  id: number;
  role: "system" | "user" | "assistant";
  content: string;
  tokens: number;
  created_at: string | null;
}

export interface ConversationDetail extends Conversation {
  messages: ConversationMessage[];
}
