"use client";

import { useEffect, useState, useMemo, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { motion } from "framer-motion";
import {
  ChevronRight,
  Download,
  ArrowLeftRight,
  ExternalLink,
  Cpu,
  HardDrive,
  Zap,
  MemoryStick,
  Gauge,
  Shield,
  Check,
  AlertTriangle,
  X,
  Star,
} from "lucide-react";
import DashboardShell from "@/shared/layout/DashboardShell";
import NeuralNetwork from "@/shared/ui/NeuralNetwork";
import Card from "@/shared/ui/Card";
import Badge from "@/shared/ui/Badge";
import Button from "@/shared/ui/Button";
import Skeleton from "@/shared/ui/Skeleton";
import { modelsApi } from "@/shared/api";
import { useAuth } from "@/shared/auth/AuthProvider";
import { useLiveMetrics } from "@/shared/hooks/useLiveMetrics";
import type { ModelCatalogEntry, HardwareProfile, ModelVariantInfo } from "@/shared/types";

/* ── Helpers ── */

function getFitRating(vramRequired: number, vramAvailable: number) {
  if (vramAvailable <= 0) return { level: "unknown", label: "Unknown", color: "text-text-muted", icon: null };
  const ratio = vramRequired / vramAvailable;
  if (ratio <= 0.6) return { level: "excellent", label: "Excellent", color: "text-success", icon: Check };
  if (ratio <= 0.85) return { level: "good", label: "Good", color: "text-cyan-400", icon: Check };
  if (ratio <= 1.0) return { level: "usable", label: "Usable", color: "text-warning", icon: AlertTriangle };
  return { level: "oversized", label: "Oversized", color: "text-error", icon: X };
}

function estimateTps(sizeGb: number, bandwidthGbps: number | null): number {
  if (!bandwidthGbps || bandwidthGbps <= 0) return 0;
  return Math.round(bandwidthGbps / (2 * sizeGb));
}

function estimatePromptTps(sizeGb: number, bandwidthGbps: number | null): number {
  if (!bandwidthGbps || bandwidthGbps <= 0) return 0;
  return Math.round((bandwidthGbps / (2 * sizeGb)) * 2);
}

function getPerfColor(percent: number): string {
  if (percent >= 70) return "bg-success";
  if (percent >= 40) return "bg-cyan-400";
  if (percent >= 20) return "bg-warning";
  return "bg-error";
}

function getPerfTextColor(percent: number): string {
  if (percent >= 70) return "text-success";
  if (percent >= 40) return "text-cyan-400";
  if (percent >= 20) return "text-warning";
  return "text-error";
}

function formatSize(bytes: number): string {
  const gb = bytes / (1024 ** 3);
  if (gb >= 1) return `${gb.toFixed(1)}GB`;
  const mb = bytes / (1024 ** 2);
  return `${mb.toFixed(0)}MB`;
}

/* ── Performance Bar ── */

function PerfBar({ value, max, label }: { value: number; max: number; label: string }) {
  const percent = max > 0 ? Math.min((value / max) * 100, 100) : 0;
  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between">
        <span className="text-xs text-text-secondary">{label}</span>
        <span className="text-xs font-mono text-text">{value}</span>
      </div>
      <div className="h-1.5 rounded-full bg-bg-surface overflow-hidden">
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${percent}%` }}
          transition={{ duration: 0.8, ease: "easeOut", delay: 0.2 }}
          className={`h-full rounded-full ${getPerfColor(percent)}`}
        />
      </div>
    </div>
  );
}

/* ── Hardware Check Row ── */

function HardwareCheck({ label, available, required, unit }: {
  label: string;
  available: number;
  required: number;
  unit: string;
}) {
  const fits = available >= required;
  return (
    <div className="flex items-center justify-between py-2">
      <span className="text-xs text-text-secondary">{label} ({available}{unit})</span>
      <div className="flex items-center gap-1.5">
        {fits ? (
          <Check size={12} className="text-success" />
        ) : (
          <X size={12} className="text-error" />
        )}
        <span className={`text-xs font-medium ${fits ? "text-success" : "text-error"}`}>
          {fits ? "Fits" : "Insufficient"}
        </span>
      </div>
    </div>
  );
}

/* ── Benchmark Card ── */

function BenchmarkCard({ score, name }: { score: number; name: string }) {
  return (
    <div className="flex flex-col items-center p-3 rounded-xl bg-bg-surface border border-border-subtle">
      <span className="text-lg font-bold font-mono text-text">{score.toFixed(1)}</span>
      <span className="text-[10px] text-text-muted mt-0.5">{name}</span>
    </div>
  );
}

/* ── Variant Row ── */

function VariantRow({
  variant,
  isRecommended,
  hardware,
  downloading,
  onDownload,
}: {
  variant: ModelVariantInfo;
  isRecommended: boolean;
  hardware: HardwareProfile | null;
  downloading: boolean;
  onDownload: (quantization: string) => void;
}) {
  const vramAvailable = hardware?.gpu?.vram_available_gb ?? 0;
  const fit = getFitRating(variant.vram_required_gb, vramAvailable);
  const tps = estimateTps(variant.size_gb, hardware?.gpu?.memory_bandwidth_gbps ?? null);
  const qualityPercent = Math.round(variant.quality_score * 100);

  const FitIcon = fit.icon;

  return (
    <tr className={`border-b border-border-subtle transition-colors ${isRecommended ? "bg-accent/5" : "hover:bg-bg-hover/50"}`}>
      <td className="px-4 py-3">
        <div className="flex items-center gap-2">
          <span className="text-sm font-mono text-text">{variant.quantization}</span>
          {isRecommended && (
            <Badge variant="accent" className="text-[9px]">
              <Star size={8} className="mr-0.5" /> REC
            </Badge>
          )}
        </div>
      </td>
      <td className="px-4 py-3 text-sm font-mono text-text-secondary">{variant.size_gb.toFixed(1)}GB</td>
      <td className="px-4 py-3 text-sm font-mono text-text-secondary">{variant.vram_required_gb.toFixed(1)}GB</td>
      <td className="px-4 py-3">
        <span className="text-sm font-mono text-text">{qualityPercent}%</span>
      </td>
      <td className="px-4 py-3">
        <div className="flex items-center gap-1.5">
          {FitIcon && <FitIcon size={12} className={fit.color} />}
          <span className={`text-xs font-medium ${fit.color}`}>{fit.label}</span>
        </div>
      </td>
      <td className="px-4 py-3">
        <span className="text-sm font-mono text-text-secondary">~{tps || "—"}</span>
      </td>
      <td className="px-4 py-3">
        <Button
          variant={variant.downloaded ? "secondary" : "primary"}
          size="sm"
          onClick={() => onDownload(variant.quantization)}
          disabled={downloading || variant.downloaded}
          loading={downloading}
        >
          {variant.downloaded ? "Installed" : <><Download size={12} /> Download</>}
        </Button>
      </td>
    </tr>
  );
}

/* ── Loading Skeleton ── */

function ModelDetailSkeleton() {
  return (
    <DashboardShell>
      <NeuralNetwork intensity="low" />
      <div className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 py-8 space-y-8">
        <div className="space-y-2">
          <Skeleton className="h-4 w-32" />
          <div className="flex items-center gap-4">
            <Skeleton className="h-14 w-14 rounded-xl" />
            <div className="space-y-2">
              <Skeleton className="h-7 w-64" />
              <Skeleton className="h-4 w-48" />
            </div>
          </div>
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-4">
            <Skeleton className="h-64 rounded-xl" />
            <Skeleton className="h-40 rounded-xl" />
          </div>
          <div className="space-y-4">
            <Skeleton className="h-48 rounded-xl" />
            <Skeleton className="h-32 rounded-xl" />
          </div>
        </div>
      </div>
    </DashboardShell>
  );
}

/* ── Main Component ── */

export default function ModelDetailPage() {
  const params = useParams();
  const router = useRouter();
  const { user, loading: authLoading } = useAuth();
  const id = params.id as string;

  const [model, setModel] = useState<ModelCatalogEntry | null>(null);
  const [hardware, setHardware] = useState<HardwareProfile | null>(null);
  const liveMetrics = useLiveMetrics();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [downloadingVariant, setDownloadingVariant] = useState<string | null>(null);

  useEffect(() => {
    if (!authLoading && !user) router.replace("/auth");
  }, [user, authLoading, router]);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [modelData, hardwareData] = await Promise.all([
        modelsApi.getModelDetail(id),
        modelsApi.hardware(),
      ]);
      setModel(modelData);
      setHardware(hardwareData);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load model details");
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    if (user) fetchData();
  }, [user, fetchData]);

  const handleDownload = async (quantization: string) => {
    if (!model) return;
    setDownloadingVariant(quantization);
    try {
      await modelsApi.download(model.model_id, quantization);
      setModel((prev) =>
        prev
          ? {
              ...prev,
              variants: prev.variants.map((v) =>
                v.quantization === quantization ? { ...v, downloaded: true } : v
              ),
            }
          : prev
      );
    } catch (err) {
      console.error("Download failed:", err);
    } finally {
      setDownloadingVariant(null);
    }
  };

  const recommendedVariant = useMemo(() => {
    if (!model?.variants?.length || !hardware) return null;
    const vramAvail = hardware.gpu?.vram_available_gb ?? 0;
    const candidates = model.variants
      .filter((v) => v.vram_required_gb <= vramAvail)
      .sort((a, b) => b.quality_score - a.quality_score);
    return candidates[0] ?? null;
  }, [model, hardware]);

  if (authLoading || loading) return <ModelDetailSkeleton />;
  if (!model) return null;

  const vramAvail = liveMetrics?.gpu_percent != null && hardware?.gpu?.vram_gb
    ? hardware.gpu.vram_gb * (1 - liveMetrics.gpu_percent / 100)
    : hardware?.gpu?.vram_available_gb ?? 0;
  const bandwidth = hardware?.gpu?.memory_bandwidth_gbps ?? null;
  const recVariant = recommendedVariant;
  const recTps = recVariant ? estimateTps(recVariant.size_gb, bandwidth) : 0;
  const recPromptTps = recVariant ? estimatePromptTps(recVariant.size_gb, bandwidth) : 0;
  const recVramPercent = recVariant && vramAvail > 0 ? Math.min((recVariant.vram_required_gb / vramAvail) * 100, 100) : 0;
  const contextLength = model.context_length_max ?? model.context_length_default;
  const contextPercent = contextLength > 0 ? Math.min((contextLength / 131072) * 100, 100) : 0;

  const tags = [
    model.architecture,
    model.family,
    model.license,
    ...(model.capabilities?.slice(0, 3) || []),
  ].filter(Boolean);

  const benchmarks = model.benchmarks ?? [];

  return (
    <DashboardShell>
      <NeuralNetwork intensity="low" />
      <div className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 py-8">
        {/* Breadcrumb */}
        <motion.nav
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.3 }}
          className="flex items-center gap-1.5 text-xs text-text-muted mb-6"
        >
          <Link href="/models" className="hover:text-accent transition-colors">
            Models
          </Link>
          <ChevronRight size={12} />
          <span className="text-text-secondary">{model.display_name}</span>
        </motion.nav>

        {/* Hero Section */}
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, ease: "easeOut" }}
          className="mb-8"
        >
          <div className="flex items-start gap-4 mb-4">
            <div className="w-14 h-14 rounded-xl bg-accent/10 flex items-center justify-center shrink-0">
              <Cpu size={28} className="text-accent" />
            </div>
            <div className="flex-1 min-w-0">
              <h1 className="text-2xl font-semibold text-text mb-1">{model.display_name}</h1>
              <p className="text-sm text-text-secondary">
                by {model.provider} · {model.parameter_count}B params · {model.license}
              </p>
            </div>
          </div>
          <p className="text-sm text-text-secondary leading-relaxed mb-4 max-w-3xl">
            {model.description}
          </p>
          <div className="flex flex-wrap gap-2 mb-5">
            {tags.map((tag) => (
              <Badge key={tag} variant="default">
                {tag}
              </Badge>
            ))}
          </div>
          <div className="flex flex-wrap items-center gap-3">
            {recVariant && (
              <Button
                variant="primary"
                size="md"
                onClick={() => handleDownload(recVariant.quantization)}
                disabled={downloadingVariant === recVariant.quantization || recVariant.downloaded}
                loading={downloadingVariant === recVariant.quantization}
              >
                {recVariant.downloaded ? "Installed" : (
                  <>
                    <Download size={14} />
                    Download {recVariant.quantization} ({recVariant.size_gb.toFixed(1)}GB)
                  </>
                )}
              </Button>
            )}
            <Button variant="secondary" size="md" onClick={() => {
              try {
                const compareIds: string[] = JSON.parse(sessionStorage.getItem('compareModels') || '[]');
                if (!compareIds.includes(model.model_id)) {
                  compareIds.push(model.model_id);
                  sessionStorage.setItem('compareModels', JSON.stringify(compareIds.slice(-3)));
                }
                router.push('/models/compare');
              } catch {
                sessionStorage.setItem('compareModels', JSON.stringify([model.model_id]));
                router.push('/models/compare');
              }
            }}>
              <ArrowLeftRight size={14} />
              Add to Compare
            </Button>
            <a
              href={`https://huggingface.co/models/${model.model_id}`}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center justify-center gap-2 h-10 px-4 text-sm font-medium rounded-xl text-text-secondary hover:text-text hover:bg-bg-hover active:scale-[0.97] transition-all duration-200"
            >
              View on Provider <ExternalLink size={12} />
            </a>
          </div>
        </motion.div>

        {/* Content Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column — Variant Table + Specs */}
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.1 }}
            className="lg:col-span-2 space-y-6"
          >
            {/* Variant Table */}
            <Card className="overflow-hidden" gradient>
              <div className="px-5 py-4 border-b border-border-subtle">
                <h2 className="text-sm font-semibold text-text">Variants</h2>
                <p className="text-xs text-text-muted mt-0.5">Choose a quantization level for your hardware</p>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-border-subtle bg-bg-surface/50">
                      <th className="px-4 py-2.5 text-left text-[10px] font-mono uppercase tracking-wider text-text-muted">Quantization</th>
                      <th className="px-4 py-2.5 text-left text-[10px] font-mono uppercase tracking-wider text-text-muted">Size</th>
                      <th className="px-4 py-2.5 text-left text-[10px] font-mono uppercase tracking-wider text-text-muted">VRAM</th>
                      <th className="px-4 py-2.5 text-left text-[10px] font-mono uppercase tracking-wider text-text-muted">Quality</th>
                      <th className="px-4 py-2.5 text-left text-[10px] font-mono uppercase tracking-wider text-text-muted">Fit</th>
                      <th className="px-4 py-2.5 text-left text-[10px] font-mono uppercase tracking-wider text-text-muted">TPS</th>
                      <th className="px-4 py-2.5 text-left text-[10px] font-mono uppercase tracking-wider text-text-muted">Action</th>
                    </tr>
                  </thead>
                  <tbody>
                    {model.variants?.map((v) => (
                      <VariantRow
                        key={v.variant_id}
                        variant={v}
                        isRecommended={recVariant?.variant_id === v.variant_id}
                        hardware={hardware}
                        downloading={downloadingVariant === v.quantization}
                        onDownload={handleDownload}
                      />
                    ))}
                  </tbody>
                </table>
              </div>
            </Card>

            {/* Model Specs Grid */}
            <Card className="p-5" gradient>
              <h2 className="text-sm font-semibold text-text mb-4">Specifications</h2>
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
                {[
                  { label: "Parameters", value: `${model.parameter_count}B` },
                  { label: "Architecture", value: model.architecture },
                  { label: "Context Length", value: contextLength.toLocaleString() },
                  { label: "Training Data", value: "5.5T tokens" },
                  { label: "License", value: model.license },
                  { label: "Family", value: model.family },
                ].map((spec) => (
                  <div key={spec.label} className="space-y-1">
                    <span className="text-[10px] font-mono uppercase tracking-wider text-text-muted">{spec.label}</span>
                    <p className="text-sm font-medium text-text">{spec.value}</p>
                  </div>
                ))}
              </div>
            </Card>
          </motion.div>

          {/* Right Column — Sidebar */}
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.2 }}
            className="space-y-6"
          >
            {/* Performance on Your Hardware */}
            <Card className="p-5" gradient>
              <div className="flex items-center gap-2 mb-4">
                <Gauge size={14} className="text-accent" />
                <h2 className="text-sm font-semibold text-text">Performance on Your Hardware</h2>
              </div>
              {hardware ? (
                <div className="space-y-4">
                  <PerfBar value={recTps} max={80} label="Generation Speed" />
                  <PerfBar value={recPromptTps} max={160} label="Prompt Processing" />
                  <PerfBar value={recVariant?.vram_required_gb ?? 0} max={vramAvail} label="VRAM Usage" />
                  <PerfBar value={contextLength} max={131072} label="Max Context" />
                  <p className="text-[10px] text-text-muted mt-2">
                    Estimated for {hardware.gpu?.name || "CPU only"} · {vramAvail}GB VRAM
                  </p>
                </div>
              ) : (
                <p className="text-xs text-text-muted">Hardware info unavailable</p>
              )}
            </Card>

            {/* Hardware Compatibility */}
            <Card className="p-5" gradient>
              <div className="flex items-center gap-2 mb-3">
                <HardDrive size={14} className="text-accent" />
                <h2 className="text-sm font-semibold text-text">Hardware Compatibility</h2>
              </div>
              {hardware ? (
                <div className="divide-y divide-border-subtle">
                  <HardwareCheck
                    label="GPU VRAM"
                    available={vramAvail}
                    required={recVariant?.vram_required_gb ?? 0}
                    unit="GB"
                  />
                  <HardwareCheck
                    label="System RAM"
                    available={hardware.ram_available_gb}
                    required={recVariant?.vram_required_gb ? recVariant.vram_required_gb * 1.2 : 0}
                    unit="GB"
                  />
                  <HardwareCheck
                    label="Disk Space"
                    available={hardware.disk_free_gb}
                    required={recVariant?.size_gb ?? 0}
                    unit="GB"
                  />
                  <HardwareCheck
                    label="CUDA Support"
                    available={hardware.supports_cuda ? 1 : 0}
                    required={1}
                    unit=""
                  />
                  <HardwareCheck
                    label="Backend"
                    available={1}
                    required={1}
                    unit=""
                  />
                </div>
              ) : (
                <p className="text-xs text-text-muted">Hardware info unavailable</p>
              )}
            </Card>

            {/* Benchmarks */}
            <Card className="p-5" gradient>
              <div className="flex items-center gap-2 mb-4">
                <Zap size={14} className="text-accent" />
                <h2 className="text-sm font-semibold text-text">Benchmarks</h2>
              </div>
              <div className="grid grid-cols-2 gap-3">
                {benchmarks.map((b) => (
                  <BenchmarkCard key={b.name} score={b.score} name={b.name} />
                ))}
              </div>
            </Card>

            {/* About Quantization */}
            <Card className="p-5" gradient>
              <div className="flex items-center gap-2 mb-3">
                <MemoryStick size={14} className="text-accent" />
                <h2 className="text-sm font-semibold text-text">About Quantization</h2>
              </div>
              <p className="text-xs text-text-secondary leading-relaxed">
                Q4_K_M is a balanced quantization that uses 4-bit precision with k-quant methodology.
                It provides an excellent balance between model size reduction and output quality,
                making it ideal for consumer GPUs with limited VRAM. Quality loss is minimal for
                most tasks compared to full precision.
              </p>
            </Card>
          </motion.div>
        </div>
      </div>
    </DashboardShell>
  );
}
