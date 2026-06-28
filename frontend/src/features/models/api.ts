/**
 * Models API Client — merges catalog + downloads + adds page-specific types
 *
 * Backend routes: /api/v1/models/* (catalog + downloads)
 */
export { catalog } from "@/features/developer/api";
export { downloads, sync } from "@/features/integration/api";
export type {
  ModelCatalogEntry,
  ModelVariantEntry,
  HardwareInfo,
  ModelComparison,
  RecommendedModel,
} from "@/features/developer/api";
export type {
  InstalledModel,
  DownloadJob,
  DownloadHistoryItem,
} from "@/features/integration/api";

// ── Page-specific types ────────────────────────────────────────────────────

export type RamFitStatus = "good" | "tight" | "insufficient";

export interface ModelWithFit {
  model_id: string;
  display_name: string;
  provider: string;
  parameter_count: number | null;
  size_bytes: number | null;
  context_length: number | null;
  capabilities: string[];
  description: string;
  downloaded: boolean;
  variants: {
    variant_id: string;
    quantization: string;
    size_bytes: number | null;
    size_gb: number | null;
    downloaded: boolean;
    quality_score: number | null;
  }[];
  hardware_requirements: { min_ram_gb: number; recommended_ram_gb: number } | null;
  ramFitPercent: number;
  ramFitStatus: RamFitStatus;
  isDefault: boolean;
}

export type TabKey = "browse" | "compare" | "downloads" | "installed";

export interface DownloadProgress {
  model: string;
  progress: number;
  speed_bytes_sec: number | null;
  eta_seconds: number | null;
}

// ── Helpers ────────────────────────────────────────────────────────────────

const STORAGE_KEY = "cortex_default_model";

export function getDefaultModel(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(STORAGE_KEY);
}

export function setDefaultModel(modelId: string): void {
  localStorage.setItem(STORAGE_KEY, modelId);
}

export function calculateRamFit(
  ramGb: number,
  minRamNeeded: number | null,
): { percent: number; status: RamFitStatus } {
  if (!minRamNeeded || minRamNeeded <= 0) return { percent: 100, status: "good" };
  const percent = Math.min(100, Math.round((ramGb / minRamNeeded) * 100));
  const status: RamFitStatus = percent >= 100 ? "good" : percent >= 50 ? "tight" : "insufficient";
  return { percent, status };
}

export function formatBytes(bytes: number): string {
  if (bytes === 0) return "0 B";
  const k = 1024;
  const sizes = ["B", "KB", "MB", "GB", "TB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${(bytes / Math.pow(k, i)).toFixed(1)} ${sizes[i]}`;
}

export function formatSpeed(bytesPerSec: number): string {
  if (bytesPerSec <= 0) return "—";
  return `${(bytesPerSec / (1024 * 1024)).toFixed(1)} MB/s`;
}

export function formatEta(seconds: number | null): string {
  if (seconds === null || seconds <= 0) return "—";
  if (seconds < 60) return `${Math.round(seconds)}s remaining`;
  const mins = Math.floor(seconds / 60);
  const secs = Math.round(seconds % 60);
  return `${mins}m ${secs}s remaining`;
}

export function formatParamCount(count: number | null): string {
  if (count === null) return "Unknown";
  if (count >= 1_000_000_000) return `${(count / 1_000_000_000).toFixed(1)}B`;
  if (count >= 1_000_000) return `${(count / 1_000_000).toFixed(0)}M`;
  return `${count}`;
}
