"use client";

import { useState, useEffect } from "react";
import { Card, Badge, Spinner, Button } from "@/components/ui/base";
import { adminService } from "@/services/api/admin";
import { AlertCircle, RefreshCw, ServerCrash } from "lucide-react";

export default function ServicesPage() {
  const [services, setServices] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [restarting, setRestarting] = useState<Record<string, boolean>>({});
  const [error, setError] = useState("");

  const fetchServices = async () => {
    try {
      const data = await adminService.listServices();
      setServices(data || []);
    } catch (err: any) {
      console.error(err);
      setError(err.message || "Failed to query background services.");
    }
  };

  useEffect(() => {
    const init = async () => {
      setLoading(true);
      setError("");
      await fetchServices();
      setLoading(false);
    };
    init();

    const interval = setInterval(fetchServices, 4000);
    return () => clearInterval(interval);
  }, []);

  const handleRestart = async (name: string) => {
    setRestarting((prev) => ({ ...prev, [name]: true }));
    setError("");
    try {
      await adminService.restartService(name);
      await fetchServices();
    } catch (err: any) {
      console.error(err);
      setError(err.message || `Failed to restart service ${name}`);
    } finally {
      setRestarting((prev) => ({ ...prev, [name]: false }));
    }
  };

  if (loading) {
    return (
      <div className="p-6 flex items-center justify-center min-h-[400px]">
        <Spinner />
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6 max-w-4xl mx-auto animate-fade-in">
      <div className="flex items-center justify-between border-b border-slate-800 pb-4">
        <div>
          <h1 className="text-3xl font-bold font-mono tracking-wide">Background Services</h1>
          <p className="text-xs text-slate-400 mt-1">Monitor thread watch loops and clean/restart connection pools in real-time.</p>
        </div>
        <button
          onClick={fetchServices}
          className="flex items-center gap-1 px-3 py-1.5 bg-slate-900 border border-slate-800 rounded-lg text-xs font-mono hover:bg-slate-800 text-slate-300"
        >
          <RefreshCw size={12} />
          Poll Status
        </button>
      </div>

      {error && (
        <div className="flex items-start gap-2.5 bg-rose-950/20 border border-rose-900/30 rounded-xl p-4 text-rose-400 text-xs font-sans">
          <AlertCircle className="w-4.5 h-4.5 text-rose-500 shrink-0 mt-0.5" />
          <span className="leading-relaxed">{error}</span>
        </div>
      )}

      {services.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-16 gap-3 text-center border border-dashed border-slate-800 rounded-2xl">
          <ServerCrash className="w-10 h-10 text-slate-600" />
          <p className="text-xs font-mono text-slate-500 uppercase tracking-widest">No Active Telemetry Handlers Registered</p>
        </div>
      ) : (
        <Card className="p-6 bg-slate-900/40 border-slate-800/80 rounded-2xl">
          <div className="space-y-4">
            {services.map((service, idx) => (
              <div
                key={idx}
                className="flex items-center justify-between p-4 bg-slate-950/40 border border-slate-900 rounded-xl hover:border-slate-850 transition-colors"
              >
                <div>
                  <p className="font-mono text-xs font-semibold text-slate-200">{service.name}</p>
                  <p className="text-[10px] text-slate-500 font-mono uppercase mt-1">Status: {service.uptime || "N/A"}</p>
                </div>
                <div className="flex items-center gap-4">
                  <Badge
                    variant={
                      service.status === "running" ? "secondary" : "danger"
                    }
                  >
                    {service.status.toUpperCase()}
                  </Badge>
                  
                  {service.name !== "API Gateway" ? (
                    <Button 
                      size="sm" 
                      variant="ghost" 
                      onClick={() => handleRestart(service.name)}
                      loading={!!restarting[service.name]}
                      className="text-cyan-400 hover:text-cyan-300 font-semibold rounded-xl border border-slate-850/50 bg-slate-950/40 px-3"
                    >
                      {restarting[service.name] ? "Restarting" : "Restart"}
                    </Button>
                  ) : (
                    <span className="text-[10px] font-mono text-slate-600 italic px-2">immutable</span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}
    </div>
  );
}
