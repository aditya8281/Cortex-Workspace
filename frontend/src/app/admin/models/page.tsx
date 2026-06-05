"use client";

import { useState, useEffect } from "react";
import { Card, Badge, Spinner, Button } from "@/components/ui/base";
import { modelsService } from "@/services/api/models";
import type { CortexModel } from "@/types/api";

export default function AdminModelsPage() {
  const [models, setModels] = useState<CortexModel[]>([]);
  const [loading, setLoading] = useState(true);
  const [viewingModel, setViewingModel] = useState<CortexModel | null>(null);

  useEffect(() => {
    const fetchModels = async () => {
      try {
        setLoading(true);
        const data = await modelsService.listAllModels();
        setModels(data);
      } catch (error) {
        console.error("Failed to fetch models:", error);
      } finally {
        setLoading(false);
      }
    };
    fetchModels();
  }, []);

  if (loading) {
    return (
      <div className="p-6 flex items-center justify-center min-h-[400px]">
        <Spinner />
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6 max-w-5xl mx-auto animate-fade-in relative">
      <div className="border-b border-slate-800 pb-4">
        <h1 className="text-3xl font-bold font-mono tracking-wide">Model Registry</h1>
        <p className="text-xs text-slate-400 mt-1">Admin catalog listing all active and registered cognitive models in the workspace.</p>
      </div>

      <Card className="bg-slate-900/40 border-slate-800/80 rounded-2xl overflow-hidden p-4">
        <div className="overflow-x-auto">
          <table className="w-full text-left font-sans text-xs">
            <thead className="border-b border-slate-800 text-slate-400 font-mono uppercase tracking-wider">
              <tr>
                <th className="pb-3 text-[10px] font-bold">Name</th>
                <th className="pb-3 text-[10px] font-bold">Type</th>
                <th className="pb-3 text-[10px] font-bold">Provider</th>
                <th className="pb-3 text-[10px] font-bold">Context Limit</th>
                <th className="pb-3 text-[10px] font-bold text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/50">
              {models.map((model) => (
                <tr key={model.id} className="hover:bg-slate-900/30 transition-colors">
                  <td className="py-3.5 font-medium text-slate-200">{model.name}</td>
                  <td className="py-3.5">
                    <Badge>{model.type}</Badge>
                  </td>
                  <td className="py-3.5 text-slate-400 font-mono">
                    {model.provider_id || "N/A"}
                  </td>
                  <td className="py-3.5 text-slate-400 font-mono">
                    {model.context_length ? model.context_length.toLocaleString() : "-"}
                  </td>
                  <td className="py-3.5 text-right">
                    <Button size="sm" variant="ghost" onClick={() => setViewingModel(model)} className="text-cyan-400 hover:text-cyan-300">
                      View
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      {/* Model View Modal */}
      {viewingModel && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-fade-in">
          <Card className="w-full max-w-lg p-6 bg-slate-900 border-slate-800/80 rounded-2xl shadow-2xl relative">
            <h2 className="text-sm font-mono font-bold tracking-wider text-slate-200 uppercase mb-4 pb-2 border-b border-slate-800">
              Model Details: {viewingModel.name}
            </h2>

            <div className="space-y-4 font-mono text-[11px] text-slate-300 leading-relaxed">
              <div className="grid grid-cols-3 gap-2 py-1.5 border-b border-slate-800/50">
                <span className="text-slate-500 uppercase">Model Identifier</span>
                <span className="col-span-2 text-slate-200 break-all">{viewingModel.name}</span>
              </div>
              <div className="grid grid-cols-3 gap-2 py-1.5 border-b border-slate-800/50">
                <span className="text-slate-500 uppercase">Engine Type</span>
                <span className="col-span-2 text-slate-200">{viewingModel.type}</span>
              </div>
              <div className="grid grid-cols-3 gap-2 py-1.5 border-b border-slate-800/50">
                <span className="text-slate-500 uppercase">Provider Source</span>
                <span className="col-span-2 text-slate-200">{viewingModel.provider_id || "System"}</span>
              </div>
              <div className="grid grid-cols-3 gap-2 py-1.5 border-b border-slate-800/50">
                <span className="text-slate-500 uppercase">Context window</span>
                <span className="col-span-2 text-slate-200">{viewingModel.context_length ? `${viewingModel.context_length.toLocaleString()} tokens` : "System Managed"}</span>
              </div>
              {viewingModel.parameters && (
                <div className="grid grid-cols-3 gap-2 py-1.5 border-b border-slate-800/50">
                  <span className="text-slate-500 uppercase">Parameters Size</span>
                  <span className="col-span-2 text-slate-200">{viewingModel.parameters}</span>
                </div>
              )}
              {viewingModel.api_endpoint && (
                <div className="grid grid-cols-3 gap-2 py-1.5 border-b border-slate-800/50">
                  <span className="text-slate-500 uppercase">API Connection</span>
                  <span className="col-span-2 text-slate-200 break-all">{viewingModel.api_endpoint}</span>
                </div>
              )}
              <div className="grid grid-cols-3 gap-2 py-1.5 border-b border-slate-800/50">
                <span className="text-slate-500 uppercase">Status</span>
                <span className="col-span-2">
                  <Badge variant={viewingModel.status === "active" ? "secondary" : "danger"}>
                    {viewingModel.status || "inactive"}
                  </Badge>
                </span>
              </div>
            </div>

            <div className="flex justify-end pt-4 mt-6 border-t border-slate-800/80">
              <Button
                type="button"
                variant="secondary"
                onClick={() => setViewingModel(null)}
                className="border border-slate-800 rounded-xl bg-slate-950 text-slate-300 px-4 text-xs font-semibold"
              >
                Close details
              </Button>
            </div>
          </Card>
        </div>
      )}
    </div>
  );
}
