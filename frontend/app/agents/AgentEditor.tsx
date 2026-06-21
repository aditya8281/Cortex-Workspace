"use client";

import { useState, useEffect } from "react";
import { X } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import Button from "../../src/shared/ui/Button";
import Input from "../../src/shared/ui/Input";
import type { Agent } from "../../src/shared/types";
import { agentApi } from "../../src/shared/api/agent";
import { modelsApi } from "../../src/shared/api/models";
import type { ModelInfo } from "../../src/shared/types";

const AVAILABLE_TOOLS = [
  { id: "search", label: "Search", description: "Search the codebase" },
  { id: "read_file", label: "Read File", description: "Read file contents" },
  { id: "write_file", label: "Write File", description: "Create or modify files" },
  { id: "list_files", label: "List Files", description: "List directory contents" },
];

interface AgentEditorProps {
  agent: Agent;
  open: boolean;
  onClose: () => void;
  onSaved: (agent: Agent) => void;
}

export default function AgentEditor({ agent, open, onClose, onSaved }: AgentEditorProps) {
  const [name, setName] = useState(agent.name);
  const [description, setDescription] = useState(agent.description ?? "");
  const [systemPrompt, setSystemPrompt] = useState(agent.system_prompt);
  const [modelId, setModelId] = useState(agent.model_id);
  const [selectedTools, setSelectedTools] = useState<string[]>([]);
  const [models, setModels] = useState<ModelInfo[]>([]);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (open) {
      setName(agent.name);
      setDescription(agent.description ?? "");
      setSystemPrompt(agent.system_prompt);
      setModelId(agent.model_id);
      setError(null);

      setSelectedTools(agent.tools ?? []);

      modelsApi
        .list({ downloaded_only: true })
        .then((res) => setModels(res.models))
        .catch(() => setModels([]));
    }
  }, [open, agent]);

  function toggleTool(toolId: string) {
    setSelectedTools((prev) =>
      prev.includes(toolId) ? prev.filter((t) => t !== toolId) : [...prev, toolId],
    );
  }

  async function handleSave() {
    if (!name.trim() || !systemPrompt.trim()) return;
    setSaving(true);
    setError(null);
    try {
      await agentApi.update(agent.id, {
        name: name.trim(),
        description: description.trim() || undefined,
        system_prompt: systemPrompt.trim(),
        model_id: modelId,
        tools: selectedTools.length > 0 ? selectedTools : undefined,
      });
      onSaved({
        ...agent,
        name: name.trim(),
        description: description.trim() || null,
        system_prompt: systemPrompt.trim(),
        model_id: modelId,
        tools: selectedTools,
      });
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update agent");
    } finally {
      setSaving(false);
    }
  }

  return (
    <AnimatePresence>
      {open && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/60"
          onClick={onClose}
        >
          <motion.div
            initial={{ scale: 0.95, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.95, opacity: 0 }}
            onClick={(e) => e.stopPropagation()}
            className="w-full max-w-lg rounded-2xl border border-border-subtle bg-bg-elevated shadow-modal p-6 max-h-[85vh] overflow-y-auto"
          >
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-text">Edit Agent</h2>
              <button
                onClick={onClose}
                className="text-text-muted hover:text-text transition-colors p-1"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            {error && (
              <div className="mb-4 rounded-xl border border-error/20 bg-error/5 px-4 py-3 text-sm text-error">
                {error}
              </div>
            )}

            <div className="space-y-4">
              <Input
                label="Name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g., Code Reviewer"
              />

              <Input
                label="Description"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="What does this agent do?"
              />

              <div className="grid gap-1.5">
                <label className="text-xs font-medium text-text-secondary">
                  System Prompt
                </label>
                <textarea
                  value={systemPrompt}
                  onChange={(e) => setSystemPrompt(e.target.value)}
                  placeholder="Instructions for the agent..."
                  rows={4}
                  className="w-full rounded-xl bg-bg-surface border border-border-subtle px-3.5 py-2.5 text-sm text-text placeholder:text-text-muted outline-none focus:border-accent/40 focus:ring-2 focus:ring-accent/10 resize-y min-h-[80px]"
                />
              </div>

              <div className="grid gap-1.5">
                <label className="text-xs font-medium text-text-secondary">
                  Model
                </label>
                <select
                  value={modelId}
                  onChange={(e) => setModelId(e.target.value)}
                  className="w-full rounded-xl bg-bg-surface border border-border-subtle px-3.5 py-2.5 text-sm text-text outline-none focus:border-accent/40 focus:ring-2 focus:ring-accent/10"
                >
                  <option value="local">Local (default)</option>
                  {models.map((m) => (
                    <option key={m.name} value={m.name}>
                      {m.display_name}
                    </option>
                  ))}
                </select>
              </div>

              <div className="grid gap-1.5">
                <label className="text-xs font-medium text-text-secondary">
                  Tools
                </label>
                <div className="space-y-2">
                  {AVAILABLE_TOOLS.map((tool) => (
                    <label
                      key={tool.id}
                      className="flex items-center gap-3 rounded-xl border border-border-subtle bg-bg-surface px-3.5 py-2.5 cursor-pointer hover:border-border-accent transition-colors"
                    >
                      <input
                        type="checkbox"
                        checked={selectedTools.includes(tool.id)}
                        onChange={() => toggleTool(tool.id)}
                        className="h-4 w-4 rounded border-border-subtle text-accent focus:ring-accent/20"
                      />
                      <div>
                        <p className="text-sm text-text">{tool.label}</p>
                        <p className="text-[10px] text-text-muted">
                          {tool.description}
                        </p>
                      </div>
                    </label>
                  ))}
                </div>
              </div>
            </div>

            <div className="flex justify-end gap-2 mt-6">
              <Button variant="secondary" onClick={onClose}>
                Cancel
              </Button>
              <Button loading={saving} onClick={handleSave}>
                Save
              </Button>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
