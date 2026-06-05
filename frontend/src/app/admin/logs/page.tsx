"use client";

import { useState, useEffect } from "react";
import { Card, Badge, Spinner, Button } from "@/components/ui/base";
import { adminService } from "@/services/api/admin";
import { aiService } from "@/services/api/ai";
import { Terminal, Clock, Activity, Play, CheckCircle, XCircle, FileText, AlertCircle, RefreshCw } from "lucide-react";

export default function LogsPage() {
  const [executions, setExecutions] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [filterStatus, setFilterStatus] = useState("ALL");
  const [viewingExecutionId, setViewingExecutionId] = useState<string | null>(null);
  const [replaySteps, setReplaySteps] = useState<any[]>([]);
  const [replayLoading, setReplayLoading] = useState(false);
  const [error, setError] = useState("");

  const fetchExecutions = async () => {
    try {
      const data = await adminService.getExecutionLogs(100);
      setExecutions(data || []);
    } catch (err: any) {
      console.error(err);
      setError(err.message || "Failed to load execution runs.");
    }
  };

  useEffect(() => {
    const init = async () => {
      setLoading(true);
      setError("");
      await fetchExecutions();
      setLoading(false);
    };
    init();
  }, []);

  const handleOpenReplay = async (execId: string) => {
    setViewingExecutionId(execId);
    setReplayLoading(true);
    setReplaySteps([]);
    try {
      const data = await aiService.replayExecution(execId);
      setReplaySteps(data?.replay || []);
    } catch (err: any) {
      console.error(err);
      setError(`Failed to retrieve trace for ${execId}`);
    } finally {
      setReplayLoading(false);
    }
  };

  const filteredExecutions = executions.filter((exec) => {
    if (filterStatus === "ALL") return true;
    return (exec.status || "").toUpperCase() === filterStatus;
  });

  if (loading) {
    return (
      <div className="p-6 flex items-center justify-center min-h-[400px]">
        <Spinner />
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6 max-w-5xl mx-auto animate-fade-in relative">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between border-b border-slate-800 pb-4 gap-4">
        <div>
          <h1 className="text-3xl font-bold font-mono tracking-wide flex items-center gap-2">
            <Terminal className="text-cyan-400 w-8 h-8" />
            Agent Execution Runs
          </h1>
          <p className="text-xs text-slate-400 mt-1">Audit execution traces, cognitive orchestration stages, and tool execution logs.</p>
        </div>

        <div className="flex items-center gap-2 font-mono text-xs">
          <select
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value)}
            className="bg-slate-900 border border-slate-800 px-4 py-2 rounded-xl text-slate-200 focus:outline-none"
          >
            <option value="ALL">ALL STATUSES</option>
            <option value="RUNNING">RUNNING</option>
            <option value="SUCCESS">SUCCESS</option>
            <option value="FAILED">FAILED</option>
          </select>

          <button
            onClick={fetchExecutions}
            className="flex items-center gap-1.5 px-4 py-2 bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-300 font-semibold rounded-xl"
          >
            <RefreshCw size={12} />
            Refresh
          </button>
        </div>
      </div>

      {error && (
        <div className="flex items-start gap-2.5 bg-rose-955/20 border border-rose-900/30 rounded-xl p-4 text-rose-400 text-xs font-sans">
          <AlertCircle className="w-4.5 h-4.5 text-rose-500 shrink-0 mt-0.5" />
          <span className="leading-relaxed">{error}</span>
        </div>
      )}

      <div className="grid grid-cols-1 gap-4">
        {filteredExecutions.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-16 text-center border border-dashed border-slate-800 rounded-2xl">
            <Activity className="w-8 h-8 text-slate-600 mb-2" />
            <p className="text-xs font-mono text-slate-500 uppercase tracking-wider">No Execution Runs Tracked</p>
          </div>
        ) : (
          filteredExecutions.map((exec) => {
            const statusUpper = (exec.status || "UNKNOWN").toUpperCase();
            const startedAt = exec.summary?.started_at ? new Date(exec.summary.started_at).toLocaleString() : "";
            const isFailed = statusUpper === "FAILED" || (exec.summary?.error_count || 0) > 0;
            
            return (
              <Card key={exec.execution_id} className="p-4 bg-slate-900/40 border-slate-800/80 rounded-2xl hover:border-slate-800 transition-all flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div className="space-y-2 min-w-0">
                  <div className="flex items-center gap-2">
                    <Badge variant={statusUpper === "SUCCESS" ? "primary" : isFailed ? "danger" : "secondary"}>
                      {statusUpper}
                    </Badge>
                    <span className="font-mono text-xs text-slate-200 truncate">{exec.execution_id}</span>
                  </div>
                  
                  <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-[10px] font-mono text-slate-500">
                    <div className="flex items-center gap-1">
                      <Clock size={11} />
                      <span>{startedAt || exec.last_timestamp || "N/A"}</span>
                    </div>
                    {exec.event_count > 0 && (
                      <div className="flex items-center gap-1">
                        <Activity size={11} />
                        <span>{exec.event_count} telemetry events</span>
                      </div>
                    )}
                    {exec.summary?.steps_executed > 0 && (
                      <div className="flex items-center gap-1">
                        <Play size={11} />
                        <span>{exec.summary.steps_executed} steps executed</span>
                      </div>
                    )}
                  </div>
                  {exec.summary?.tools_used?.length > 0 && (
                    <div className="text-[10px] font-mono text-slate-500">
                      Tools: <span className="text-slate-400 font-semibold">{exec.summary.tools_used.join(", ")}</span>
                    </div>
                  )}
                </div>

                <div className="shrink-0 flex items-center justify-end">
                  <Button
                    size="sm"
                    onClick={() => handleOpenReplay(exec.execution_id)}
                    className="px-4 py-1.5 bg-slate-950 border border-slate-850 hover:border-slate-700 text-cyan-400 hover:text-cyan-300 rounded-xl font-semibold text-xs"
                  >
                    View Trace
                  </Button>
                </div>
              </Card>
            );
          })
        )}
      </div>

      {/* Execution Trace Modal */}
      {viewingExecutionId && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-fade-in">
          <Card className="w-full max-w-2xl p-6 bg-slate-900 border-slate-800/80 rounded-2xl shadow-2xl relative flex flex-col max-h-[85vh]">
            <h2 className="text-sm font-mono font-bold tracking-wider text-slate-200 uppercase mb-4 pb-2 border-b border-slate-800 flex items-center justify-between">
              <span>Execution replay: {viewingExecutionId.slice(0, 18)}...</span>
              <span className="text-[10px] text-slate-500 lowercase">trace logs</span>
            </h2>

            <div className="flex-1 overflow-y-auto space-y-3.5 pr-2 scrollbar-thin">
              {replayLoading ? (
                <div className="flex flex-col items-center justify-center py-12 gap-2.5">
                  <Spinner />
                  <span className="text-[10px] font-mono text-slate-500 uppercase tracking-wider animate-pulse">Loading step replay telemetry...</span>
                </div>
              ) : replaySteps.length === 0 ? (
                <div className="text-xs text-slate-500 font-mono italic text-center py-8">No steps registered for this execution.</div>
              ) : (
                replaySteps.map((step, idx) => {
                  const stepType = (step.raw?.type || "").toUpperCase();
                  const isErr = stepType.includes("FAILED") || stepType.includes("ERROR");
                  const isComp = stepType.includes("COMPLETED") || stepType.includes("END");
                  
                  return (
                    <div key={idx} className="p-3 bg-slate-950/40 border border-slate-900 rounded-xl flex items-start gap-2.5 font-mono text-[11px] hover:border-slate-850 transition-colors">
                      <div className="mt-0.5">
                        {isErr ? (
                          <XCircle className="w-3.5 h-3.5 text-rose-500" />
                        ) : isComp ? (
                          <CheckCircle className="w-3.5 h-3.5 text-emerald-500" />
                        ) : (
                          <FileText className="w-3.5 h-3.5 text-cyan-400" />
                        )}
                      </div>
                      
                      <div className="space-y-1 flex-1 min-w-0">
                        <div className="flex items-center justify-between gap-4">
                          <span className="text-slate-400 font-bold">Step {step.step != null ? step.step : idx}</span>
                          <span className="text-[9px] text-slate-600">{step.raw?.timestamp ? new Date(step.raw.timestamp).toLocaleTimeString() : ""}</span>
                        </div>
                        <p className="text-slate-200 leading-relaxed break-words">{step.action}</p>
                        {step.raw?.payload?.tool && (
                          <div className="text-[9px] text-slate-500 bg-slate-900/60 p-1 px-1.5 rounded inline-block mt-1">
                            tool: {step.raw.payload.tool}
                          </div>
                        )}
                      </div>
                    </div>
                  );
                })
              )}
            </div>

            <div className="flex justify-end pt-4 mt-4 border-t border-slate-800/80 shrink-0">
              <Button
                type="button"
                variant="secondary"
                onClick={() => setViewingExecutionId(null)}
                className="border border-slate-800 rounded-xl bg-slate-950 text-slate-300 px-4 text-xs font-semibold"
              >
                Close Trace
              </Button>
            </div>
          </Card>
        </div>
      )}
    </div>
  );
}
