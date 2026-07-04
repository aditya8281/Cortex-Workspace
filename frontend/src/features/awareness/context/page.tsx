"use client";

import { useEffect, useState, useCallback } from "react";
import { useAuth } from "@/shared/auth/AuthProvider";
import { useRouter } from "next/navigation";
import { Card } from "@/shared/ui/Card";
import { Badge } from "@/shared/ui/Badge";
import { Button } from "@/shared/ui/Button";
import { Skeleton } from "@/shared/ui/Skeleton";
import { Input } from "@/shared/ui/Input";
import { EmptyState } from "@/shared/ui/EmptyState";
import { Modal } from "@/shared/ui/Modal";
import { SystemSnapshotCard } from "../components/SystemSnapshotCard";
import { AttentionSessionCard } from "../components/AttentionSessionCard";
import { ContextRuleCard } from "../components/ContextRuleCard";
import { ContextStatePanel } from "../components/ContextStatePanel";
import { ContextEventLog } from "../components/ContextEventLog";
import {
  systemApi,
  attentionApi,
  contextRulesApi,
  type SystemSnapshot,
  type AttentionSession,
  type AttentionStats,
  type ContextRule,
} from "../contextApi";

// ── Tab Definition ─────────────────────────────────────────────────────────

const TABS = [
  { id: "system", label: "System" },
  { id: "attention", label: "Attention" },
  { id: "rules", label: "Rules" },
  { id: "state", label: "State" },
  { id: "events", label: "Events" },
] as const;

type TabId = (typeof TABS)[number]["id"];

// ── Loading Skeleton ───────────────────────────────────────────────────────

function PageSkeleton() {
  return (
      <div className="max-w-5xl space-y-6">
        <div>
          <Skeleton className="h-6 w-48" />
          <Skeleton className="h-4 w-72 mt-2" />
        </div>
        <div className="flex gap-2">
          {[1, 2, 3, 4, 5].map((i) => (
            <Skeleton key={i} className="h-8 w-20 rounded-md" />
          ))}
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[1, 2, 3].map((i) => (
            <Card key={i} className="space-y-3">
              <Skeleton className="h-4 w-28" />
              <Skeleton className="h-3 w-full" />
              <Skeleton className="h-3 w-2/3" />
            </Card>
          ))}
        </div>
      </div>
  );
}

// ── Create Rule Modal ──────────────────────────────────────────────────────

function CreateRuleModal({
  open,
  onClose,
  onCreated,
}: {
  open: boolean;
  onClose: () => void;
  onCreated: () => void;
}) {
  const [name, setName] = useState("");
  const [ruleType, setRuleType] = useState("trigger");
  const [description, setDescription] = useState("");
  const [priority, setPriority] = useState("10");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async () => {
    if (!name.trim()) return;
    setSaving(true);
    setError(null);
    try {
      await contextRulesApi.create({
        name: name.trim(),
        rule_type: ruleType,
        description: description.trim() || undefined,
        priority: parseInt(priority, 10) || 10,
      });
      setName("");
      setRuleType("trigger");
      setDescription("");
      setPriority("10");
      onCreated();
      onClose();
    } catch (err: any) {
      setError(err.message ?? "Failed to create rule");
    } finally {
      setSaving(false);
    }
  };

  return (
    <Modal open={open} onClose={onClose} title="Create Context Rule">
      <div className="space-y-4">
        {error && (
          <p className="text-sm text-danger bg-danger/5 border border-danger/20 rounded-md px-3 py-2">
            {error}
          </p>
        )}
        <Input
          label="Name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="e.g., high-cpu-alert"
        />
        <div className="flex flex-col gap-1.5">
          <label className="text-xs font-medium text-text-secondary">
            Type
          </label>
          <select
            value={ruleType}
            onChange={(e) => setRuleType(e.target.value)}
            className="h-11 rounded-md border border-border-default bg-bg-surface px-3 text-sm text-text-primary focus:border-border-input-focus focus:outline-none motion-safe:transition-colors motion-safe:duration-150"
          >
            <option value="trigger">Trigger</option>
            <option value="filter">Filter</option>
            <option value="transform">Transform</option>
            <option value="guard">Guard</option>
          </select>
        </div>
        <div className="flex flex-col gap-1.5">
          <label className="text-xs font-medium text-text-secondary">
            Description
          </label>
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="What this rule does..."
            rows={3}
            className="rounded-md border border-border-default bg-bg-surface px-3 py-2 text-sm text-text-primary placeholder:text-text-muted focus:border-border-input-focus focus:outline-none motion-safe:transition-colors motion-safe:duration-150 resize-none"
          />
        </div>
        <Input
          label="Priority"
          type="number"
          value={priority}
          onChange={(e) => setPriority(e.target.value)}
          placeholder="10"
        />
        <div className="flex justify-end gap-2 pt-2">
          <Button variant="ghost" size="sm" onClick={onClose}>
            Cancel
          </Button>
          <Button
            size="sm"
            onClick={handleSubmit}
            loading={saving}
            disabled={!name.trim()}
          >
            Create Rule
          </Button>
        </div>
      </div>
    </Modal>
  );
}

// ── Start Session Modal ────────────────────────────────────────────────────

function StartSessionModal({
  open,
  onClose,
  onCreated,
}: {
  open: boolean;
  onClose: () => void;
  onCreated: () => void;
}) {
  const [sessionType, setSessionType] = useState("deep_work");
  const [taskDescription, setTaskDescription] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async () => {
    setSaving(true);
    setError(null);
    try {
      await attentionApi.startSession({
        session_type: sessionType,
        task_description: taskDescription.trim() || undefined,
      });
      setSessionType("deep_work");
      setTaskDescription("");
      onCreated();
      onClose();
    } catch (err: any) {
      setError(err.message ?? "Failed to start session");
    } finally {
      setSaving(false);
    }
  };

  return (
    <Modal open={open} onClose={onClose} title="Start Attention Session">
      <div className="space-y-4">
        {error && (
          <p className="text-sm text-danger bg-danger/5 border border-danger/20 rounded-md px-3 py-2">
            {error}
          </p>
        )}
        <div className="flex flex-col gap-1.5">
          <label className="text-xs font-medium text-text-secondary">
            Session Type
          </label>
          <select
            value={sessionType}
            onChange={(e) => setSessionType(e.target.value)}
            className="h-11 rounded-md border border-border-default bg-bg-surface px-3 text-sm text-text-primary focus:border-border-input-focus focus:outline-none motion-safe:transition-colors motion-safe:duration-150"
          >
            <option value="deep_work">Deep Work</option>
            <option value="research">Research</option>
            <option value="coding">Coding</option>
            <option value="review">Review</option>
          </select>
        </div>
        <div className="flex flex-col gap-1.5">
          <label className="text-xs font-medium text-text-secondary">
            Task Description
          </label>
          <textarea
            value={taskDescription}
            onChange={(e) => setTaskDescription(e.target.value)}
            placeholder="What are you working on?"
            rows={3}
            className="rounded-md border border-border-default bg-bg-surface px-3 py-2 text-sm text-text-primary placeholder:text-text-muted focus:border-border-input-focus focus:outline-none motion-safe:transition-colors motion-safe:duration-150 resize-none"
          />
        </div>
        <div className="flex justify-end gap-2 pt-2">
          <Button variant="ghost" size="sm" onClick={onClose}>
            Cancel
          </Button>
          <Button size="sm" onClick={handleSubmit} loading={saving}>
            Start Session
          </Button>
        </div>
      </div>
    </Modal>
  );
}

// ── Main Page ──────────────────────────────────────────────────────────────

export default function ContextPage() {
  const { user, loading } = useAuth();
  const router = useRouter();

  // Auth guard
  useEffect(() => {
    if (!loading && !user) router.push("/auth");
  }, [user, loading, router]);

  // ── Tab state ──────────────────────────────────────────────────────────
  const [activeTab, setActiveTab] = useState<TabId>("system");

  // ── System state ───────────────────────────────────────────────────────
  const [latestSnapshot, setLatestSnapshot] = useState<SystemSnapshot | null>(
    null,
  );
  const [recentSnapshots, setRecentSnapshots] = useState<SystemSnapshot[]>([]);
  const [snapshotLoading, setSnapshotLoading] = useState(false);
  const [systemLoading, setSystemLoading] = useState(true);
  const [anomalies, setAnomalies] = useState<
    Array<{ type: string; value: number; threshold: number }>
  >([]);

  // ── Attention state ────────────────────────────────────────────────────
  const [sessions, setSessions] = useState<AttentionSession[]>([]);
  const [stats, setStats] = useState<AttentionStats | null>(null);
  const [attentionLoading, setAttentionLoading] = useState(false);
  const [endingId, setEndingId] = useState<number | null>(null);
  const [sessionModalOpen, setSessionModalOpen] = useState(false);

  // ── Rules state ────────────────────────────────────────────────────────
  const [rules, setRules] = useState<ContextRule[]>([]);
  const [rulesLoading, setRulesLoading] = useState(false);
  const [ruleFilter, setRuleFilter] = useState<string | undefined>(undefined);
  const [ruleModalOpen, setRuleModalOpen] = useState(false);

  // ── Fetchers ───────────────────────────────────────────────────────────

  const fetchSystem = useCallback(async () => {
    setSystemLoading(true);
    try {
      const [recentRes, anomalyRes] = await Promise.allSettled([
        systemApi.getRecent(10),
        systemApi.getAnomalies(),
      ]);
      if (recentRes.status === "fulfilled") {
        setRecentSnapshots(recentRes.value.snapshots);
        setLatestSnapshot(recentRes.value.snapshots[0] ?? null);
      }
      if (anomalyRes.status === "fulfilled") {
        setAnomalies(anomalyRes.value.anomalies);
      }
    } finally {
      setSystemLoading(false);
    }
  }, []);

  const fetchAttention = useCallback(async () => {
    setAttentionLoading(true);
    try {
      const [sessionsRes, statsRes] = await Promise.allSettled([
        attentionApi.getSessions(20),
        attentionApi.getStats(),
      ]);
      if (sessionsRes.status === "fulfilled") {
        setSessions(sessionsRes.value.sessions);
      }
      if (statsRes.status === "fulfilled") {
        setStats(statsRes.value);
      }
    } finally {
      setAttentionLoading(false);
    }
  }, []);

  const fetchRules = useCallback(async () => {
    setRulesLoading(true);
    try {
      const data = await contextRulesApi.list(ruleFilter);
      setRules(data);
    } finally {
      setRulesLoading(false);
    }
  }, [ruleFilter]);

  // ── Effects ────────────────────────────────────────────────────────────

  useEffect(() => {
    if (user) fetchSystem();
  }, [user, fetchSystem]);

  useEffect(() => {
    if (user && activeTab === "attention") fetchAttention();
  }, [user, activeTab, fetchAttention]);

  useEffect(() => {
    if (user && activeTab === "rules") fetchRules();
  }, [user, activeTab, fetchRules]);

  // ── Handlers ───────────────────────────────────────────────────────────

  const handleTakeSnapshot = async () => {
    setSnapshotLoading(true);
    try {
      const snap = await systemApi.takeSnapshot();
      setLatestSnapshot(snap);
      setRecentSnapshots((prev) => [snap, ...prev].slice(0, 10));
    } finally {
      setSnapshotLoading(false);
    }
  };

  const handleEndSession = async (id: number) => {
    setEndingId(id);
    try {
      await attentionApi.endSession(id);
      await fetchAttention();
    } finally {
      setEndingId(null);
    }
  };

  const handleToggleRule = async (id: number, enabled: boolean) => {
    try {
      await contextRulesApi.update(id, { enabled });
      setRules((prev) =>
        prev.map((r) => (r.id === id ? { ...r, enabled } : r)),
      );
    } catch {
      // Silently fail — user can retry
    }
  };

  const handleDeleteRule = async (id: number) => {
    try {
      await contextRulesApi.remove(id);
      setRules((prev) => prev.filter((r) => r.id !== id));
    } catch {
      // Silently fail
    }
  };

  // ── Auth loading guard ─────────────────────────────────────────────────

  if (loading || !user) return <PageSkeleton />;

  // ── Render ─────────────────────────────────────────────────────────────

  return (
      <div className="max-w-5xl mx-auto space-y-6 animate-fade-in">
        {/* Page Header */}
        <div>
          <h1 className="text-headline font-semibold text-text-primary">
            Context &amp; Attention
          </h1>
          <p className="text-sm text-text-secondary mt-1">
            System awareness, attention tracking, and context management
          </p>
        </div>

        {/* Tab Bar */}
        <div className="flex gap-1 p-1 bg-bg-surface rounded-lg border border-border-subtle w-fit">
          {TABS.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-3 py-1.5 rounded-md text-sm font-medium motion-safe:transition-colors motion-safe:duration-150 ${
                activeTab === tab.id
                  ? "bg-accent text-white"
                  : "text-text-muted hover:text-text-primary hover:bg-bg-hover"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* ── System Tab ─────────────────────────────────────────────────── */}
        {activeTab === "system" && (
          <div className="space-y-6">
            {/* Anomaly Banner */}
            {anomalies.length > 0 && (
              <Card className="bg-danger/5 border-danger/20">
                <div className="flex items-start gap-3">
                  <svg
                    className="w-5 h-5 text-danger shrink-0 mt-0.5"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                  >
                    <path d="M12 9v4m0 4h.01M10.29 3.86l-8.57 14.86A1 1 0 002.62 20h18.76a1 1 0 00.87-1.28L13.71 3.86a1 1 0 00-1.42 0z" />
                  </svg>
                  <div>
                    <p className="text-sm font-medium text-danger">
                      {anomalies.length} anomal{anomalies.length === 1 ? "y" : "ies"} detected
                    </p>
                    <div className="flex flex-wrap gap-2 mt-1">
                      {anomalies.map((a, i) => (
                        <Badge key={i} variant="danger">
                          {a.type}: {a.value.toFixed(1)}% (threshold: {a.threshold}%)
                        </Badge>
                      ))}
                    </div>
                  </div>
                </div>
              </Card>
            )}

            {/* Snapshot Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              <SystemSnapshotCard
                snapshot={latestSnapshot}
                loading={systemLoading}
                onTakeSnapshot={handleTakeSnapshot}
                snapshotLoading={snapshotLoading}
              />

              {/* Snapshot History */}
              <Card className="md:col-span-1 lg:col-span-2">
                <h3 className="text-title font-medium text-text-primary mb-3">
                  Recent Snapshots
                </h3>
                {systemLoading ? (
                  <div className="space-y-2">
                    {[1, 2, 3].map((i) => (
                      <Skeleton key={i} className="h-12 w-full" />
                    ))}
                  </div>
                ) : recentSnapshots.length === 0 ? (
                  <EmptyState
                    title="No snapshots yet"
                    description="Take a snapshot to capture current system metrics."
                  />
                ) : (
                  <div className="space-y-2">
                    {recentSnapshots.map((snap) => (
                      <div
                        key={snap.id}
                        className="flex items-center gap-4 p-2 rounded-md hover:bg-bg-hover motion-safe:transition-colors motion-safe:duration-150"
                      >
                        <span className="font-mono text-xs text-text-muted w-16 shrink-0">
                          {new Date(snap.created_at).toLocaleTimeString("en-US", {
                            hour: "2-digit",
                            minute: "2-digit",
                          })}
                        </span>
                        <div className="flex-1 flex items-center gap-4 text-xs">
                          <span className="font-mono text-text-secondary">
                            CPU {snap.cpu_percent.toFixed(0)}%
                          </span>
                          <span className="font-mono text-text-secondary">
                            MEM {snap.memory_percent.toFixed(0)}%
                          </span>
                          <span className="font-mono text-text-secondary">
                            DISK {snap.disk_percent.toFixed(0)}%
                          </span>
                          <span className="font-mono text-text-muted hidden sm:inline">
                            {snap.process_count} proc
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </Card>
            </div>
          </div>
        )}

        {/* ── Attention Tab ───────────────────────────────────────────────── */}
        {activeTab === "attention" && (
          <div className="space-y-6">
            {/* Stats Row */}
            {stats && (
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <Card>
                  <span className="text-label uppercase text-text-muted tracking-wider">
                    Total Sessions
                  </span>
                  <p className="font-mono text-title font-medium text-text-primary mt-1">
                    {stats.total_sessions}
                  </p>
                </Card>
                <Card>
                  <span className="text-label uppercase text-text-muted tracking-wider">
                    Total Duration
                  </span>
                  <p className="font-mono text-title font-medium text-text-primary mt-1">
                    {stats.total_duration_minutes}m
                  </p>
                </Card>
                <Card>
                  <span className="text-label uppercase text-text-muted tracking-wider">
                    Avg Focus
                  </span>
                  <div className="flex items-center gap-2 mt-1">
                    <p className="font-mono text-title font-medium text-text-primary">
                      {stats.average_focus.toFixed(0)}
                    </p>
                    <span className="text-xs text-text-muted">/100</span>
                  </div>
                </Card>
              </div>
            )}

            {/* Session Type Breakdown */}
            {stats && Object.keys(stats.sessions_by_type).length > 0 && (
              <Card>
                <span className="text-label uppercase text-text-muted tracking-wider">
                  Sessions by Type
                </span>
                <div className="flex flex-wrap gap-2 mt-2">
                  {Object.entries(stats.sessions_by_type).map(([type, count]) => (
                    <Badge key={type}>
                      {type.replace(/_/g, " ")}: {count}
                    </Badge>
                  ))}
                </div>
              </Card>
            )}

            {/* Start Session Button + List */}
            <div className="flex items-center justify-between">
              <h3 className="text-title font-medium text-text-primary">
                Sessions
              </h3>
              <Button size="sm" onClick={() => setSessionModalOpen(true)}>
                Start Session
              </Button>
            </div>

            {attentionLoading ? (
              <div className="space-y-3">
                {[1, 2, 3].map((i) => (
                  <Card key={i} className="space-y-3">
                    <Skeleton className="h-4 w-24" />
                    <Skeleton className="h-3 w-full" />
                    <Skeleton className="h-3 w-2/3" />
                  </Card>
                ))}
              </div>
            ) : sessions.length === 0 ? (
              <EmptyState
                title="No attention sessions"
                description="Start a session to begin tracking your focus."
                action={
                  <Button size="sm" onClick={() => setSessionModalOpen(true)}>
                    Start Session
                  </Button>
                }
              />
            ) : (
              <div className="space-y-3">
                {sessions.map((session) => (
                  <AttentionSessionCard
                    key={session.id}
                    session={session}
                    onEnd={handleEndSession}
                    ending={endingId === session.id}
                  />
                ))}
              </div>
            )}

            <StartSessionModal
              open={sessionModalOpen}
              onClose={() => setSessionModalOpen(false)}
              onCreated={fetchAttention}
            />
          </div>
        )}

        {/* ── Rules Tab ───────────────────────────────────────────────────── */}
        {activeTab === "rules" && (
          <div className="space-y-6">
            {/* Filter + Create */}
            <div className="flex items-center justify-between gap-3">
              <div className="flex items-center gap-2">
                <span className="text-label uppercase text-text-muted tracking-wider text-[0.625rem]">
                  Filter
                </span>
                <button
                  onClick={() => setRuleFilter(undefined)}
                  className={`px-2 py-1 rounded text-xs font-medium motion-safe:transition-colors motion-safe:duration-150 ${
                    !ruleFilter
                      ? "bg-accent/12 text-accent"
                      : "bg-bg-surface text-text-muted hover:text-text-primary"
                  }`}
                >
                  All
                </button>
                {["trigger", "filter", "transform", "guard"].map((type) => (
                  <button
                    key={type}
                    onClick={() => setRuleFilter(type)}
                    className={`px-2 py-1 rounded text-xs font-medium motion-safe:transition-colors motion-safe:duration-150 ${
                      ruleFilter === type
                        ? "bg-accent/12 text-accent"
                        : "bg-bg-surface text-text-muted hover:text-text-primary"
                    }`}
                  >
                    {type}
                  </button>
                ))}
              </div>
              <Button size="sm" onClick={() => setRuleModalOpen(true)}>
                Create Rule
              </Button>
            </div>

            {rulesLoading ? (
              <div className="space-y-3">
                {[1, 2, 3].map((i) => (
                  <Card key={i} className="space-y-3">
                    <Skeleton className="h-4 w-32" />
                    <Skeleton className="h-3 w-full" />
                    <Skeleton className="h-3 w-2/3" />
                  </Card>
                ))}
              </div>
            ) : rules.length === 0 ? (
              <EmptyState
                title="No context rules"
                description="Create rules to automate context management."
                action={
                  <Button size="sm" onClick={() => setRuleModalOpen(true)}>
                    Create Rule
                  </Button>
                }
              />
            ) : (
              <div className="space-y-3">
                {rules.map((rule) => (
                  <ContextRuleCard
                    key={rule.id}
                    rule={rule}
                    onToggle={handleToggleRule}
                    onDelete={handleDeleteRule}
                  />
                ))}
              </div>
            )}

            <CreateRuleModal
              open={ruleModalOpen}
              onClose={() => setRuleModalOpen(false)}
              onCreated={fetchRules}
            />
          </div>
        )}

        {/* ── State Tab ───────────────────────────────────────────────────── */}
        {activeTab === "state" && (
          <div className="space-y-4">
            <h3 className="text-title font-medium text-text-primary">
              Context States
            </h3>
            <ContextStatePanel />
          </div>
        )}

        {/* ── Events Tab ──────────────────────────────────────────────────── */}
        {activeTab === "events" && (
          <div className="space-y-4">
            <h3 className="text-title font-medium text-text-primary">
              Context Events
            </h3>
            <ContextEventLog limit={50} />
          </div>
        )}
      </div>
  );
}
