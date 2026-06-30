"use client";

import { useCallback, useEffect, useState } from "react";
import { useAuth } from "@/shared/auth/AuthProvider";
import { useRouter } from "next/navigation";
import { AppShell } from "@/shared/layout/AppShell";
import {
  planning,
  errors,
  hypothesis,
  confidence,
} from "./api";
import type {
  TaskPlan,
  TaskPlanListResponse,
  ErrorAnalysis,
  Hypothesis,
  ConfidenceResult,
} from "./api";
import { TaskPlanCard } from "./components/TaskPlanCard";
import { ErrorAnalysisCard } from "./components/ErrorAnalysisCard";
import { HypothesisCard } from "./components/HypothesisCard";
import { ConfidencePanel } from "./components/ConfidencePanel";

// ── Tabs ────────────────────────────────────────────────────────────────────

type Tab = "planning" | "errors" | "hypothesis" | "confidence";

const tabs: { key: Tab; label: string }[] = [
  { key: "planning", label: "Task Planning" },
  { key: "errors", label: "Error Analysis" },
  { key: "hypothesis", label: "Hypothesis" },
  { key: "confidence", label: "Confidence" },
];

// ── Shared skeleton ─────────────────────────────────────────────────────────

function CardSkeleton() {
  return (
    <div className="bg-bg-elevated rounded-lg border border-border-subtle p-4 space-y-3">
      <div className="h-4 w-3/4 bg-bg-surface rounded animate-pulse" />
      <div className="h-3 w-1/2 bg-bg-surface rounded animate-pulse" />
      <div className="space-y-1.5">
        <div className="h-3 w-full bg-bg-surface rounded animate-pulse" />
        <div className="h-3 w-5/6 bg-bg-surface rounded animate-pulse" />
      </div>
    </div>
  );
}

function SectionSkeleton({ count = 3 }: { count?: number }) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {Array.from({ length: count }).map((_, i) => (
        <CardSkeleton key={i} />
      ))}
    </div>
  );
}

// ── Error Banner ────────────────────────────────────────────────────────────

function ErrorBanner({
  message,
  onRetry,
}: {
  message: string;
  onRetry: () => void;
}) {
  return (
    <div className="rounded-lg border border-danger/20 bg-danger/5 p-4">
      <p className="text-sm text-danger">{message}</p>
      <button
        onClick={onRetry}
        className="mt-2 px-3 py-1.5 rounded-md text-sm font-medium bg-danger/10 text-danger hover:bg-danger/20 transition-colors"
      >
        Retry
      </button>
    </div>
  );
}

// ── Planning Section ────────────────────────────────────────────────────────

function PlanningSection() {
  const [goal, setGoal] = useState("");
  const [plans, setPlans] = useState<TaskPlan[]>([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchPlans = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res: TaskPlanListResponse = await planning.listPlans({ limit: 20 });
      setPlans(res.items);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load plans");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchPlans();
  }, [fetchPlans]);

  const handleCreate = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault();
      if (!goal.trim()) return;
      setSubmitting(true);
      setError(null);
      try {
        const created = await planning.createPlan(goal.trim());
        setPlans((prev) => [created, ...prev]);
        setGoal("");
      } catch (e) {
        setError(e instanceof Error ? e.message : "Failed to create plan");
      } finally {
        setSubmitting(false);
      }
    },
    [goal],
  );

  return (
    <div className="space-y-4">
      <form onSubmit={handleCreate} className="flex gap-3">
        <input
          type="text"
          value={goal}
          onChange={(e) => setGoal(e.target.value)}
          placeholder="Enter a goal to plan..."
          className="flex-1 px-3 py-2 rounded-md bg-bg-surface border border-border-subtle text-text-primary text-sm placeholder:text-text-muted focus:outline-none focus:border-accent transition-colors"
        />
        <button
          type="submit"
          disabled={submitting || !goal.trim()}
          className="px-3 py-1.5 rounded-md text-sm font-medium bg-accent text-void hover:bg-accent/90 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
        >
          {submitting ? "Creating..." : "Create Plan"}
        </button>
      </form>

      {error && !loading && <ErrorBanner message={error} onRetry={fetchPlans} />}

      {loading ? (
        <SectionSkeleton />
      ) : plans.length === 0 ? (
        <p className="text-sm text-text-muted text-center py-8">
          No plans yet. Enter a goal above to get started.
        </p>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {plans.map((plan) => (
            <TaskPlanCard key={plan.id} plan={plan} />
          ))}
        </div>
      )}
    </div>
  );
}

// ── Error Analysis Section ──────────────────────────────────────────────────

function ErrorAnalysisSection() {
  const [errorType, setErrorType] = useState("");
  const [errorMessage, setErrorMessage] = useState("");
  const [analyses, setAnalyses] = useState<ErrorAnalysis[]>([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchAnalyses = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await errors.list({ limit: 20 });
      setAnalyses(res);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load analyses");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchAnalyses();
  }, [fetchAnalyses]);

  const handleAnalyze = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault();
      if (!errorType.trim() || !errorMessage.trim()) return;
      setSubmitting(true);
      setError(null);
      try {
        const result = await errors.analyze(
          errorType.trim(),
          errorMessage.trim(),
          {},
        );
        setAnalyses((prev) => [result, ...prev]);
        setErrorType("");
        setErrorMessage("");
      } catch (e) {
        setError(e instanceof Error ? e.message : "Failed to analyze error");
      } finally {
        setSubmitting(false);
      }
    },
    [errorType, errorMessage],
  );

  return (
    <div className="space-y-4">
      <form onSubmit={handleAnalyze} className="space-y-3">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <input
            type="text"
            value={errorType}
            onChange={(e) => setErrorType(e.target.value)}
            placeholder="Error type (e.g. TypeError)"
            className="px-3 py-2 rounded-md bg-bg-surface border border-border-subtle text-text-primary text-sm placeholder:text-text-muted focus:outline-none focus:border-accent transition-colors"
          />
          <input
            type="text"
            value={errorMessage}
            onChange={(e) => setErrorMessage(e.target.value)}
            placeholder="Error message"
            className="px-3 py-2 rounded-md bg-bg-surface border border-border-subtle text-text-primary text-sm placeholder:text-text-muted focus:outline-none focus:border-accent transition-colors"
          />
        </div>
        <div className="flex justify-end">
          <button
            type="submit"
            disabled={submitting || !errorType.trim() || !errorMessage.trim()}
            className="px-3 py-1.5 rounded-md text-sm font-medium bg-accent text-void hover:bg-accent/90 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          >
            {submitting ? "Analyzing..." : "Analyze Error"}
          </button>
        </div>
      </form>

      {error && !loading && (
        <ErrorBanner message={error} onRetry={fetchAnalyses} />
      )}

      {loading ? (
        <SectionSkeleton />
      ) : analyses.length === 0 ? (
        <p className="text-sm text-text-muted text-center py-8">
          No error analyses yet. Submit an error above to get started.
        </p>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {analyses.map((a) => (
            <ErrorAnalysisCard key={a.id} analysis={a} />
          ))}
        </div>
      )}
    </div>
  );
}

// ── Hypothesis Section ──────────────────────────────────────────────────────

function HypothesisSection() {
  const [hypothesisText, setHypothesisText] = useState("");
  const [hypotheses, setHypotheses] = useState<Hypothesis[]>([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchHypotheses = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await hypothesis.listActive();
      setHypotheses(res);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load hypotheses");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchHypotheses();
  }, [fetchHypotheses]);

  const handleGenerate = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault();
      if (!hypothesisText.trim()) return;
      setSubmitting(true);
      setError(null);
      try {
        const result = await hypothesis.generate(hypothesisText.trim());
        setHypotheses((prev) => [result, ...prev]);
        setHypothesisText("");
      } catch (e) {
        setError(
          e instanceof Error ? e.message : "Failed to generate hypothesis",
        );
      } finally {
        setSubmitting(false);
      }
    },
    [hypothesisText],
  );

  return (
    <div className="space-y-4">
      <form onSubmit={handleGenerate} className="flex gap-3">
        <input
          type="text"
          value={hypothesisText}
          onChange={(e) => setHypothesisText(e.target.value)}
          placeholder="Enter a hypothesis..."
          className="flex-1 px-3 py-2 rounded-md bg-bg-surface border border-border-subtle text-text-primary text-sm placeholder:text-text-muted focus:outline-none focus:border-accent transition-colors"
        />
        <button
          type="submit"
          disabled={submitting || !hypothesisText.trim()}
          className="px-3 py-1.5 rounded-md text-sm font-medium bg-accent text-void hover:bg-accent/90 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
        >
          {submitting ? "Generating..." : "Generate"}
        </button>
      </form>

      {error && !loading && (
        <ErrorBanner message={error} onRetry={fetchHypotheses} />
      )}

      {loading ? (
        <SectionSkeleton />
      ) : hypotheses.length === 0 ? (
        <p className="text-sm text-text-muted text-center py-8">
          No active hypotheses. Enter one above to get started.
        </p>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {hypotheses.map((h) => (
            <HypothesisCard key={h.id} hypothesis={h} />
          ))}
        </div>
      )}
    </div>
  );
}

// ── Confidence Section ──────────────────────────────────────────────────────

function ConfidenceSection() {
  const [taskType, setTaskType] = useState("");
  const [results, setResults] = useState<ConfidenceResult[]>([]);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleEstimate = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault();
      if (!taskType.trim()) return;
      setSubmitting(true);
      setError(null);
      try {
        const result = await confidence.estimate(taskType.trim());
        setResults((prev) => [result, ...prev]);
        setTaskType("");
      } catch (e) {
        setError(
          e instanceof Error ? e.message : "Failed to estimate confidence",
        );
      } finally {
        setSubmitting(false);
      }
    },
    [taskType],
  );

  return (
    <div className="space-y-4">
      <form onSubmit={handleEstimate} className="flex gap-3">
        <input
          type="text"
          value={taskType}
          onChange={(e) => setTaskType(e.target.value)}
          placeholder="Task type to evaluate (e.g. code_generation, classification)..."
          className="flex-1 px-3 py-2 rounded-md bg-bg-surface border border-border-subtle text-text-primary text-sm placeholder:text-text-muted focus:outline-none focus:border-accent transition-colors"
        />
        <button
          type="submit"
          disabled={submitting || !taskType.trim()}
          className="px-3 py-1.5 rounded-md text-sm font-medium bg-accent text-void hover:bg-accent/90 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
        >
          {submitting ? "Estimating..." : "Estimate"}
        </button>
      </form>

      {error && (
        <div className="rounded-lg border border-danger/20 bg-danger/5 p-4">
          <p className="text-sm text-danger">{error}</p>
        </div>
      )}

      {results.length === 0 && !error ? (
        <p className="text-sm text-text-muted text-center py-8">
          No confidence estimates yet. Enter a task type above to get started.
        </p>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {results.map((r, i) => (
            <ConfidencePanel key={i} result={r} />
          ))}
        </div>
      )}
    </div>
  );
}

// ── Main Page ───────────────────────────────────────────────────────────────

export default function CognitionPage() {
  const { user, loading } = useAuth();
  const router = useRouter();
  const [activeTab, setActiveTab] = useState<Tab>("planning");

  useEffect(() => {
    if (!loading && !user) router.push("/auth");
  }, [user, loading, router]);

  if (loading || !user)
    return (
      <AppShell>
        <div className="max-w-5xl mx-auto space-y-6">
          <div className="h-6 w-24 bg-bg-elevated rounded animate-pulse" />
          <div className="h-4 w-40 bg-bg-elevated rounded animate-pulse" />
          <div className="flex gap-2">
            {tabs.map((t) => (
              <div
                key={t.key}
                className="h-8 w-28 bg-bg-elevated rounded animate-pulse"
              />
            ))}
          </div>
          <SectionSkeleton />
        </div>
      </AppShell>
    );

  return (
    <AppShell>
      <div className="max-w-5xl mx-auto space-y-6 animate-fade-in">
        <div>
          <h1 className="text-headline font-semibold text-text-primary">
            Cognition
          </h1>
          <p className="mt-1 text-sm text-text-secondary">
            Planning, error analysis, hypothesis testing, and confidence
            estimation
          </p>
        </div>

        {/* Tab bar */}
        <div className="flex gap-1 border-b border-border-subtle">
          {tabs.map((tab) => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={`px-3 py-2 text-sm font-medium transition-colors border-b-2 -mb-px ${
                activeTab === tab.key
                  ? "border-accent text-accent"
                  : "border-transparent text-text-muted hover:text-text-primary"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Tab content */}
        {activeTab === "planning" && <PlanningSection />}
        {activeTab === "errors" && <ErrorAnalysisSection />}
        {activeTab === "hypothesis" && <HypothesisSection />}
        {activeTab === "confidence" && <ConfidenceSection />}
      </div>
    </AppShell>
  );
}
