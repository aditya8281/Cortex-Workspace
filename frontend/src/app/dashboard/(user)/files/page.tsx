"use client";

import { useEffect, useState, useRef } from "react";
import { useIsMounted } from "@/hooks/useIsMounted";
import { Card } from "@/components/ui/base";
import { ErrorBoundary } from "@/components/shared/ErrorBoundary";
import { syncService } from "@/services/api/sync";
import { contextService } from "@/services/api/context";

export default function FilesPage() {
  const [intelligence, setIntelligence] = useState<any>(null);
  const [latestRun, setLatestRun] = useState<any>(null);
  const [includePath, setIncludePath] = useState("");
  const [loading, setLoading] = useState(false);
  const [attachContent, setAttachContent] = useState("");
  const [message, setMessage] = useState("");

  const fetchData = async () => {
    try {
      // create a dedicated abort controller for this fetch
      const ac = new AbortController();
      dataAbortRef.current = ac;
      const [intel, run] = await Promise.all([
        syncService.getIntelligence(ac.signal),
        syncService.getLatestRun(ac.signal),
      ]);
      if (!mountedRef.current) return;
      setIntelligence(intel);
      setLatestRun(run);
    } catch (err: any) {
      console.error(err);
    }
  };

  const dataAbortRef = useRef<AbortController | null>(null);
  const pollAbortRef = useRef<AbortController | null>(null);
  const pollTimerRef = useRef<number | null>(null);
  const mountedRef = useIsMounted();

  useEffect(() => {
    fetchData();
    // poll latest run periodically with cancellable requests
    const startPolling = () => {
      if (pollTimerRef.current) {
        try { window.clearInterval(pollTimerRef.current); } catch (e) {}
      }
      pollTimerRef.current = window.setInterval(async () => {
        try {
          if (pollAbortRef.current) {
            try { pollAbortRef.current.abort(); } catch (e) {}
          }
          pollAbortRef.current = new AbortController();
          const run = await syncService.getLatestRun(pollAbortRef.current.signal);
          if (!mountedRef.current) return;
          setLatestRun(run);
        } catch (e) {
          // ignore poll errors
        }
      }, 3000) as unknown as number;
    };

    startPolling();

    return () => {
      // abort any in-flight data fetch
      if (dataAbortRef.current) {
        try { dataAbortRef.current.abort(); } catch (e) {}
        dataAbortRef.current = null;
      }
      if (pollAbortRef.current) {
        try { pollAbortRef.current.abort(); } catch (e) {}
        pollAbortRef.current = null;
      }
      if (pollTimerRef.current) {
        try { window.clearInterval(pollTimerRef.current); } catch (e) {}
        pollTimerRef.current = null;
      }
    };
  }, []);

  const handleAddInclude = async () => {
    if (!includePath) return;
    setLoading(true);
    try {
      // allow include add to be cancellable if needed
      const ac = new AbortController();
      dataAbortRef.current = ac;
      await syncService.addIncludePath(includePath);
      setIncludePath("");
      await fetchData();
      setMessage("Include path saved.");
    } catch (err: any) {
      setMessage(err?.message || "Failed to add include path");
    } finally {
      setLoading(false);
      setTimeout(() => setMessage(""), 3000);
    }
  };

  const handleTriggerSync = async () => {
    setLoading(true);
    try {
      const ac = new AbortController();
      dataAbortRef.current = ac;
      const run = await syncService.triggerSync(ac.signal);
      setLatestRun(run);
      setMessage("Workspace sync started.");
    } catch (err: any) {
      setMessage(err?.message || "Failed to start sync");
    } finally {
      setLoading(false);
      setTimeout(() => setMessage(""), 3000);
    }
  };

  const handleAttach = async () => {
    if (!attachContent) return setMessage("Paste content to attach");
    setLoading(true);
    try {
      await contextService.attachContext({ content: attachContent });
      setAttachContent("");
      setMessage("Context attached successfully.");
    } catch (err: any) {
      setMessage(err?.message || "Failed to attach context");
    } finally {
      setLoading(false);
      setTimeout(() => setMessage(""), 3000);
    }
  };

  return (
    <ErrorBoundary>
      <div className="max-w-4xl mx-auto p-4 md:p-6 space-y-6 animate-fade-in">
      <div className="flex items-center justify-between border-b border-slate-800/60 pb-4">
        <div>
          <h1 className="text-xl font-bold tracking-wide text-white uppercase font-mono">Files & RAG</h1>
          <p className="text-xs text-slate-400 mt-1">Manage workspace sync, indexing, and attach ad-hoc context.</p>
        </div>
        <div className="flex items-center gap-3">
          <button onClick={handleTriggerSync} disabled={loading} className="px-3 py-1 bg-slate-900 border border-slate-800 rounded-lg text-xs text-slate-300">Trigger Sync</button>
        </div>
      </div>

      {message && (
        <div className="text-xs text-slate-300 bg-slate-900/40 p-3 rounded-md">{message}</div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card className="p-4 bg-slate-900/40 border-slate-800/80 rounded-2xl">
          <h2 className="text-xs font-mono font-bold text-slate-300 uppercase mb-3">Workspace Intelligence</h2>
          <pre className="text-[11px] text-slate-400 max-h-60 overflow-auto whitespace-pre-wrap">{JSON.stringify(intelligence ?? {}, null, 2)}</pre>
        </Card>

        <Card className="p-4 bg-slate-900/40 border-slate-800/80 rounded-2xl">
          <h2 className="text-xs font-mono font-bold text-slate-300 uppercase mb-3">Latest Sync Run</h2>
          {latestRun ? (
            <div className="text-xs text-slate-300">
              <div>Status: <span className="font-mono text-slate-200 font-bold">{latestRun.status}</span></div>
              <div className="mt-2 text-[11px] text-slate-400">{latestRun.progress_message}</div>
            </div>
          ) : (
            <div className="text-xs text-slate-500 italic">No recent sync run.</div>
          )}
        </Card>
      </div>

      <Card className="p-4 bg-slate-900/40 border-slate-800/80 rounded-2xl">
        <h2 className="text-xs font-mono font-bold text-slate-300 uppercase mb-3">Add Include Path</h2>
        <div className="flex gap-2">
          <input value={includePath} onChange={(e) => setIncludePath(e.target.value)} placeholder="/home/user/projects/myrepo" className="flex-1 px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-sm text-slate-200" />
          <button onClick={handleAddInclude} disabled={loading} className="px-3 py-2 bg-cyan-800 text-xs rounded-lg">Add</button>
        </div>
      </Card>

      <Card className="p-4 bg-slate-900/40 border-slate-800/80 rounded-2xl">
        <h2 className="text-xs font-mono font-bold text-slate-300 uppercase mb-3">Attach Ad-hoc Context</h2>
        <textarea value={attachContent} onChange={(e) => setAttachContent(e.target.value)} rows={6} className="w-full p-3 bg-slate-950 border border-slate-800 rounded-lg text-sm text-slate-200" placeholder="Paste text or small document content to attach for immediate retrieval in RAG..."></textarea>
        <div className="flex justify-end mt-3">
          <button onClick={handleAttach} disabled={loading} className="px-3 py-2 bg-cyan-800 text-xs rounded-lg">Attach</button>
        </div>
      </Card>
      </div>
    </ErrorBoundary>
  );
}
