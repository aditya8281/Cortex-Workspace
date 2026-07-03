"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useGSAP } from "@gsap/react";
import gsap from "gsap";
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

gsap.registerPlugin(useGSAP);

// ── Types ─────────────────────────────────────────────────────────────
interface HealthData {
  status: string;
  checks?: Record<string, boolean>;
}

interface ModelCatalog {
  models?: Array<{ name: string; display_name?: string }>;
  total_count?: number;
  downloaded_count?: number;
  available_from_providers?: Array<{ name: string }>;
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
  spanFull?: boolean;
  /** API endpoint to fetch preview data (returns JSON) */
  fetchUrl?: string;
  /** Render live data from API */
  renderLive?: (data: unknown) => React.ReactNode;
  /** Static fallback content */
  fallback?: React.ReactNode;
}

type WidgetDataMap = Record<string, unknown>;

// ── Loading skeleton ──────────────────────────────────────────────────
function HubSkeleton() {
  return (
    <div className="relative h-dvh overflow-hidden bg-bg-base">
      <div className="absolute inset-0 top-6 flex flex-col px-4 sm:px-8 py-6">
        {/* Greeting skeleton */}
        <div className="mb-6 max-w-sm">
          <div className="h-8 w-64 rounded-lg bg-bg-widget motion-safe:animate-pulse" />
          <div className="h-4 w-48 mt-2 rounded bg-bg-widget motion-safe:animate-pulse opacity-60" />
        </div>
        {/* Search bar skeleton */}
        <div className="mx-auto mb-6 w-full max-w-md h-11 rounded-xl border border-border-subtle bg-bg-widget motion-safe:animate-pulse" />
        {/* Widget grid skeleton */}
        <div className="grid grid-cols-2 gap-3 max-w-2xl mx-auto w-full">
          {[0, 1, 2, 3].map((i) => (
            <div
              key={i}
              className={cn(
                "rounded-2xl border border-border-subtle bg-bg-widget motion-safe:animate-pulse p-4",
                i === 0 && "sm:col-span-2",
              )}
              style={{ animationDelay: `${i * 80}ms` }}
            >
              <div className="flex items-center gap-2 mb-2.5">
                <div className="h-5 w-5 rounded bg-bg-elevated" />
                <div className="h-3 w-16 rounded bg-bg-elevated" />
              </div>
              <div className="space-y-1.5">
                <div className="h-3 w-24 rounded bg-bg-elevated opacity-60" />
                <div className="h-3 w-16 rounded bg-bg-elevated opacity-40" />
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// ── Component ─────────────────────────────────────────────────────────
export default function HubPage() {
  const { user, loading } = useAuth();
  const router = useRouter();
  const [widgetData, setWidgetData] = useState<WidgetDataMap>({});
  const [widgetErrors, setWidgetErrors] = useState<Record<string, boolean>>({});
  const greetingRef = useRef<HTMLDivElement>(null);
  const searchBarRef = useRef<HTMLButtonElement>(null);
  const gridRef = useRef<HTMLDivElement>(null);

  // ── GSAP entrance stagger ──────────────────────────────────────────
  useGSAP(() => {
    const mm = gsap.matchMedia();
    mm.add("(prefers-reduced-motion: no-preference)", () => {
      const tl = gsap.timeline({ defaults: { ease: "power3.out" } });

      // Greeting fade-down
      if (greetingRef.current) {
        tl.from(greetingRef.current, { y: -12, opacity: 0, duration: 0.35 });
      }

      // Search bar
      if (searchBarRef.current) {
        tl.from(searchBarRef.current, { y: -8, opacity: 0, duration: 0.3 }, "-=0.1");
      }

      // Widgets stagger — use set+to to avoid flash from render-timing
      if (gridRef.current) {
        const widgets = gridRef.current.querySelectorAll("[data-widget]");
        gsap.set(widgets, { y: 16, opacity: 0, scale: 0.96 });
        tl.to(widgets, { y: 0, opacity: 1, scale: 1, stagger: { from: "start", each: 0.04 }, duration: 0.35 }, "-=0.05");
      }
    });
    return () => mm.revert();
  }, { scope: gridRef.current ? undefined : undefined });

  // ── Navigate handler — routes mode via router or window ────────
  const handleNavigate = useCallback((modeId: string) => {
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

  // Show skeleton while auth is loading (not blank)
  if (loading) return <HubSkeleton />;

  // If auth completed but no user, return null (will redirect to /auth)
  if (!user) return null;

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
        <div ref={greetingRef}>
          <HubGreeting />
        </div>

        {/* ── Quick-jump input — ⌘K trigger area ─────────────────── */}
        <button
          ref={searchBarRef}
          onClick={() => window.dispatchEvent(new KeyboardEvent("keydown", { metaKey: true, key: "k" }))}
          className={cn(
            "mx-auto mb-6 w-full max-w-md",
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

        {/* ── Widget grid ─────────────────────────────────────────── */}
        <div ref={gridRef} className="grid grid-cols-2 gap-3 max-w-2xl mx-auto w-full">
          {WIDGETS.map((widget) => (
            <HubWidget
              key={widget.id}
              icon={widget.icon}
              label={widget.label}
              glowColor={widget.glowColor}
              spanFull={widget.spanFull}
              onClick={() => handleNavigate(widget.id)}
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

const API_BASE = "";

const WIDGETS: WidgetConfig[] = [
  {
    id: "brain",
    icon: <BrainIcon size={20} />,
    label: "Brain",
    glowColor: "cyan",
    spanFull: true,
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
    id: "systems",
    icon: <SystemsIcon size={20} />,
    label: "Systems",
    glowColor: "red",
    spanFull: true,
    fetchUrl: `${API_BASE}/api/v1/health/deep`,
    renderLive: (data) => {
      const d = data as HealthData | undefined;
      if (!d) return <p>Checking system…</p>;

      const serviceList = d.checks
        ? Object.entries(d.checks).map(([s, ok]) => `${s}=${ok ? "✓" : "✗"}`).join(" ")
        : "";
      return (
        <>
          <p>
            <span className="text-text-secondary">Status:</span>{" "}
            <span className={d.status === "healthy" ? "text-success" : "text-warning"}>
              {d.status}
            </span>
          </p>
          <p className="text-[11px] text-text-muted font-mono">{serviceList}</p>
        </>
      );
    },
    fallback: <p>Deep health check unavailable</p>,
  },
  {
    id: "models",
    icon: <ModelsIcon size={20} />,
    label: "Models",
    glowColor: "cyan",
    fetchUrl: `${API_BASE}/api/v1/models`,
    renderLive: (data) => {
      const d = data as ModelCatalog | undefined;
      if (!d) return <p>Loading models…</p>;
      const count = d.total_count ?? d.models?.length ?? 0;
      const dl = d.downloaded_count ?? 0;
      return (
        <>
          <p><span className="text-text-secondary">Total:</span> {count} model{count !== 1 ? "s" : ""}</p>
          <p><span className="text-text-secondary">Downloaded:</span> {dl}</p>
        </>
      );
    },
    fallback: <p>Model info unavailable</p>,
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
