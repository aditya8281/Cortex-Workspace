"use client";

import { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/shared/auth/AuthProvider";
import { AppShell } from "@/shared/layout/AppShell";
import { HardwareBar } from "./components/HardwareBar";
import { BrowseView } from "./components/BrowseView";
import { CompareView } from "./components/CompareView";
import { DownloadsView } from "./components/DownloadsView";
import { InstalledView } from "./components/InstalledView";
import { ModelDetailModal } from "./components/ModelDetailModal";
import { catalog, downloads, getDefaultModel, setDefaultModel } from "./api";
import { DownloadProvider } from "@/shared/downloads/DownloadProvider";
import { DockedDownloadPanel } from "./components/DockedDownloadPanel";
import { Card } from "@/shared/ui/Card";
import { Skeleton } from "@/shared/ui/Skeleton";
import type { HardwareInfo, TabKey } from "./api";

// ── Tab definitions ──────────────────────────────────────────────────────────

const TABS: { key: TabKey; label: string }[] = [
  { key: "browse", label: "Browse" },
  { key: "compare", label: "Compare" },
  { key: "downloads", label: "Downloads" },
  { key: "installed", label: "Installed" },
];

// ── Main page ────────────────────────────────────────────────────────────────

export default function ModelsPage() {
  const router = useRouter();
  const { user, loading: authLoading } = useAuth();

  // Tab state
  const [activeTab, setActiveTab] = useState<TabKey>("browse");

  // Hardware
  const [hardware, setHardware] = useState<HardwareInfo | null>(null);
  const [hardwareLoading, setHardwareLoading] = useState(true);

  // Compare selection
  const [compareSelectedIds, setCompareSelectedIds] = useState<string[]>([]);

  // Detail modal
  const [detailModalModelId, setDetailModalModelId] = useState<string | null>(null);

  // ── Auth redirect ───────────────────────────────────────────────────────

  useEffect(() => {
    if (!authLoading && !user) {
      router.replace("/auth");
    }
  }, [authLoading, user, router]);

  const [hardwareError, setHardwareError] = useState<string | null>(null);

  // ── Load hardware on mount ──────────────────────────────────────────────

  const loadHardware = useCallback(() => {
    setHardwareError(null);
    catalog
      .hardware()
      .then(setHardware)
      .catch(() => {
        setHardware(null);
        setHardwareError("Failed to load hardware info");
      })
      .finally(() => setHardwareLoading(false));
  }, []);

  useEffect(() => {
    loadHardware();
  }, [loadHardware]);

  // State for default model
  const [defaultModel, setDefaultModelState] = useState<string | null>(null);

  useEffect(() => {
    setDefaultModelState(getDefaultModel());
  }, []);

  // ── Handlers ─────────────────────────────────────────────────────────────

  const handleOpenChat = useCallback((_modelId: string) => {
    router.push("/chat");
  }, [router]);

  const handleSetDefaultModel = useCallback((modelId: string) => {
    setDefaultModel(modelId);
    setDefaultModelState(modelId);
  }, []);

  const handleDeleteModel = useCallback(
    async (modelId: string) => {
      try {
        await downloads.deleteLocal(modelId);
        if (defaultModel === modelId) {
          setDefaultModelState(null);
          localStorage.removeItem("cortex_default_model");
        }
      } catch {
        // ignore — InstalledView handles its own error state
      }
    },
    [defaultModel],
  );

  const handleToggleCompare = useCallback((modelId: string) => {
    setCompareSelectedIds((prev) => {
      if (prev.includes(modelId)) {
        return prev.filter((id) => id !== modelId);
      }
      if (prev.length >= 5) return prev;
      return [...prev, modelId];
    });
  }, []);

  const handleClearCompare = useCallback(() => {
    setCompareSelectedIds([]);
  }, []);

  const handleViewDetail = useCallback((modelId: string) => {
    setDetailModalModelId(modelId);
  }, []);

  const handleCloseDetail = useCallback(() => {
    setDetailModalModelId(null);
  }, []);

  const handleDownloadFromBrowse = useCallback(
    (modelId: string) => {
      // Show model detail so user can pick variant before downloading
      setDetailModalModelId(modelId);
    },
    [],
  );

  const handleDownloadFromModal = useCallback(
    (_modelName: string) => {
      // The modal already calls downloads.download internally,
      // so we just close and refresh the downloading state
      setDetailModalModelId(null);
    },
    [],
  );

  // ── Show loading while checking auth ─────────────────────────────────────

  if (authLoading) {
    return (
      <AppShell>
        <div className="mx-auto max-w-6xl space-y-6">
          <div className="space-y-1">
            <Skeleton className="h-6 w-20" />
            <Skeleton className="h-4 w-64" />
          </div>
          <Skeleton className="h-12 w-full rounded-lg" />
          <div className="flex gap-2">
            {[1, 2, 3, 4].map((i) => (
              <Skeleton key={i} className="h-10 w-24 rounded-md" />
            ))}
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
            {Array.from({ length: 6 }).map((_, i) => (
              <Card key={i} className="p-4">
                <div className="space-y-3">
                  <Skeleton className="h-5 w-3/4" />
                  <Skeleton className="h-4 w-1/2" />
                  <Skeleton className="h-3 w-1/3" />
                  <Skeleton className="h-1.5 w-full rounded-full" />
                </div>
              </Card>
            ))}
          </div>
        </div>
      </AppShell>
    );
  }

  if (!user) {
    return null; // Redirecting
  }

  // ── Derived ──────────────────────────────────────────────────────────────

  const compareDisabled = compareSelectedIds.length >= 5;

  // ── Render ───────────────────────────────────────────────────────────────

  return (
    <AppShell>
      <DownloadProvider>
        <div className="mx-auto max-w-6xl space-y-6 animate-fade-in">
        {/* Page header */}
        <div>
          <h1 className="text-xl font-semibold text-text-primary">Models</h1>
          <p className="text-sm text-text-secondary mt-0.5">
            Browse, compare, download, and manage your local models
          </p>
        </div>

        {/* Hardware bar */}
        <HardwareBar hardware={hardware} loading={hardwareLoading} />

        {hardwareError && (
          <div className="rounded-lg border border-danger/20 bg-danger/5 px-4 py-3 text-sm text-danger">
            {hardwareError}
            <button
              onClick={loadHardware}
              className="ml-2 text-xs font-medium text-danger underline hover:text-danger/80"
            >
              Retry
            </button>
          </div>
        )}

        {/* Tab bar */}
        <div
          className="flex items-center border-b border-border-subtle gap-1"
          role="tablist"
          aria-label="Model catalog tabs"
        >
          {TABS.map((tab) => {
            const isActive = activeTab === tab.key;
            return (
              <button
                key={tab.key}
                role="tab"
                aria-selected={isActive}
                onClick={() => setActiveTab(tab.key)}
                className={`relative px-4 py-2.5 text-sm font-medium transition-colors duration-150 ${
                  isActive
                    ? "text-text-primary"
                    : "text-text-muted hover:text-text-secondary"
                }`}
              >
                {tab.label}
                {isActive && (
                  <span className="absolute bottom-0 left-2 right-2 h-0.5 rounded-full bg-accent" />
                )}
              </button>
            );
          })}
        </div>

        {/* Tab content */}
        <div role="tabpanel" aria-label={`${activeTab} tab`} className="animate-fade-in" key={activeTab}>
          {activeTab === "browse" && (
            <BrowseView
              hardware={hardware}
              onDownload={handleDownloadFromBrowse}
              onViewDetail={handleViewDetail}
              compareSelectedIds={compareSelectedIds}
              onToggleCompare={handleToggleCompare}
              compareDisabled={compareDisabled}
            />
          )}

          {activeTab === "compare" && (
            <CompareView
              selectedIds={compareSelectedIds}
              onClearSelection={handleClearCompare}
            />
          )}

          {activeTab === "downloads" && <DownloadsView />}

          {activeTab === "installed" && (
            <InstalledView
              hardware={hardware}
              onDelete={handleDeleteModel}
              onOpenChat={handleOpenChat}
              onSetDefault={handleSetDefaultModel}
              defaultModel={defaultModel}
            />
          )}
        </div>
      </div>

      {/* Floating compare button */}
      {compareSelectedIds.length >= 2 && activeTab !== "compare" && (
        <button
          onClick={() => setActiveTab("compare")}
          className="fixed bottom-6 right-6 z-50 flex items-center gap-2 rounded-full bg-accent px-5 py-3 text-sm font-semibold text-white shadow-lg hover:bg-accent/90 transition-colors duration-150"
          aria-label={`Compare ${compareSelectedIds.length} models`}
        >
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
            <rect x="2" y="3" width="5" height="10" rx="1" stroke="currentColor" strokeWidth="1.5" fill="none" />
            <rect x="9" y="1" width="5" height="14" rx="1" stroke="currentColor" strokeWidth="1.5" fill="none" />
          </svg>
          Compare {compareSelectedIds.length} models
        </button>
      )}

      {/* Detail modal */}
      <ModelDetailModal
        open={!!detailModalModelId}
        onClose={handleCloseDetail}
        modelId={detailModalModelId ?? ""}
        onDownload={handleDownloadFromModal}
      />
        <DockedDownloadPanel />
      </DownloadProvider>
    </AppShell>
  );
}
