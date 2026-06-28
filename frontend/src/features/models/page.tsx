"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/shared/auth/AuthProvider";
import { AppShell } from "@/shared/layout/AppShell";
import { HardwareBar } from "./components/HardwareBar";
import { BrowseView } from "./components/BrowseView";
import { CompareView } from "./components/CompareView";
import { DownloadsView } from "./components/DownloadsView";
import { InstalledView } from "./components/InstalledView";
import { ModelDetailModal } from "./components/ModelDetailModal";
import { catalog, downloads } from "./api";
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

  // Download management
  const [downloadingModels, setDownloadingModels] = useState<Map<string, number>>(new Map());
  const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Detail modal
  const [detailModalModelId, setDetailModalModelId] = useState<string | null>(null);

  // ── Auth redirect ───────────────────────────────────────────────────────

  useEffect(() => {
    if (!authLoading && !user) {
      router.replace("/auth");
    }
  }, [authLoading, user, router]);

  // ── Load hardware on mount ──────────────────────────────────────────────

  useEffect(() => {
    catalog
      .hardware()
      .then(setHardware)
      .catch(() => {
        // Fallback: estimate from available RAM
        setHardware(null);
      })
      .finally(() => setHardwareLoading(false));
  }, []);

  // ── Download progress polling ───────────────────────────────────────────

  useEffect(() => {
    if (downloadingModels.size === 0) {
      if (pollingRef.current) {
        clearInterval(pollingRef.current);
        pollingRef.current = null;
      }
      return;
    }

    pollingRef.current = setInterval(async () => {
      const modelIds = Array.from(downloadingModels.keys());
      const updates: [string, number][] = [];

      for (const modelId of modelIds) {
        try {
          const res = await downloads.progress(modelId);
          updates.push([modelId, res.progress]);
        } catch {
          // Model finished or not found — remove from tracking
          updates.push([modelId, 1]);
        }
      }

      setDownloadingModels((prev) => {
        const next = new Map(prev);
        for (const [id, progress] of updates) {
          if (progress >= 1) {
            next.delete(id);
          } else {
            next.set(id, progress);
          }
        }
        return next;
      });
    }, 2000);

    return () => {
      if (pollingRef.current) {
        clearInterval(pollingRef.current);
        pollingRef.current = null;
      }
    };
  }, [downloadingModels.size]);

  // ── Handlers ─────────────────────────────────────────────────────────────

  const handleDownload = useCallback(async (modelId: string) => {
    setDownloadingModels((prev) => {
      const next = new Map(prev);
      next.set(modelId, 0);
      return next;
    });

    try {
      await downloads.download(modelId);
    } catch {
      // If download fails, remove tracking
      setDownloadingModels((prev) => {
        const next = new Map(prev);
        next.delete(modelId);
        return next;
      });
    }
  }, []);

  const handleCancelDownload = useCallback(async (modelId: string) => {
    try {
      await downloads.cancel(modelId);
    } catch {
      // ignore
    }
    setDownloadingModels((prev) => {
      const next = new Map(prev);
      next.delete(modelId);
      return next;
    });
  }, []);

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
      handleDownload(modelId);
    },
    [handleDownload],
  );

  const handleDownloadFromCompare = useCallback(
    (modelId: string) => {
      handleDownload(modelId);
    },
    [handleDownload],
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
        <div className="flex items-center justify-center py-24">
          <div className="h-5 w-5 animate-spin rounded-full border-2 border-accent border-t-transparent" />
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
      <div className="mx-auto max-w-6xl space-y-6">
        {/* Page header */}
        <div>
          <h1 className="text-xl font-semibold text-text-primary">Models</h1>
          <p className="text-sm text-text-secondary mt-0.5">
            Browse, compare, download, and manage your local models
          </p>
        </div>

        {/* Hardware bar */}
        <HardwareBar hardware={hardware} loading={hardwareLoading} />

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
        <div role="tabpanel" aria-label={`${activeTab} tab`}>
          {activeTab === "browse" && (
            <BrowseView
              hardware={hardware}
              onDownload={handleDownloadFromBrowse}
              onViewDetail={handleViewDetail}
              compareSelectedIds={compareSelectedIds}
              onToggleCompare={handleToggleCompare}
              compareDisabled={compareDisabled}
              downloadingModels={downloadingModels}
              onCancelDownload={handleCancelDownload}
            />
          )}

          {activeTab === "compare" && (
            <CompareView
              selectedIds={compareSelectedIds}
              onClearSelection={handleClearCompare}
              onDownloadModel={handleDownloadFromCompare}
            />
          )}

          {activeTab === "downloads" && <DownloadsView />}

          {activeTab === "installed" && (
            <InstalledView onViewDetail={handleViewDetail} />
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
    </AppShell>
  );
}
