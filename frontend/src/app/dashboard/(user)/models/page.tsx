"use client";

import { useState, useEffect } from "react";
import { Card, Badge } from "@/components/ui/base";
import { modelsService, routingService } from "@/services/api/models";
import type { CortexModel, CortexProvider, CortexRoutingProfile } from "@/types/api";
import { Cpu, Server, ToggleLeft, Layers, RefreshCw, AlertCircle, HelpCircle } from "lucide-react";

export default function ModelsPage() {
  const [models, setModels] = useState<CortexModel[]>([]);
  const [providers, setProviders] = useState<CortexProvider[]>([]);
  const [profiles, setProfiles] = useState<CortexRoutingProfile[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const fetchData = async () => {
    try {
      setLoading(true);
      setError("");
      const [modelsData, providersData, profilesData] = await Promise.all([
        modelsService.listAllModels(),
        modelsService.listProviders(),
        routingService.getProfiles(),
      ]);
      setModels(modelsData);
      setProviders(providersData);
      setProfiles(profilesData);
    } catch (err: any) {
      setError(err.message || "Failed to fetch data");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[calc(100vh-6rem)]">
        <div className="flex flex-col items-center gap-3">
          <RefreshCw className="w-8 h-8 text-cyan-400 animate-spin" />
          <span className="text-xs font-mono text-slate-500 uppercase tracking-widest">Loading registry telemetry...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto p-4 md:p-6 space-y-6 animate-fade-in">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between border-b border-slate-800/60 pb-4 gap-4">
        <div>
          <h1 className="text-xl font-bold tracking-wide text-white uppercase font-mono flex items-center gap-2">
            <Layers className="text-cyan-400 w-5 h-5" />
            Model Registry & Routing
          </h1>
          <p className="text-xs text-slate-400 font-sans mt-1">
            Manage provider connections, model telemetry parameters, and cognitive workflow routing profiles.
          </p>
        </div>

        <button
          onClick={fetchData}
          disabled={loading}
          className="flex items-center gap-1.5 px-4 py-2 bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-300 text-xs font-semibold rounded-xl active:translate-y-[1px] transition-all"
        >
          <RefreshCw size={12} className={loading ? "animate-spin" : ""} />
          Refresh Stats
        </button>
      </div>

      {error && (
        <div className="flex items-start gap-2.5 bg-red-950/20 border border-red-900/30 rounded-xl p-4 text-red-400 text-xs font-sans">
          <AlertCircle className="w-4 h-4 text-red-500 shrink-0 mt-0.5" />
          <span className="leading-relaxed">{error}</span>
        </div>
      )}

      {/* Grid of Telemetry */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Routing Profiles */}
        <Card className="bg-slate-900/40 border-slate-800/80 p-5 rounded-2xl relative">
          <div className="absolute top-0 right-0 p-3 text-[9px] font-mono text-slate-500">ROUTING_PROFILES</div>
          <h2 className="text-xs font-mono font-bold tracking-wider text-slate-300 uppercase mb-4 flex items-center gap-2 border-b border-slate-900 pb-2">
            <ToggleLeft className="text-cyan-400 w-4 h-4" />
            Orchestration Routing
          </h2>

          <div className="space-y-3">
            {profiles.length === 0 ? (
              <p className="text-xs text-slate-500 italic">No routing profiles detected.</p>
            ) : (
              profiles.map((profile) => (
                <div key={profile.id} className="flex items-center justify-between p-3 bg-slate-950/40 border border-slate-900 rounded-xl hover:border-slate-800 transition-all">
                  <div className="min-w-0 pr-3">
                    <p className="text-xs font-semibold text-slate-200 font-mono">{profile.name}</p>
                    <p className="text-[10px] text-slate-400 truncate max-w-xs">{profile.description}</p>
                  </div>
                  {profile.is_active ? (
                    <span className="text-[9px] font-mono font-bold tracking-wide uppercase px-2 py-0.5 bg-cyan-950/20 border border-cyan-900/30 rounded-full text-cyan-400">
                      Active
                    </span>
                  ) : (
                    <span className="text-[9px] font-mono tracking-wide uppercase px-2 py-0.5 bg-slate-900 border border-slate-800/40 rounded-full text-slate-500">
                      Standby
                    </span>
                  )}
                </div>
              ))
            )}
          </div>
        </Card>

        {/* Providers */}
        <Card className="bg-slate-900/40 border-slate-800/80 p-5 rounded-2xl relative">
          <div className="absolute top-0 right-0 p-3 text-[9px] font-mono text-slate-500">API_PROVIDERS</div>
          <h2 className="text-xs font-mono font-bold tracking-wider text-slate-300 uppercase mb-4 flex items-center gap-2 border-b border-slate-900 pb-2">
            <Server className="text-cyan-400 w-4 h-4" />
            Active Connections
          </h2>

          <div className="space-y-3">
            {providers.length === 0 ? (
              <p className="text-xs text-slate-500 italic">No backend providers configured.</p>
            ) : (
              providers.map((provider) => (
                <div key={provider.id} className="flex items-center justify-between p-3 bg-slate-950/40 border border-slate-900 rounded-xl hover:border-slate-800 transition-all">
                  <div>
                    <p className="text-xs font-semibold text-slate-200 font-mono">{provider.name}</p>
                    <p className="text-[10px] text-slate-500 font-sans mt-0.5">{provider.models?.length || 0} models linked</p>
                  </div>
                  <Badge variant={provider.status === "active" ? "secondary" : "danger"}>
                    {provider.status}
                  </Badge>
                </div>
              ))
            )}
          </div>
        </Card>
      </div>

      {/* Available Models */}
      <Card className="bg-slate-900/40 border-slate-800/80 p-5 rounded-2xl relative">
        <div className="absolute top-0 right-0 p-3 text-[9px] font-mono text-slate-500">MODELS_INVENTORY</div>
        <h2 className="text-xs font-mono font-bold tracking-wider text-slate-300 uppercase mb-4 flex items-center gap-2 border-b border-slate-900 pb-2">
          <Cpu className="text-cyan-400 w-4 h-4" />
          Available Cognitive Engine Inventory
        </h2>

        {models.length === 0 ? (
          <p className="text-xs text-slate-500 italic py-4">No compatible models indexed in registry.</p>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {models.map((model) => (
              <div key={model.id} className="p-4 bg-slate-950/40 border border-slate-900 rounded-xl hover:border-slate-800 transition-all relative overflow-hidden group">
                <div className="absolute top-0 right-0 px-2 py-0.5 bg-slate-900 text-[8px] font-mono text-slate-500 rounded-bl border-l border-b border-slate-800/40 uppercase group-hover:text-cyan-400 group-hover:border-cyan-500/20 transition-all">
                  {model.type}
                </div>
                <h3 className="font-mono text-xs font-semibold text-slate-200 truncate pr-16">{model.name}</h3>
                
                <div className="flex items-center gap-4 mt-3 text-[10px] font-mono text-slate-500">
                  {model.context_length ? (
                    <div>
                      CTX: <span className="text-slate-300 font-bold">{model.context_length.toLocaleString()} tokens</span>
                    </div>
                  ) : (
                    <div>CTX: <span className="text-slate-600">Auto-configured</span></div>
                  )}
                  {model.provider_id && (
                    <div>
                      SRC: <span className="text-slate-300 font-bold">{model.provider_id}</span>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>
    </div>
  );
}
