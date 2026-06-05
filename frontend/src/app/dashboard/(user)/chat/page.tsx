"use client";

import { useState, useEffect, useRef } from "react";
import { useIsMounted } from "@/hooks/useIsMounted";
import { useDispatch, useSelector } from "react-redux";
import { Button, Card, Spinner } from "@/components/ui/base";
import { aiService } from "@/services/api/ai";
import { modelsService } from "@/services/api/models";
import { addMessage, setLoading, setCurrentModel } from "@/state/slices/chat";
import type { RootState } from "@/state/store";
import type { ChatMessage } from "@/types/api";
import { Send, Sparkles, Terminal } from "lucide-react";
import { ExecutionTraceLog } from "@/components/shared/ExecutionTraceLog";
import { ErrorMessage } from "@/components/shared/ErrorDisplay";
import { ErrorBoundary } from "@/components/shared/ErrorBoundary";

export default function ChatPage() {
  const dispatch = useDispatch();
  const { messages, loading, currentModel } = useSelector((state: RootState) => state.chat);
  const [query, setQuery] = useState("");
  const [models, setModels] = useState<any[]>([]);
  const [pageError, setPageError] = useState<string | null>(null);

  // Execution Trace states
  const [activeExecutionId, setActiveExecutionId] = useState<string | null>(null);
  const [activeQueryText, setActiveQueryText] = useState<string>("");
  const [isProcessing, setIsProcessing] = useState<boolean>(false);
  const mountedRef = useIsMounted();
  const askAbortRef = useRef<AbortController | null>(null);

  useEffect(() => {
    const mounted = mountedRef.current;
    const fetchModels = async () => {
      try {
        const data = await modelsService.listAllModels();
        if (!mountedRef.current) return;
        setModels(data);
        // Set auto or first model as default if none set
        if (data.length > 0 && !currentModel) {
          dispatch(setCurrentModel(data[0].name));
        }
      } catch (error) {
        console.error("Failed to fetch models:", error);
      }
    };
    fetchModels();
  }, [currentModel, dispatch]);

  const handleSendQuery = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    const currentQuery = query;
    const userMessage: ChatMessage = {
      role: "user",
      content: currentQuery,
      timestamp: new Date().toISOString(),
    };
    
    dispatch(addMessage(userMessage));
    dispatch(setLoading(true));
    setQuery("");

    // Start tracking trace logs
    setActiveExecutionId(null);
    setActiveQueryText(currentQuery);
    setIsProcessing(true);

    try {
      if (askAbortRef.current) {
        try { askAbortRef.current.abort(); } catch (e) {}
      }
      const ac = new AbortController();
      askAbortRef.current = ac;
      const response = await aiService.ask(
        {
          query: currentQuery,
          llm_model: currentModel,
        },
        ac.signal
      );

      if (!response || !response.response) {
        throw new Error("Invalid response from AI service");
      }

      const assistantMessage: ChatMessage = {
        role: "assistant",
        content: response.response,
        timestamp: new Date().toISOString(),
        execution_id: response.execution_id,
      };
      
      if (response.execution_id) {
        if (mountedRef.current) setActiveExecutionId(response.execution_id);
      }
      
      if (mountedRef.current) dispatch(addMessage(assistantMessage));
    } catch (error) {
      const errorMsg = error instanceof Error ? error.message : "Failed to get response";
      const errorMessage: ChatMessage = {
        role: "assistant",
        content: `Error: ${errorMsg}`,
        timestamp: new Date().toISOString(),
      };
      if (mountedRef.current) dispatch(addMessage(errorMessage));
      console.error("Query failed:", error);
      if (mountedRef.current) setPageError(errorMsg);
    } finally {
      if (mountedRef.current) dispatch(setLoading(false));
      if (mountedRef.current) setIsProcessing(false);
      // clear ask abort
      try { askAbortRef.current = null; } catch (e) {}
    }
  };

  useEffect(() => {
    return () => {
      if (askAbortRef.current) {
        try { askAbortRef.current.abort(); } catch (e) {}
      }
    };
  }, []);

  return (
    <ErrorBoundary>
      <div className="max-w-4xl mx-auto p-4 md:p-6 flex flex-col h-[calc(100vh-2.75rem)] gap-4">
      {/* Top Header Controls */}
      <div className="flex items-center justify-between border-b border-slate-800/60 pb-3">
        <div className="flex items-center gap-2">
          <Terminal size={18} className="text-cyan-400" />
          <h1 className="text-lg font-mono font-bold tracking-wider text-slate-100 uppercase">SYS_WORKFLOW_AGENT</h1>
        </div>
        
        <div className="flex items-center gap-2">
          <span className="text-[10px] font-mono text-slate-500 uppercase">Model Target</span>
          <select
            value={currentModel}
            onChange={(e) => dispatch(setCurrentModel(e.target.value))}
            className="bg-slate-900 border border-slate-800 px-3 py-1 text-xs rounded font-sans text-slate-300 focus:outline-none focus:border-cyan-500/40"
          >
            {models.map((m) => (
              <option key={m.id || m.name} value={m.name}>
                {m.name}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Messages Window */}
      <Card className="flex-1 overflow-y-auto p-4 space-y-4 bg-slate-900/40 border-slate-800/80 shadow-[inset_0_2px_4px_rgba(0,0,0,0.15)] flex flex-col scrollbar-thin rounded-xl">
        {messages.length === 0 ? (
          <div className="flex-1 flex flex-col items-center justify-center text-center p-8 space-y-4">
            <div className="p-3 bg-cyan-500/5 rounded-full border border-cyan-500/10">
              <Sparkles size={28} className="text-cyan-400 animate-pulse" />
            </div>
            <div className="max-w-xs space-y-1">
              <h3 className="font-mono text-xs font-bold tracking-wide text-slate-200 uppercase">AWAITING INPUT</h3>
              <p className="text-xs text-slate-500 font-sans">Ask Cortex to analyze files, fetch memories, sync intelligence, or explain code structures.</p>
            </div>
          </div>
        ) : (
          <div className="space-y-4 flex-1">
            {messages.map((msg, idx) => {
              const isUser = msg.role === "user";
              return (
                <div
                  key={idx}
                  className={`flex flex-col max-w-[80%] ${isUser ? "ml-auto items-end" : "mr-auto items-start"}`}
                >
                  <div
                    className={`px-4 py-3 rounded-2xl ${
                      isUser
                        ? "bg-slate-800/80 border border-cyan-500/20 text-slate-100 rounded-tr-none shadow-[0_4px_12px_rgba(6,182,212,0.05)]"
                        : "bg-slate-900/60 border border-slate-800/80 text-slate-200 rounded-tl-none shadow-[0_4px_12px_rgba(0,0,0,0.1)]"
                    }`}
                  >
                    <p className="text-xs whitespace-pre-wrap leading-relaxed select-text font-sans">{msg.content}</p>
                  </div>
                  <span className="text-[9px] font-mono text-slate-500 mt-1 px-1">
                    {new Date(msg.timestamp || "").toLocaleTimeString()}
                  </span>
                </div>
              );
            })}
            
            {/* Show thinking state inside messages */}
            {loading && (
              <div className="flex items-center gap-2 px-4 py-3 bg-slate-900/60 border border-slate-800/60 rounded-2xl rounded-tl-none mr-auto max-w-[80%]">
                <Spinner />
                <span className="text-xs font-mono text-slate-400 tracking-wider uppercase animate-pulse">Orchestrator reasoning...</span>
              </div>
            )}
          </div>
        )}
      </Card>

      {/* Real-time execution tracing */}
      {(isProcessing || activeExecutionId) && (
        <ExecutionTraceLog
          active={isProcessing}
          executionId={activeExecutionId}
          onExecutionFound={(id) => setActiveExecutionId(id)}
          queryText={activeQueryText}
        />
      )}

      {/* Input Form */}
      <form onSubmit={handleSendQuery} className="flex gap-2">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Query workspace or run tasks..."
          className="flex-1 bg-slate-900/80 border border-slate-800/80 px-4 py-2.5 rounded-xl text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-cyan-500/40 font-sans shadow-inner transition-colors duration-150"
          disabled={loading}
        />
        <Button 
          type="submit" 
          loading={loading} 
          size="md" 
          className="rounded-xl px-5 bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 border-none transition-all shadow-[0_4px_12px_rgba(6,182,212,0.15)] flex items-center justify-center"
        >
          <Send size={16} />
        </Button>
      </form>
      </div>
    </ErrorBoundary>
  );
}
