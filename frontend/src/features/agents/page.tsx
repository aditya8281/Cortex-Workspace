"use client";

import { useEffect, useState, useCallback } from "react";
import { useAuth } from "@/shared/auth/AuthProvider";
import { useRouter } from "next/navigation";
import { AppShell } from "@/shared/layout/AppShell";
import { Card } from "@/shared/ui/Card";
import { Button } from "@/shared/ui/Button";
import { StatusDot } from "@/shared/ui/StatusDot";
import { EmptyState } from "@/shared/ui/EmptyState";
import { Skeleton } from "@/shared/ui/Skeleton";
import { Modal } from "@/shared/ui/Modal";
import { Input } from "@/shared/ui/Input";
import { AgentCard } from "./components/AgentCard";
import { RunHistory } from "./components/RunHistory";
import { RunDetail } from "./components/RunDetail";
import { agentsApi, type Agent, type AgentRun, type AgentStep } from "./api";
import { useWebSocket, type WSStatus } from "@/shared/ws/useWebSocket";

export default function AgentsPage() {
  const { user, loading } = useAuth();
  const router = useRouter();

  const [agents, setAgents] = useState<Agent[]>([]);
  const [runs, setRuns] = useState<AgentRun[]>([]);
  const [selectedRun, setSelectedRun] = useState<{ run: AgentRun; steps: AgentStep[] } | null>(null);

  const [showCreate, setShowCreate] = useState(false);
  const [createForm, setCreateForm] = useState({
    name: "",
    description: "",
    system_prompt: "",
    model_id: "local",
  });
  const [creating, setCreating] = useState(false);

  const [runModal, setRunModal] = useState<{ agentId: number; input: string } | null>(null);
  const [running, setRunning] = useState(false);

  useEffect(() => {
    if (!loading && !user) router.push("/auth");
  }, [user, loading, router]);

  const loadAgents = useCallback(async () => {
    try {
      const res = await agentsApi.list();
      setAgents(res.agents);
    } catch {
      // ignore
    }
  }, []);

  const loadRuns = useCallback(async () => {
    try {
      const res = await agentsApi.listRuns();
      setRuns(res.runs);
    } catch {
      // ignore
    }
  }, []);

  useEffect(() => {
    loadAgents();
    loadRuns();
  }, [loadAgents, loadRuns]);

  // ── Real-time agent run progress via WebSocket ──────────────────────────

  const handleAgentWSMessage = useCallback((data: Record<string, unknown>) => {
    if (data.type === "agent_runs" && Array.isArray(data.runs)) {
      const wsRuns = data.runs as Array<{
        id: number;
        agent_id: number;
        status: string;
        created_at: string;
      }>;
      if (wsRuns.length > 0) {
        setRuns((prev) => {
          const existing = new Map(prev.map((r) => [r.id, r]));
          for (const wsRun of wsRuns) {
            const existingRun = existing.get(wsRun.id);
            if (existingRun) {
              existing.set(wsRun.id, { ...existingRun, status: wsRun.status as AgentRun["status"] });
            } else {
              // New run — add with partial data, full data on next REST fetch
              existing.set(wsRun.id, {
                id: wsRun.id,
                agent_id: wsRun.agent_id,
                status: wsRun.status as AgentRun["status"],
                input: "",
                output: null,
                token_usage: 0,
                error: null,
                created_at: wsRun.created_at,
                completed_at: null,
              });
            }
          }
          return Array.from(existing.values());
        });
      }
    }
  }, []);

  const { status: agentWsStatus } = useWebSocket({
    path: "/api/v1/ws/agents",
    enabled: !!user,
    onMessage: handleAgentWSMessage,
  });

  const handleCreate = async () => {
    if (!createForm.name.trim() || !createForm.system_prompt.trim()) return;
    setCreating(true);
    try {
      await agentsApi.create(createForm);
      setShowCreate(false);
      setCreateForm({ name: "", description: "", system_prompt: "", model_id: "local" });
      loadAgents();
    } catch {
      // ignore
    } finally {
      setCreating(false);
    }
  };

  const handleRun = async () => {
    if (!runModal || !runModal.input.trim()) return;
    setRunning(true);
    try {
      await agentsApi.startRun(runModal.agentId, runModal.input);
      setRunModal(null);
      loadRuns();
    } catch {
      // ignore
    } finally {
      setRunning(false);
    }
  };

  const handleSelectRun = async (run: AgentRun) => {
    try {
      const res = await agentsApi.getRun(run.id);
      setSelectedRun(res);
    } catch {
      // ignore
    }
  };

  if (loading || !user) return (
    <AppShell>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div className="space-y-1">
            <Skeleton className="h-6 w-24" />
            <Skeleton className="h-4 w-32" />
          </div>
          <Skeleton className="h-9 w-24 rounded-md" />
        </div>
        <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
          {[1, 2].map((i) => (
            <Card key={i} className="p-4">
              <div className="space-y-2">
                <Skeleton className="h-4 w-3/4" />
                <Skeleton className="h-3 w-1/2" />
                <Skeleton className="h-3 w-1/3" />
              </div>
            </Card>
          ))}
        </div>
        <Card className="divide-y divide-border-subtle">
          {[1, 2, 3].map((i) => (
            <div key={i} className="flex items-start gap-3 px-4 py-3">
              <Skeleton className="h-5 w-16 rounded-md" />
              <Skeleton className="h-4 w-48" />
            </div>
          ))}
        </Card>
      </div>
    </AppShell>
  );

  return (
    <AppShell>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div>
              <h1 className="text-headline font-semibold text-text-primary">Agents</h1>
              <p className="mt-1 text-sm text-text-secondary">
                {agents.length} autonomous agent{agents.length !== 1 && "s"}
              </p>
            </div>
            <StatusDot
              color={agentWsStatus === "connected" ? "success" : "danger"}
              pulse={agentWsStatus === "connected"}
            />
          </div>
          <Button onClick={() => setShowCreate(true)}>New Agent</Button>
        </div>

        {/* Agent cards */}
        {agents.length === 0 ? (
          <EmptyState
            title="No agents yet"
            description="Create an agent to start automating tasks with your local LLM"
            action={<Button onClick={() => setShowCreate(true)}>Create Agent</Button>}
          />
        ) : (
          <div className="grid grid-cols-1 gap-3 md:grid-cols-2 stagger-children">
            {agents.map((agent) => (
              <AgentCard
                key={agent.id}
                agent={agent}
                onRun={(id) => setRunModal({ agentId: id, input: "" })}
                onClick={() => {}}
              />
            ))}
          </div>
        )}

        {/* Run history */}
        <div>
          <h2 className="text-title font-semibold text-text-primary mb-3">Recent Runs</h2>
          <RunHistory runs={runs} onSelect={handleSelectRun} />
        </div>

        {/* Run detail */}
        {selectedRun && (
          <RunDetail run={selectedRun.run} steps={selectedRun.steps} />
        )}
      </div>

      {/* Create agent modal */}
      <Modal open={showCreate} onClose={() => setShowCreate(false)} title="New Agent">
        <div className="space-y-4">
          <Input
            label="Name"
            value={createForm.name}
            onChange={(e) => setCreateForm({ ...createForm, name: e.target.value })}
            placeholder="e.g. Code Reviewer"
          />
          <Input
            label="Description"
            value={createForm.description}
            onChange={(e) => setCreateForm({ ...createForm, description: e.target.value })}
            placeholder="What does this agent do?"
          />
          <div>
            <label className="block text-sm font-medium text-text-secondary mb-1.5">
              System Prompt
            </label>
            <textarea
              value={createForm.system_prompt}
              onChange={(e) => setCreateForm({ ...createForm, system_prompt: e.target.value })}
              rows={4}
              placeholder="You are a helpful agent that..."
              className="w-full rounded-lg border border-border-default bg-bg-surface px-3 py-2 text-sm text-text-primary placeholder:text-text-muted focus:border-accent/50 focus:outline-none focus:ring-1 focus:ring-accent/25 transition-colors duration-150"
            />
          </div>
          <Input
            label="Model"
            value={createForm.model_id}
            onChange={(e) => setCreateForm({ ...createForm, model_id: e.target.value })}
          />
          <div className="flex justify-end gap-2 pt-2">
            <Button variant="ghost" onClick={() => setShowCreate(false)}>
              Cancel
            </Button>
            <Button
              onClick={handleCreate}
              disabled={!createForm.name.trim() || !createForm.system_prompt.trim()}
              loading={creating}
            >
              Create Agent
            </Button>
          </div>
        </div>
      </Modal>

      {/* Run agent modal */}
      <Modal
        open={!!runModal}
        onClose={() => setRunModal(null)}
        title="Run Agent"
      >
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-text-secondary mb-1.5">
              Input
            </label>
            <textarea
              value={runModal?.input ?? ""}
              onChange={(e) =>
                setRunModal((prev) => (prev ? { ...prev, input: e.target.value } : null))
              }
              rows={3}
              placeholder="What should the agent do?"
              className="w-full rounded-lg border border-border-default bg-bg-surface px-3 py-2 text-sm text-text-primary placeholder:text-text-muted focus:border-accent/50 focus:outline-none focus:ring-1 focus:ring-accent/25 transition-colors duration-150"
            />
          </div>
          <div className="flex justify-end gap-2 pt-2">
            <Button variant="ghost" onClick={() => setRunModal(null)}>
              Cancel
            </Button>
            <Button
              onClick={handleRun}
              disabled={!runModal?.input.trim()}
              loading={running}
            >
              Start Run
            </Button>
          </div>
        </div>
      </Modal>
    </AppShell>
  );
}
