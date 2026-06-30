"use client";

import { useState, useEffect, useCallback } from "react";
import { workflows, tools, type ToolInfo, type WorkflowStep } from "../api";

interface WorkflowBuilderProps {
  onCreated?: (workflowId: number) => void;
}

export function WorkflowBuilder({ onCreated }: WorkflowBuilderProps) {
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [steps, setSteps] = useState<WorkflowStep[]>([]);
  const [availableTools, setAvailableTools] = useState<ToolInfo[]>([]);
  const [loadingTools, setLoadingTools] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // Editing state for the form below the step list
  const [selectedTool, setSelectedTool] = useState("");
  const [stepParams, setStepParams] = useState("{}");

  const loadTools = useCallback(async () => {
    setLoadingTools(true);
    try {
      const data = await tools.list();
      setAvailableTools(data);
      if (data.length > 0 && !selectedTool) {
        setSelectedTool(data[0].name);
      }
    } catch {
      // Silent — tools list is best-effort
    } finally {
      setLoadingTools(false);
    }
  }, [selectedTool]);

  useEffect(() => {
    loadTools();
  }, [loadTools]);

  const addStep = () => {
    if (!selectedTool) return;
    let params: Record<string, unknown> = {};
    try {
      params = JSON.parse(stepParams);
    } catch {
      setError("Invalid JSON in parameters");
      return;
    }
    setError(null);
    setSteps((prev) => [...prev, { tool: selectedTool, params }]);
    setStepParams("{}");
  };

  const removeStep = (idx: number) => {
    setSteps((prev) => prev.filter((_, i) => i !== idx));
  };

  const moveStep = (idx: number, dir: -1 | 1) => {
    const newIdx = idx + dir;
    if (newIdx < 0 || newIdx >= steps.length) return;
    setSteps((prev) => {
      const next = [...prev];
      [next[idx], next[newIdx]] = [next[newIdx], next[idx]];
      return next;
    });
  };

  const handleSubmit = async () => {
    if (!name.trim()) {
      setError("Workflow name is required");
      return;
    }
    if (steps.length === 0) {
      setError("Add at least one step");
      return;
    }
    setSubmitting(true);
    setError(null);
    setSuccess(null);
    try {
      const wf = await workflows.create(name.trim(), steps, description.trim() || undefined);
      setSuccess(`Workflow "${wf.name}" created (ID ${wf.id})`);
      setName("");
      setDescription("");
      setSteps([]);
      onCreated?.(wf.id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create workflow");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-4">
      <span className="text-label uppercase text-text-muted tracking-wider text-[11px]">
        New Workflow
      </span>

      {/* Name + Description */}
      <div className="space-y-3">
        <input
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="Workflow name"
          className="w-full px-3 py-2 rounded-md text-sm bg-bg-surface border border-border-subtle text-text-primary placeholder:text-text-muted focus:outline-none focus:border-accent/60"
        />
        <input
          type="text"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="Description (optional)"
          className="w-full px-3 py-2 rounded-md text-sm bg-bg-surface border border-border-subtle text-text-primary placeholder:text-text-muted focus:outline-none focus:border-accent/60"
        />
      </div>

      {/* Steps list */}
      {steps.length > 0 && (
        <div className="space-y-2">
          <span className="text-label uppercase text-text-muted tracking-wider text-[11px]">
            Steps ({steps.length})
          </span>
          {steps.map((step, idx) => (
            <div
              key={idx}
              className="flex items-center gap-2 bg-bg-surface rounded p-2"
            >
              <span className="text-xs text-text-muted font-mono w-5 text-center shrink-0">
                {idx + 1}
              </span>
              <span className="font-mono text-sm text-text-primary truncate flex-1">
                {step.tool}
              </span>
              {step.params && Object.keys(step.params).length > 0 && (
                <span className="text-[11px] text-text-muted truncate max-w-[200px]">
                  {JSON.stringify(step.params).slice(0, 60)}
                  {JSON.stringify(step.params).length > 60 ? "..." : ""}
                </span>
              )}
              <div className="flex items-center gap-1 shrink-0">
                <button
                  onClick={() => moveStep(idx, -1)}
                  disabled={idx === 0}
                  className="w-5 h-5 flex items-center justify-center rounded text-text-muted hover:text-text-primary disabled:opacity-30 text-xs"
                  title="Move up"
                >
                  &#9650;
                </button>
                <button
                  onClick={() => moveStep(idx, 1)}
                  disabled={idx === steps.length - 1}
                  className="w-5 h-5 flex items-center justify-center rounded text-text-muted hover:text-text-primary disabled:opacity-30 text-xs"
                  title="Move down"
                >
                  &#9660;
                </button>
                <button
                  onClick={() => removeStep(idx)}
                  className="w-5 h-5 flex items-center justify-center rounded text-danger/60 hover:text-danger text-xs"
                  title="Remove step"
                >
                  &#10005;
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Add step form */}
      <div className="flex items-end gap-3 flex-wrap">
        <div className="flex-1 min-w-[200px] space-y-1">
          <label className="text-xs text-text-muted">Tool</label>
          {loadingTools ? (
            <div className="h-9 bg-bg-surface rounded animate-pulse" />
          ) : (
            <select
              value={selectedTool}
              onChange={(e) => setSelectedTool(e.target.value)}
              className="w-full px-3 py-2 rounded-md text-sm bg-bg-surface border border-border-subtle text-text-primary focus:outline-none focus:border-accent/60"
            >
              {availableTools.map((t) => (
                <option key={t.name} value={t.name}>
                  {t.name}
                </option>
              ))}
            </select>
          )}
        </div>
        <div className="flex-1 min-w-[200px] space-y-1">
          <label className="text-xs text-text-muted">Parameters (JSON)</label>
          <input
            type="text"
            value={stepParams}
            onChange={(e) => setStepParams(e.target.value)}
            placeholder='{"key": "value"}'
            className="w-full px-3 py-2 rounded-md text-sm font-mono bg-bg-surface border border-border-subtle text-text-primary placeholder:text-text-muted focus:outline-none focus:border-accent/60"
          />
        </div>
        <button
          onClick={addStep}
          disabled={!selectedTool}
          className="px-3 py-2 rounded-md text-sm font-medium bg-bg-surface border border-border-subtle text-text-primary hover:bg-bg-hover disabled:opacity-50"
        >
          + Add Step
        </button>
      </div>

      {/* Status messages */}
      {error && (
        <div className="rounded border border-danger/20 bg-danger/5 p-3">
          <p className="text-sm text-danger">{error}</p>
        </div>
      )}
      {success && (
        <div className="rounded border border-success/20 bg-success/5 p-3">
          <p className="text-sm text-success">{success}</p>
        </div>
      )}

      {/* Submit */}
      <button
        onClick={handleSubmit}
        disabled={submitting || !name.trim() || steps.length === 0}
        className="px-3 py-1.5 rounded-md text-sm font-medium bg-accent text-void hover:bg-accent/90 disabled:opacity-50"
      >
        {submitting ? "Creating..." : "Create Workflow"}
      </button>
    </div>
  );
}
