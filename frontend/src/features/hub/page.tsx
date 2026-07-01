"use client";

import { useCallback, useEffect, useState } from "react";
import { useAuth } from "@/shared/auth/AuthProvider";
import { useRouter } from "next/navigation";
import { HubWidget } from "@/shared/layout/HubWidget";
import { HubGreeting } from "@/shared/layout/HubGreeting";
import { NeuralParticles } from "@/shared/layout/NeuralParticles";
import { CommandBar } from "@/shared/layout/CommandBar";
import {
  ChatIcon, SearchIcon, BrainIcon, VaultIcon, ModelsIcon,
  CodeIcon, UtilityIcon, SettingsIcon, SystemsIcon, ProfileIcon,
  LightningIcon,
} from "@/shared/ui/icons";
import { cn } from "@/shared/lib/utils";

// ── Types ─────────────────────────────────────────────────────────────
interface HealthData {
  status: string;
  version: string;
  services?: Record<string, string>;
}

interface ModelCatalog {
  active_model?: string;
  models?: Array<{ name: string }>;
}

interface BrainStats {
  total_chunks?: number;
  indexed_files?: number;
  knowledge_graph_nodes?: number;
}

interface VaultStatus {
  locked?: boolean;
  file_count?: number;
}

// ── Widget configuration ──────────────────────────────────────────────
interface WidgetConfig {
  id: string;
  icon: React.ReactNode;
  label: string;
  glowColor: "red" | "cyan";
  /** API endpoint to fetch preview data (returns JSON) */
  fetchUrl?: string;
  /** Render live data from API */
  renderLive?: (data: unknown) => React.ReactNode;
  /** Static fallback content */
  fallback?: React.ReactNode;
}

type WidgetDataMap = Record<string, unknown>;

// ── Component ─────────────────────────────────────────────────────────
export default function HubPage() {
  const { user, loading } = useAuth();
  const router = useRouter();
  const [widgetData, setWidgetData] = useState<WidgetDataMap>({});
  const [widgetErrors, setWidgetErrors] = useState<Record<string, boolean>>({});

  // ── Navigate handler — routes mode via router or window ────────
  const handleNavigate = useCallback((modeId: string) => {
    // For now, modes are navigated via the dock (ModeView handles it).
    // The HubPage lives inside ModeView, so we dispatch a custom event
    // that the ModeView's Dock listens to for mode changes.
    // In P04+, this uses the ModeStack directly.
    window.dispatchEvent(new CustomEvent("hub:navigate", { detail: { modeId } }));
  }, []);

  const goToHub = useCallback(() => {
    // Already on hub
  }, []);

  // ── Fetch widget data ─────────────────────────────────────────
  const fetchWidget = useCallback(async (widget: WidgetConfig) => {
    if (!widget.fetchUrl) return;
    try {
      const res = await fetch(widget.fetchUrl);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setWidgetData((prev) => ({ ...prev, [widget.id]: data }));
      setWidgetErrors((prev) => ({ ...prev, [widget.id]: false }));
    } catch {
      setWidgetErrors((prev) => ({ ...prev, [widget.id]: true }));
    }
  }, []);

  useEffect(() => {
    for (const w of WIDGETS) {
      fetchWidget(w);
    }
  }, [fetchWidget]);

  // ── Redirect if not auth'd ────────────────────────────────────
  useEffect(() => {
    if (!loading && !user) router.push("/auth");
  }, [user, loading, router]);

  if (loading || !user) return null;

  return (
    <>
      <NeuralParticles />
      <CommandBar
        onNavigate={handleNavigate}
        goToHub={goToHub}
        currentMode="hub"
      />

      <div className="relative z-10 flex h-full flex-col px-4 sm:px-8 py-6 overflow-y-auto">
        {/* ── Greeting ────────────────────────────────────────────── */}
        <HubGreeting />

        {/* ── Quick-jump input — ⌘K trigger area ─────────────────── */}
        <button
          onClick={() => window.dispatchEvent(new KeyboardEvent("keydown", { metaKey: true, key: "k" }))}
          className={cn(
            "mx-auto mb-8 w-full max-w-md",
            "flex items-center gap-3 rounded-xl border border-border-subtle px-4 py-2.5",
            "bg-bg-widget backdrop-blur-xl",
            "text-sm text-text-muted text-left",
            "hover:border-border-default hover:text-text-secondary",
            "motion-safe:transition-all motion-safe:duration-200",
            "focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-border-input-focus",
          )}
        >
          <LightningIcon size={20} />
          <span className="flex-1">Ask Cortex anything…</span>
          <span className="text-[10px] font-mono text-text-muted bg-bg-elevated px-1.5 py-0.5 rounded">
            ⌘K
          </span>
        </button>

        {/* ── Widget grid (2×5) ──────────────────────────────────── */}
        <div className="grid grid-cols-2 gap-3 max-w-2xl mx-auto w-full">
          {WIDGETS.map((widget, i) => (
            <HubWidget
              key={widget.id}
              icon={widget.icon}
              label={widget.label}
              glowColor={widget.glowColor}
              onClick={() => handleNavigate(widget.id)}
              style={{ "--i": i } as React.CSSProperties}
            >
              {widgetErrors[widget.id]
                ? <span className="text-danger/70 italic">Offline</span>
                : widget.renderLive
                ? widget.renderLive(widgetData[widget.id])
                : widget.fallback
              }
            </HubWidget>
          ))}
        </div>
      </div>
    </>
  );
}

// ── Widget grid configuration ────────────────────────────────────────

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const WIDGETS: WidgetConfig[] = [
  {
    id: "chat",
    icon: <ChatIcon size={20} />,
    label: "Chat",
    glowColor: "cyan",
    renderLive: () => (
      <p>Open a conversation to start chatting with your AI</p>
    ),
    fallback: <p>Open a conversation to start chatting with your AI</p>,
  },
  {
    id: "search",
    icon: <SearchIcon size={20} />,
    label: "Search",
    glowColor: "cyan",
    renderLive: () => (
      <p>Search your knowledge base, files, and conversations</p>
    ),
    fallback: <p>Search your knowledge base, files, and conversations</p>,
  },
  {
    id: "brain",
    icon: <BrainIcon size={20} />,
    label: "Brain",
    glowColor: "cyan",
    fetchUrl: `${API_BASE}/api/v1/memory/knowledge/stats`,
    renderLive: (data) => {
      const d = data as BrainStats | undefined;
      if (!d) return <p>Loading stats…</p>;
      return (
        <>
          <p><span className="text-text-secondary">Chunks:</span> {d.total_chunks ?? "—"}</p>
          <p><span className="text-text-secondary">Files:</span> {d.indexed_files ?? "—"}</p>
          <p><span className="text-text-secondary">Graph nodes:</span> {d.knowledge_graph_nodes ?? "—"}</p>
        </>
      );
    },
    fallback: <p>Index stats unavailable</p>,
  },
  {
    id: "vault",
    icon: <VaultIcon size={20} />,
    label: "Vault",
    glowColor: "red",
    fetchUrl: `${API_BASE}/api/v1/privacy/vault/status`,
    renderLive: (data) => {
      const d = data as VaultStatus | undefined;
      if (!d) return <p>Checking vault…</p>;
      return (
        <>
          <p><span className="text-text-secondary">Status:</span> {d.locked ? "Locked" : "Unlocked"}</p>
          <p><span className="text-text-secondary">Files:</span> {d.file_count ?? "—"}</p>
        </>
      );
    },
    fallback: <p>Vault status unavailable</p>,
  },
  {
    id: "models",
    icon: <ModelsIcon size={20} />,
    label: "Models",
    glowColor: "cyan",
    fetchUrl: `${API_BASE}/api/v1/models/ollama/catalog`,
    renderLive: (data) => {
      const d = data as ModelCatalog | undefined;
      if (!d) return <p>Loading models…</p>;
      const active = d.active_model ?? d.models?.[0]?.name;
      const count = d.models?.length ?? 0;
      return (
        <>
          <p><span className="text-text-secondary">Active:</span> {active ?? "None"}</p>
          <p><span className="text-text-secondary">Available:</span> {count} model{count !== 1 ? "s" : ""}</p>
        </>
      );
    },
    fallback: <p>Model info unavailable</p>,
  },
  {
    id: "code",
    icon: <CodeIcon size={20} />,
    label: "Code",
    glowColor: "cyan",
    renderLive: () => (
      <>
        <p><span className="text-text-secondary">LSP:</span> Not connected</p>
        <p className="text-text-muted/50">Requires v1.12</p>
      </>
    ),
    fallback: <p>Code intelligence awaits v1.12</p>,
  },
  {
    id: "utility",
    icon: <UtilityIcon size={20} />,
    label: "Utility",
    glowColor: "cyan",
    renderLive: () => (
      <p>Tools & utilities at your fingertips</p>
    ),
    fallback: <p>Tools & utilities at your fingertips</p>,
  },
  {
    id: "settings",
    icon: <SettingsIcon size={20} />,
    label: "Settings",
    glowColor: "cyan",
    renderLive: () => (
      <p>Configure your Cortex experience</p>
    ),
    fallback: <p>Configure your Cortex experience</p>,
  },
  {
    id: "systems",
    icon: <SystemsIcon size={20} />,
    label: "Systems",
    glowColor: "red",
    fetchUrl: `${API_BASE}/api/v1/system/health`,
    renderLive: (data) => {
      const d = data as HealthData | undefined;
      if (!d) return <p>Checking system…</p>;
      return (
        <>
          <p>
            <span className="text-text-secondary">Status:</span>{" "}
            <span className={d.status === "healthy" ? "text-green-400" : "text-yellow-400"}>
              {d.status}
            </span>
          </p>
          <p><span className="text-text-secondary">Version:</span> {d.version ?? "—"}</p>
        </>
      );
    },
    fallback: <p>System health unavailable</p>,
  },
  {
    id: "profile",
    icon: <ProfileIcon size={20} />,
    label: "Profile",
    glowColor: "red",
    renderLive: () => (
      <p>Your account & preferences</p>
    ),
    fallback: <p>Your account & preferences</p>,
  },
];
