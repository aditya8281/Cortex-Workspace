"use client";

import { useEffect, useState, useRef } from "react";
import { Card } from "@/components/ui/base";
import { ErrorBoundary } from "@/components/shared/ErrorBoundary";
import { modelsService } from "@/services/api/models";
import { useIsMounted } from "@/hooks/useIsMounted";

export default function MarketplacePage() {
  const [items, setItems] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [jobs, setJobs] = useState<Record<string, any>>({});
  const [inProgressByModel, setInProgressByModel] = useState<Record<string, boolean>>({});
  const [modelErrors, setModelErrors] = useState<Record<string, string>>({});
  const timersRef = useRef<Record<string, number>>({});
  const abortsRef = useRef<Record<string, AbortController>>({});
  const mountedRef = useIsMounted();

  const setupPolling = (jobId: string, modelName: string) => {
    if (timersRef.current[jobId]) return;

    // Set initial job structure in state
    setJobs((s) => ({
      ...s,
      [jobId]: {
        job_id: jobId,
        model: modelName,
        status: "running",
        progress: 0,
      },
    }));

    const ac = new AbortController();
    abortsRef.current[jobId] = ac;

    const t = window.setInterval(async () => {
      try {
        const prog = await modelsService.getDownloadProgress(jobId, ac.signal);
        if (!mountedRef.current) return;
        if (prog == null) return;

        setJobs((s) => ({ ...s, [jobId]: { ...prog, model: modelName } }));

        if (prog.status === "completed" || (prog.progress || 0) >= 100 || prog.status === "failed" || prog.status === "cancelled") {
          window.clearInterval(t);
          delete timersRef.current[jobId];
          try { delete abortsRef.current[jobId]; } catch (e) {}
          // Refresh catalog to update installed status
          fetchMarketplaceOnly();
        }
      } catch (e) {
        window.clearInterval(t);
        delete timersRef.current[jobId];
        try { delete abortsRef.current[jobId]; } catch (e) {}
      }
    }, 2000);
    timersRef.current[jobId] = t;
  };

  const fetchMarketplaceOnly = async () => {
    try {
      const data = await modelsService.getMarketplace();
      if (mountedRef.current) {
        setItems(data || []);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const fetch = async () => {
    setLoading(true);
    try {
      const data = await modelsService.getMarketplace();
      setItems(data || []);
      // Auto-poll active downloads received from the backend
      data.forEach((item: any) => {
        if (item.download_job_id && item.download_status === "running") {
          setupPolling(item.download_job_id, item.name);
        }
      });
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetch();
  }, []);

  const startDownload = async (model: any) => {
    const modelKey = model.id || model.name || String(model);
    const modelName = model.name || model.id || model;
    setModelErrors((s) => ({ ...s, [modelKey]: "" }));
    setInProgressByModel((s) => ({ ...s, [modelKey]: true }));
    try {
      const job = await modelsService.startDownload(modelName);
      if (job?.job_id) {
        setupPolling(job.job_id, modelName);
      }
    } catch (err: any) {
      console.error(err);
      setModelErrors((s) => ({ ...s, [modelKey]: err?.message || "Failed to start download" }));
    } finally {
      setInProgressByModel((s) => ({ ...s, [modelKey]: false }));
    }
  };

  const cancelJob = async (jobId: string) => {
    // abort polling
    if (abortsRef.current[jobId]) {
      try { abortsRef.current[jobId].abort(); } catch (e) {}
      delete abortsRef.current[jobId];
    }
    if (timersRef.current[jobId]) {
      window.clearInterval(timersRef.current[jobId]);
      delete timersRef.current[jobId];
    }
    try {
      await modelsService.cancelDownload(jobId);
    } catch (e) {
      console.error("Failed to cancel download on backend:", e);
    }
    setJobs((s) => ({ ...s, [jobId]: { ...(s[jobId] || {}), status: "cancelled" } }));
  };

  useEffect(() => {
    return () => {
      Object.values(timersRef.current).forEach((id) => window.clearInterval(id));
      timersRef.current = {};
    };
  }, []);

  return (
    <ErrorBoundary>
      <div className="max-w-4xl mx-auto p-4 md:p-6 space-y-6 animate-fade-in">
      <div className="flex items-center justify-between border-b border-slate-800/60 pb-4">
        <div>
          <h1 className="text-xl font-bold tracking-wide text-white uppercase font-mono">Model Marketplace</h1>
          <p className="text-xs text-slate-400 mt-1">Browse community models and install them into your registry.</p>
        </div>
        <div>
          <button onClick={fetch} className="px-3 py-1 bg-slate-900 border border-slate-800 rounded-lg text-xs text-slate-300">Refresh</button>
        </div>
      </div>

      {loading && <div className="text-xs text-slate-400 font-mono animate-pulse">Loading marketplace registry...</div>}

      <div className="grid grid-cols-1 gap-4">
        {items.map((it) => {
          const activeJob = Object.values(jobs).find((j: any) => j.model === it.name || j.job_id === it.download_job_id);
          const isInstalled = it.is_installed || it.download_status === "installed";
          
          return (
            <Card key={it.id || it.name} className="p-5 bg-slate-900/40 border-slate-800/80 rounded-2xl">
              <div className="flex items-start justify-between">
                <div>
                  <h3 className="font-mono text-xs font-semibold text-slate-200">{it.name}</h3>
                  <p className="text-[11px] text-slate-400 mt-1.5 leading-relaxed max-w-xl">{it.description || "Ollama community registry model."}</p>
                  
                  {it.size && (
                    <div className="flex gap-4 mt-3 text-[10px] text-slate-500 font-mono">
                      <div>SIZE: <span className="text-slate-300 font-semibold">{it.size}</span></div>
                      {it.parameters && <div>PARAMS: <span className="text-slate-300 font-semibold">{it.parameters}</span></div>}
                      {it.source && <div>SOURCE: <span className="text-slate-300 font-semibold">{it.source}</span></div>}
                    </div>
                  )}
                </div>
                
                <div className="flex flex-col items-end gap-2 shrink-0">
                  <div className="flex items-center gap-2">
                    {activeJob ? (
                      <div className="flex flex-col items-end gap-1 font-mono text-[10px]">
                        <div className="flex items-center gap-1.5">
                          <span className="text-cyan-400 uppercase tracking-widest font-semibold">{activeJob.status}</span>
                          <span className="text-slate-200 font-bold">{Math.round(activeJob.progress || 0)}%</span>
                        </div>
                        {activeJob.status !== "completed" && activeJob.status !== "failed" && activeJob.status !== "cancelled" ? (
                          <button onClick={() => cancelJob(activeJob.job_id)} className="text-[9px] text-rose-400 hover:text-rose-300 hover:underline">Cancel</button>
                        ) : activeJob.status === "failed" ? (
                          <button onClick={() => startDownload(it)} className="text-[9px] text-amber-400 hover:text-amber-300 hover:underline">Retry</button>
                        ) : null}
                      </div>
                    ) : isInstalled ? (
                      <span className="text-[9px] font-mono font-bold tracking-wide uppercase px-2.5 py-0.5 bg-emerald-950/20 border border-emerald-900/30 rounded-full text-emerald-400">
                        Installed
                      </span>
                    ) : (
                      <button
                        onClick={() => startDownload(it)}
                        disabled={!!inProgressByModel[it.id || it.name]}
                        className="px-3.5 py-1.5 bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white font-semibold text-xs rounded-xl shadow-[0_4px_12px_rgba(6,182,212,0.15)] disabled:opacity-50"
                      >
                        {inProgressByModel[it.id || it.name] ? "Starting..." : "Download"}
                      </button>
                    )}
                  </div>
                  {modelErrors[it.id || it.name] && (
                    <div className="text-[10px] font-mono text-rose-400 mt-1 max-w-xs text-right">{modelErrors[it.id || it.name]}</div>
                  )}
                </div>
              </div>
            </Card>
          );
        })}
      </div>
      </div>
    </ErrorBoundary>
  );
}
