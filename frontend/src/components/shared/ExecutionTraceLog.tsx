"use client";

import React, { useEffect, useState, useRef } from "react";
import { apiClient } from "@/services/api/client";
import { Play, Check, AlertCircle, Loader2, Code, Terminal, ChevronDown, ChevronUp } from "lucide-react";

interface TraceEvent {
  index: number;
  type: string;
  timestamp: string;
  source: string;
  payload: any;
  human_readable: string;
}

interface ExecutionTraceLogProps {
  active: boolean;
  executionId: string | null;
  onExecutionFound: (id: string) => void;
  queryText: string;
}

export function ExecutionTraceLog({
  active,
  executionId,
  onExecutionFound,
  queryText,
}: ExecutionTraceLogProps) {
  const [events, setEvents] = useState<TraceEvent[]>([]);
  const [status, setStatus] = useState<string>("idle");
  const [isExpanded, setIsExpanded] = useState(true);
  const logEndRef = useRef<HTMLDivElement>(null);
  const pollIntervalRef = useRef<NodeJS.Timeout | null>(null);

  // Auto-scroll to bottom of logs
  useEffect(() => {
    if (isExpanded) {
      logEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  }, [events, isExpanded]);

  // Main polling logic
  useEffect(() => {
    // Clear any active polling on change
    if (pollIntervalRef.current) {
      clearInterval(pollIntervalRef.current);
      pollIntervalRef.current = null;
    }

    if (!active) {
      // If no longer active but we have an executionId, fetch it one final time to show complete status
      if (executionId) {
        fetchExecutionDetails(executionId);
      }
      return;
    }

    setStatus("running");

    const poll = async () => {
      try {
        if (!executionId) {
          // 1. Poll the executions list to find the active running job
          const res = await apiClient.get<any[]>("/execution?limit=5");
          const runningJob = res.data.find(
            (job) => job.status === "running" || job.summary?.goal?.toLowerCase().includes(queryText.toLowerCase().slice(0, 15))
          );

          if (runningJob) {
            onExecutionFound(runningJob.execution_id);
          }
        } else {
          // 2. Poll details of the found execution
          await fetchExecutionDetails(executionId);
        }
      } catch (err) {
        console.error("Trace polling error:", err);
      }
    };

    // Run poll immediately, then set interval
    poll();
    pollIntervalRef.current = setInterval(poll, 700);

    return () => {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
      }
    };
  }, [active, executionId, queryText]);

  const fetchExecutionDetails = async (id: string) => {
    try {
      const res = await apiClient.get<any>(`/execution/${id}`);
      if (res.data && res.data.timeline) {
        setEvents(res.data.timeline);
        setStatus(res.data.status);
      }
    } catch (err) {
      console.error("Failed to load execution details:", err);
    }
  };

  if (!active && events.length === 0) return null;

  // Render specific styles/icons for stages
  const getEventIcon = (event: TraceEvent) => {
    const stage = event.payload?.stage?.toLowerCase();
    const type = event.type;

    if (stage === "workflow_start") {
      return <Play size={12} className="text-cyan-400 shrink-0 mt-0.5" />;
    }
    if (stage === "node_start") {
      return <Loader2 size={12} className="text-amber-400 animate-spin shrink-0 mt-0.5" />;
    }
    if (stage === "node_completed") {
      return event.payload?.status === "success" 
        ? <Check size={12} className="text-emerald-400 shrink-0 mt-0.5" />
        : <AlertCircle size={12} className="text-rose-400 shrink-0 mt-0.5" />;
    }
    if (type === "EXECUTION_COMPLETED") {
      return <Check size={12} className="text-emerald-400 shrink-0 mt-0.5" />;
    }
    return <Code size={12} className="text-slate-400 shrink-0 mt-0.5" />;
  };

  return (
    <div className="border border-slate-800/80 rounded-lg bg-slate-950/80 backdrop-blur-sm overflow-hidden transition-all duration-300">
      {/* Header */}
      <button 
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full px-3 py-2 flex items-center justify-between bg-slate-900/60 border-b border-slate-800/60 text-slate-300 font-mono text-[10px] tracking-wider uppercase select-none hover:bg-slate-900 transition-colors"
      >
        <span className="flex items-center gap-2">
          <Terminal size={12} className="text-cyan-400" />
          <span>System Execution Log ({status})</span>
          {executionId && <span className="text-slate-500 font-normal">#{executionId.slice(0, 8)}</span>}
        </span>
        {isExpanded ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
      </button>

      {/* Body */}
      {isExpanded && (
        <div className="p-3 max-h-56 overflow-y-auto space-y-2 font-mono text-[11px] leading-relaxed text-slate-300 select-text scrollbar-thin">
          {events.length === 0 ? (
            <div className="flex items-center gap-2 text-slate-500">
              <Loader2 size={12} className="animate-spin text-cyan-400" />
              <span>Spawning execution engine graph...</span>
            </div>
          ) : (
            events.map((event, idx) => {
              const dateStr = event.timestamp ? new Date(event.timestamp).toLocaleTimeString() : "";
              const stage = event.payload?.stage;
              const isStart = stage === "workflow_start";
              const isEnd = event.type === "EXECUTION_COMPLETED";
              const isNodeStart = stage === "node_start";
              const isNodeEnd = stage === "node_completed";
              
              let textClass = "text-slate-300";
              if (isStart || isEnd) textClass = "text-cyan-400 font-semibold";
              if (isNodeStart) textClass = "text-amber-400/90";
              if (isNodeEnd && event.payload?.status === "success") textClass = "text-slate-400";
              if (isNodeEnd && event.payload?.status === "failed") textClass = "text-rose-400 font-medium";

              return (
                <div key={idx} className={`flex items-start gap-2.5 ${textClass}`}>
                  <span className="text-slate-600 select-none">{dateStr}</span>
                  {getEventIcon(event)}
                  <div className="flex-1">
                    <span>{event.human_readable}</span>
                    {isNodeEnd && event.payload?.duration_ms && (
                      <span className="text-slate-500 ml-1.5 font-normal">
                        ({event.payload.duration_ms}ms)
                      </span>
                    )}
                    
                    {/* Render tool details if expanded/detailed */}
                    {isNodeEnd && event.payload?.tool && isExpanded && (
                      <div className="text-[10px] text-slate-500 pl-4 mt-0.5 border-l border-slate-800">
                        <span>Args: {JSON.stringify(event.payload.input)}</span>
                      </div>
                    )}
                  </div>
                </div>
              );
            })
          )}

          {/* Flash cursor if running */}
          {active && events.length > 0 && (
            <div className="flex items-center gap-2 text-cyan-400 select-none pl-[60px] animate-pulse">
              <span>●</span>
              <span className="text-slate-500">SYS_EXEC_WAITING</span>
              <span className="w-1.5 h-3 bg-cyan-400 inline-block animate-ping"></span>
            </div>
          )}
          <div ref={logEndRef} />
        </div>
      )}
    </div>
  );
}
