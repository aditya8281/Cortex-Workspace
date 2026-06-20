"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Bot, Plus, Trash2, Clock, Play, CheckCircle, XCircle } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import Button from "../../src/shared/ui/Button";
import DashboardShell from "../../src/shared/layout/DashboardShell";
import { CollapsiblePanel } from "../../src/shared/ui/CollapsiblePanel";
import type { Agent, AgentRun } from "../../src/shared/types";
import { agentApi } from "../../src/shared/api/agent";
import { useAuth } from "../../src/shared/auth/AuthProvider";
import { cn } from "../../src/lib/utils";
import AgentChat from "./AgentChat";
import NeuralNetwork from "../../src/shared/ui/NeuralNetwork";

const statusIcons: Record<string, typeof Clock> = {
  pending: Clock,
  running: Play,
  completed: CheckCircle,
  failed: XCircle,
};

const statusColors: Record<string, string> = {
  pending: "text-text-muted",
  running: "text-accent",
  completed: "text-success",
  failed: "text-error",
};

export default function AgentsPage() {
  const router = useRouter();
  const { user, loading: authLoading } = useAuth();
  const [agents, setAgents] = useState<Agent[]>([]);
  const [runs, setRuns] = useState<AgentRun[]>([]);
  const [selectedAgent, setSelectedAgent] = useState<Agent | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [showCreate, setShowCreate] = useState(false);
  const [newName, setNewName] = useState("");
  const [newDesc, setNewDesc] = useState("");
  const [newPrompt, setNewPrompt] = useState("");
  const [creating, setCreating] = useState(false);

  useEffect(() => {
    if (!authLoading && !user) router.replace("/auth");
  }, [authLoading, user, router]);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [agentsData, runsData] = await Promise.all([
        agentApi.list(),
        agentApi.listRuns({ limit: 20 }),
      ]);
      setAgents(agentsData.agents);
      setRuns(runsData.runs);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load agents");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  async function handleCreateAgent() {
    if (!newName.trim() || !newPrompt.trim()) return;
    setCreating(true);
    try {
      const result = await agentApi.create({
        name: newName.trim(),
        description: newDesc.trim() || undefined,
        system_prompt: newPrompt.trim(),
      });
      setAgents((prev) => [...prev, result.agent]);
      setShowCreate(false);
      setNewName("");
      setNewDesc("");
      setNewPrompt("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create agent");
    } finally {
      setCreating(false);
    }
  }

  async function handleDeleteAgent(agentId: number) {
    if (!window.confirm("Delete this agent?")) return;
    try {
      await agentApi.delete(agentId);
      setAgents((prev) => prev.filter((a) => a.id !== agentId));
      if (selectedAgent?.id === agentId) setSelectedAgent(null);
    } catch {
      // silently fail
    }
  }

  function handleRunComplete(run: AgentRun) {
    setRuns((prev) => [run, ...prev]);
  }

  return (
    <DashboardShell>
      <NeuralNetwork intensity="low" />
      <div className="flex h-full bg-transparent">
        <CollapsiblePanel
          header={
            <div className="flex items-center gap-2">
              <div className="h-8 w-8 rounded-lg bg-accent/10 flex items-center justify-center">
                <Bot className="h-4 w-4 text-accent" />
              </div>
              <div>
                <h2 className="text-sm font-semibold text-text">Agents</h2>
                <p className="text-[10px] font-mono text-text-muted">{agents.length} agents</p>
              </div>
            </div>
          }
        >
          <div className="flex flex-col h-full">
            <div className="flex items-center justify-between mb-3">
              <span className="text-[10px] font-mono font-bold text-text-muted uppercase tracking-wider px-1">
                Agent List
              </span>
              <Button onClick={() => setShowCreate(true)} size="sm">
                <Plus className="h-3.5 w-3.5" />
              </Button>
            </div>

            {loading ? (
              Array.from({ length: 3 }).map((_, i) => (
                <div key={i} className="h-16 animate-pulse rounded-xl bg-bg-elevated border border-border-subtle mb-1" />
              ))
            ) : agents.length === 0 ? (
              <div className="text-center py-8">
                <Bot className="h-8 w-8 text-text-muted/30 mx-auto mb-2" />
                <p className="text-xs text-text-muted">No agents yet</p>
                <Button onClick={() => setShowCreate(true)} size="sm" className="mt-2">
                  Create Agent
                </Button>
              </div>
            ) : (
              agents.map((agent) => (
                <button
                  key={agent.id}
                  onClick={() => setSelectedAgent(agent)}
                  className={cn(
                    "w-full rounded-xl border p-3 text-left transition-all duration-200 mb-1",
                    selectedAgent?.id === agent.id
                      ? "border-accent/30 bg-accent-faint"
                      : "border-border-subtle bg-bg-elevated hover:border-border-accent",
                  )}
                >
                  <div className="flex items-start justify-between">
                    <div className="min-w-0 flex-1">
                      <h3 className="text-sm font-medium text-text truncate">{agent.name}</h3>
                      <p className="text-xs text-text-muted mt-0.5 line-clamp-1">
                        {agent.description || agent.system_prompt.slice(0, 60)}
                      </p>
                    </div>
                    <span
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDeleteAgent(agent.id);
                      }}
                      role="button"
                      tabIndex={0}
                      onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") { e.stopPropagation(); handleDeleteAgent(agent.id); } }}
                      className="text-text-muted/40 hover:text-error transition-colors p-1 cursor-pointer"
                    >
                      <Trash2 className="h-3 w-3" />
                    </span>
                  </div>
                </button>
              ))
            )}

            {/* Recent Runs */}
            <div className="mt-auto pt-3 border-t border-border-subtle">
              <p className="text-[10px] font-mono font-bold text-text-muted uppercase tracking-wider mb-2 px-1">
                Recent Runs
              </p>
              <div className="space-y-1 max-h-40 overflow-y-auto">
                {runs.slice(0, 5).map((run) => {
                  const StatusIcon = statusIcons[run.status] || Clock;
                  return (
                    <div key={run.id} className="flex items-center gap-2 text-xs px-2 py-1 rounded-lg bg-bg-surface">
                      <StatusIcon className={cn("h-3 w-3", statusColors[run.status])} />
                      <span className="text-text-secondary truncate flex-1">{run.input.slice(0, 30)}</span>
                      <span className="text-[10px] text-text-muted">{run.status}</span>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        </CollapsiblePanel>

        {/* Main Content */}
        <div className="flex-1 flex flex-col min-w-0">
          {error && (
            <div className="mx-6 mt-4 rounded-xl border border-error/20 bg-error/5 px-4 py-3 text-sm text-error">
              {error}
            </div>
          )}

          {selectedAgent ? (
            <AgentChat agent={selectedAgent} onRunComplete={handleRunComplete} />
          ) : (
            <div className="flex-1 flex flex-col items-center justify-center">
              <motion.div
                animate={{ y: [0, -8, 0] }}
                transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
              >
                <Bot className="h-16 w-16 text-accent/30 mb-4" />
              </motion.div>
              <p className="text-sm font-medium text-text mb-1">Select or create an agent</p>
              <p className="text-xs text-text-muted max-w-xs text-center">
                Agents can plan tasks, search your codebase, read files, and execute complex workflows.
              </p>
              <Button onClick={() => setShowCreate(true)} className="mt-4">
                <Plus className="h-4 w-4" />
                Create Agent
              </Button>
            </div>
          )}
        </div>

        {/* Create Agent Modal */}
        <AnimatePresence>
          {showCreate && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 z-50 flex items-center justify-center bg-black/60"
              onClick={() => setShowCreate(false)}
            >
              <motion.div
                initial={{ scale: 0.95, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                exit={{ scale: 0.95, opacity: 0 }}
                onClick={(e) => e.stopPropagation()}
                className="w-full max-w-md rounded-2xl border border-border-subtle bg-bg-elevated shadow-modal p-6"
              >
                <h2 className="text-lg font-semibold text-text mb-4">Create Agent</h2>
                <div className="space-y-3">
                  <div>
                    <label className="text-xs font-medium text-text-secondary">Name</label>
                    <input
                      value={newName}
                      onChange={(e) => setNewName(e.target.value)}
                      placeholder="e.g., Code Reviewer"
                      className="w-full mt-1 rounded-xl bg-bg-surface border border-border-subtle px-3.5 py-2.5 text-sm text-text placeholder:text-text-muted outline-none focus:border-accent/40 focus:ring-2 focus:ring-accent/10"
                    />
                  </div>
                  <div>
                    <label className="text-xs font-medium text-text-secondary">Description</label>
                    <input
                      value={newDesc}
                      onChange={(e) => setNewDesc(e.target.value)}
                      placeholder="What does this agent do?"
                      className="w-full mt-1 rounded-xl bg-bg-surface border border-border-subtle px-3.5 py-2.5 text-sm text-text placeholder:text-text-muted outline-none focus:border-accent/40 focus:ring-2 focus:ring-accent/10"
                    />
                  </div>
                  <div>
                    <label className="text-xs font-medium text-text-secondary">System Prompt</label>
                    <textarea
                      value={newPrompt}
                      onChange={(e) => setNewPrompt(e.target.value)}
                      placeholder="Instructions for the agent..."
                      rows={4}
                      className="w-full mt-1 rounded-xl bg-bg-surface border border-border-subtle px-3.5 py-2.5 text-sm text-text placeholder:text-text-muted outline-none focus:border-accent/40 focus:ring-2 focus:ring-accent/10 resize-y min-h-[80px]"
                    />
                  </div>
                </div>
                <div className="flex justify-end gap-2 mt-4">
                  <Button variant="secondary" onClick={() => setShowCreate(false)}>
                    Cancel
                  </Button>
                  <Button loading={creating} onClick={handleCreateAgent}>
                    Create
                  </Button>
                </div>
              </motion.div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </DashboardShell>
  );
}
