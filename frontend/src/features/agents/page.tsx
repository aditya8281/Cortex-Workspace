"use client";

import { useEffect, useState, useCallback } from "react";
import { useAuth } from "@/shared/auth/AuthProvider";
import { useRouter } from "next/navigation";
import { AppShell } from "@/shared/layout/AppShell";
import { Button } from "@/shared/ui/Button";
import { EmptyState } from "@/shared/ui/EmptyState";
import { Modal } from "@/shared/ui/Modal";
import { Input } from "@/shared/ui/Input";
import { AgentCard } from "./components/AgentCard";
import { RunHistory } from "./components/RunHistory";
import { RunDetail } from "./components/RunDetail";
import { agentsApi, type Agent, type AgentRun, type AgentStep } from "./api";

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

  if (loading || !user) return null;

  return (
    <AppShell>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-headline font-semibold text-text-primary">Agents</h1>
            <p className="mt-1 text-sm text-text-secondary">
              {agents.length} autonomous agent{agents.length !== 1 && "s"}
            </p>
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
          <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
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
