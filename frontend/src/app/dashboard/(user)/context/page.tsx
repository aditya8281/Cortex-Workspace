"use client";

import { useState, useEffect } from "react";
import { Card } from "@/components/ui/base";
import { contextService } from "@/services/api/context";
import { Input, Button } from "@/components/ui/base";

export default function ContextPage() {
  const [path, setPath] = useState("");
  const [content, setContent] = useState("");
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  useEffect(() => {
    setMessage(null);
  }, []);

  const handleAttach = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setMessage(null);
    try {
      const payload: any = {};
      if (path.trim()) payload.path = path.trim();
      if (content.trim()) payload.content = content.trim();
      const res = await contextService.attachContext(payload);
      setMessage(res?.message || "Context attached successfully.");
      setPath("");
      setContent("");
    } catch (err: any) {
      setMessage(err?.response?.data?.detail || err?.message || "Failed to attach context.");
      console.error("Attach context error:", err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto p-4 md:p-6 space-y-6 animate-fade-in">
      <div className="border-b border-slate-800/60 pb-4">
        <h1 className="text-xl font-bold tracking-wide text-white uppercase font-mono">Attach Context</h1>
        <p className="text-xs text-slate-400 mt-1">Attach a file path or paste a snippet to include as context for intelligence queries.</p>
      </div>

      <Card className="p-6">
        <form onSubmit={handleAttach} className="space-y-4">
          <div>
            <label className="text-xs text-slate-400 block mb-1">Path (optional)</label>
            <input
              value={path}
              onChange={(e) => setPath(e.target.value)}
              placeholder="/path/to/file/or/folder"
              className="w-full px-3 py-2 bg-slate-950/60 border border-slate-800 rounded-xl text-xs text-slate-200"
            />
          </div>

          <div>
            <label className="text-xs text-slate-400 block mb-1">Content (optional)</label>
            <textarea
              value={content}
              onChange={(e) => setContent(e.target.value)}
              placeholder="Paste code, notes or contextual text..."
              className="w-full min-h-[120px] p-3 bg-slate-950/60 border border-slate-800 rounded-xl text-xs text-slate-200"
            />
          </div>

          <div className="flex items-center gap-2">
            <button
              type="submit"
              disabled={loading}
              className="px-4 py-2 bg-gradient-to-r from-cyan-600 to-blue-600 text-white text-xs rounded-xl disabled:opacity-50"
            >
              {loading ? "Attaching..." : "Attach Context"}
            </button>
            {message && <span className="text-xs text-slate-400">{message}</span>}
          </div>
        </form>
      </Card>
    </div>
  );
}
